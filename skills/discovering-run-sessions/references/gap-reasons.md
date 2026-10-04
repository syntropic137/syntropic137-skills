# Gap reasons

What each gap `reason` in the session inventory means. Read this during step
4 of the workflow, when mapping gaps to sessions. The vocabulary is open: an
unknown reason is still a gap, and is reported as one.

| gap `reason` | meaning |
|---|---|
| `invocation_failed`, `invocation_cancelled` | the process ended abnormally |
| `invocation_launch_failed`, `invocation_launch_failed_<cause>` | it never started. Causes include `process_start_failed`, `codex_sandbox_unavailable`, `native_tool_failed`, `native_tool_interrupted`, `capture_hook_failed`, `hook_watchdog`, `capture_hook_unreachable` |
| `invocation_transport_failed_before_announce` | failed before announcing itself; not known to have run |
| `invocation_running`, `invocation_pending` | no outcome yet. Provisional while coverage is `open` |
| `invocation_unsettled_at_seal`, `capture_unsettled_at_seal`, `child_context_unresolved_at_seal`, `parentage_unresolved_at_seal` | still unsettled when the settlement deadline passed |
| `expected_body_unavailable` | an expected session has no present transcript |
| `conflicting_*`, `lineage_cycle`, `unresolved_parentage`, `unverified_invocation_context` | identity, parentage or attribution evidence disagrees or is unverified |
| `no_host_registration` | the run was not instrumented; coverage `unsupported` |
