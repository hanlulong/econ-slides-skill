#!/usr/bin/env bash
# econ-slides test suite. Requires a TeX Live engine, Python 3, and PyMuPDF.
#   bash tests/run-tests.sh
# With PyMuPDF in a venv, put that venv first on PATH:
#   PATH="$HOME/.venvs/econ-slides/bin:$PATH" bash tests/run-tests.sh
set -uo pipefail
cd "$(dirname "$0")/.."
# Every PDF check needs PyMuPDF; fail once, clearly, rather than test by test.
if ! python3 -c 'import pymupdf' 2>/dev/null; then
  echo "error: PyMuPDF is not importable by python3 ($(command -v python3))." >&2
  echo "  The suite needs PyMuPDF 1.24.3 or newer (older releases provide only 'fitz')." >&2
  echo "  Put the venv that has it first on PATH, for example:" >&2
  echo "    PATH=\"\$HOME/.venvs/econ-slides/bin:\$PATH\" bash tests/run-tests.sh" >&2
  exit 2
fi
# The skill (SKILL.md, references, scripts, templates, themes) lives here;
# Python snippets below import its helpers as ``scripts.*``.
SKILL_DIR=skills/econ-slides
export PYTHONPATH="$PWD/$SKILL_DIR${PYTHONPATH:+:$PYTHONPATH}"
PASS=0; FAIL=0
# Generated sources live beside their originals so relative \input paths
# resolve; remove them even when the run is interrupted.
cleanup() { rm -f skills/econ-slides/templates/_swap-*.tex tests/_*.tex; rm -rf tests/bib-subdir/build; }
trap cleanup EXIT
ok()  { echo "  PASS  $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL  $1"; FAIL=$((FAIL+1)); }

compile_clean() {
  local output
  output=$(python3 skills/econ-slides/scripts/compile_deck.py "$@" --json 2>/dev/null) || return 1
  python3 -c 'import json,sys
r=json.load(sys.stdin)
raise SystemExit(0 if r.get("ok") and r.get("overfull")==0 and isinstance(r.get("pages"),int) else 1)' \
    <<<"$output"
}

ship_clean() {
  local output
  output=$(python3 skills/econ-slides/scripts/check_deck.py "$1" --tex "$2" --log "$3" --json 2>/dev/null) || return 1
  python3 -c 'import json,sys
r=json.load(sys.stdin)
raise SystemExit(0 if r.get("verdict")=="ship" and not r.get("blockers") else 1)' \
    <<<"$output"
}

echo "== semantic interface under bundled themes and engines =="
for theme in econ-slides-house econ-slides-clean econ-slides-boxed; do
  src="tests/_iface-$theme.tex"
  sed "1,8s/\\\\def\\\\ecoslidestheme{econ-slides-house}/\\\\def\\\\ecoslidestheme{$theme}/" \
      tests/interface-test.tex > "$src"
  stem="_iface-$theme"
  if compile_clean "$src" --build-dir tests/build-suite \
      && ship_clean "tests/build-suite/$stem.pdf" "$src" "tests/build-suite/$stem.log"; then
    ok "interface is overfull-free and ships [$theme]"
  else
    bad "interface quality [$theme]"
  fi
  rm -f "$src"
done

echo "== multi-author title metadata stays mapped and readable =="
for theme in econ-slides-house econ-slides-clean econ-slides-boxed; do
  src="tests/_title-$theme.tex"
  sed "s/\\\\def\\\\ecoslidestheme{econ-slides-house}/\\\\def\\\\ecoslidestheme{$theme}/" \
      tests/title-metadata-test.tex > "$src"
  stem="_title-$theme"
  if compile_clean "$src" --build-dir tests/build-suite \
      && ship_clean "tests/build-suite/$stem.pdf" "$src" "tests/build-suite/$stem.log"; then
    ok "four-author title page compiles cleanly [$theme]"
  else
    bad "four-author title page [$theme]"
  fi
  rm -f "$src"
done

for theme in econ-slides-house econ-slides-clean econ-slides-boxed; do
  for engine in pdflatex lualatex; do
    src="tests/_engine-$theme-$engine.tex"
    sed "1,8s/\\\\def\\\\ecoslidestheme{econ-slides-house}/\\\\def\\\\ecoslidestheme{$theme}/" \
        tests/interface-test.tex > "$src"
    if compile_clean "$src" --engine "$engine" --build-dir tests/build-suite; then
      ok "interface compiles cleanly [$theme/$engine]"
    else
      bad "interface compile [$theme/$engine]"
    fi
    rm -f "$src"
  done
done

echo "== handout mode collapses, rather than overprinting, builds =="
sed 's/\\documentclass\[11pt, aspectratio=169\]{beamer}/\\documentclass[11pt, aspectratio=169, handout]{beamer}/' \
    tests/interface-test.tex > tests/_handout.tex
if compile_clean tests/_handout.tex --build-dir tests/build-suite; then
  HPAGES=$(python3 -c "import pymupdf; print(pymupdf.open('tests/build-suite/_handout.pdf').page_count)")
  [ "$HPAGES" = "7" ] && ok "handout collapses overlays (7 pages)" \
                      || bad "handout page count $HPAGES (want 7)"
else
  bad "handout compile"
fi
rm -f tests/_handout.tex

echo "== compatibility adapter on stock themes =="
for stock in Madrid CambridgeUS; do
  src="tests/_compat-$stock.tex"
  printf '\\def\\ecoslidesstocktheme{%s}\\def\\ecoslidestheme{econ-slides-compat}\\input{interface-test.tex}\n' "$stock" > "$src"
  stem="_compat-$stock"
  if compile_clean "$src" --build-dir tests/build-suite \
      && ship_clean "tests/build-suite/$stem.pdf" "$src" "tests/build-suite/$stem.log" \
      && python3 - "$stock" <<'PY'
import pymupdf as fitz, re, sys
stock = sys.argv[1]
text = fitz.open(f"tests/build-suite/_compat-{stock}.pdf")[-1].get_text()
raise SystemExit(0 if re.search(r"A\s*1", text) else 1)
PY
  then
    ok "compat is overfull-free, ships, and labels appendix A1 [$stock]"
  else
    bad "compat quality [$stock]"
  fi
  rm -f "$src"
done

echo "== templates embody the rendered standard under every theme =="
for tpl in paper-talk discussion; do
  for theme in econ-slides-house econ-slides-clean econ-slides-boxed; do
    src="skills/econ-slides/templates/_swap-$tpl-$theme.tex"
    sed "s/\\\\usepackage{econ-slides-[a-z]*}/\\\\usepackage{$theme}/" \
        "skills/econ-slides/templates/$tpl.tex" > "$src"
    stem="_swap-$tpl-$theme"
    if compile_clean "$src" --build-dir tests/build-suite \
        && ship_clean "tests/build-suite/$stem.pdf" "$src" "tests/build-suite/$stem.log"; then
      ok "$tpl template is overfull-free and ships [$theme]"
    else
      bad "$tpl template quality [$theme]"
    fi
    rm -f "$src"
  done
done

if compile_clean skills/econ-slides/templates/script.tex --build-dir tests/build-suite; then
  ok "speaker-script template compiles cleanly"
else
  bad "speaker-script template compile"
fi

if bash tests/run-theory-template-tests.sh >/dev/null; then
  ok "optional theory deck/script starters compile, ship, and stay synchronized"
else
  bad "theory deck/script starter regression"
fi

benchmark_contract() {
  local label="$1" source_dir="$2" expected_deck_pages="$3"
  local expected_main="$4" expected_script_pages="$5" expected_qa="$6"
  local build="tests/build-suite/benchmark-$label"
  mkdir -p "$build"
  if ! compile_clean "$source_dir/conference-30min.tex" --build-dir "$build" \
      || ! compile_clean "$source_dir/script.tex" --build-dir "$build"; then
    return 1
  fi
  python3 - "$source_dir" "$build" "$expected_deck_pages" \
      "$expected_main" "$expected_script_pages" "$expected_qa" <<'PY'
import pymupdf as fitz
import json
from pathlib import Path
import subprocess
import sys

source = Path(sys.argv[1])
build = Path(sys.argv[2])
expected_deck_pages = int(sys.argv[3])
expected_main = int(sys.argv[4])
expected_script_pages = int(sys.argv[5])
expected_qa = int(sys.argv[6])

deck = json.loads(subprocess.check_output([
    sys.executable, "skills/econ-slides/scripts/check_deck.py",
    str(build / "conference-30min.pdf"),
    "--tex", str(source / "conference-30min.tex"),
    "--log", str(build / "conference-30min.log"), "--json",
], text=True))
script = json.loads(subprocess.check_output([
    sys.executable, "skills/econ-slides/scripts/check_script.py", str(source / "script.tex"),
    "--deck", str(source / "conference-30min.tex"),
    "--slot-minutes", "30", "--json",
], text=True))

assert fitz.open(build / "conference-30min.pdf").page_count == expected_deck_pages
script_pdf = fitz.open(build / "script.pdf")
assert script_pdf.page_count == expected_script_pages
for page in list(script_pdf)[1:]:
    opening_lines = [line.strip() for line in page.get_text().splitlines()[:4]]
    assert not any(line.startswith("Live cue:") for line in opening_lines)
assert deck["pages"] == expected_deck_pages
assert deck["score"] == 100 and deck["verdict"] == "ship"
assert not deck["blockers"]
assert {item["check"] for item in deck["findings"]} <= {"layout-balance"}
assert script["main_blocks"] == expected_main
assert script["qa_blocks"] == expected_qa
assert script["timing_mode"] == "total-session"
assert 22.5 <= script["talking_minutes"] <= 24.0
assert script["qa_minutes"] == [6.0, 7.5]
assert not script["findings"]
PY
}

if benchmark_contract primary docs/sample-talk 23 11 9 9; then
  ok "30-minute staggered-rollout benchmark compiles, ships, and stays synchronized"
else
  bad "30-minute staggered-rollout benchmark contract"
fi

if python3 - <<'PY'
from pathlib import Path
from scripts.check_script import deck_frames, script_blocks, tex_tree
frames = deck_frames(tex_tree(Path("skills/econ-slides/templates/paper-talk.tex")))
_opening, blocks = script_blocks(tex_tree(Path("skills/econ-slides/templates/script.tex")))
main = [frame["title"] for frame in frames if not frame["appendix"]]
appendix = [frame["title"] for frame in frames if frame["appendix"]]
scripted = [block["title"] for block in blocks if block["kind"] == "main"]
qa = [block["title"] for block in blocks if block["kind"] == "qa"]
selected = [title for title in appendix if title in set(qa)]
raise SystemExit(0 if main == scripted and qa == selected else 1)
PY
then
  ok "paper and script templates have identical title order"
else
  bad "paper/script template synchronization"
fi

if python3 - <<'PY'
from pathlib import Path

paper = Path("skills/econ-slides/templates/paper-talk.tex").read_text()
discussion = Path("skills/econ-slides/templates/discussion.tex").read_text()
script = Path("skills/econ-slides/templates/script.tex").read_text()
results = Path("skills/econ-slides/templates/results.tex").read_text()
main = paper.split(r"\AppendixStart", 1)[0]
themes = [Path(path).read_text() for path in (
    "skills/econ-slides/themes/econ-slides-house.sty",
    "skills/econ-slides/themes/econ-slides-clean.sty",
    "skills/econ-slides/themes/econ-slides-boxed.sty",
    "skills/econ-slides/themes/econ-slides-compat.sty",
)]
interface = Path("tests/interface-test.tex").read_text()

assert r"\title[\PaperShortTitle]{\PaperTitle}" in paper
assert r"\newcommand{\PaperTitle}{[Exact paper title]}" in results
assert r"\subtitle" not in paper
assert r"\newcommand{\TitleDisclaimer}{}" in results
assert r"\begin{columns}" not in paper
assert r"\begin{columns}" not in discussion
assert "[Comment 1" not in discussion and "[Comment 2" not in discussion
assert "[State the first actionable comment]" in discussion
assert "[State the second actionable comment]" in discussion
assert r"\begin{minipage}" not in script
assert r"\begin{columns}" not in script
assert r"\newcommand{\Cue}[1]{\par\nobreak" in script
assert r"\begin{samepage}" + "\n" + r"\scriptframe{Conclusion}" in script
assert main.count(r"\begin{ResultBox}") <= 1
assert discussion.count(r"\begin{ResultBox}") <= 2
assert "design diagram" not in paper.lower()
assert "dag" not in paper.lower()
assert r"\item[$\Rightarrow$]" not in paper
assert r"\item[$\rightarrow$]" not in paper
assert "economic question" not in paper.lower()
assert "economic question" not in script.lower()
assert all(r"\newcommand{\KeyIdea}[1]{\textcolor{cHighlight}" not in src
           for src in themes)
assert all(r"\newlength{\ExhibitReadingGapRoomy}" in src for src in themes)
assert all(r"\newcommand{\Takeaway}[2][\ExhibitReadingGap]" in src
           for src in themes)
assert all(r"\newcommand{\TakeawayWithNav}[2][\ExhibitReadingGap]" in src
           for src in themes)
assert r"\TakeawayWithNav[\ExhibitReadingGapRoomy]" in interface
punch = paper.split(r"\begin{frame}{This paper}", 1)[1].split(
    r"\end{frame}", 1)[0]
close = paper.split(r"\begin{frame}{Conclusion}", 1)[1].split(
    r"\end{frame}", 1)[0]
assert punch.count(r"\KeyIdea") == 1
assert close.count(r"\KeyIdea") == 1
assert not any(token in close for token in (
    r"\PlaceNav", r"\hyperlink", r"\beamergotobutton", r"\beamerbutton",
    r"\BackButton"))
assert "[What the paper adds.]" not in punch + close
assert r"here at \VenueShort" in script

main_titles = []
import re
for match in re.finditer(
        r"\\begin\{frame\}(?:<[^>]*>)?(?:\[[^]]*\])?\s*\{([^{}]+)\}",
        main):
    main_titles.append(match.group(1))
assert "not a mandatory sequence" in paper.splitlines()[0].lower()
assert main_titles[:4] == [r"\KeyQuestion", "This paper", "Roadmap", "Data"]
roadmap = paper.split(r"\begin{frame}{Roadmap}", 1)[1].split(
    r"\end{frame}", 1)[0]
assert len(re.findall(r"\\item(?![A-Za-z@])", roadmap)) == 3
assert r"\textbf" not in roadmap and r"\bfseries" not in roadmap
for required in ("Sources and linkage", r"\RunIn{Sample:}",
                 r"\RunIn{Outcome:}", r"\RunIn{Treatment or exposure:}",
                 r"\RunIn{Key measure:}"):
    assert required in paper
assert len(re.findall(r"\\item(?![A-Za-z@])", close)) <= 3
PY
then
  ok "empirical starter contract: exact title, explicit adaptability, clean conclusion"
else
  bad "empirical starter contract"
fi

if python3 - <<'PY'
from pathlib import Path

skill = Path("skills/econ-slides/SKILL.md").read_text()
assert "For a **mixed paper**" in skill
mixed = skill.split("For a **mixed paper**", 1)[1].split("### Phase 2", 1)[0]
for concept in ("dependency", "mechanism", "disciplines or identifies",
                "quantifies", "prerequisite"):
    assert concept in mixed
PY
then
  ok "mixed-paper workflow orders model and evidence by economic dependency"
else
  bad "mixed-paper dependency workflow contract"
fi

echo "== deck checker positive and negative gates =="
compile_clean tests/interface-test.tex --build-dir tests/build-suite >/dev/null
SCORE=$(python3 skills/econ-slides/scripts/check_deck.py tests/build-suite/interface-test.pdf \
    --tex tests/interface-test.tex --log tests/build-suite/interface-test.log \
    --json 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin)['score'])")
[ "$SCORE" = "100" ] && ok "clean deck score is 100" \
                         || bad "clean deck score is $SCORE (want 100)"

compile_clean tests/violations-test.tex --build-dir tests/build-suite >/dev/null
CHECKS=$(python3 skills/econ-slides/scripts/check_deck.py tests/build-suite/violations-test.pdf \
    --tex tests/violations-test.tex --log tests/build-suite/violations-test.log \
    --json 2>/dev/null | python3 -c '
import json, sys
r=json.load(sys.stdin)
found={f["check"] for f in r["findings"]}
want={"wrapped-title", "wrapped-bullet", "edge-overflow", "density",
      "overfull", "pause-chain", "dead-link", "emphasis-overuse",
      "prose-columns", "arrow-bullet", "question-label",
      "question-subtitle", "roadmap-emphasis",
      "exhibit-reading", "conclusion-link",
      "conclusion-density"}
print("OK" if want <= found and r["verdict"]=="must fix"
      and sum(f["check"]=="emphasis-overuse" for f in r["findings"]) >= 2
      and sum(f["check"]=="prose-columns" for f in r["findings"]) >= 2
      else "MISSING:"+",".join(sorted(want-found)))')
[ "$CHECKS" = "OK" ] && ok "review detectors fire and objective violations block shipping" \
                         || bad "violation detectors: $CHECKS"

if python3 - <<'PY'
from pathlib import Path
from scripts.check_deck import DEDUCT, HARD_BLOCKERS, check_tex, score_findings, verdict_for

findings = check_tex(Path("tests/violations-test.tex"))
soft = {"question-subtitle", "roadmap-emphasis", "conclusion-density"}
selected = [finding for finding in findings if finding["check"] in soft]
counts = {name: sum(finding["check"] == name for finding in selected)
          for name in soft}
assert counts == {name: 1 for name in soft}
assert all(DEDUCT[name] == 0 and name not in HARD_BLOCKERS for name in soft)
assert verdict_for(score_findings(selected), []) == "ship"
conclusion = next(finding for finding in selected
                  if finding["check"] == "conclusion-density")
assert "rare case" in conclusion["detail"]
PY
then
  ok "question placement, Roadmap weight, and conclusion density stay soft and scoped"
else
  bad "soft deck-review diagnostic contract"
fi

compile_clean tests/static-footer-test.tex --build-dir tests/build-suite >/dev/null
STATIC=$(python3 skills/econ-slides/scripts/check_deck.py tests/build-suite/static-footer-test.pdf \
  --tex tests/static-footer-test.tex --log tests/build-suite/static-footer-test.log \
  --json 2>/dev/null | python3 -c '
import json,sys
r=json.load(sys.stdin)
print("OK" if any(f["check"]=="density" and f["page"]==1 for f in r["findings"])
      else "MISSED")')
[ "$STATIC" = "OK" ] && ok "static footers do not hide adjacent frames" \
                          || bad "static-footer grouping regression"

compile_clean tests/repeated-counter-test.tex --build-dir tests/build-suite >/dev/null
REPEATED=$(python3 skills/econ-slides/scripts/check_deck.py tests/build-suite/repeated-counter-test.pdf \
  --tex tests/repeated-counter-test.tex --log tests/build-suite/repeated-counter-test.log \
  --json 2>/dev/null | python3 -c '
import json,sys
r=json.load(sys.stdin)
print("OK" if any(f["check"]=="density" and f["page"]==1 for f in r["findings"])
      else "MISSED")')
[ "$REPEATED" = "OK" ] && ok "repeated numeric counters do not hide distinct frames" \
                              || bad "noframenumbering grouping regression"

compile_clean tests/sparse-test.tex --build-dir tests/build-suite >/dev/null
SPARSE=$(python3 skills/econ-slides/scripts/check_deck.py tests/build-suite/sparse-test.pdf \
  --tex tests/sparse-test.tex --log tests/build-suite/sparse-test.log \
  --json 2>/dev/null | python3 -c '
import json,sys
r=json.load(sys.stdin)
pages={f["page"] for f in r["findings"] if f["check"]=="layout-balance"}
print("OK" if {1,3} <= pages and r["verdict"]=="ship" else "MISSED")')
[ "$SPARSE" = "OK" ] && ok "sparse frames prompt review without forcing filler" \
                          || bad "sparse-frame regression"

compile_clean tests/nav-overlap-test.tex --build-dir tests/build-suite >/dev/null
NAV_OVERLAP=$(python3 skills/econ-slides/scripts/check_deck.py tests/build-suite/nav-overlap-test.pdf \
  --tex tests/nav-overlap-test.tex --log tests/build-suite/nav-overlap-test.log \
  --json 2>/dev/null | python3 -c '
import json,sys
r=json.load(sys.stdin)
print("OK" if any(f["check"]=="nav-footer-overlap" and f["page"]==1
                  for f in r["findings"]) else "MISSED")')
[ "$NAV_OVERLAP" = "OK" ] && ok "navigation/takeaway collisions are blocked" \
                                 || bad "navigation-overlap regression"

if python3 - <<'PY'
from pathlib import Path
from scripts.check_deck import check_tex
checks = check_tex(Path("tests/modular-link.tex"))
raise SystemExit(0 if not any(x["check"] == "dead-link" for x in checks) else 1)
PY
then
  ok "navigation targets resolve through local input files"
else
  bad "modular navigation target"
fi

if python3 - <<'PY'
from pathlib import Path
from scripts.check_deck import check_tex
checks = check_tex(Path("tests/ordinary-economic-question.tex"))
raise SystemExit(0 if not any(x["check"] == "question-label" for x in checks) else 1)
PY
then
  ok "ordinary prose may use economic question without relabeling the opening"
else
  bad "question-label scope regression"
fi

if python3 skills/econ-slides/scripts/check_deck.py tests/build-suite/interface-test.pdf \
     --tex tests/does-not-exist.tex >/dev/null 2>&1; then
  bad "explicitly missing checker input is rejected"
else
  ok "explicitly missing checker input is rejected"
fi

# Without --tex/--log the run is partial: it never ships, and says why.
python3 skills/econ-slides/scripts/check_deck.py tests/build-suite/interface-test.pdf \
  --json > tests/build-suite/partial.json 2>/dev/null
PARTIAL_STATUS=$?
PARTIAL_TEXT=$(python3 skills/econ-slides/scripts/check_deck.py \
  tests/build-suite/interface-test.pdf --log tests/build-suite/interface-test.log 2>/dev/null)
if python3 - "$PARTIAL_STATUS" "$PARTIAL_TEXT" <<'PY'
import json, sys
status, text = int(sys.argv[1]), sys.argv[2]
r = json.load(open("tests/build-suite/partial.json"))
assert status == 1 and r["verdict"] == "incomplete" and r["complete"] is False
assert "dead-link" in r["skipped_checks"] and "overfull" in r["skipped_checks"]
assert "— incomplete" in text and "ship" not in text.splitlines()[0]
assert "partial check: pass --tex" in text and "overfull" not in text.split("partial check")[1].split(";")[0]
PY
then
  ok "a run without --tex or --log is reported as incomplete, never ship"
else
  bad "partial checker run verdict"
fi

# A crash exits 3, so `|| [ "$?" -eq 1 ]` cannot mistake it for "must fix".
python3 - >/dev/null 2>&1 <<'PY'
import runpy, sys
import pymupdf
def boom(*args, **kwargs):
    raise RuntimeError("simulated PyMuPDF failure")
pymupdf.Page.get_text = boom
sys.argv = ["check_deck.py", "tests/build-suite/interface-test.pdf",
            "--tex", "tests/interface-test.tex",
            "--log", "tests/build-suite/interface-test.log", "--json"]
runpy.run_path("skills/econ-slides/scripts/check_deck.py", run_name="__main__")
PY
CRASH_STATUS=$?
[ "$CRASH_STATUS" = "3" ] && ok "a checker crash exits 3, apart from must-fix (1)" \
                          || bad "checker crash exit status is $CRASH_STATUS (want 3)"

# PyMuPDF 1.26.5 (the newest release for Python 3.9) has no Rect.get_area.
if python3 - >/dev/null 2>&1 <<'PY'
import runpy, sys
import pymupdf
for name in ("get_area", "getArea"):
    if hasattr(pymupdf.Rect, name):
        delattr(pymupdf.Rect, name)
sys.argv = ["check_deck.py", "tests/build-suite/sparse-test.pdf",
            "--tex", "tests/sparse-test.tex",
            "--log", "tests/build-suite/sparse-test.log", "--json"]
try:
    runpy.run_path("skills/econ-slides/scripts/check_deck.py", run_name="__main__")
except SystemExit as exc:
    raise SystemExit(0 if exc.code in (0, 1) else 1)
PY
then
  ok "checker runs on a PyMuPDF without Rect.get_area"
else
  bad "checker depends on Rect.get_area"
fi

echo "== existing-deck baseline comparison separates inherited regressions =="
BASELINE_FIXTURES_OK=1
for fixture in baseline-regression-base baseline-regression-shifted baseline-regression-new; do
  python3 skills/econ-slides/scripts/compile_deck.py "tests/$fixture.tex" \
    --build-dir tests/build-suite >/dev/null 2>&1 || BASELINE_FIXTURES_OK=0
done
if [ "$BASELINE_FIXTURES_OK" = "1" ]; then
  python3 skills/econ-slides/scripts/check_deck.py \
    tests/build-suite/baseline-regression-base.pdf \
    --tex tests/baseline-regression-base.tex \
    --log tests/build-suite/baseline-regression-base.log \
    --json > tests/build-suite/baseline-regression.json 2>/dev/null
  BASELINE_STATUS=$?

  python3 skills/econ-slides/scripts/check_deck.py \
    tests/build-suite/baseline-regression-shifted.pdf \
    --tex tests/baseline-regression-shifted.tex \
    --log tests/build-suite/baseline-regression-shifted.log \
    --baseline-json tests/build-suite/baseline-regression.json \
    --json > tests/build-suite/baseline-regression-shifted.json 2>/dev/null
  SHIFTED_STATUS=$?

  python3 skills/econ-slides/scripts/check_deck.py \
    tests/build-suite/baseline-regression-new.pdf \
    --tex tests/baseline-regression-new.tex \
    --log tests/build-suite/baseline-regression-new.log \
    --baseline-json tests/build-suite/baseline-regression.json \
    --json > tests/build-suite/baseline-regression-new.json 2>/dev/null
  NEW_STATUS=$?

  if python3 - "$BASELINE_STATUS" "$SHIFTED_STATUS" <<'PY'
import json
import sys
from scripts.check_deck import classify_blocker_regressions

baseline_status, shifted_status = map(int, sys.argv[1:])
baseline = json.load(open("tests/build-suite/baseline-regression.json"))
shifted = json.load(open("tests/build-suite/baseline-regression-shifted.json"))
inherited = shifted["inherited_blockers"]
assert baseline_status == 1 and shifted_status == 0
assert shifted["verdict"] == "ship" and shifted["blockers"] == []
assert shifted["score"] < 90 and shifted["regression_score"] == 100
assert {x["check"] for x in inherited} == {"edge-overflow", "overfull"}
assert any(x["check"] == "edge-overflow" and x["page"] == 2
           for x in inherited)
assert shifted["new_blockers"] == []
assert set(shifted["all_blockers"]) == {"edge-overflow", "overfull"}
assert baseline["pages"] == 1 and shifted["pages"] == 2

# Signature matching is a multiset: one moved occurrence is inherited, while
# an additional identical occurrence is still a regression.
base_finding = {
    "check": "edge-overflow", "page": 1,
    "detail": "text reaches x=460 of 454: 'same object'",
}
current_findings = [
    {**base_finding, "page": 7,
     "detail": "text reaches x=462 of 454: 'same object'"},
    {**base_finding, "page": 8},
]
matched, new, resolved = classify_blocker_regressions(
    current_findings, [base_finding]
)
assert len(matched) == 1 and len(new) == 1 and resolved == []
PY
  then
    ok "page-shifted objective blockers remain visible but do not fail a scoped edit"
  else
    bad "inherited-blocker baseline comparison"
  fi

  if python3 - "$NEW_STATUS" <<'PY'
import json
import sys

status = int(sys.argv[1])
result = json.load(open("tests/build-suite/baseline-regression-new.json"))
assert status == 1 and result["verdict"] == "must fix"
assert result["blockers"] == ["arrow-bullet"]
assert {x["check"] for x in result["inherited_blockers"]} == {
    "edge-overflow", "overfull"
}
assert [x["check"] for x in result["new_blockers"]] == ["arrow-bullet"]
PY
  then
    ok "a genuinely new objective blocker still fails against the baseline"
  else
    bad "new-blocker baseline comparison"
  fi
else
  bad "baseline-regression fixture compile"
  bad "new-blocker baseline fixture compile"
fi

CROP_ERR=$(python3 skills/econ-slides/scripts/crop_figure.py tests/build-suite/interface-test.pdf \
  --page 1 --bbox bad,input --out tests/build-suite/invalid.png 2>&1)
CROP_STATUS=$?
if [ "$CROP_STATUS" != "0" ] && [[ "$CROP_ERR" != *Traceback* ]]; then
  ok "crop tool rejects malformed coordinates without a traceback"
else
  bad "crop malformed-coordinate handling"
fi

echo "== script checker counts opening/main, excludes Q&A, and syncs builds =="
SCHECKS=$(python3 skills/econ-slides/scripts/check_script.py tests/script-sync/mini-script.tex \
    --deck tests/script-sync/mini-deck.tex --slot-minutes 15 --json 2>/dev/null | python3 -c '
import json, sys
result=json.load(sys.stdin)
found={f.split("]")[0].lstrip("[")
       for f in result["findings"] + result["warnings"]}
want={"title-sync", "oral-tells", "click-sync", "opening", "total-time"}
print("OK" if want <= found else "MISSING:"+",".join(sorted(want-found)))')
[ "$SCHECKS" = "OK" ] && ok "script negative fixture" \
                         || bad "script checks: $SCHECKS"

GOOD=$(python3 skills/econ-slides/scripts/check_script.py tests/script-sync/good-script.tex \
    --deck tests/script-sync/mini-deck.tex --slot-minutes 2 --json 2>/dev/null)
GOOD_STATUS=$?
GOOD_FIELDS=$(python3 -c '
import json,sys
r=json.load(sys.stdin)
print("OK" if r["main_blocks"]==2 and r["qa_blocks"]==1 and r["qa_words"]>0
      and r["planned_words"]==sum(x["words"] for x in r["blocks"])
      and not r["findings"] else "BAD")' <<<"$GOOD")
[ "$GOOD_STATUS" = "0" ] && [ "$GOOD_FIELDS" = "OK" ] \
  && ok "script positive fixture separates planned speech from Q&A" \
  || bad "script positive fixture"

REPEATED_TITLES=$(python3 skills/econ-slides/scripts/check_script.py \
    tests/script-sync/repeated-title-script.tex \
    --deck tests/script-sync/repeated-title-deck.tex \
    --speaking-minutes 2 --json 2>/dev/null)
REPEATED_TITLE_STATUS=$?
REPEATED_TITLE_FIELDS=$(python3 -c '
import json,sys
r=json.load(sys.stdin)
titles=[b["title"] for b in r["blocks"] if b["kind"]=="main"]
print("OK" if titles==["Roadmap", "Evidence", "Roadmap"]
      and r["timing_mode"]=="speaking-time"
      and r["slot_minutes"] is None and r["speaking_minutes"]==2
      and not r["findings"] else "BAD")' <<<"$REPEATED_TITLES")
[ "$REPEATED_TITLE_STATUS" = "0" ] && [ "$REPEATED_TITLE_FIELDS" = "OK" ] \
  && ok "repeated frame titles sync by occurrence under an explicit speaking clock" \
  || bad "repeated-title or speaking-clock regression"

if python3 - <<'PY'
import json
from pathlib import Path
import subprocess
import sys
import tempfile

opening = ("We begin with evidence. " * 10
           + "The question is simple. " * 3
           + "Listen closely.")
main = "Evidence matters. " * 168 + "Today."
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    deck = root / "deck.tex"
    script = root / "script.tex"
    deck.write_text(r"""\documentclass{beamer}
\begin{document}
\begin{frame}{Main result}Evidence\end{frame}
\end{document}
""")
    script.write_text(r"""\documentclass{article}
\newcommand{\scriptopening}[2]{#2}
\newcommand{\scriptframe}[3]{#3}
\begin{document}
\scriptopening{0.4 min}{%s}
\scriptframe{Main result}{2.5 min}{%s}
\end{document}
""" % (opening, main))
    result = json.loads(subprocess.check_output([
        sys.executable, "skills/econ-slides/scripts/check_script.py", str(script),
        "--deck", str(deck), "--speaking-minutes", "3", "--json",
    ], text=True))

main_block = next(block for block in result["blocks"]
                  if block["title"] == "Main result")
assert main_block["words"] == 337
assert not any("[word-budget] 'Main result'" in item
               for item in result["findings"] + result["warnings"])
assert not any("[time-label] 'Main result'" in item
               for item in result["findings"] + result["warnings"])
PY
then
  ok "a timed 337-word main explanation is judged by delivery time, not a fixed ceiling"
else
  bad "time-aware main-block delivery regression"
fi

if python3 skills/econ-slides/scripts/check_script.py tests/script-sync/good-script.tex \
     --deck tests/script-sync/mini-deck.tex --speaking-minutes 1 \
     >/dev/null 2>&1; then
  bad "explicit speaking allocation overrun"
else
  ok "explicit speaking allocation blocks overruns"
fi

# The speech window depends on genre and fails only on overruns.
if python3 - <<'PY'
import json, subprocess, sys
def run(*extra):
    proc = subprocess.run(
        [sys.executable, "skills/econ-slides/scripts/check_script.py",
         "docs/sample-talk/script.tex", "--deck",
         "docs/sample-talk/conference-30min.tex", "--json", *extra],
        capture_output=True, text=True)
    return proc.returncode, json.loads(proc.stdout)
def timing(result, bucket):
    return [x for x in result[bucket] if x.startswith("[total-time]")]
# 22.5 min of speech. Under the 32-min conference window: a warning only,
# and no fill target for the declared minute labels.
status, r = run("--slot-minutes", "32")
assert status == 0 and timing(r, "warnings") and not timing(r, "findings")
assert r["genre"] == "conference" and r["wpm"] == 135
assert not any("target about" in w for w in r["warnings"])
# Far below a 90-min seminar window: the warning names Piazzesi's 10 minutes.
status, r = run("--slot-minutes", "90", "--genre", "seminar")
assert status == 0 and "10 minutes early" in timing(r, "warnings")[0]
# Over the 28-min conference ceiling (22.4): a finding.
status, r = run("--slot-minutes", "28")
assert status == 1 and timing(r, "findings")
# Two thirds of a 34-min seminar slot fits the 60--70% seminar window.
status, r = run("--slot-minutes", "34", "--genre", "seminar")
assert status == 0 and not timing(r, "warnings") + timing(r, "findings")
assert r["speech_window_minutes"] == [20.4, 23.8]
# The same script overruns a 30-min seminar slot (at most 21 min).
status, r = run("--slot-minutes", "30", "--genre", "job-talk")
assert status == 1 and timing(r, "findings")
# A discussant has a ceiling and no floor.
status, r = run("--slot-minutes", "60", "--genre", "discussant")
assert status == 0 and not timing(r, "warnings") and r["qa_minutes"][1] is None
# A slower speaker turns a fitting script into an overrun.
status, r = run("--slot-minutes", "30", "--wpm", "115")
assert status == 1 and "115 wpm" in timing(r, "findings")[0]
PY
then
  ok "speech windows follow the genre, and only overruns fail"
else
  bad "genre-aware speech window"
fi

if python3 - <<'PY'
from scripts.check_script import (
    clean_title, has_semantic_build, overlay_max, overlay_specs, spoken_text,
    zero_arg_macros, ROADMAP_HARD_MIN, ROADMAP_PREFERRED_LO,
    ROADMAP_PREFERRED_HI, ROADMAP_HARD_MAX,
)
assert (ROADMAP_HARD_MIN, ROADMAP_PREFERRED_LO,
        ROADMAP_PREFERRED_HI, ROADMAP_HARD_MAX) == (20, 25, 45, 60)
assert overlay_specs(r"$0 < x < 2, y > 0$") == []
assert overlay_max(r"$x<2$ and later $y>0$") == 1
assert not has_semantic_build(r"$0 < x < 2$")
assert has_semantic_build(r"\only<+->{A}\uncover<+->{B}")
assert overlay_max(r"\only<+->{A}\uncover<+->{B}") == 2
assert has_semantic_build(r"\alert<2>{key term}")
assert not has_semantic_build(
    r"\begin{itemize}[<+->]\item one\item two\end{itemize}"
)
macros = zero_arg_macros(
    r"\newcommand{\ResMainSpoken}{a little over three percent}"
)
assert spoken_text(r"The effect is \ResMainSpoken today.", macros) == (
    "The effect is a little over three percent today."
)
assert clean_title(
    r"Can \textcolor{cMessage}{messages} raise \textbf{filing}?"
) == "Can messages raise filing?"
PY
then
  ok "script parser distinguishes builds, math inequalities, and shared macros"
else
  bad "script overlay/macro parser regression"
fi

sed -E 's/\\Click\{[0-9]+\}//g' tests/script-sync/good-script.tex \
  > tests/_missing-click-script.tex
MISSING_CLICK=$(python3 skills/econ-slides/scripts/check_script.py tests/_missing-click-script.tex \
    --deck tests/script-sync/mini-deck.tex --slot-minutes 3 --json 2>/dev/null | python3 -c '
import json,sys
r=json.load(sys.stdin)
print("OK" if any("semantic builds require" in f for f in r["findings"])
      else "MISSED")')
rm -f tests/_missing-click-script.tex
[ "$MISSING_CLICK" = "OK" ] && ok "semantic build requires ordered click markers" \
                                || bad "missing-click regression"

MISSING_QA=$(python3 skills/econ-slides/scripts/check_script.py tests/script-sync/missing-qa-script.tex \
    --deck tests/script-sync/mini-deck.tex --slot-minutes 3 --json 2>/dev/null | python3 -c '
import json,sys
r=json.load(sys.stdin)
print("OK" if not any("appendix frame has no Q&A block" in f
                      for f in r["findings"])
      else "REJECTED")')
[ "$MISSING_QA" = "OK" ] && ok "Q&A may cover selected high-probability backups" \
                             || bad "optional Q&A regression"

if python3 - <<'PY'
from scripts.compile_deck import find_error
figure = find_error("! LaTeX Error: File `figures/fig2' not found.\n\nl.3 \\includegraphics")
package = find_error("! LaTeX Error: File `needspacezz.sty' not found.\n\nl.2 \\usepackage")
assert "tlmgr" not in figure[1] and "path" in figure[1]
assert "tlmgr search --global --file /needspacezz.sty" in package[1]
# A figure named with its extension: XeTeX, pdfTeX and LuaTeX messages. The
# pdfTeX/LuaTeX lines exceed 79 columns, so TeX wraps them; the error is
# still read whole and the hint names the file.
for message in (
        "! Unable to load picture or PDF file 'figures/missing-plot.png'.\n"
        "<to be read again>",
        "! Package pdftex.def Error: File `figures/missing-plot.png' not found: using dr\n"
        "aft setting.",
        "! Package luatex.def Error: File `figures/missing-plot.png' not found: using dr\n"
        "aft setting."):
    line, hint = find_error(message)
    assert "Missing file figures/missing-plot.png" in hint and "tlmgr" not in hint, hint
    assert "using dr\n" not in line, line
PY
then
  ok "a missing figure (with or without extension) gets a path hint, a .sty a tlmgr hint"
else
  bad "missing-file triage hints"
fi

if python3 skills/econ-slides/scripts/check_script.py tests/script-sync/good-script.tex \
     --deck tests/script-sync/mini-deck.tex --slot-minutes 2 --wpm 0 >/dev/null 2>&1; then
  bad "nonpositive script timing input"
else
  ok "nonpositive script timing input is rejected"
fi

if python3 skills/econ-slides/scripts/compile_deck.py tests/interface-test.tex --passes 0 \
     >/dev/null 2>&1; then
  bad "nonpositive compile pass count"
else
  ok "nonpositive compile pass count is rejected"
fi

if python3 - <<'PY'
from scripts.compile_deck import page_count
wrapped = "Output written on /a/very/long/build/name.pdf (1\n3 pag\nes, 42 bytes)."
raise SystemExit(0 if page_count(wrapped) == 13 else 1)
PY
then
  ok "wrapped multi-digit page counts are parsed"
else
  bad "wrapped multi-digit page-count regression"
fi

echo "== a TeX error in the log blocks, and only this PDF's log is trusted =="
CE_OK=1
# compile_deck halts at the error; xelatex has still written page 1.
python3 skills/econ-slides/scripts/compile_deck.py tests/compile-error-test.tex \
  --build-dir tests/build-suite >/dev/null 2>&1 && CE_OK=0
ce() { python3 skills/econ-slides/scripts/check_deck.py "$@" --json 2>/dev/null; }
CE_HALT=$(ce tests/build-suite/compile-error-test.pdf --tex tests/compile-error-test.tex \
  --log tests/build-suite/compile-error-test.log); CE_HALT_STATUS=$?
# A nonstopmode build without -halt-on-error writes every page despite the error.
mkdir -p tests/build-suite/nonstop
(cd tests && TEXINPUTS=".:$PWD/../$SKILL_DIR/themes:" xelatex -interaction=nonstopmode \
  -output-directory=build-suite/nonstop compile-error-test.tex >/dev/null 2>&1)
CE_NONSTOP=$(ce tests/build-suite/nonstop/compile-error-test.pdf \
  --tex tests/compile-error-test.tex --log tests/build-suite/nonstop/compile-error-test.log)
CE_NONSTOP_STATUS=$?
MF_OUT=$(python3 skills/econ-slides/scripts/compile_deck.py tests/missing-figure-test.tex \
  --build-dir tests/build-suite --json 2>/dev/null)
compile_clean tests/nested-marker-test.tex --build-dir tests/build-suite || CE_OK=0
NESTED=$(ce tests/build-suite/nested-marker-test.pdf --tex tests/nested-marker-test.tex \
  --log tests/build-suite/nested-marker-test.log); NESTED_STATUS=$?
: > tests/build-suite/empty.log
LOG_STATUSES=""
for log in tests/build-suite/empty.log /dev/null tests/nested-marker-test.tex \
           tests/build-suite/compile-error-test.log; do
  python3 skills/econ-slides/scripts/check_deck.py tests/build-suite/nested-marker-test.pdf \
    --tex tests/nested-marker-test.tex --log "$log" >/dev/null 2>&1
  LOG_STATUSES="$LOG_STATUSES$?"
done
python3 skills/econ-slides/scripts/compile_deck.py tests/hyperref-dead-test.tex \
  --build-dir tests/build-suite >/dev/null 2>&1 || CE_OK=0
HYPER=$(ce tests/build-suite/hyperref-dead-test.pdf --tex tests/hyperref-dead-test.tex \
  --log tests/build-suite/hyperref-dead-test.log)
if [ "$CE_OK" = "1" ] && python3 - "$CE_HALT" "$CE_HALT_STATUS" "$CE_NONSTOP" \
     "$CE_NONSTOP_STATUS" "$MF_OUT" "$NESTED" "$NESTED_STATUS" "$LOG_STATUSES" \
     "$HYPER" <<'PY'
import json, sys
(halt, halt_status, nonstop, nonstop_status, missing_figure, nested,
 nested_status, log_statuses, hyper) = sys.argv[1:]
halt, nonstop, missing_figure, nested, hyper = map(
    json.loads, (halt, nonstop, missing_figure, nested, hyper))
for result, status in ((halt, halt_status), (nonstop, nonstop_status)):
    assert status == "1" and result["verdict"] == "must fix", result["verdict"]
    assert result["blockers"] == ["compile-error"], result["blockers"]
    assert any("Undefined control sequence" in f["detail"]
               for f in result["findings"] if f["check"] == "compile-error")
assert halt["pages"] == 1 and nonstop["pages"] == 2
# A figure path with an extension gets the path hint, not "Unrecognized".
assert not missing_figure["ok"] and "figures/missing-plot.png" in missing_figure["hint"]
# An allowance two \input levels down, resolved from the main file's folder.
assert nested_status == "0" and nested["allowed_literal_markers"], nested
# An empty log, /dev/null, the .tex itself, another deck's log: exit 2.
assert log_statuses == "2222", log_statuses
# A dead \hyperref is a dead link with its key, not an unexplained ??.
assert hyper["blockers"] == ["dead-link"], hyper["blockers"]
assert any("sec:nosuchbackup" in f["detail"] for f in hyper["findings"])
assert hyper["undefined_refs"] == 0
PY
then
  ok "compile errors block, foreign logs stop the check, nested inputs and dead hyperrefs resolve"
else
  bad "compile-error blocker or log validation"
fi

echo "== undefined citations and references never ship =="
UNDEF_COMPILE=$(python3 skills/econ-slides/scripts/compile_deck.py tests/undefined-ref-test.tex \
    --build-dir tests/build-suite --json 2>/dev/null)
if python3 -c '
import json,sys
r=json.load(sys.stdin)
keys={(u["kind"], u["key"]) for u in r["undefined"]}
raise SystemExit(0 if r["ok"] and r["undefined_refs"]==2 and keys=={
    ("citation","missingFixtureKey"), ("reference","tab:missing")} else 1)' \
    <<<"$UNDEF_COMPILE"; then
  ok "compile reports undefined citation and reference keys"
else
  bad "compile undefined-reference report"
fi

python3 skills/econ-slides/scripts/check_deck.py tests/build-suite/undefined-ref-test.pdf \
  --tex tests/undefined-ref-test.tex --log tests/build-suite/undefined-ref-test.log \
  --json > tests/build-suite/undefined-ref.json 2>/dev/null
UNDEF_STATUS=$?
python3 skills/econ-slides/scripts/check_deck.py tests/build-suite/undefined-ref-test.pdf \
  --json > tests/build-suite/undefined-ref-pdf-only.json 2>/dev/null
UNDEF_PDF_STATUS=$?
python3 skills/econ-slides/scripts/check_deck.py tests/build-suite/undefined-ref-test.pdf \
  --tex tests/undefined-ref-test.tex --log tests/build-suite/undefined-ref-test.log \
  --baseline-json tests/build-suite/undefined-ref.json \
  --json > tests/build-suite/undefined-ref-baseline.json 2>/dev/null
UNDEF_BASE_STATUS=$?
if python3 - "$UNDEF_STATUS" "$UNDEF_PDF_STATUS" "$UNDEF_BASE_STATUS" <<'PY'
import json
import sys

status, pdf_status, base_status = map(int, sys.argv[1:])
full = json.load(open("tests/build-suite/undefined-ref.json"))
pdf_only = json.load(open("tests/build-suite/undefined-ref-pdf-only.json"))
base = json.load(open("tests/build-suite/undefined-ref-baseline.json"))
assert status == 1 and full["verdict"] == "must fix"
assert "undefined-ref" in full["blockers"]
details = " ".join(f["detail"] for f in full["findings"]
                   if f["check"] == "undefined-ref")
assert "missingFixtureKey" in details and "tab:missing" in details
assert full["undefined_refs"] >= 3
# Without --log, the rendered [?] and ?? markers alone still block.
assert pdf_status == 1 and "undefined-ref" in pdf_only["blockers"]
# An inherited undefined reference is never waived by a baseline.
assert base_status == 1 and base["verdict"] == "must fix"
assert base["blockers"] == ["undefined-ref"]
assert base["new_blockers"]
assert all(item["non_waivable"] and item["in_baseline"]
           for item in base["new_blockers"])
assert base["resolved_blockers"] == []
PY
then
  ok "undefined citations/references block, even without a log or with a baseline"
else
  bad "undefined-reference blocker"
fi

# A deck may declare literal ?? / (?) text; a clean log is still required.
LIT_OK=1
compile_clean tests/literal-marker-test.tex --build-dir tests/build-suite || LIT_OK=0
lit() { python3 skills/econ-slides/scripts/check_deck.py "$@" --json 2>/dev/null; }
LIT_DECLARED=$(lit tests/build-suite/literal-marker-test.pdf \
  --tex tests/literal-marker-test.tex --log tests/build-suite/literal-marker-test.log)
LIT_DECLARED_STATUS=$?
LIT_UNDECLARED=$(lit tests/build-suite/literal-marker-test.pdf \
  --log tests/build-suite/literal-marker-test.log)
LIT_FLAG=$(lit tests/build-suite/literal-marker-test.pdf \
  --log tests/build-suite/literal-marker-test.log \
  --allow-literal-marker '(?)' --allow-literal-marker '??')
LIT_NOLOG=$(lit tests/build-suite/literal-marker-test.pdf --tex tests/literal-marker-test.tex)
LIT_REAL=$(lit tests/build-suite/undefined-ref-test.pdf \
  --tex tests/undefined-ref-test.tex --log tests/build-suite/undefined-ref-test.log \
  --allow-literal-marker '[?] ??')
python3 skills/econ-slides/scripts/check_deck.py tests/build-suite/literal-marker-test.pdf \
  --allow-literal-marker 'x' >/dev/null 2>&1
LIT_BAD_STATUS=$?
if [ "$LIT_OK" = "1" ] && python3 - "$LIT_DECLARED" "$LIT_DECLARED_STATUS" "$LIT_UNDECLARED" \
     "$LIT_FLAG" "$LIT_NOLOG" "$LIT_REAL" "$LIT_BAD_STATUS" <<'PY'
import json, sys
declared, declared_status, undeclared, flag, nolog, real, bad_status = sys.argv[1:]
declared, undeclared, flag, nolog, real = map(
    json.loads, (declared, undeclared, flag, nolog, real))
# Declared in the source and the log is clean: waived, and the deck ships.
assert declared_status == "0" and declared["verdict"] == "ship"
assert declared["allowed_literal_markers"] and declared["undefined_refs"] == 0
# Not declared: the literal markers still block.
assert "undefined-ref" in undeclared["blockers"]
# The CLI flag does the same as the source comment.
assert "undefined-ref" not in flag["blockers"] and flag["allowed_literal_markers"]
# Without --log nothing is waived.
assert "undefined-ref" in nolog["blockers"]
# A real undefined key in the log keeps even declared markers blocking.
assert "undefined-ref" in real["blockers"] and not real["allowed_literal_markers"]
assert any(f.get("allowed_literal") for f in real["findings"])
assert bad_status == "2"
PY
then
  ok "declared literal ?? and (?) are waived only with a clean log"
else
  bad "literal-marker allowance"
fi

if python3 - <<'PY'
from scripts.check_deck import UNRESOLVED_MARKER_RE
from scripts.compile_deck import undefined_references, undefined_count

wrapped = (
    "Package natbib Warning: Citation `missingkey' on page 1 undefined on input line\n"
    " 6.\n\n"
    "Package natbib Warning: Citation `thisisaveryveryveryveryverylongcitationkeynam\n"
    "e2024abc' on page 1 undefined on input line 6.\n"
    "LaTeX Warning: Citation 'blkey' on page 2 undefined on input line 7.\n"
    "LaTeX Warning: Citation 'blkey' on page 3 undefined on input line 9.\n"
    # Captured from pdflatex/natbib logs: a 40-48 character key moves TeX's
    # 79-column break into "on page N undefined" itself.
    "LaTeX Warning: Citation `angristPischke2009mostlyHarmlessEconometrics' on page \n"
    "1 undefined on input line 3.\n"
    "LaTeX Warning: Citation `chettyFriedmanRockoff2014teacherValueAddedBiasAb' on p\n"
    "age 1 undefined on input line 4.\n"
    "LaTeX Warning: Reference `imbensRubin2015causalInferenceStatistics' on page 1 u\n"
    "ndefined on input line 5.\n"
    "Package natbib Warning: Citation `chettyFriedmanRockoff2014teacherValueAddedBia\n"
    "sAb' on page 1 undefined on input line 5.\n"
)
info = undefined_references(wrapped)
keys = [item["key"] for item in info["items"]]
assert keys == ["missingkey",
                "thisisaveryveryveryveryverylongcitationkeyname2024abc",
                "blkey",
                "angristPischke2009mostlyHarmlessEconometrics",
                "chettyFriedmanRockoff2014teacherValueAddedBiasAb",
                "imbensRubin2015causalInferenceStatistics"], keys
assert [item["kind"] for item in info["items"]][-1] == "reference"
assert undefined_count(undefined_references(
    "Package biblatex Warning: Please (re)run Biber on the file:")) == 1
assert undefined_count(undefined_references("No warnings here.")) == 0
text = "Effects match [?, ?] and Table ??. Authors (?) agree. What?? Why? [1]"
assert UNRESOLVED_MARKER_RE.findall(text) == ["[?, ?]", "??", "(?)"]
PY
then
  ok "undefined-reference parsers handle wrapped, natbib, and biblatex forms"
else
  bad "undefined-reference parser regression"
fi

BIB_COMPILE=$(python3 skills/econ-slides/scripts/compile_deck.py tests/bib-test.tex \
    --build-dir tests/build-suite --json 2>/dev/null)
if python3 -c '
import json,sys
import pymupdf
r=json.load(sys.stdin)
text="".join(page.get_text() for page in pymupdf.open(r["pdf"]))
raise SystemExit(0 if r["ok"] and r["bibliography"]["tool"]=="bibtex"
                 and r["bibliography"]["ran"] and r["undefined_refs"]==0
                 and "[?]" not in text and "[1]" in text
                 and "fictional rollout fixture" in text.lower() else 1)' \
    <<<"$BIB_COMPILE" \
    && ship_clean tests/build-suite/bib-test.pdf tests/bib-test.tex \
       tests/build-suite/bib-test.log; then
  ok "compile runs BibTeX for a \\bibliography deck, which then ships"
else
  bad "bibliography-aware compile"
fi

# BibTeX runs from the source folder, so \bibliography{../x} resolves, and a
# prebuilt .bbl beside the source survives a missing database. Build folders
# outside the source, hidden ones, and the source folder itself all count.
cited_clean() {
  python3 -c '
import json,sys
import pymupdf
r=json.load(sys.stdin)
text="".join(page.get_text() for page in pymupdf.open(r["pdf"]))
raise SystemExit(0 if r["ok"] and r["undefined_refs"]==0
                 and "[?]" not in text and "[1]" in text
                 and "fictional rollout fixture" in text.lower() else 1)'
}
# (tests/bib-subdir/build is the default build folder; the trap removes it.)
for case in "tests/bib-subdir/bib-parent-test.tex tests/bib-subdir/build" \
            "tests/bib-subdir/bib-parent-test.tex tests/build-suite/relative" \
            "tests/bib-subdir/bib-parent-test.tex tests/build-suite/.hidden-build" \
            "tests/bbl-only/bbl-only-test.tex tests/build-suite/bbl-only" \
            "tests/bib-subdir/biblatex-bibtex-test.tex tests/bib-subdir/build" \
            "tests/bib-subdir/biblatex-bibtex-test.tex tests/build-suite/biblatex-bibtex"; do
  read -r src build <<<"$case"
  stem=$(basename "$src" .tex)
  args=(--build-dir "$build")
  [ "$build" = "tests/bib-subdir/build" ] && args=()
  # ${args[@]+...}: bash 3.2 (macOS) treats an empty array as unset under -u.
  if python3 skills/econ-slides/scripts/compile_deck.py "$src" ${args[@]+"${args[@]}"} \
        --json 2>/dev/null | cited_clean \
      && ship_clean "$build/$stem.pdf" "$src" "$build/$stem.log"; then
    ok "citations resolve and the deck ships [$stem -> $build]"
  else
    bad "source-relative bibliography [$stem -> $build]"
  fi
done
rm -rf tests/bib-subdir/build
# Biber is optional: some TeX installs ship a binary that cannot run.
if biber --version >/dev/null 2>&1; then
  build=tests/build-suite/biblatex
  if python3 skills/econ-slides/scripts/compile_deck.py \
        tests/bib-subdir/biblatex-parent-test.tex --build-dir "$build" \
        --json 2>/dev/null | cited_clean \
      && ship_clean "$build/biblatex-parent-test.pdf" \
         tests/bib-subdir/biblatex-parent-test.tex "$build/biblatex-parent-test.log"; then
    ok "Biber resolves an \\addbibresource{../x.bib} from the source folder"
  else
    bad "source-relative Biber datasource"
  fi
else
  echo "  SKIP  source-relative Biber datasource (biber does not run here)"
fi
inplace=tests/build-suite/bbl-in-place
rm -rf "$inplace"; mkdir -p "$inplace"
cp tests/bbl-only/bbl-only-test.tex tests/bbl-only/bbl-only-test.bbl "$inplace/"
if python3 skills/econ-slides/scripts/compile_deck.py "$inplace/bbl-only-test.tex" \
      --build-dir "$inplace" --json 2>/dev/null | cited_clean \
    && cmp -s "$inplace/bbl-only-test.bbl" tests/bbl-only/bbl-only-test.bbl \
    && ship_clean "$inplace/bbl-only-test.pdf" "$inplace/bbl-only-test.tex" \
       "$inplace/bbl-only-test.log"; then
  ok "an in-place build keeps the prebuilt .bbl when the database is missing"
else
  bad "in-place prebuilt .bbl preservation"
fi

printf '%s\n' '\documentclass{article}' '\begin{document}' \
  '\def\loopforever{\loopforever}\loopforever' '\end{document}' > tests/_loop.tex
LOOP_OUT=$(python3 skills/econ-slides/scripts/compile_deck.py tests/_loop.tex --timeout 2 \
    --build-dir tests/build-suite --json 2>&1)
LOOP_STATUS=$?
if [ "$LOOP_STATUS" = "1" ] && [[ "$LOOP_OUT" != *Traceback* ]] \
    && python3 -c '
import json,sys
r=json.load(sys.stdin)
raise SystemExit(0 if not r["ok"] and "timed out after 2s" in r["error"] else 1)' \
    <<<"$LOOP_OUT"; then
  ok "engine timeout is reported as JSON, not a traceback"
else
  bad "engine timeout handling"
fi
rm -f tests/_loop.tex

if python3 skills/econ-slides/scripts/compile_deck.py tests/interface-test.tex --timeout 0 \
     >/dev/null 2>&1; then
  bad "nonpositive compile timeout"
else
  ok "nonpositive compile timeout is rejected"
fi

echo "== engine choice and non-UTF-8 locales =="
# A % !TEX program line picks the engine when --engine is not given.
printf '%s\n' '% !TEX program = pdflatex' '\documentclass{beamer}' \
  '\input{glyphtounicode}' '\pdfgentounicode=1' '\begin{document}' \
  '\begin{frame}{Engine directive}' 'Built with pdfLaTeX.' '\end{frame}' \
  '\end{document}' > tests/_directive.tex
DIRECTIVE_OUT=$(python3 skills/econ-slides/scripts/compile_deck.py tests/_directive.tex \
    --build-dir tests/build-suite/directive 2>&1)
DIRECTIVE_STATUS=$?
if [ "$DIRECTIVE_STATUS" = "0" ] \
    && [[ "$DIRECTIVE_OUT" == *"engine: pdflatex (from % !TEX program)"* ]]; then
  ok "a % !TEX program = pdflatex line selects pdfLaTeX"
else
  bad "engine directive [$DIRECTIVE_STATUS]"
fi
# An explicit --engine still wins, and the hint names the pdfTeX primitive.
FORCED_OUT=$(python3 skills/econ-slides/scripts/compile_deck.py tests/_directive.tex \
    --engine xelatex --build-dir tests/build-suite/directive-xe --json 2>/dev/null)
FORCED_STATUS=$?
if [ "$FORCED_STATUS" = "1" ] && python3 -c '
import json,sys
r=json.load(sys.stdin)
raise SystemExit(0 if not r["ok"] and r["engine"]=="xelatex"
                 and r["engine_source"]=="flag"
                 and "pdfTeX-only primitive" in r["hint"]
                 and "--engine pdflatex" in r["hint"] else 1)' <<<"$FORCED_OUT"; then
  ok "--engine overrides the directive and the hint names a pdfTeX-only primitive"
else
  bad "explicit engine or pdfTeX-primitive hint [$FORCED_STATUS]"
fi
rm -f tests/_directive.tex

# TeX output is UTF-8 whatever the locale: a GBK locale and a CJK folder name
# used to crash the helper (exit 3) while decoding the engine's output.
GBK=$(locale -a 2>/dev/null | grep -i -m1 -E '^zh_CN\.gbk$')
if [ -n "$GBK" ]; then
  cjk="tests/build-suite/讲稿"
  rm -rf "$cjk"; mkdir -p "$cjk"
  printf '%s\n' '\documentclass{beamer}' '\begin{document}' \
    '\begin{frame}{Locale}' 'A deck in a CJK folder.' '\end{frame}' \
    '\end{document}' > "$cjk/deck.tex"
  if env -u PYTHONUTF8 LC_ALL="$GBK" python3 skills/econ-slides/scripts/compile_deck.py \
       "$cjk/deck.tex" >/dev/null 2>&1; then
    ok "compiles under a $GBK locale in a CJK-named folder"
  else
    bad "non-UTF-8 locale compile"
  fi
else
  echo "  SKIP  non-UTF-8 locale compile (no zh_CN.GBK locale here)"
fi

echo "== characters missing from the font =="
# A β or ≥ typed in text is dropped by the house theme's text font: a blocker.
printf '%s\n' '\documentclass[aspectratio=169,11pt]{beamer}' \
  '\usepackage{econ-slides-house}' '\begin{document}' \
  '\begin{frame}{Effect of the reform on employment}' '\begin{itemize}' \
  '  \item Effect ≥ 5 percent in rural counties' \
  '  \item The elasticity is β = 0.4 for teens' '\end{itemize}' \
  '\Takeaway{The decline is concentrated in rural counties.}' '\end{frame}' \
  '\end{document}' > tests/_glyph.tex
GLYPH_OUT=$(python3 skills/econ-slides/scripts/compile_deck.py tests/_glyph.tex \
    --build-dir tests/build-suite 2>&1)
GLYPH_CHECK=$(python3 skills/econ-slides/scripts/check_deck.py tests/build-suite/_glyph.pdf \
    --tex tests/_glyph.tex --log tests/build-suite/_glyph.log 2>&1)
GLYPH_STATUS=$?
if [[ "$GLYPH_OUT" == *"warning: 2 characters are missing from the font"* ]] \
    && [ "$GLYPH_STATUS" = "1" ] && [[ "$GLYPH_CHECK" == *"[missing-glyph]"* ]] \
    && [[ "$GLYPH_CHECK" == *"'β' (U+03B2) is missing from font"* ]]; then
  ok "a character missing from the font is reported and blocks delivery"
else
  bad "missing-glyph blocker [$GLYPH_STATUS]"
fi
# A stray character inside a TikZ picture lands in nullfont: a note only.
printf '%s\n' '\documentclass[aspectratio=169,11pt]{beamer}' \
  '\usepackage{econ-slides-house}' '\usepackage{tikz}' '\begin{document}' \
  '\begin{frame}{A rule drawn with a stray semicolon}' '\centering' \
  '\begin{tikzpicture}\draw (0,0) -- (3,0);;\end{tikzpicture}' \
  '\Takeaway{The rule still draws; the extra semicolon is dropped.}' \
  '\end{frame}' '\end{document}' > tests/_nullfont.tex
if compile_clean tests/_nullfont.tex --build-dir tests/build-suite; then
  NULL_CHECK=$(python3 skills/econ-slides/scripts/check_deck.py tests/build-suite/_nullfont.pdf \
      --tex tests/_nullfont.tex --log tests/build-suite/_nullfont.log 2>&1)
  NULL_STATUS=$?
else
  NULL_CHECK=""; NULL_STATUS=compile
fi
if [ "$NULL_STATUS" = "0" ] && [[ "$NULL_CHECK" == *"[lost-char]"* ]] \
    && [[ "$NULL_CHECK" != *"[missing-glyph]"* ]]; then
  ok "a stray TikZ character is a lost-char note and the deck still ships"
else
  bad "lost-char note [$NULL_STATUS]"
fi
rm -f tests/_glyph.tex tests/_nullfont.tex

echo "== conclusion and roadmap title variants =="
printf '%s\n' '\documentclass[aspectratio=169,11pt]{beamer}' \
  '\usepackage{econ-slides-house}' '\begin{document}' \
  '\begin{frame}{Conclusions}' '\begin{itemize}' \
  '  \item Broadband raised small-firm productivity' \
  '  \item The gain tracks communication intensity' '\end{itemize}' \
  '\hyperlink{bk}{\beamergotobutton{Backup}}' '\end{frame}' '\appendix' \
  '\begin{frame}{Backup}\hypertarget{bk}{}' 'Detail' '\end{frame}' \
  '\end{document}' > tests/_conclusions.tex
if compile_clean tests/_conclusions.tex --build-dir tests/build-suite; then
  CONC_OUT=$(python3 skills/econ-slides/scripts/check_deck.py tests/build-suite/_conclusions.pdf \
      --tex tests/_conclusions.tex --log tests/build-suite/_conclusions.log 2>&1)
  CONC_STATUS=$?
else
  CONC_OUT=""; CONC_STATUS=compile
fi
if [ "$CONC_STATUS" = "1" ] && [[ "$CONC_OUT" == *"[conclusion-link]"* ]]; then
  ok "a navigation button on a 'Conclusions' slide blocks delivery"
else
  bad "conclusion title variant [$CONC_STATUS]"
fi
rm -f tests/_conclusions.tex

echo "== TODO placeholders are listed, never scored =="
printf '%s\n' '\documentclass[aspectratio=169,11pt]{beamer}' \
  '\usepackage{econ-slides-house}' \
  '\newcommand{\TODO}[1]{\textcolor{cAccentB}{\textbf{TODO: #1}}}' \
  '\begin{document}' '\begin{frame}{Productivity rose after broadband arrived}' \
  '\begin{itemize}' '  \item Revenue per worker: +3.4 percent' \
  '  \item Standard error: \TODO{need SE for col 3}' '\end{itemize}' \
  '\Takeaway{The gain is concentrated in communication-intensive firms.}' \
  '\end{frame}' '\end{document}' > tests/_todo.tex
if compile_clean tests/_todo.tex --build-dir tests/build-suite; then
  TODO_JSON=$(python3 skills/econ-slides/scripts/check_deck.py tests/build-suite/_todo.pdf \
      --tex tests/_todo.tex --log tests/build-suite/_todo.log --json 2>/dev/null)
  TODO_STATUS=$?
  TODO_PDF=$(python3 skills/econ-slides/scripts/check_deck.py tests/build-suite/_todo.pdf \
      --log tests/build-suite/_todo.log --json 2>/dev/null)
else
  TODO_JSON="{}"; TODO_PDF="{}"; TODO_STATUS=compile
fi
if [ "$TODO_STATUS" = "0" ] && python3 - "$TODO_JSON" "$TODO_PDF" <<'PY'
import json, sys
full, pdf_only = (json.loads(arg) for arg in sys.argv[1:])
todo = [f for f in full["findings"] if f["check"] == "todo-placeholder"]
assert full["verdict"] == "ship" and full["score"] == 100 and len(todo) == 1
assert "need SE for col 3" in todo[0]["detail"]
pdf_todo = [f for f in pdf_only["findings"] if f["check"] == "todo-placeholder"]
assert [f["page"] for f in pdf_todo] == [1]
PY
then
  ok "a \\TODO placeholder is listed (source and PDF) and costs no points"
else
  bad "todo-placeholder prompt [$TODO_STATUS]"
fi
rm -f tests/_todo.tex

echo "== plugin packaging stays consistent =="
if python3 - <<'PY'
import json
import re
from pathlib import Path

claude = json.loads(Path(".claude-plugin/plugin.json").read_text())
codex = json.loads(Path(".codex-plugin/plugin.json").read_text())
skill = Path("skills/econ-slides/SKILL.md").read_text()
front = skill.split("---", 2)[1]
assert re.search(r"^name: econ-slides$", front, re.M)
version = re.search(r'^  version: "([^"]+)"$', front, re.M).group(1)
assert claude["name"] == codex["name"] == "econ-slides"
assert claude["version"] == codex["version"] == version
assert claude["skills"] == codex["skills"] == "./skills/"
assert claude["license"] == codex["license"] == "MIT"
assert {k: v for k, v in codex.items() if k != "interface"} == claude
prompts = codex["interface"]["defaultPrompt"]
assert 1 <= len(prompts) <= 3
assert all(len(p) <= 128 and "econ-slides" in p for p in prompts)
# One copy of the skill: no root SKILL.md shim, no top-level Beamer themes/.
assert not Path("SKILL.md").exists() and not Path("themes").exists()
assert [p.parent.name for p in Path("skills").glob("*/SKILL.md")] == ["econ-slides"]
changelog = Path("CHANGELOG.md").read_text()
assert f"## {version} " in changelog
PY
then
  ok "plugin manifests, skill metadata, and CHANGELOG agree on name and version"
else
  bad "plugin packaging consistency"
fi

echo
echo "$PASS passed, $FAIL failed"
exit $((FAIL > 0))
