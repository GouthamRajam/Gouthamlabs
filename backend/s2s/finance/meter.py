"""Usage metering and budget controls (MASTER_SPEC Part 19.2-19.3).

Every metered call writes one `usage_records` row with its cost, committed immediately in
its own transaction: money spent stays recorded even if the agent step that spent it later
fails or the process crashes. Usage totals are always computed from usage_records (the
single source of truth), never kept as a separate counter.

Budget controls, checked after every record:
  - task budget (tokens and tool runs, config/budgets.yaml): one `budget.warning` at the
    soft threshold; at 100% a hard stop (BudgetExceeded): the task pauses and escalates,
    it never silently continues;
  - run budget (USD, budgets.yaml per_run): `budget.alert` at each level in finance.yaml
    alerts_pct, each with a budget_events row.
"""
from __future__ import annotations

import datetime as dt

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from s2s.config import budgets as budgets_cfg
from s2s.config import finance, spend_caps
from s2s.db.models import Budget, BudgetEvent, Event, Run, UsageRecord
from s2s.db.session import session as db_session
from s2s.events.bus import emit
from s2s.ids import new_id


@dataclass(frozen=True)
class TaskRef:
    """The task a cost is charged to (plain values, usable across sessions)."""
    id: str
    run_id: str
    agent_id: str
    stage: str
    team_id: str | None
    budget: dict


class BudgetExceeded(RuntimeError):
    def __init__(self, task_id: str, what: str, used: float, limit: float):
        super().__init__(f"task {task_id} hit its {what} budget: {used:g} of {limit:g}")
        self.task_id, self.what, self.used, self.limit = task_id, what, used, limit


class SpendCapReached(BudgetExceeded):
    """A Settings spend cap (Part 28.3) is reached: the run stops, no overage."""
    def __init__(self, task_id: str, what: str, used: float, limit: float):
        cap = f"{limit:,.2f}" if round(limit, 2) == limit else f"{limit:g}"
        RuntimeError.__init__(self, f"{what} reached: ${used:.4f} spent of ${cap}")
        self.task_id, self.what, self.used, self.limit = task_id, what, used, limit


def task_budget(agent_id: str) -> dict:
    cfg = budgets_cfg()
    return {**cfg["defaults"], **(cfg.get("per_agent", {}).get(agent_id) or {})}


def price(model: str) -> tuple[Decimal, Decimal]:
    """USD per input token, per output token. An unpriced model raises (never metered at $0)."""
    p = finance()["model_prices"][model]
    return Decimal(str(p["input_per_mtok"])) / 1_000_000, Decimal(str(p["output_per_mtok"])) / 1_000_000


def record_llm(task: TaskRef, model: str, input_tokens: int, output_tokens: int,
               call_id: str) -> UsageRecord:
    p_in, p_out = price(model)
    cost = p_in * input_tokens + p_out * output_tokens
    qty = input_tokens + output_tokens
    rec = UsageRecord(
        id=new_id("use"), task_id=task.id, agent_id=task.agent_id, source="llm", quantity=qty,
        unit="tokens", unit_cost=(cost / qty) if qty else Decimal(0), cost_usd=cost,
        run_id=task.run_id, model=model,
        detail={"call_id": call_id, "input_tokens": input_tokens, "output_tokens": output_tokens},
    )
    with db_session() as s:
        s.add(rec)
    check_budgets(task)
    return rec


def record_llm_untasked(agent_id: str, model: str, input_tokens: int, output_tokens: int,
                        call_id: str, purpose: str) -> UsageRecord:
    """A model call made outside any task (e.g. Settings -> Test connection): still metered."""
    p_in, p_out = price(model)
    cost = p_in * input_tokens + p_out * output_tokens
    qty = input_tokens + output_tokens
    rec = UsageRecord(id=new_id("use"), agent_id=agent_id, source="llm", quantity=qty, unit="tokens",
                      unit_cost=(cost / qty) if qty else Decimal(0), cost_usd=cost, model=model,
                      detail={"call_id": call_id, "input_tokens": input_tokens,
                              "output_tokens": output_tokens, "purpose": purpose})
    with db_session() as s:
        s.add(rec)
    return rec


def spend_so_far(s: Session, run_id: str | None = None) -> dict:
    """Spend today (since 00:00 UTC, all work) and, given a run, its design's total spend."""
    midnight = dt.datetime.now(dt.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    out = {"today_usd": Decimal(str(s.scalar(select(func.coalesce(func.sum(UsageRecord.cost_usd), 0))
                                             .where(UsageRecord.ts >= midnight))))}
    if run_id:
        design_runs = select(Run.id).where(Run.design_id == select(Run.design_id).where(Run.id == run_id)
                                           .scalar_subquery())
        out["design_usd"] = Decimal(str(s.scalar(select(func.coalesce(func.sum(UsageRecord.cost_usd), 0))
                                                 .where(UsageRecord.run_id.in_(design_runs)))))
    return out


def check_spend_caps(task: TaskRef) -> None:
    """Raise SpendCapReached if the daily or per-design cap (config/finance.yaml spend_caps) is
    reached. Called before every model call and after every metered cost."""
    caps = spend_caps()
    with db_session() as s:
        spent = spend_so_far(s, task.run_id)
    if caps.get("daily_usd") is not None and spent["today_usd"] >= Decimal(str(caps["daily_usd"])):
        raise SpendCapReached(task.id, "daily spend cap", float(spent["today_usd"]), float(caps["daily_usd"]))
    if caps.get("per_design_usd") is not None and spent["design_usd"] >= Decimal(str(caps["per_design_usd"])):
        raise SpendCapReached(task.id, "per-design spend cap", float(spent["design_usd"]),
                              float(caps["per_design_usd"]))


def record_compute(task: TaskRef, cpu_seconds: float, tool: str) -> UsageRecord:
    rate = Decimal(str(finance()["compute_usd_per_cpu_hour"])) / 3600
    rec = UsageRecord(id=new_id("use"), task_id=task.id, agent_id=task.agent_id, source="compute",
                      quantity=cpu_seconds, unit="cpu_seconds", unit_cost=rate,
                      cost_usd=rate * Decimal(str(cpu_seconds)), run_id=task.run_id,
                      detail={"tool": tool})
    with db_session() as s:
        s.add(rec)
    check_budgets(task)
    return rec


def task_usage(s: Session, task_id: str) -> dict:
    """Totals for one task, computed from usage_records."""
    rows = s.execute(select(UsageRecord.source, func.count(), func.coalesce(func.sum(UsageRecord.quantity), 0),
                            func.coalesce(func.sum(UsageRecord.cost_usd), 0))
                     .where(UsageRecord.task_id == task_id).group_by(UsageRecord.source)).all()
    by = {src: (n, qty, cost) for src, n, qty, cost in rows}
    return {
        "model_calls": by.get("llm", (0, 0, 0))[0],
        "tokens": int(by.get("llm", (0, 0, 0))[1]),
        "tool_runs": by.get("compute", (0, 0, 0))[0],
        "cost_usd": float(sum(Decimal(str(c)) for _, _, c in by.values())),
    }


def check_budgets(task: TaskRef) -> None:
    with db_session() as s:
        usage = task_usage(s, task.id)
        exceeded = None
        for what, limit in (("tokens", task.budget.get("max_tokens")),
                            ("tool_runs", task.budget.get("max_tool_runs"))):
            if not limit:
                continue
            used = usage[what]
            if used >= limit:
                exceeded = exceeded or BudgetExceeded(task.id, what, used, limit)
            elif used >= limit * float(budgets_cfg().get("task_warning_pct", 80)) / 100 \
                    and not _warned(s, task.id, what):
                emit(s, "budget.warning", f"{task.agent_id}: {what} at {used / limit:.0%} of task budget "
                     f"({used:g} of {limit:g})", run_id=task.run_id, agent_id=task.agent_id,
                     task_id=task.id, stage=task.stage, team=task.team_id,
                     detail={"budget": what, "used": used, "limit": limit,
                             "pct": round(100 * used / limit, 1)})
        _check_run_budget(s, task)
    if exceeded:
        raise exceeded
    check_spend_caps(task)


def _warned(s: Session, task_id: str, what: str) -> bool:
    return s.scalar(select(func.count()).select_from(Event).where(
        Event.type == "budget.warning", Event.task_id == task_id,
        Event.detail["budget"].astext == what)) > 0


def ensure_run_budget(s: Session, run_id: str) -> Budget:
    b = s.scalar(select(Budget).where(Budget.scope == "run", Budget.scope_id == run_id))
    if b is None:
        per_run = budgets_cfg()["per_run"]
        b = Budget(id=new_id("bud"), scope="run", scope_id=run_id,
                   limit_usd=Decimal(str(per_run["max_cost_usd"])),
                   soft_pct=float(per_run.get("alert_at_pct", 80)),
                   hard_limit_usd=Decimal(str(per_run["max_cost_usd"])))
        s.add(b)
        s.flush()
    return b


def _check_run_budget(s: Session, task: TaskRef) -> None:
    b = ensure_run_budget(s, task.run_id)
    spent = Decimal(str(s.scalar(select(func.coalesce(func.sum(UsageRecord.cost_usd), 0))
                                 .where(UsageRecord.run_id == task.run_id))))
    limit = Decimal(str(b.limit_usd))
    done = {int(a) for (a,) in s.execute(select(BudgetEvent.amount).where(
        BudgetEvent.budget_id == b.id, BudgetEvent.type == "warning"))}
    for pct in finance().get("alerts_pct", [80, 100]):
        if spent >= limit * Decimal(pct) / 100 and pct not in done:
            s.add(BudgetEvent(id=new_id("bev"), budget_id=b.id, type="warning", amount=pct))
            emit(s, "budget.alert", f"Run {task.run_id} spend ${spent:.4f} reached {pct}% of its "
                 f"${limit} budget", run_id=task.run_id, agent_id="Penny", team="finops",
                 detail={"scope": "run", "scope_id": task.run_id, "spent_usd": float(spent),
                         "limit_usd": float(limit), "pct": pct})
