#!/usr/bin/env python3
"""Focused contract checks for the optional pure-theory starter pair."""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.check_script import deck_frames, script_blocks, tex_tree  # noqa: E402


DECK = ROOT / "templates" / "theory-talk.tex"
SCRIPT = ROOT / "templates" / "theory-script.tex"

deck_text = DECK.read_text(encoding="utf-8")
script_text = SCRIPT.read_text(encoding="utf-8")
frames = deck_frames(tex_tree(DECK))
_opening, blocks = script_blocks(tex_tree(SCRIPT))

main_titles = [frame["title"] for frame in frames if not frame["appendix"]]
appendix_titles = [frame["title"] for frame in frames if frame["appendix"]]
scripted = [block["title"] for block in blocks if block["kind"] == "main"]
qa = [block["title"] for block in blocks if block["kind"] == "qa"]
selected_qa = [title for title in appendix_titles if title in set(qa)]

assert main_titles == scripted, (main_titles, scripted)
assert qa == selected_qa, (appendix_titles, qa)
assert r"\title[\PaperShortTitle]{\PaperTitle}" in deck_text
assert r"\subtitle" not in deck_text
assert r"\begin{columns}" not in deck_text + script_text
assert r"\begin{minipage}" not in script_text
assert r"\item[$\Rightarrow$]" not in deck_text
assert r"\item[$\rightarrow$]" not in deck_text
assert "economic question" not in (deck_text + script_text).lower()

# The template is explicitly adaptable and does not import empirical structure.
comments_and_source = (deck_text + script_text).lower()
for token in ("not a mandatory sequence", "reorder", "merge", "delete", "optional"):
    assert token in comments_and_source, token
assert not any(title.lower() == "data" for title in main_titles)

# The theory-specific audience obligations are present before the proposition.
environment = deck_text.split(r"\begin{frame}{Environment}", 1)[1].split(
    r"\end{frame}", 1
)[0]
for token in ("Agents:", "Timing and information:", "Choices and constraints:",
              "Solution:", "Key assumption:"):
    assert token in environment, token

mechanism = deck_text.split(r"\begin{frame}{Mechanism}", 1)[1].split(
    r"\end{frame}", 1
)[0]
for token in ("Direct force:", "Equilibrium feedback:", "Sign:", "Intuition:"):
    assert token in mechanism, token

proposition = deck_text.split(r"\begin{frame}{Main proposition}", 1)[1].split(
    r"\end{frame}", 1
)[0]
assert proposition.index("In words.") < proposition.index("formal statement")
assert "Conditions." in proposition and "Intuition:" in proposition
assert deck_text.split(r"\AppendixStart", 1)[0].count(r"\begin{ResultBox}") == 1

conclusion = deck_text.split(r"\begin{frame}{Conclusion}", 1)[1].split(
    r"\end{frame}", 1
)[0]
assert len(re.findall(r"\\item(?![A-Za-z@])", conclusion)) <= 3
assert not any(token in conclusion for token in (
    r"\PlaceNav", r"\hyperlink", r"\beamergotobutton", r"\BackButton"
))

print("theory template contract: PASS")
