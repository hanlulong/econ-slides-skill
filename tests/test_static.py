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


def source_checks(body: str) -> set[str]:
    """Run check_tex on a one-off deck written to a temporary folder."""
    import tempfile
    from check_deck import check_tex
    deck = ("\\documentclass{beamer}\n\\begin{document}\n" + body
            + "\n\\end{document}\n")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "deck.tex"
        path.write_text(deck, encoding="utf-8")
        return {f["check"] for f in check_tex(path)}


class HouseRuleTitleTest(unittest.TestCase):
    BUTTON = ("\\hyperlink{bk}{\\beamergotobutton{Backup}}\n\\end{frame}\n"
              "\\begin{frame}{Backup}\\hypertarget{bk}{}Detail\\end{frame}")

    def frame(self, title: str, inner: str) -> str:
        return f"\\begin{{frame}}{{{title}}}\n{inner}"

    def test_conclusion_variants_fire(self):
        for title in ("Conclusion", "Conclusions", "Concluding remarks",
                      "Conclusions.", "Conclusion and next steps"):
            self.assertIn("conclusion-link",
                          source_checks(self.frame(title, self.BUTTON)), title)
        found = source_checks("\\begin{frame}{Concluding remarks}\n"
                              "\\beamergotobutton{More}\n\\end{frame}")
        self.assertIn("conclusion-link", found)

    def test_other_titles_do_not_fire(self):
        for title in ("Summary", "Conclusions and extensions"):
            self.assertNotIn("conclusion-link",
                             source_checks(self.frame(title, self.BUTTON)), title)

    def test_roadmap_variants(self):
        for title in ("Roadmap", "Outline", "Agenda", "Plan of the talk"):
            found = source_checks(f"\\begin{{frame}}{{{title}}}\n"
                                  "\\textbf{x}\n\\end{frame}")
            self.assertIn("roadmap-emphasis", found, title)
        self.assertNotIn("roadmap-emphasis", source_checks(
            "\\begin{frame}{Outline of the model}\n\\textbf{x}\n\\end{frame}"))

    def test_violations_fixture_still_fires(self):
        from check_deck import check_tex
        found = {f["check"] for f in check_tex(ROOT / "tests/violations-test.tex")}
        self.assertIn("conclusion-link", found)
        self.assertIn("roadmap-emphasis", found)


class MissingGlyphTest(unittest.TestCase):
    # Four lines from a real XeTeX log of a house-theme deck with ≥ and β in
    # text, wrapped at 79 columns as TeX writes them.
    WRAPPED = (
        "Missing character: There is no ≥ (U+2265) in font [lmsans10-regular]:mapping=te\n"
        "x-text;!\n"
        "Missing character: There is no β (U+03B2) in font [lmsans10-regular]:mapping=te\n"
        "x-text;!\n")

    def checks(self, log: str) -> list[str]:
        from check_deck import check_log
        return [f["check"] for f in check_log(log)]

    def test_wrapped_xetex_lines_are_blockers(self):
        from check_deck import check_log
        findings = check_log(self.WRAPPED)
        self.assertEqual([f["check"] for f in findings],
                         ["missing-glyph", "missing-glyph"])
        self.assertIn("'≥' (U+2265) is missing from font lmsans10-regular",
                      findings[0]["detail"])
        self.assertIn("'β' (U+03B2)", findings[1]["detail"])
        self.assertTrue(all(f["page"] is None for f in findings))

    def test_harmless_losses_are_notes(self):
        self.assertEqual(self.checks(
            'Missing character: There is no ; ("3B) in font nullfont!\n'),
            ["lost-char"])
        self.assertEqual(self.checks(
            "Missing character: There is no \u200b (U+200B) in font "
            "[lmroman10-regular]:mapping=tex-text;!\n"), ["lost-char"])

    def test_pdftex_form_and_clean_log(self):
        self.assertEqual(self.checks(
            "Missing character: There is no ^^b2 in font cmr10!\n"),
            ["missing-glyph"])
        self.assertEqual(self.checks("Overfull \\hbox (0.5pt too wide)\n"), [])

    def test_weights(self):
        from check_deck import HARD_BLOCKERS, NON_WAIVABLE_BLOCKERS, score_findings
        self.assertEqual(score_findings([{"check": "missing-glyph"}]), 90)
        self.assertEqual(score_findings([{"check": "lost-char"}]), 100)
        self.assertIn("missing-glyph", HARD_BLOCKERS)
        self.assertNotIn("missing-glyph", NON_WAIVABLE_BLOCKERS)

    def test_inherited_glyph_is_waived_by_a_baseline(self):
        from check_deck import check_log, classify_blocker_regressions
        findings = check_log(self.WRAPPED)
        inherited, new, _ = classify_blocker_regressions(findings, findings)
        self.assertEqual((len(inherited), new), (2, []))

class CompileDeckTest(unittest.TestCase):
    def test_engine_directive(self):
        from compile_deck import engine_from_directive
        cases = {
            "% !TEX program = pdflatex\n\\documentclass{beamer}": ("pdflatex", None),
            "% !TEX program = xelatex\n": ("xelatex", None),
            "%!TEX program=lualatex\n": ("lualatex", None),
            "% !TEX TS-program = xelatex\n": ("xelatex", None),
            "% !TeX Program = LuaLaTeX\n": ("lualatex", None),
            "% !TEX program = latexmk\n": (None, "latexmk"),
            "\n" * 24 + "% !TEX program = pdflatex\n": (None, None),
            "\\documentclass{beamer}\n% just a comment\n": (None, None),
        }
        for text, expected in cases.items():
            self.assertEqual(engine_from_directive(text), expected, text)

    def test_pdftex_only_primitive(self):
        from compile_deck import pdftex_only_primitive
        log = ("! Undefined control sequence.\n"
               "l.7 \\pdfglyphtounicode\n"
               "                       {A}{0041}\n")
        self.assertEqual(pdftex_only_primitive(log), "\\pdfglyphtounicode")
        self.assertIsNone(pdftex_only_primitive(
            "! Undefined control sequence.\nl.19 \\undefinedmacro\n"))
        self.assertIsNone(pdftex_only_primitive("! Missing $ inserted.\n"))

    def test_text_mode_subprocesses_name_an_encoding(self):
        # text=True alone decodes TeX output in the locale's code page, which
        # crashed under GBK on a UTF-8 log.
        import ast
        for path in sorted(SCRIPTS.glob("*.py")):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if not (isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "run"
                        and isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "subprocess"):
                    continue
                keywords = {k.arg: k.value for k in node.keywords}
                text = keywords.get("text")
                if isinstance(text, ast.Constant) and text.value is True:
                    self.assertIn("encoding", keywords,
                                  f"{path.name}:{node.lineno}")


if __name__ == "__main__":
    unittest.main()
