"""Tests for check_versions.py. Run: python3 -m unittest discover -s scripts"""

from __future__ import annotations

import unittest

from check_versions import check, read_version


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


if __name__ == "__main__":
    unittest.main()
