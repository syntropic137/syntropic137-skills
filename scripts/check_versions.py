#!/usr/bin/env python3
"""Check that every skill is versioned and every changed skill is released.

Usage:
    python3 scripts/check_versions.py [BASE_REF]

BASE_REF defaults to origin/main. The check compares the working tree with
the merge base of BASE_REF and HEAD and fails when:

- a SKILL.md has no `metadata.version`, or it is not a quoted semver string;
- any file under skills/<name>/ changed but that skill's version did not go up;
- a changed skill's new version has no CHANGELOG.md line of the form
  "- `<name>` <version>: ..." that was not already on the base;
- a skill on the base has no SKILL.md any more (removed, renamed, or its
  manifest deleted) and CHANGELOG.md gains no line for it at the next MAJOR
  version of its base version, "- `<name>` <MAJOR+1>.0.0: ...".

A change anywhere in the skill folder counts, because that is what the
`skills` CLI hashes to decide a skill changed. Standard library only.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
VERSION_LINE = re.compile(r"""^  version:\s*(?P<quote>["']?)(?P<value>[^"'\s]*)(?P=quote)\s*$""")


@dataclass(frozen=True)
class Problem:
    skill: str
    message: str

    def __str__(self) -> str:
        return f"{self.skill}: {self.message}"


def read_version(skill_md: str) -> str | None:
    """Return the quoted `metadata.version` string from SKILL.md text, if any.

    Returns "" for a version that is present but unquoted, so the caller can
    say so: the Agent Skills spec requires metadata values to be strings.
    """
    if not skill_md.startswith("---\n"):
        return None
    frontmatter = skill_md[4:].split("\n---\n", 1)[0].splitlines()
    in_metadata = False
    for line in frontmatter:
        if line.startswith("metadata:"):
            in_metadata = True
            continue
        if in_metadata and not line.startswith(" "):
            in_metadata = False
        if in_metadata:
            match = VERSION_LINE.match(line)
            if match:
                return match["value"] if match["quote"] else ""
    return None


def semver_key(version: str) -> tuple[int, int, int]:
    major, minor, patch = (int(part) for part in version.split("."))
    return (major, minor, patch)


def changelog_entries(changelog: str) -> set[tuple[str, str]]:
    """(skill, version) pairs announced by "- `<skill>` <version>:" lines."""
    pattern = re.compile(r"^- `(?P<skill>[a-z0-9-]+)` (?P<version>\d+\.\d+\.\d+):", re.MULTILINE)
    return {(m["skill"], m["version"]) for m in pattern.finditer(changelog)}


def check(
    current: dict[str, str],
    base: dict[str, str],
    changed_skills: set[str],
    changelog: str,
    base_changelog: str,
) -> list[Problem]:
    """current/base map skill name -> SKILL.md text; changed_skills are folders that differ.

    base holds every skill on the base, so a skill missing from current was
    removed or renamed, and still has to be released.
    """
    problems: list[Problem] = []
    new_entries = changelog_entries(changelog) - changelog_entries(base_changelog)
    for skill in sorted(set(base) - set(current)):
        base_version = read_version(base[skill])
        if base_version and SEMVER.match(base_version):
            expected = f"{semver_key(base_version)[0] + 1}.0.0"
            if (skill, expected) not in new_entries:
                problems.append(Problem(skill, f"skills/{skill}/SKILL.md was removed or renamed, but CHANGELOG.md gains no line starting \"- `{skill}` {expected}:\" (removal is a MAJOR change)"))
        elif not any(name == skill for name, _ in new_entries):
            problems.append(Problem(skill, f"skills/{skill}/SKILL.md was removed or renamed, but CHANGELOG.md gains no line for `{skill}`"))
    for skill in sorted(current):
        version = read_version(current[skill])
        if version is None:
            problems.append(Problem(skill, 'SKILL.md has no metadata.version (add `metadata:\\n  version: "1.0.0"`)'))
            continue
        if not SEMVER.match(version):
            problems.append(Problem(skill, f'metadata.version must be a quoted "MAJOR.MINOR.PATCH" string, got {version!r}'))
            continue
        if skill not in changed_skills:
            continue
        base_version = read_version(base[skill]) if skill in base else None
        if base_version and SEMVER.match(base_version) and semver_key(version) <= semver_key(base_version):
            problems.append(Problem(skill, f"changed, but metadata.version {version} is not above the base's {base_version}"))
            continue
        if (skill, version) not in new_entries:
            problems.append(Problem(skill, f"changed to {version}, but CHANGELOG.md gains no line starting \"- `{skill}` {version}:\""))
    return problems


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def git_show(rev: str, path: str) -> str | None:
    result = subprocess.run(["git", "show", f"{rev}:{path}"], capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else None


def main(argv: list[str]) -> int:
    base_ref = argv[1] if len(argv) > 1 else "origin/main"
    root = Path(git("rev-parse", "--show-toplevel").strip())
    merge_base = git("merge-base", base_ref, "HEAD").strip()

    current = {p.parent.name: p.read_text() for p in sorted((root / "skills").glob("*/SKILL.md"))}
    # The base's skills come from the base tree, not from what survives here,
    # so a deleted manifest or folder is still checked.
    base: dict[str, str] = {}
    for path in git("ls-tree", "-r", "--name-only", "--full-tree", merge_base, "--", "skills").splitlines():
        parts = path.split("/")
        if len(parts) == 3 and parts[2] == "SKILL.md":
            base[parts[1]] = git_show(merge_base, path) or ""

    # Committed and uncommitted changes, so the check works before a commit too.
    # --no-renames keeps both sides of a move.
    changed_paths = git("diff", "--name-only", "--no-renames", merge_base, "--", "skills").splitlines()
    changed_paths += git("ls-files", "--others", "--exclude-standard", "--", "skills").splitlines()
    changed_skills = {path.split("/")[1] for path in changed_paths if path.count("/") >= 2}

    changelog_path = root / "CHANGELOG.md"
    changelog = changelog_path.read_text() if changelog_path.exists() else ""
    base_changelog = git_show(merge_base, "CHANGELOG.md") or ""

    problems = check(current, base, changed_skills, changelog, base_changelog)
    for problem in problems:
        print(f"FAIL {problem}")
    if problems:
        print(f"\n{len(problems)} problem(s). See 'Versioning' in AGENTS.md.")
        return 1
    removed = set(base) - set(current)
    print(
        f"OK {len(current)} skills versioned; {len(changed_skills & set(current))} changed and {len(removed)} removed "
        f"since {base_ref}, all bumped and in CHANGELOG.md"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
