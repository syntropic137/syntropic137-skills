# Safety guards and presets

What each trigger safety guard blocks, and what each built-in preset
registers. Read this when a history entry is `blocked`, or when choosing a
preset.

## Safety guards

Each guard is recorded by name in the rule's history when it blocks.

| guard | blocks when |
|---|---|
| `max_attempts` | this rule has fired `max_attempts` times for this pull request |
| `cooldown` | this rule fired for this pull request less than `cooldown_seconds` ago |
| `daily_limit` | this rule has fired `daily_limit` times today |
| `idempotency` | this delivery was already processed |
| `concurrency` | an execution this rule started for this pull request is still running |
| `dispatch_rate_limit` | the deployment is starting too many triggered runs per minute |

A blocked event is not retried later. Different rules do not block each other
on the same pull request. There is no spend limit on a trigger.

## Presets

Enable with `syn triggers enable <preset> -r owner/repo [-w <workflow-id>]`.

| preset | event | fires when | inputs mapped | limits |
|---|---|---|---|---|
| `self-healing` | `check_run.completed` | the check failed and belongs to a pull request | `repository`, `pr_number`, `branch`, `check_name`, `check_output_title`, `check_output_summary`, `check_html_url` | 3 attempts, 20 a day, 300 s cooldown |
| `review-fix` | `pull_request_review.submitted` | the review requested changes or commented, on a non-draft pull request | `repository`, `pr_number`, `branch`, `review_body`, `reviewer`, `review_html_url` | 2 attempts, 10 a day, 600 s cooldown |
| `comment-command` | `issue_comment.created` | a pull request comment contains `/syn` | `repository`, `pr_number`, `pr_title`, `comment_body`, `comment_author`, `comment_id`, `comment_html_url` | 5 attempts, 30 a day, 60 s cooldown |

Without `-w`, a preset dispatches the deployment's `self-heal-pr` workflow.
Enabling the same preset twice on a repository is refused.
