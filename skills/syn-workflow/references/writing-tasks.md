# Writing the task

The task (`-t`) is the only part of a run you write fresh each time, and it
decides more outcomes than the workflow does. These rules come from runs
observed on a production deployment, 2026-10-04..07. Read this before
writing a task for a multi-phase workflow, or before re-running a task that
failed.

## Name the trap, and the command that proves it was avoided

A run that failed once will fail the same way again unless the task says
where. Name the specific trap the previous run hit, and the check that shows
it was avoided:

```text
Weak:   Fix the flaky retry test.
Strong: Fix the flaky retry test. The last run "fixed" it by raising the
        timeout; that is not a fix. Show the test passing 20 times in a row
        with the timeout unchanged, and paste that output.
```

The check must be a command whose output a later phase or a reader can
compare against the claim. "Make sure it works" is not a check.

## Keep the first phase read-only when it checks a premise

Many workflows open with a phase that confirms the task's premise. Keep what
the task asks of that phase to reading: open files, list things, query the
API. Observed: tasks that opened with "install the dependencies, run the test
suite, then..." made the premise phase do implementation work, and it timed
out before reporting. Put build and test steps in the phase that implements
or verifies, and say which phase they belong to if the task names steps.

## Scope the task to what one phase can finish

A phase has a timeout. A task that says "every X" (every skill, every
endpoint, every failing test) grows with the codebase and times out
part-way, and a resume replays the same task and times out again. Split it
into batches that each fit one phase, and run one execution per batch:

```bash
syn workflow run <workflow-id> -R owner/repo -t "Migrate the endpoints in the billing module (batch 1 of 3: invoices, refunds)"
```

A phase that reports "I did these three and not those two" did its job; the
next batch is a new run.

## Require pasted output, not summaries

Ask for the command output itself, not the agent's account of it. "Tests
pass" is a claim; the pasted test summary line is evidence a verification
phase can check. Phrase it in the task: "paste the output of `<command>`".

## State the premise so it can be refused

Write the premise as a claim the run can check ("the retry test fails on
main"), not as background. An agent that finds the premise false and stops
is behaving correctly: that outcome is worth more than a change built on a
wrong premise. Read such a run's reported result before re-running anything
(see execution-control).

## Check the designs already written before briefing a design

A task that asks for a design is checked against the target repository's
existing plans, design records and open epics, and a premise phase refuses
one that contradicts them. Observed 2026-10-07: three design tasks in one
day were refused at premise because each contradicted a design already
written. The refusal was correct and the run cost little; the miss was in
the task. Read what the repository already decided, and either build on it
or say in the task which decision this one replaces and why.

## Declare every repository the change may touch

The run's workspace credential is scoped to the repositories passed with
`-R`. A change that turns out to need a second repository cannot clone or
push it, and dead-ends. Observed 2026-10-07: a fix that needed a matching
change in a dependency repository stopped there. Pass each repository the
fix may reach:

```bash
syn workflow run <workflow-id> -R owner/app -R owner/dependency -t "..."
```

## Measure deployment data before the run, and paste it in

A phase runs inside a workspace with no route to the deployment's API and
no credentials for it, so it cannot read execution lists, costs or session
data itself. Observed 2026-10-07: a run whose task depended on that data
could not get it. Query it first (`syn execution list`, `syn execution
show`, the costs API) and paste what the task needs into the task text, or
do that part outside the run.
