<!-- Copied verbatim from docs/MASTER_SPEC.md: A.20 Task envelope (appended at run time) -->
TASK
id: {task_id}            stage: {stage}            design: {design_name}
goal: {goal}
inputs: {list of artifact paths and hashes}
constraints: {constraints}
exit_criteria: {list}
budget: tokens={max_tokens}, minutes={max_minutes}, tool_runs={max_tool_runs}
allowed_write_paths: {paths}
previous_attempts: {summary of earlier attempts and failures, if any}
relevant_knowledge: {top kb entries}
