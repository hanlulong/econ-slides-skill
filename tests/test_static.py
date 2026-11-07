"""Checks that need Python and PyMuPDF but no TeX installation.

Run from the repository root:
    python -m unittest discover -s tests -p "test_*.py"

The full suite, which compiles decks, is tests/run-tests.sh.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "econ-slides"
SCRIPTS = SKILL / "scripts"
SAMPLE = ROOT / "docs" / "sample-talk"
sys.path.insert(0, str(SCRIPTS))


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args],
                          capture_output=True, text=True, cwd=ROOT)


class PackagingTest(unittest.TestCase):
    def test_manifests_skill_and_changelog_agree(self):
        claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
        codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        front = (SKILL / "SKILL.md").read_text().split("---", 2)[1]
        version = re.search(r'^  version: "([^"]+)"$', front, re.M).group(1)
        self.assertEqual(claude["version"], version)
        self.assertEqual(codex["version"], version)
        self.assertEqual({k: v for k, v in codex.items() if k != "interface"},
                         claude)
        self.assertIn(f"## {version} ", (ROOT / "CHANGELOG.md").read_text())
        prompts = codex["interface"]["defaultPrompt"]
        self.assertTrue(1 <= len(prompts) <= 3)
        self.assertTrue(all(len(p) <= 128 for p in prompts))

    def test_description_follows_the_frontmatter_limits(self):
        front = (SKILL / "SKILL.md").read_text().split("---", 2)[1]
        description = json.loads(
            re.search(r"^description: (.+)$", front, re.M).group(1))
        self.assertLessEqual(len(description), 1024)
        self.assertNotRegex(description, r"[<>]")
        for boundary in ("Beamer", "PowerPoint", "econ-write", "econ-review"):
            self.assertIn(boundary, description)

    def test_long_reference_files_have_contents(self):
        for path in sorted((SKILL / "references").glob("*.md")):
            text = path.read_text()
            if text.count("\n") > 100:
                self.assertIn("## Contents", text, path.name)


class ScriptTimingTest(unittest.TestCase):
    def timing(self, *args: str) -> tuple[int, dict]:
        proc = run("check_script.py", str(SAMPLE / "script.tex"), "--deck",
                   str(SAMPLE / "conference-30min.tex"), "--json", *args)
        self.assertIn(proc.returncode, (0, 1), proc.stderr)
        return proc.returncode, json.loads(proc.stdout)

    def test_sample_script_fits_its_30_minute_session(self):
        status, result = self.timing("--slot-minutes", "30")
        self.assertEqual(status, 0, result["findings"])
        self.assertEqual(result["genre"], "conference")

    def test_only_an_overrun_fails(self):
        under, _ = self.timing("--slot-minutes", "34")
        over, _ = self.timing("--slot-minutes", "28")
        seminar, _ = self.timing("--slot-minutes", "34", "--genre", "seminar")
        self.assertEqual((under, over, seminar), (0, 1, 0))


class CheckerUnitTest(unittest.TestCase):
    def test_source_checks_fire_without_a_pdf(self):
        from check_deck import check_tex
        found = {f["check"] for f in check_tex(ROOT / "tests/violations-test.tex")}
        for check in ("dead-link", "arrow-bullet", "question-label",
                      "conclusion-link", "pause-chain"):
            self.assertIn(check, found)

    def test_literal_marker_allowance_is_validated(self):
        from check_deck import parse_allowed_markers
        self.assertEqual(parse_allowed_markers([" (?) ??", "[?,?]"]),
                         {"(?)", "??", "[?, ?]"})
        with self.assertRaises(ValueError):
            parse_allowed_markers(["what"])

    def test_wrapped_undefined_keys_are_read(self):
        from compile_deck import undefined_references
        log = ("Package natbib Warning: Citation `thisisaveryveryveryveryverylong"
               "citationkeynam\ne2024abc' on page 1 undefined on input line 6.\n")
        keys = {item["key"] for item in undefined_references(log)["items"]}
        self.assertIn("thisisaveryveryveryveryverylongcitationkeyname2024abc", keys)

    def test_missing_file_hints(self):
        from compile_deck import find_error, missing_file_hint
        self.assertNotIn("tlmgr", missing_file_hint("figures/fig2"))
        self.assertIn("tlmgr search", missing_file_hint("needspace.sty"))
        # A figure named with its extension, as XeTeX and pdfTeX report it.
        for log in ("! Unable to load picture or PDF file 'figs/plot.png'.\n",
                    "! Package pdftex.def Error: File `figs/plot.png' not found:"
                    " using draft setting.\n"):
            self.assertIn("Missing file figs/plot.png", find_error(log)[1])

    def test_log_must_belong_to_the_pdf(self):
        import tempfile
        from check_deck import compile_errors, read_log
        pdf = SAMPLE / "conference-30min.pdf"
        banner = "This is XeTeX, Version 3.141592653-2.6-0.999997 (TeX Live 2025)\n"
        cases = {
            "good": banner + "Output written on build/conference-30min.pdf (23 pages).\n",
            "empty": "",
            "pages": banner + "Output written on conference-30min.pdf (22 pages).\n",
            "other": banner + "Output written on talk.pdf (23 pages).\n",
            "none": banner + "! Emergency stop.\nNo pages of output.\n",
        }
        with tempfile.TemporaryDirectory() as tmp:
            for name, text in cases.items():
                log = Path(tmp) / f"{name}.log"
                log.write_text(text)
                if name == "good":
                    self.assertEqual(read_log(log, pdf, 23)[0], text)
                else:
                    with self.assertRaises(ValueError, msg=name):
                        read_log(log, pdf, 23)
        errors = compile_errors(banner + "! Undefined control sequence.\n"
                                "l.19 \\undefinedmacro\n"
                                "!  ==> Fatal error occurred, no output PDF file produced!\n")
        self.assertEqual(len(errors), 1)
        self.assertIn("source line 19", errors[0]["detail"])

    def test_tracked_sample_pdf_has_no_pdf_blockers(self):
        proc = run("check_deck.py", str(SAMPLE / "conference-30min.pdf"),
                   "--tex", str(SAMPLE / "conference-30min.tex"), "--json")
        self.assertIn(proc.returncode, (0, 1), proc.stderr)
        result = json.loads(proc.stdout)
        # No log in the repository, so the run is partial and never "ship".
        self.assertEqual(result["verdict"], "incomplete")
        self.assertEqual(result["blockers"], [])
        self.assertEqual(result["pages"], 23)


if __name__ == "__main__":
    unittest.main()
