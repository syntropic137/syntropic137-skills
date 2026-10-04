# Session and cost views

Every CLI view for sessions and costs, the question it answers, and what it
shows. Read this when the short list in the workflow does not cover the
question.

| question | command | what it shows |
|---|---|---|
| what did the agent do, step by step | `syn sessions show <session-id>` | status, provider, model, tokens, cost, error, and the operations log (type, tool, success) |
| which tools ran, in order, and how long each took | `syn observe tools <session-id>` | time, tool, duration, ok or error |
| where did the tokens go | `syn observe tokens <session-id>` | input, output, total, cache creation, cache read, estimated cost |
| what did one session cost and why | `syn costs session <session-id>` | cost with coverage, tokens, cache, tool calls, turns, duration, cost by model, cost by tool |
| what did one execution cost and why | `syn costs execution <execution-id>` | cost with coverage, sessions, tokens, cache, duration, cost by phase, model and tool |
| which sessions or runs cost most | `syn costs sessions [-e <execution-id>]`, `syn costs executions`, `syn costs summary` | per-row costs; the summary adds top models and top sessions |
| per-phase totals for a workflow | `syn metrics show [-w <workflow-id>]` | workflows, sessions, tokens, cost, artifacts, and a phase table |
| deployment-wide picture | `syn insights overview`, `syn insights cost`, `syn insights heatmap [-d <days>]` | systems and repos with health and active executions; cost by repository and model; daily activity |

`syn sessions list` shows **platform** sessions only, filtered with
`--execution <id>`, `-w/--workflow <id>`, `-s/--status <status>` and
`-n/--limit`. Session statuses are `running`, `completed`, `failed` and
`cancelled`. Delegates an agent starts inside its workspace and the harness's
own transcripts are not in this list; for those, use the
discovering-run-sessions skill.

Artifacts a session produced are read with `syn artifacts list -w
<workflow-id>`, `syn artifacts show <artifact-id>` and
`syn artifacts content <artifact-id>`.
