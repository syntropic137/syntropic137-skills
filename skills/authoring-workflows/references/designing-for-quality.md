# Designing a workflow that delivers correct work

A workflow that validates can still certify wrong work. These rules decide
how often it does, and how you find out. They come from runs observed on a
production deployment, 2026-10-04..07. Read this when deciding a workflow's
phases and models, or before changing a workflow, prompt or model that
already works.

## Verification is its own phase, on a different model

The phase that wrote a change is the worst judge of it: it re-reads its own
reasoning and agrees with it. Put verification in a separate phase that
reads the change fresh, and run it on a different model from the
implementation, by setting that phase's `model` or its `agent` block
(`provider: codex` against a claude implementation, or another model id).
Different models miss different things, so the disagreements are where the
defects are.

"Different" means a different model family, not a smaller model from the
same vendor. Cross the families in both directions: a Claude model (Opus)
implements and a GPT model (GPT-6.1, through `provider: codex`) verifies, or
GPT implements and Claude verifies. A Claude verifier on a Claude
implementation is a same-family review; when a run relies on one, say so in
its report rather than calling it cross-model. Observed 2026-10-07: in a
verifier eval, Sonnet 5.5 certified two commits known to be buggy. Do not
use it as a verifier until an eval shows it catches what the current
verifier catches.

Give the verification phase only the tools it needs, and ask it to paste
the output of each check it ran, so its verdict is evidence rather than an
opinion. `allowed_tools: [Read, Grep, Glob]` is read-only. A verifier that
must run checks needs `Bash`, and `[Read, Grep, Glob, Bash]` is **not**
read-only: through the shell the phase can write files, commit, push and
reach the network. With `Bash`, the prompt is what keeps the phase from
changing anything, so say in it that the phase changes nothing.

## Bounded repair rounds

Observed outcomes, from best to worst:

- **verify, fix, re-verify, up to a fixed maximum of rounds:** most defects
  found in the first verification are fixed and confirmed in the next;
- **a single pass:** defects the verification found are reported but stay
  in the change;
- **an unbounded loop:** cost grows without a matching gain, and a run that
  cannot converge never ends on its own.

Phases run in order (`execution_type` is `sequential`), so a workflow
expresses rounds as a fixed sequence of phases, for example `implement`,
`verify-1`, `fix-1`, `verify-2`, `fix-2`, `verify-3`. Each fix phase reads the
previous verification's output (`{{verify-1}}`) and, when it found nothing to
fix, says so and ends. The last verification's report is the run's verdict.
Choose the maximum up front: it is the run's cost ceiling.

## Scale verification to the change

Verification effort should match what the change can break. A change to
documentation or skill text needs a verifier that reads it against the
product it describes; it does not need the full test suite, a build, or a
second implementation model. A change to code that runs in production needs
the full checks. Running heavy verification on light changes is where cost
goes without finding anything. Keep a separate, lighter workflow for
documentation changes rather than one workflow for everything.

## Change one variant at a time, on evidence

A phase's behaviour is set by four things, and a **variant** is one choice
of each:

| part | where it is set |
|---|---|
| model | the phase's `model`, or its `agent` block |
| prompt | the phase's prompt or `prompt_file` |
| skills | the phase's pinned `skills` and `claude_plugins` |
| tools | the phase's `allowed_tools` |

Change one part per comparison, so a difference in results has one cause.
A cheaper variant is adopted for a phase only after an eval (below) shows
the same quality on the same cases. A model that looks equivalent on one run
can certify defects the current one catches.

Quality does not transfer across kinds of work. A variant that holds up on
documentation can fail on code changes. Keep evals per **job type** (docs,
editing, code change, rework of an earlier change, testing) and per
**codebase**, tag them so (`--tag docs --tag <codebase>`), and adopt a
variant only for the job types and codebases its evals cover.

## The learning loop: escaped bugs become eval cases

An **escaped bug** is a defect that a run's verification certified and that
was found later. Each one is the most valuable test case you will get,
because it is a case the workflow is known to fail. Turn each into an eval:

```bash
# the repository pinned to the commit BEFORE the fix, and the expected finding as the goal
syn eval create --name "escaped: retry double-send" \
  --goal "Verification reports that a retry re-sends a completed request" \
  --workflow <workflow-id> --repo owner/repo@<commit-before-fix> --tag escaped-bug
```

`syn eval create` pins each `--repo` ref to a commit SHA. The goal states the
finding a correct verification must report. Add a `--tag` for the job type
and one for the codebase, so the eval is found when a variant for that kind
of work is compared.

### Clean controls

Escaped bugs alone reward a verifier that blocks everything: it "finds"
every defect and scores 100%. Add, for each escaped-bug eval, a clean
control: a certified change with no known defect, pinned the same way, with
the goal "Verification certifies the change". Report two numbers: defects
caught, and clean changes wrongly blocked. A variant that raises the first
by raising the second is not better.

### The eval environment must match the one being judged

An eval measures its environment as much as its subject. Observed
2026-10-07: a prompt comparison scored 1 of 6 against 0 of 4 because the
eval runs had no network access to the package index; the verifier blocked
on failed installs, and the scores measured the sandbox, not the prompt.
Give eval runs what production runs have for the thing being measured
(network, credential scope, repositories). Score a run that failed for an
environment reason as an error, excluded from the comparison, never as a
failed case.

Before adopting a change to a workflow, a phase prompt or a model, run the
candidate against every escaped-bug eval, and compare with the current
workflow:

```bash
syn eval list --tag escaped-bug
syn workflow run <candidate-workflow-id> -R owner/repo -t "<the original task>" --eval <eval-id>
syn eval runs <eval-id>                 # the executions in this eval
syn eval show <eval-id>                 # goal, baseline, and a tally of run statuses
```

The run status tally is not the score: read each run's reported result (see
execution-control) and decide whether it reported the expected finding.
Adopt the change only when it finds at least what the current workflow
finds and blocks no more clean controls. An execution started without `--eval` can be added later with
`syn eval attach <execution-id> <eval-id>`.

## Keep a scorecard

Record, per workflow and per period, in a durable place:

| measure | from |
|---|---|
| completion rate: runs whose reported result shows the task delivered, over runs started | each run's reported result, not its status |
| cost per completed run: total cost over delivered runs | `syn execution show` cost lines, or the costs API |
| escaped defects: bugs found after verification certified the change | the escaped-bug evals created in the period |

A change that lowers cost but raises escaped defects is a regression. The
scorecard is how that shows before it compounds. Finding the runs behind
each number across a period is mining-session-logs' job.
