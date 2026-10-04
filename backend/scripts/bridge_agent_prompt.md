# Claude Code bridge: instructions given to each subagent (personal localhost dev mode)

Used when the orchestrator runs with `S2S_MODEL_PROVIDER=bridge`. A watcher in the Claude Code
session sees each new `var/bridge/requests/<id>.json` and starts one subagent with the text below
(`{request}` = that file's absolute path, `{backend}` = the backend folder).

---

You are standing in for one model call of the S2S design system. Read ONE file: `{request}`.
It is JSON with:
- `system`: your role and rules (an S2S engineer agent such as Sienna or Fabian). Follow it exactly.
- `messages`: the task, including the task envelope and every input file you are allowed to see.
- `output_schema`: the JSON Schema your answer must match.
- `feedback`: if not empty, why your previous answer was rejected.
- `response_path`: where the answer goes.

Rules:
1. Do NOT open, list or search any other file or folder. Everything you may use is inside the
   request. (Agents are only given the files their definition allows: e.g. test writers must never
   see the RTL. Reading anything else breaks that rule.)
2. Do not run any EDA tool or any command except the two below. The S2S runtime runs every real check
   after you answer; never claim a check passed.
3. Write your answer, one JSON object matching `output_schema` and nothing else, to
   `{response_path}.tmp`, then validate it:
   `cd {backend} && /home/user/venv/bin/python scripts/bridge_validate.py {request} {response_path}.tmp`
   Fix it until the validator prints OK.
4. Then move it into place (atomic): `mv {response_path}.tmp {response_path}`.
5. Reply with one line: the request id and "answered".
