"""Core tables (MASTER_SPEC Part 7.6) and finance tables (Part 19.5).

Columns beyond the spec's key columns are noted inline; they are what the orchestrator
needs to make tasks resumable and to detect stalls.
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any

from sqlalchemy import (BigInteger, Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index,
                        Integer, Numeric, String, Text, func)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    type_annotation_map = {dict[str, Any]: JSONB, list[Any]: JSONB}


def _now() -> Mapped[dt.datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    owner: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[dt.datetime] = _now()


class Design(Base):
    __tablename__ = "designs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    pdk: Mapped[str] = mapped_column(String, nullable=False, default="sky130A")
    target_clock_mhz: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, nullable=False, default="created")
    request_text: Mapped[str | None] = mapped_column(Text)  # the design request (POST /designs)
    options: Mapped[dict[str, Any]] = mapped_column(default=dict)
    created_at: Mapped[dt.datetime] = _now()


class Run(Base):
    __tablename__ = "runs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    design_id: Mapped[str] = mapped_column(ForeignKey("designs.id"), nullable=False, index=True)
    started_at: Mapped[dt.datetime] = _now()
    ended_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending", index=True)
    current_stage: Mapped[str | None] = mapped_column(String)
    config_hash: Mapped[str | None] = mapped_column(String)
    stages: Mapped[list[Any]] = mapped_column(default=list)  # stage names this run covers
    agent_kind: Mapped[str] = mapped_column(String, nullable=False, default="dummy")


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending", index=True)
    inputs: Mapped[dict[str, Any]] = mapped_column(default=dict)
    outputs: Mapped[dict[str, Any]] = mapped_column(default=dict)
    budget: Mapped[dict[str, Any]] = mapped_column(default=dict)
    usage: Mapped[dict[str, Any]] = mapped_column(default=dict)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    # --- orchestration (resume + stall detection) ---
    title: Mapped[str] = mapped_column(String, nullable=False, default="")
    seq: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # order within the run
    depends_on: Mapped[list[Any]] = mapped_column(default=list)  # task ids
    team_id: Mapped[str | None] = mapped_column(String)
    checkpoint: Mapped[dict[str, Any]] = mapped_column(default=dict)  # last completed step + state
    expected_step_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=60.0)
    evidence_signal: Mapped[str | None] = mapped_column(String)  # measurable progress signal
    percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ready_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))  # assignment SLA
    assigned_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    last_progress_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    stalled_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    escalated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    last_checkin_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    lease_owner: Mapped[str | None] = mapped_column(String)  # orchestrator instance running it


class Artifact(Base):
    __tablename__ = "artifacts"
    sha256: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    path: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_by_task: Mapped[str | None] = mapped_column(ForeignKey("tasks.id"))
    created_at: Mapped[dt.datetime] = _now()


class Check(Base):
    __tablename__ = "checks"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), nullable=False, index=True)
    check_name: Mapped[str] = mapped_column(String, nullable=False)
    tool: Mapped[str] = mapped_column(String, nullable=False)
    command: Mapped[str | None] = mapped_column(Text)
    tool_version: Mapped[str | None] = mapped_column(String)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    metrics: Mapped[dict[str, Any]] = mapped_column(default=dict)
    log_artifact: Mapped[str | None] = mapped_column(String)


class CheckParam(Base):
    """One measured parameter of a check, against its limit (Part 27.6). Many rows per check
    (per rule, per layer, per corner). run_id and stage are copied from the check's task so
    the cockpit can filter by (run_id, stage) without joins."""
    __tablename__ = "check_params"
    __table_args__ = (
        CheckConstraint("comparison IN ('<=', '>=', '==')", name="ck_check_params_comparison"),
        Index("ix_check_params_run_id_stage", "run_id", "stage"),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    check_id: Mapped[str] = mapped_column(ForeignKey("checks.id"), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    stage: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    measured_value: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    limit_value: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    comparison: Mapped[str] = mapped_column(String(2), nullable=False)
    unit: Mapped[str | None] = mapped_column(String)
    layer_or_corner: Mapped[str | None] = mapped_column(String)
    pass_: Mapped[bool] = mapped_column("pass", Boolean, nullable=False)  # "pass" is a Python keyword


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    from_agent: Mapped[str] = mapped_column(String, nullable=False)
    to_agent: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(default=dict)
    ts: Mapped[dt.datetime] = _now()


class Event(Base):
    """Part 11.1 event schema, persisted (the Redis stream carries the same JSON)."""
    __tablename__ = "events"
    id: Mapped[str] = mapped_column(String, primary_key=True)  # time-sortable evt_<ulid>
    ts: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    run_id: Mapped[str | None] = mapped_column(String, index=True)
    design_id: Mapped[str | None] = mapped_column(String)
    team: Mapped[str | None] = mapped_column(String)
    agent_id: Mapped[str | None] = mapped_column(String, index=True)
    agent_name: Mapped[str | None] = mapped_column(String)
    stage: Mapped[str | None] = mapped_column(String)
    task_id: Mapped[str | None] = mapped_column(String, index=True)
    type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    status: Mapped[str | None] = mapped_column(String)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    detail: Mapped[dict[str, Any]] = mapped_column(default=dict)
    to_agent_id: Mapped[str | None] = mapped_column(String)
    progress: Mapped[float | None] = mapped_column(Float)


class Gate(Base):
    __tablename__ = "gates"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    gate: Mapped[str] = mapped_column(String, nullable=False)  # G1..G4
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending", index=True)
    packet_id: Mapped[str | None] = mapped_column(String)
    reviewer: Mapped[str | None] = mapped_column(String)
    decision: Mapped[str | None] = mapped_column(String)
    comments: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    after_stage: Mapped[str | None] = mapped_column(String)


class EvidencePacket(Base):
    __tablename__ = "evidence_packets"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String, nullable=False)
    manifest: Mapped[dict[str, Any]] = mapped_column(default=dict)
    sha256: Mapped[str | None] = mapped_column(String)


class Requirement(Base):
    __tablename__ = "requirements"
    id: Mapped[str] = mapped_column(String, primary_key=True)  # REQ-###
    design_id: Mapped[str] = mapped_column(ForeignKey("designs.id"), primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str | None] = mapped_column(String)
    acceptance: Mapped[str | None] = mapped_column(Text)


class TraceLink(Base):
    __tablename__ = "trace_links"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    requirement_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    artifact_sha: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str | None] = mapped_column(String)
    link_type: Mapped[str] = mapped_column(String, nullable=False)  # rtl/test/coverage/timing


class Knowledge(Base):
    """`embedding` (pgvector) is added with the knowledge base in M0.5 (see DECISIONS.md)."""
    __tablename__ = "knowledge"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list[Any]] = mapped_column(default=list)
    source_run: Mapped[str | None] = mapped_column(String)


class Finding(Base):
    __tablename__ = "findings"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    from_agent: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    target_artifact: Mapped[str | None] = mapped_column(String)
    location: Mapped[str | None] = mapped_column(String)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="open")


class OrgUnit(Base):
    __tablename__ = "org_units"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String, nullable=False)  # division/department/team
    name: Mapped[str] = mapped_column(String, nullable=False)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("org_units.id"))
    manager_agent_id: Mapped[str | None] = mapped_column(String)  # director/manager/team lead
    human_owner: Mapped[str | None] = mapped_column(String)
    zone: Mapped[str | None] = mapped_column(String)
    instances: Mapped[int | None] = mapped_column(Integer)  # engineer instances at scale (teams)
    phase: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # phase it starts in


class Heartbeat(Base):
    __tablename__ = "heartbeats"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), nullable=False, index=True)
    ts: Mapped[dt.datetime] = _now()
    percent: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_signal: Mapped[str] = mapped_column(String, nullable=False)
    step: Mapped[str | None] = mapped_column(String)
    blockers: Mapped[list[Any]] = mapped_column(default=list)


class TeamMetric(Base):
    __tablename__ = "team_metrics"
    team_id: Mapped[str] = mapped_column(String, primary_key=True)
    date: Mapped[dt.date] = mapped_column(primary_key=True)
    throughput: Mapped[float | None] = mapped_column(Float)
    cycle_time_p50: Mapped[float | None] = mapped_column(Float)
    first_pass_yield: Mapped[float | None] = mapped_column(Float)
    rework_rate: Mapped[float | None] = mapped_column(Float)
    sla_hit_rate: Mapped[float | None] = mapped_column(Float)
    escaped_defects: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[float | None] = mapped_column(Numeric(12, 6))


class ResearchBrief(Base):
    __tablename__ = "research_briefs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    author_agent: Mapped[str] = mapped_column(String, nullable=False)
    topic: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list[Any]] = mapped_column(default=list)
    confidence: Mapped[float | None] = mapped_column(Float)
    ts: Mapped[dt.datetime] = _now()


# --- Finance (Part 19.5) ---------------------------------------------------------------------
class UsageRecord(Base):
    __tablename__ = "usage_records"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    ts: Mapped[dt.datetime] = _now()
    task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id"), index=True)
    agent_id: Mapped[str | None] = mapped_column(String, index=True)
    source: Mapped[str] = mapped_column(String, nullable=False)  # llm/compute/license/storage
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(18, 12), nullable=False)
    cost_usd: Mapped[float] = mapped_column(Numeric(14, 8), nullable=False)
    run_id: Mapped[str | None] = mapped_column(String, index=True)  # for run/design roll-ups
    model: Mapped[str | None] = mapped_column(String)  # llm records: which model
    detail: Mapped[dict[str, Any]] = mapped_column(default=dict)  # e.g. input/output tokens, call id


class Budget(Base):
    __tablename__ = "budgets"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    scope: Mapped[str] = mapped_column(String, nullable=False)  # task/run/team/month
    scope_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    limit_usd: Mapped[float] = mapped_column(Numeric(14, 6), nullable=False)
    soft_pct: Mapped[float] = mapped_column(Float, nullable=False, default=80.0)
    hard_limit_usd: Mapped[float | None] = mapped_column(Numeric(14, 6))


class Credit(Base):
    __tablename__ = "credits"
    provider: Mapped[str] = mapped_column(String, primary_key=True)
    balance: Mapped[float] = mapped_column(Numeric(14, 6), nullable=False)
    expires_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[dt.datetime] = _now()


class BudgetEvent(Base):
    __tablename__ = "budget_events"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    budget_id: Mapped[str] = mapped_column(ForeignKey("budgets.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String, nullable=False)  # warning/limit/approval
    amount: Mapped[float] = mapped_column(Numeric(14, 6), nullable=False)
    decided_by: Mapped[str | None] = mapped_column(String)
    ts: Mapped[dt.datetime] = _now()


# --- Trajectory record (Phase 1: the agents' decision record is the product) ---------------------------------
ANNOTATION_LABELS = ("false_alarm", "operator_influenced", "manual_intervention", "legacy_unstructured")


class Annotation(Base):
    """An append-only label on a record of the trajectory (an event, check, model call, bridge request, task or run):
    e.g. a stall event that was a false alarm, or a task an operator influenced. History is never edited; a label is
    added with its reason and author, so consumers of the record can filter (pure-autonomous vs operator-influenced)."""
    __tablename__ = "annotations"
    id: Mapped[str] = mapped_column(String, primary_key=True)  # ann_<ulid>
    ts: Mapped[dt.datetime] = _now()
    target_kind: Mapped[str] = mapped_column(String, nullable=False)
    target_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    run_id: Mapped[str | None] = mapped_column(String, index=True)
    label: Mapped[str] = mapped_column(String, nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    detail: Mapped[dict[str, Any]] = mapped_column(default=dict)


class Analysis(Base):
    """An analysis made outside the flow's recorded steps (e.g. a what-if derated STA on a copy of a routed netlist),
    linked to its run with the hashes of its inputs, the method and the results. Never a recorded signoff."""
    __tablename__ = "analyses"
    id: Mapped[str] = mapped_column(String, primary_key=True)  # ana_<ulid>
    ts: Mapped[dt.datetime] = _now()
    run_id: Mapped[str | None] = mapped_column(String, index=True)
    task_id: Mapped[str | None] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String, nullable=False)  # what_if | diagnosis
    title: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False, default="what-if, not a recorded signoff")
    method: Mapped[str] = mapped_column(Text, nullable=False)
    inputs: Mapped[list[Any]] = mapped_column(default=list)    # [{path, sha256}]
    results: Mapped[dict[str, Any]] = mapped_column(default=dict)
    sources: Mapped[list[Any]] = mapped_column(default=list)
    author: Mapped[str] = mapped_column(String, nullable=False)
    operator_influenced: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    location: Mapped[str | None] = mapped_column(String)       # where the files are
