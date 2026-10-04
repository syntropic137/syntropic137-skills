# The session inventory model

The vocabulary of the session inventory. Read this when a field in
`inventory.json` is unfamiliar.

| term | meaning |
|---|---|
| **node** | one session, in one of three namespaces: `platform` (a session the platform created and bills; `syn sessions show` works on it), `invocation` (an agent process registered as launched inside a workspace, such as a delegate), `transcript` (a harness's own native session, with a `harness`) |
| **binding** | says a platform session or invocation and a native transcript are the same piece of work. Count them once |
| **membership** | places a node in a phase and attempt |
| **edge** | parent to child, `relation` `spawn` (started a delegate), `resume` (continued a conversation) or `fork` (branched) |
| **capture** | a receipt that a transcript was archived, with its `availability` and, for a local present body, `archived_byte_hash` |
| **gap** | a known hole: a `reason` and the `node_keys` it affects. No keys means it applies to the whole run |
| **coverage** | `summary.coverage_state`, the verdict on completeness |

A native transcript id is never a platform session id. Never pass one to
`syn sessions show`.

Each edge, membership and binding also carries a `confidence`: `registered`,
`corroborated`, `candidate` or `conflicting`.
