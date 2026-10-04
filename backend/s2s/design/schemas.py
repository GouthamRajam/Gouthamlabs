"""Design artifact schemas (MASTER_SPEC Appendix B.1, B.2, B.6) and the agents' answer formats.

Two kinds of schema live here:
- ARTIFACT schemas (SPEC_SCHEMA, ARCH_SCHEMA, TASK_RESULT_SCHEMA) validate what agents write
  (spec/spec.yaml, arch/arch.yaml, task.result). They follow Appendix B and are checked with
  `jsonschema` by s2s.design.checks: a deterministic check, not the model's opinion.
- ANSWER schemas (answer_schema(...)) are the JSON shape the model must answer in (Messages API
  structured outputs). They carry the artifacts as text files plus the B.6 task.result fields.
"""
from __future__ import annotations

REQ_TYPES = ["functional", "interface", "performance", "power", "area", "reset", "clock", "test"]
_WIDTH = {"oneOf": [{"type": "integer", "minimum": 1}, {"type": "string", "minLength": 1}]}

# --- B.1 spec.yaml ------------------------------------------------------------------------------
SPEC_SCHEMA = {
    "type": "object",
    "required": ["design", "version", "summary", "pdk", "std_cell_library", "target_clock_mhz",
                 "clocks", "resets", "interfaces", "requirements", "out_of_scope", "open_questions"],
    "properties": {
        "design": {"type": "string", "pattern": "^[a-z][a-z0-9_]*$"},
        "version": {"type": "integer", "minimum": 1},
        "summary": {"type": "string", "minLength": 10},
        "pdk": {"type": "string"},
        "std_cell_library": {"type": "string"},
        "target_clock_mhz": {"type": "number", "exclusiveMinimum": 0},
        "target_clock_note": {"type": "string"},
        "clocks": {"type": "array", "minItems": 1, "items": {
            "type": "object", "required": ["name", "freq_mhz"],
            "properties": {"name": {"type": "string"}, "freq_mhz": {"type": "number", "exclusiveMinimum": 0}}}},
        "resets": {"type": "array", "items": {
            "type": "object", "required": ["name", "active", "type"],
            "properties": {"name": {"type": "string"}, "active": {"enum": ["low", "high"]},
                           "type": {"enum": ["synchronous", "asynchronous"]}}}},
        "interfaces": {"type": "array", "minItems": 1, "items": {
            "type": "object", "required": ["name", "dir", "width"],
            "properties": {"name": {"type": "string", "pattern": "^[A-Za-z_][A-Za-z0-9_]*$"},
                           "dir": {"enum": ["in", "out", "inout"]},
                           "width": {"type": "integer", "minimum": 1},
                           "protocol": {"type": "string"}, "async": {"type": "boolean"},
                           "clock_domain": {"type": "string"},
                           "reset_value": {"type": ["integer", "string"]},
                           "values": {"type": "object"}, "description": {"type": "string"}}}},
        "requirements": {"type": "array", "minItems": 1, "items": {
            "type": "object", "required": ["id", "type", "text", "acceptance"],
            "properties": {"id": {"type": "string", "pattern": "^REQ-[0-9]{3}$"},
                           "type": {"enum": REQ_TYPES},
                           "text": {"type": "string", "minLength": 5},
                           "acceptance": {"type": "string", "minLength": 5},
                           "note": {"type": "string"}}}},
        "out_of_scope": {"type": "array", "items": {"type": "string"}},
        "open_questions": {"type": "array", "items": {"type": ["string", "object"]}},
    },
}

# --- B.2 arch.yaml ------------------------------------------------------------------------------
_PORT = {"type": "object", "required": ["name", "dir", "width"],
         "properties": {"name": {"type": "string"}, "dir": {"enum": ["in", "out", "inout"]}, "width": _WIDTH}}
ARCH_SCHEMA = {
    "type": "object",
    "required": ["design", "top", "modules", "connections", "cdc", "state_machines", "ppa_estimate",
                 "rationale"],
    "properties": {
        "design": {"type": "string"},
        "top": {"type": "string"},
        "modules": {"type": "array", "minItems": 1, "items": {
            "type": "object", "required": ["name", "kind", "implements"],
            "properties": {
                "name": {"type": "string", "pattern": "^[a-z][a-z0-9_]*$"},
                # which RTL team writes it (Reid assigns by this): Ada / Ada-C / Ada-I
                "kind": {"enum": ["datapath", "control", "interface"]},
                "ports_from_spec": {"type": "boolean"},
                "params": {"type": "object", "additionalProperties": {"type": "integer"}},
                "ports": {"type": "array", "items": _PORT},
                "instances": {"type": "array", "items": {"type": "string"}},
                "implements": {"type": "array", "items": {"type": "string", "pattern": "^REQ-[0-9]{3}$"}},
                "max_logic_depth": {"type": "integer", "minimum": 1},
                "description": {"type": "string"}}}},
        "connections": {"type": "array", "items": {
            "type": "object", "required": ["from", "to"],
            "properties": {"from": {"type": "string"},
                           "to": {"type": "array", "minItems": 1, "items": {"type": "string"}}}}},
        "cdc": {"type": "array", "items": {
            "type": "object", "required": ["signal", "from", "to", "synchronizer"],
            "properties": {"signal": {"type": "string"}, "from": {"type": "string"},
                           "to": {"type": "string"}, "synchronizer": {"type": "string"}}}},
        "state_machines": {"type": "array", "items": {
            "type": "object", "required": ["module", "states"],
            "properties": {"module": {"type": "string"},
                           "states": {"type": "array", "minItems": 2, "items": {"type": "string"}}}}},
        "ppa_estimate": {"type": "object", "required": ["cells", "critical_path_levels", "slack_margin_pct"],
                         "properties": {"cells": {"type": "integer", "minimum": 1},
                                        "critical_path_levels": {"type": "integer", "minimum": 1},
                                        "slack_margin_pct": {"type": "number"}}},
        "rationale": {"type": "array", "minItems": 1, "items": {"type": "string"}},
        "verification_hooks": {"type": "array", "items": {"type": "string"}},
    },
}

# --- B.6 task.result ----------------------------------------------------------------------------
TASK_RESULT_SCHEMA = {
    "type": "object",
    "required": ["task_id", "status", "summary", "outputs", "checks_run", "assumptions", "open_issues",
                 "messages", "self_assessment"],
    "properties": {
        "task_id": {"type": "string"},
        "status": {"enum": ["success", "failure", "escalate"]},
        "summary": {"type": "string"},
        "outputs": {"type": "array", "items": {"type": "object", "required": ["path", "sha256"],
                                                "properties": {"path": {"type": "string"},
                                                               "sha256": {"type": "string"}}}},
        "checks_run": {"type": "array", "items": {"type": "string"}},
        "assumptions": {"type": "array", "items": {"type": "string"}},
        "open_issues": {"type": "array", "items": {"type": "string"}},
        "messages": {"type": "array"},
        "self_assessment": {"type": "object", "required": ["confidence", "reason"],
                            "properties": {"confidence": {"enum": ["high", "medium", "low"]},
                                           "reason": {"type": "string"}}},
    },
}

# --- answer formats (structured outputs: every object closed, every field required) -------------
def _obj(props: dict) -> dict:
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


_STR = {"type": "string"}
_STRS = {"type": "array", "items": _STR}
FILES = {"type": "array", "items": _obj({"path": _STR, "content": _STR})}
# The agent's own part of B.6; the runtime adds task_id, output hashes and the checks it ran.
RESULT_FIELDS = {
    "plan": _STR,  # the short plan (Plan -> Act -> Check -> Report), emitted as a `plan` event
    "status": {"type": "string", "enum": ["success", "failure", "escalate"]},
    "summary": _STR,
    "assumptions": _STRS,
    "open_issues": _STRS,
    "self_assessment": _obj({"confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                             "reason": _STR}),
}
FINDING = _obj({
    "severity": {"type": "string", "enum": ["blocking", "major", "minor"]},
    "target": _STR,  # artifact and location, e.g. "spec/spec.yaml: REQ-003"
    "what": _STR,
    "evidence": _STR,
    "suggested_action": _STR,
})


def answer_schema(**extra: dict) -> dict:
    """The JSON shape an agent answers in: its B.6 fields plus `extra` (files, findings...)."""
    return _obj({**RESULT_FIELDS, **extra})


WRITER_ANSWER = answer_schema(files=FILES)  # Iris, Kepler, Ada: write files
REVIEW_ANSWER = answer_schema(findings={"type": "array", "items": FINDING})  # Sentinel
REPORT_ANSWER = answer_schema(report_markdown=_STR)  # Ivy, Pascal, Watt
SAGE_ANSWER = answer_schema(
    report_markdown=_STR,
    lessons={"type": "array", "items": _obj({"title": _STR, "symptom": _STR, "root_cause": _STR,
                                              "fix": _STR, "detect_earlier": _STR, "tags": _STRS})})


# --- M0.6: test plan (Vera) and the verification answer formats ------------------------------------
_IDENT = {"type": "string", "pattern": "^[A-Za-z_][A-Za-z0-9_]*$"}
TESTPLAN_SCHEMA = {
    "type": "object",
    "required": ["design", "clock", "reset", "transaction", "requirements", "coverage_bins"],
    "properties": {
        "design": {"type": "string"},
        "clock": _IDENT,
        "reset": {"type": "object", "required": ["name", "active"],
                  "properties": {"name": _IDENT, "active": {"enum": ["low", "high"]}}},
        # the reference-model transaction: input fields with bit widths, and the outputs it predicts
        "transaction": {"type": "object", "required": ["fields", "outputs"],
                        "properties": {"description": {"type": "string"},
                                       "fields": {"type": "object", "minProperties": 1,
                                                  "additionalProperties": {"type": "integer", "minimum": 1, "maximum": 64}},
                                       "outputs": {"type": "array", "minItems": 1, "items": _IDENT},
                                       "reset_every": {"type": "integer", "minimum": 0}}},
        "requirements": {"type": "array", "minItems": 1, "items": {
            "type": "object", "required": ["id", "tests"],
            "properties": {"id": {"type": "string", "pattern": "^REQ-[0-9]{3}$"},
                           "tests": {"type": "array", "minItems": 1, "items": {
                               "type": "object", "required": ["name", "kind", "description"],
                               "properties": {"name": {"type": "string", "pattern": "^test_[a-z0-9_]+$"},
                                              "kind": {"enum": ["directed", "random", "formal"]},
                                              "description": {"type": "string"}}}}}}},
        "coverage_bins": {"type": "array", "minItems": 1, "items": {
            "type": "object", "required": ["name", "expr", "req"],
            "properties": {"name": _IDENT, "expr": {"type": "string", "minLength": 1},
                           "req": {"type": "string", "pattern": "^REQ-[0-9]{3}$"}}}},
    },
}

DEX_ANSWER = answer_schema(bugs={"type": "array", "items": _obj({
    "id": _STR,
    "classification": {"type": "string", "enum": ["DESIGN", "TEST", "SPEC"]},
    "failures": _STRS,          # failing test names / formal property names this bug explains
    "requirement": _STR,
    "root_cause": _STR,          # one sentence
    "evidence": _STR,            # seed, cycle, expected vs actual, waveform window
    "expected": _STR,
    "actual": _STR,
    "module": _STR,              # DESIGN: the RTL module to fix ("" otherwise)
    "suggested_fix": _STR,
})})
ADJUDICATE_ANSWER = answer_schema(
    decision={"type": "string", "enum": ["model_a", "model_b", "spec_question"]},
    reason=_STR, spec_question=_STR)
