# Registering and updating a workflow

Flag-level detail for `syn workflow create`, `install` and `update`, and every
provenance refusal with what it means. Read this when registering a
definition, or when an update was refused.

## `create`

- `--from` takes a `.yaml` or `.yml` file, not a directory. The deployment
  rejects a file whose `prompt_file` it cannot resolve; install the package
  instead.
- The positional name overrides the name in the YAML.
- Without `--from`, `create` builds a minimal workflow from flags (`--type`,
  `--description`, `--repo`, `--ref`, `--repos`, `--no-repos`); those flags
  conflict with `--from`.

## `install`

- `install --dry-run` (`-n`) shows what would be registered without
  registering it.
- `--ref <branch-or-tag>` pins a git or marketplace source; the default is
  `main`.
- A package with no manifest (`syntropic137-plugin.json`) is recorded as
  version `0.0.0`.

## Refusals

| message contains | meaning | do |
|---|---|---|
| `version X is already installed. Pass --force to reinstall it.` | same version, changed content | bump the version, or `--force` if overwriting is intended |
| `resolves to a different source than the installed copy` | same version, different source digest | confirm the source is the one you meant, then `--force` |
| `is installed with version ..., but this install declares no version. Refusing to overwrite recorded provenance with nothing.` | it was installed with `install`, and you are updating it with `create --from` | use `syn workflow install <dir> --force`. `--force` does not bypass this refusal from `create`, and `version:` is not a valid YAML key |
| the same refusal naming `source digest` | as above, for the source digest | as above |

A byte-identical reinstall is reported as already installed and changes
nothing. Reinstalling an archived workflow restores it.

Run `syn workflow <subcommand> --help` for the full flag list of the
installed CLI version.
