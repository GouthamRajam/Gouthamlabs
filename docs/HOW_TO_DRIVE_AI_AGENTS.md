# How to drive AI coding agents without the big-context error problem

The worry is correct: a big context makes an AI lose the thread, anchor on an early
wrong guess, and compound it into every later file. The fix is not a bigger document.
It is small, bounded context per step, with a hard check between steps. Here is the method.

## The rule: never load the whole spec at once
The 28k-word MASTER_SPEC is a reference library, not a prompt. Each session loads only:
1. `CONTEXT.md` (1 page — always), and
2. the ONE spec section for the current milestone (e.g. just Part 13.2's M0.3), and
3. the files that milestone actually edits.
Nothing else. A session that has only what it needs makes far fewer mistakes.

## One milestone per session, fresh each time
- Start a NEW session for each milestone (M0.1, then M0.2, ...). Don't let one long
  session accumulate 9 milestones of context — that is exactly where errors compound.
- Paste the matching prompt from `SESSION_PROMPTS.md`.
- At the end, the agent writes `docs/milestones/M0.x.md` (what was built, how to run it,
  test output, what's next). THAT short report — not the whole history — is the context
  the next session reads. This is how you hand off without dragging the full transcript.

## The check between steps is what stops compounding
Every milestone has acceptance tests that RUN REAL CODE (build the Docker image, run the
parser on a real log, resume after a crash, take a GDS through DRC). A hallucinated
"it's done" fails the test immediately. So a wrong assumption cannot silently flow into
the next milestone — the gate catches it while it's cheap. This is the same principle as
the chip Trust Layer, applied to building the software.

## When the agent goes down a wrong path (the thing you described)
If you see it "fixing" the same thing repeatedly, or confidently building on something
wrong — STOP. Do not keep saying "that's wrong" inside the same session; a polluted
context rarely recovers, it just rationalizes. Instead:
1. End the session.
2. Fix the root: add one clear line to `CONTEXT.md` or the milestone's note that rules
   out the wrong path ("X is NOT how we do this; do Y").
3. Start a fresh session and re-run that milestone from its last green checkpoint.
A clean restart with one corrected sentence beats ten corrections in a dirty context.

## Keep CONTEXT.md and your agent config tiny and true
These are loaded constantly, so every wrong or stale word in them costs you on every
turn. Keep them short. When a real decision is made, record it in `docs/DECISIONS.md`
(short), not by growing CONTEXT. CONTEXT holds only what's true for the whole project.

## Order of what to paste, start to finish
1. (once) Make sure `CONTEXT.md` and `docs/MASTER_SPEC.md` are in the repo.
2. New session → paste "read CONTEXT.md, then do M0.1" (Session 1 prompt).
3. Let it finish, pass tests, write M0.1.md. Review the report.
4. New session → M0.2. Repeat.
5. If a session derails: stop, correct CONTEXT/DECISIONS in one line, restart that
   milestone fresh.

## Why this works
Small context = the model keeps the thread. Fresh sessions = no accumulated drift.
Real-tool checks between milestones = a wrong step is caught before the next is built on
it. Short handoff reports = continuity without dragging the whole history. Together they
turn "one wrong guess poisons everything" into "one wrong guess fails one test and stops".
