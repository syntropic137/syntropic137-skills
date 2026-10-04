# Publishing a marketplace

The `marketplace.json` index format and the export options. Read this during
step 7 of the workflow, when turning deployed workflows into a marketplace
someone else can install from.

## Exporting

```bash
syn workflow export <workflow-id>                          # writes ./<slug>-export/
syn workflow export <workflow-id> -o ./my-flows -f plugin  # -o is a DIRECTORY; --format package|plugin
```

## The index

A marketplace repository needs `marketplace.json` at its root:

```json
{
  "name": "team-flows",
  "syntropic137": { "type": "workflow-marketplace", "min_platform_version": "0.20.0" },
  "plugins": [
    {
      "name": "pr-review",
      "source": "./plugins/pr-review",
      "version": "1.0.0",
      "description": "Reviews a pull request and posts findings",
      "category": "review",
      "tags": ["review", "github"]
    }
  ]
}
```

- The index needs `name` and `plugins`.
- Each entry needs `name` and `source`. It may also set `version`,
  `description`, `category`, `tags` and a pinned `ref`.
- `source` is a path inside the repository. An absolute path, or one
  containing `..`, is refused.
- When a package's content changes, bump `version` in its
  `syntropic137-plugin.json`, so installers see an update rather than a
  refusal.
- Tag releases so installers can pin them.

Without a `marketplace.json` at the root, `syn marketplace add` refuses the
repository. A repository with no index can still be installed directly with
`syn workflow install org/repo`.
