# Reading a run's transcripts

Capture receipts versus the current state of a body, and a loop that fetches
every local transcript of a run. Read this during step 6 of the workflow.

## Receipts are history

A capture receipt is history. In the human view, `recorded=` is what the
receipt said and `current=` is the body's state now (`expired`, `deleted` or
`withheld` override it). A remote receipt carries a `sha256:...` content hash,
which the local transcript route cannot read.

## Every local transcript of a run

Run after `syn execution sessions <execution-id> --all --json > inventory.json`:

```bash
EXEC=<execution-id>
mkdir -p transcripts
jq -c '.pages[] | select(.kind == "capture") | .items[]
  | select((.destination // "local") == "local" and .availability == "present")
  | {harness: .node.harness, native: .node.local_id, sha: .archived_byte_hash}' inventory.json | sort -u |
while IFS= read -r rec; do
  harness=$(jq -r .harness <<<"$rec"); native=$(jq -r .native <<<"$rec"); sha=$(jq -r .sha <<<"$rec")
  syn execution transcript "$EXEC" "$harness" "$native" "$sha" --json > "transcripts/$sha.json" \
    || echo "unavailable: $rec"
done
```

Every `unavailable:` line goes in the report with the status the server gave.
