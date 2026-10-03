"""Org structure from config/management.yaml (MASTER_SPEC Part 6.2-6.4).

`load_org()` flattens the YAML into org units; `sync_org(session)` writes them to the
org_units table (idempotent). Agent ids are the agent names used in the YAML.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

from sqlalchemy.orm import Session

from s2s.config import management
from s2s.db.models import OrgUnit


@dataclass(frozen=True)
class Unit:
    id: str
    kind: str  # division / department / team
    name: str
    parent_id: str | None
    manager_agent_id: str | None  # director (division), manager (department), lead (team)
    human_owner: str | None
    zone: str | None
    instances: int | None
    phase: int


@dataclass
class Org:
    units: list[Unit] = field(default_factory=list)

    def by_id(self, uid: str) -> Unit:
        return next(u for u in self.units if u.id == uid)

    def teams(self) -> list[Unit]:
        return [u for u in self.units if u.kind == "team"]

    def division_of(self, uid: str) -> Unit:
        u = self.by_id(uid)
        while u.kind != "division":
            u = self.by_id(u.parent_id)
        return u

    def team_of_agent(self, agent_id: str) -> Unit | None:
        return next((u for u in self.units if u.kind == "team" and u.manager_agent_id == agent_id), None)

    def agents(self) -> list[dict]:
        """Every named agent: directors, department managers, team leads (one row each)."""
        roles = {"division": "director", "department": "manager", "team": "team_lead"}
        seen: dict[str, dict] = {}
        for u in self.units:
            if u.manager_agent_id and u.manager_agent_id not in seen:
                seen[u.manager_agent_id] = {
                    "id": u.manager_agent_id, "role": roles[u.kind], "unit_id": u.id,
                    "unit_name": u.name, "division_id": self.division_of(u.id).id, "phase": u.phase,
                }
        return list(seen.values())

    def manager_chain(self, team_id: str) -> list[str]:
        """Agents above a team, nearest first (department manager, then director)."""
        chain, u = [], self.by_id(team_id)
        while u.parent_id:
            u = self.by_id(u.parent_id)
            if u.manager_agent_id:
                chain.append(u.manager_agent_id)
        return chain


def _team(t: dict, parent: str, zone: str | None, phase: int) -> Unit:
    return Unit(t["id"], "team", t["name"], parent, t["lead"], None, zone, int(t["instances"]),
                int(t.get("phase", phase)))


@lru_cache(maxsize=1)
def load_org() -> Org:
    org = Org()
    for d in management()["org"]["divisions"]:
        phase = int(d.get("phase", 0))
        org.units.append(Unit(d["id"], "division", d["name"], None, d.get("director"),
                              d.get("human_owner"), d.get("zone"), None, phase))
        for t in d.get("teams", []):
            org.units.append(_team(t, d["id"], d.get("zone"), phase))
        for dep in d.get("departments", []):
            org.units.append(Unit(dep["id"], "department", dep["name"], d["id"], dep.get("manager"),
                                  dep.get("human_owner"), dep.get("zone"), None,
                                  int(dep.get("phase", phase))))
            for t in dep["teams"]:
                org.units.append(_team(t, dep["id"], dep.get("zone"), phase))
    return org


def sync_org(session: Session) -> int:
    """Upsert org units from config into org_units. Returns the number of units."""
    org = load_org()
    for u in org.units:  # parents come before children in load order
        session.merge(OrgUnit(id=u.id, kind=u.kind, name=u.name, parent_id=u.parent_id,
                              manager_agent_id=u.manager_agent_id, human_owner=u.human_owner,
                              zone=u.zone, instances=u.instances, phase=u.phase))
        session.flush()
    return len(org.units)
