# S2S — Spec-to-Silicon

READ `CONTEXT.md` FIRST (1 page). It is the seed context for every session.
`docs/MASTER_SPEC.md` is a REFERENCE — load only the one section a task needs, never all of it.
`docs/HOW_TO_DRIVE_CLAUDE_CODE.md` explains the small-context, one-milestone-per-session method.

Hard rules (never break):
1. Never fake a tool result. A check passes only when the real tool ran and passed.
2. Never weaken a test/constraint or add a waiver to make something pass.
3. One milestone at a time (SESSION_PROMPTS.md). Acceptance tests (real runs) define "done".
4. Change only what the task needs.
5. If unsure, stop and ask — don't guess and build on the guess.
6. Every agent action emits an event (MASTER_SPEC Part 11). Record decisions in docs/DECISIONS.md.
7. Phase 0 = open-source tools + open SKY130 only. No commercial tools, NDAs, or customer data.
8. Check PHASE_GATES.md before building beyond the current phase. Do NOT build Phase 3
   work until a human marks the gate PASSED. Build only what the current phase needs.
