# Designing a workflow that delivers correct work

A workflow that validates can still certify wrong work. These rules decide
how often it does, and how you find out. They come from runs observed on a
production deployment, 2026-10-04..06. Read this when deciding a workflow's
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

Give the verification phase read-only tools where it only needs to read
(`allowed_tools: [Read, Grep, Glob, Bash]`), and ask it to paste the output
of each check it ran, so its verdict is evidence rather than an opinion.

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

## Change models only on evidence

A cheaper model is adopted for a phase only after an eval (below) shows the
same quality on the same cases. A model that looks equivalent on one run
can certify defects the current one catches.

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
finding a correct verification must report.

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
finds. An execution started without `--eval` can be added later with
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
