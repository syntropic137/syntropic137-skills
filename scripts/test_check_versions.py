"""Tests for check_versions.py. Run: python3 -m unittest discover -s scripts"""

from __future__ import annotations

import contextlib
import io
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from check_versions import check, main, read_version


def skill_md(version_line: str | None) -> str:
    meta = f"metadata:\n{version_line}\n" if version_line is not None else ""
    return f"---\nname: s\ndescription: d\n{meta}---\n\n# Body\n"


V110 = skill_md('  version: "1.1.0"')
V100 = skill_md('  version: "1.0.0"')
ENTRY_110 = "## [1.1.0] - 2026-10-07\n### Changed\n- `s` 1.1.0: did a thing\n"


class ReadVersionTest(unittest.TestCase):
    def test_reads_quoted_version(self) -> None:
        self.assertEqual(read_version(V110), "1.1.0")

    def test_unquoted_version_is_reported_as_empty(self) -> None:
        self.assertEqual(read_version(skill_md("  version: 1.1.0")), "")

    def test_missing_metadata(self) -> None:
        self.assertIsNone(read_version(skill_md(None)))

    def test_version_outside_metadata_is_ignored(self) -> None:
        self.assertIsNone(read_version("---\nname: s\nversion: \"1.0.0\"\n---\n"))


class CheckTest(unittest.TestCase):
    def test_changed_skill_bumped_with_entry_passes(self) -> None:
        self.assertEqual(check({"s": V110}, {"s": V100}, {"s"}, ENTRY_110, ""), [])

    def test_changed_skill_without_bump_fails(self) -> None:
        problems = check({"s": V100}, {"s": V100}, {"s"}, ENTRY_110, "")
        self.assertIn("not above", problems[0].message)

    def test_downgrade_fails(self) -> None:
        problems = check({"s": V100}, {"s": V110}, {"s"}, "- `s` 1.0.0: x\n", "")
        self.assertIn("not above", problems[0].message)

    def test_bump_without_changelog_entry_fails(self) -> None:
        problems = check({"s": V110}, {"s": V100}, {"s"}, "", "")
        self.assertIn("CHANGELOG.md", problems[0].message)

    def test_entry_already_on_base_does_not_count(self) -> None:
        problems = check({"s": V110}, {"s": V100}, {"s"}, ENTRY_110, ENTRY_110)
        self.assertIn("CHANGELOG.md", problems[0].message)

    def test_entry_for_other_version_does_not_count(self) -> None:
        problems = check({"s": V110}, {"s": V100}, {"s"}, "- `s` 1.2.0: x\n", "")
        self.assertIn("CHANGELOG.md", problems[0].message)

    def test_first_version_needs_entry(self) -> None:
        self.assertEqual(len(check({"s": V100}, {"s": skill_md(None)}, {"s"}, "", "")), 1)
        self.assertEqual(check({"s": V100}, {"s": skill_md(None)}, {"s"}, "- `s` 1.0.0: x\n", ""), [])

    def test_new_skill_needs_entry(self) -> None:
        self.assertEqual(len(check({"s": V100}, {}, {"s"}, "", "")), 1)

    def test_unchanged_skill_needs_only_a_version(self) -> None:
        self.assertEqual(check({"s": V100}, {"s": V100}, set(), "", ""), [])
        self.assertEqual(len(check({"s": skill_md(None)}, {}, set(), "", "")), 1)

    def test_unquoted_or_non_semver_version_fails(self) -> None:
        for line in ("  version: 1.0.0", '  version: "1.0"', '  version: "v1.0.0"'):
            with self.subTest(line=line):
                problems = check({"s": skill_md(line)}, {}, set(), "", "")
                self.assertIn("quoted", problems[0].message)


    def test_removed_skill_needs_next_major_entry(self) -> None:
        self.assertIn("removed", check({}, {"s": V110}, set(), "", "")[0].message)
        self.assertEqual(len(check({}, {"s": V110}, set(), "- `s` 1.2.0: x\n", "")), 1)
        self.assertEqual(check({}, {"s": V110}, set(), "- `s` 2.0.0: removed\n", ""), [])


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false", *args],
        cwd=repo, check=True, capture_output=True,
    )


class MainTest(unittest.TestCase):
    """Runs main() against a real git repository, so the base is discovered as in CI."""

    def setUp(self) -> None:
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo)
        for name in ("a", "b"):
            (self.repo / "skills" / name / "references").mkdir(parents=True)
            (self.repo / "skills" / name / "SKILL.md").write_text(V100)
            (self.repo / "skills" / name / "references" / "r.md").write_text("ref\n")
        (self.repo / "CHANGELOG.md").write_text("# Changelog\n\n## [Unreleased]\n")
        _git(self.repo, "init", "-q", "-b", "main")
        _git(self.repo, "add", ".")
        _git(self.repo, "commit", "-q", "-m", "base")
        cwd = os.getcwd()
        os.chdir(self.repo)
        self.addCleanup(os.chdir, cwd)

    def run_main(self) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["check_versions.py", "HEAD"])
        return code, out.getvalue()

    def add_entries(self, *lines: str) -> None:
        with (self.repo / "CHANGELOG.md").open("a") as f:
            f.write("".join(f"{line}\n" for line in lines))

    def test_an_unbumped_change_fails_even_when_run_from_a_subdirectory(self) -> None:
        # git pathspecs are relative to the working directory; run from
        # scripts/, `-- skills` matched nothing and the check passed (#7 review).
        (self.repo / "scripts").mkdir()
        os.chdir(self.repo / "scripts")
        (self.repo / "skills/a/references/r.md").write_text("changed\n")
        self.assertEqual(self.run_main()[0], 1)

    def test_unchanged_passes(self) -> None:
        self.assertEqual(self.run_main()[0], 0)

    def test_reference_change_bumped_with_entry_passes(self) -> None:
        (self.repo / "skills/a/references/r.md").write_text("changed\n")
        (self.repo / "skills/a/SKILL.md").write_text(V110)
        self.add_entries("- `a` 1.1.0: x")
        self.assertEqual(self.run_main(), (0, "OK 2 skills versioned; 1 changed and 0 removed since HEAD, all bumped and in CHANGELOG.md\n"))

    def test_reference_change_without_bump_fails(self) -> None:
        (self.repo / "skills/a/references/r.md").write_text("changed\n")
        code, out = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("FAIL a: changed", out)

    def test_deleted_manifest_fails_without_entry(self) -> None:
        (self.repo / "skills/b/SKILL.md").unlink()
        code, out = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("FAIL b: skills/b/SKILL.md was removed", out)

    def test_deleted_folder_fails_without_entry(self) -> None:
        shutil.rmtree(self.repo / "skills/b")
        code, out = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("FAIL b: skills/b/SKILL.md was removed", out)

    def test_deleted_folder_with_major_entry_passes(self) -> None:
        shutil.rmtree(self.repo / "skills/b")
        self.add_entries("### Removed", "- `b` 2.0.0: removed")
        self.assertEqual(self.run_main(), (0, "OK 1 skills versioned; 0 changed and 1 removed since HEAD, all bumped and in CHANGELOG.md\n"))

    def test_committed_deletion_fails_without_entry(self) -> None:
        _git(self.repo, "checkout", "-q", "-b", "topic")
        _git(self.repo, "rm", "-q", "-r", "skills/b")
        _git(self.repo, "commit", "-q", "-m", "drop b")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["check_versions.py", "main"])
        self.assertEqual(code, 1)
        self.assertIn("FAIL b:", out.getvalue())

    def test_rename_needs_both_entries(self) -> None:
        _git(self.repo, "mv", "skills/b", "skills/c")
        code, out = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("FAIL b: skills/b/SKILL.md was removed", out)
        self.assertIn("FAIL c: changed to 1.0.0", out)
        self.add_entries("- `c` 1.0.0: renamed from `b`")
        code, out = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("FAIL b:", out)
        self.add_entries("- `b` 2.0.0: renamed to `c`")
        self.assertEqual(self.run_main()[0], 0)


if __name__ == "__main__":
    unittest.main()
