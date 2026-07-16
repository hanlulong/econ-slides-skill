#!/usr/bin/env bash
# econ-slides test suite. Requires a TeX Live engine, Python 3, and PyMuPDF.
#   bash tests/run-tests.sh
set -uo pipefail
cd "$(dirname "$0")/.."
PASS=0; FAIL=0
ok()  { echo "  PASS  $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL  $1"; FAIL=$((FAIL+1)); }

compile_clean() {
  local output
  output=$(python3 scripts/compile_deck.py "$@" --json 2>/dev/null) || return 1
  python3 -c 'import json,sys
r=json.load(sys.stdin)
raise SystemExit(0 if r.get("ok") and r.get("overfull")==0 and isinstance(r.get("pages"),int) else 1)' \
    <<<"$output"
}

ship_clean() {
  local output
  output=$(python3 scripts/check_deck.py "$1" --tex "$2" --log "$3" --json 2>/dev/null) || return 1
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
  HPAGES=$(python3 -c "import fitz; print(fitz.open('tests/build-suite/_handout.pdf').page_count)")
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
import fitz, re, sys
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
    src="templates/_swap-$tpl-$theme.tex"
    sed "s/\\\\usepackage{econ-slides-[a-z]*}/\\\\usepackage{$theme}/" \
        "templates/$tpl.tex" > "$src"
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

if compile_clean templates/script.tex --build-dir tests/build-suite; then
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
import fitz
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
    sys.executable, "scripts/check_deck.py",
    str(build / "conference-30min.pdf"),
    "--tex", str(source / "conference-30min.tex"),
    "--log", str(build / "conference-30min.log"), "--json",
], text=True))
script = json.loads(subprocess.check_output([
    sys.executable, "scripts/check_script.py", str(source / "script.tex"),
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

if benchmark_contract primary docs/sample-talk 23 11 9 8; then
  ok "30-minute staggered-rollout benchmark compiles, ships, and stays synchronized"
else
  bad "30-minute staggered-rollout benchmark contract"
fi

if python3 - <<'PY'
from pathlib import Path
from scripts.check_script import deck_frames, script_blocks, tex_tree
frames = deck_frames(tex_tree(Path("templates/paper-talk.tex")))
_opening, blocks = script_blocks(tex_tree(Path("templates/script.tex")))
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

paper = Path("templates/paper-talk.tex").read_text()
discussion = Path("templates/discussion.tex").read_text()
script = Path("templates/script.tex").read_text()
results = Path("templates/results.tex").read_text()
main = paper.split(r"\AppendixStart", 1)[0]
themes = [Path(path).read_text() for path in (
    "themes/econ-slides-house.sty",
    "themes/econ-slides-clean.sty",
    "themes/econ-slides-boxed.sty",
    "themes/econ-slides-compat.sty",
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

skill = Path("SKILL.md").read_text()
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
SCORE=$(python3 scripts/check_deck.py tests/build-suite/interface-test.pdf \
    --tex tests/interface-test.tex --log tests/build-suite/interface-test.log \
    --json 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin)['score'])")
[ "$SCORE" = "100" ] && ok "clean deck score is 100" \
                         || bad "clean deck score is $SCORE (want 100)"

compile_clean tests/violations-test.tex --build-dir tests/build-suite >/dev/null
CHECKS=$(python3 scripts/check_deck.py tests/build-suite/violations-test.pdf \
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
STATIC=$(python3 scripts/check_deck.py tests/build-suite/static-footer-test.pdf \
  --tex tests/static-footer-test.tex --log tests/build-suite/static-footer-test.log \
  --json 2>/dev/null | python3 -c '
import json,sys
r=json.load(sys.stdin)
print("OK" if any(f["check"]=="density" and f["page"]==1 for f in r["findings"])
      else "MISSED")')
[ "$STATIC" = "OK" ] && ok "static footers do not hide adjacent frames" \
                          || bad "static-footer grouping regression"

compile_clean tests/repeated-counter-test.tex --build-dir tests/build-suite >/dev/null
REPEATED=$(python3 scripts/check_deck.py tests/build-suite/repeated-counter-test.pdf \
  --tex tests/repeated-counter-test.tex --log tests/build-suite/repeated-counter-test.log \
  --json 2>/dev/null | python3 -c '
import json,sys
r=json.load(sys.stdin)
print("OK" if any(f["check"]=="density" and f["page"]==1 for f in r["findings"])
      else "MISSED")')
[ "$REPEATED" = "OK" ] && ok "repeated numeric counters do not hide distinct frames" \
                              || bad "noframenumbering grouping regression"

compile_clean tests/sparse-test.tex --build-dir tests/build-suite >/dev/null
SPARSE=$(python3 scripts/check_deck.py tests/build-suite/sparse-test.pdf \
  --tex tests/sparse-test.tex --log tests/build-suite/sparse-test.log \
  --json 2>/dev/null | python3 -c '
import json,sys
r=json.load(sys.stdin)
pages={f["page"] for f in r["findings"] if f["check"]=="layout-balance"}
print("OK" if {1,3} <= pages and r["verdict"]=="ship" else "MISSED")')
[ "$SPARSE" = "OK" ] && ok "sparse frames prompt review without forcing filler" \
                          || bad "sparse-frame regression"

compile_clean tests/nav-overlap-test.tex --build-dir tests/build-suite >/dev/null
NAV_OVERLAP=$(python3 scripts/check_deck.py tests/build-suite/nav-overlap-test.pdf \
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

if python3 scripts/check_deck.py tests/build-suite/interface-test.pdf \
     --tex tests/does-not-exist.tex >/dev/null 2>&1; then
  bad "explicitly missing checker input is rejected"
else
  ok "explicitly missing checker input is rejected"
fi

echo "== existing-deck baseline comparison separates inherited regressions =="
BASELINE_FIXTURES_OK=1
for fixture in baseline-regression-base baseline-regression-shifted baseline-regression-new; do
  python3 scripts/compile_deck.py "tests/$fixture.tex" \
    --build-dir tests/build-suite >/dev/null 2>&1 || BASELINE_FIXTURES_OK=0
done
if [ "$BASELINE_FIXTURES_OK" = "1" ]; then
  python3 scripts/check_deck.py \
    tests/build-suite/baseline-regression-base.pdf \
    --tex tests/baseline-regression-base.tex \
    --log tests/build-suite/baseline-regression-base.log \
    --json > tests/build-suite/baseline-regression.json 2>/dev/null
  BASELINE_STATUS=$?

  python3 scripts/check_deck.py \
    tests/build-suite/baseline-regression-shifted.pdf \
    --tex tests/baseline-regression-shifted.tex \
    --log tests/build-suite/baseline-regression-shifted.log \
    --baseline-json tests/build-suite/baseline-regression.json \
    --json > tests/build-suite/baseline-regression-shifted.json 2>/dev/null
  SHIFTED_STATUS=$?

  python3 scripts/check_deck.py \
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

CROP_ERR=$(python3 scripts/crop_figure.py tests/build-suite/interface-test.pdf \
  --page 1 --bbox bad,input --out tests/build-suite/invalid.png 2>&1)
CROP_STATUS=$?
if [ "$CROP_STATUS" != "0" ] && [[ "$CROP_ERR" != *Traceback* ]]; then
  ok "crop tool rejects malformed coordinates without a traceback"
else
  bad "crop malformed-coordinate handling"
fi

echo "== script checker counts opening/main, excludes Q&A, and syncs builds =="
SCHECKS=$(python3 scripts/check_script.py tests/script-sync/mini-script.tex \
    --deck tests/script-sync/mini-deck.tex --slot-minutes 15 --json 2>/dev/null | python3 -c '
import json, sys
result=json.load(sys.stdin)
found={f.split("]")[0].lstrip("[")
       for f in result["findings"] + result["warnings"]}
want={"title-sync", "oral-tells", "click-sync", "opening", "total-time"}
print("OK" if want <= found else "MISSING:"+",".join(sorted(want-found)))')
[ "$SCHECKS" = "OK" ] && ok "script negative fixture" \
                         || bad "script checks: $SCHECKS"

GOOD=$(python3 scripts/check_script.py tests/script-sync/good-script.tex \
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

REPEATED_TITLES=$(python3 scripts/check_script.py \
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
        sys.executable, "scripts/check_script.py", str(script),
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

if python3 scripts/check_script.py tests/script-sync/good-script.tex \
     --deck tests/script-sync/mini-deck.tex --speaking-minutes 1 \
     >/dev/null 2>&1; then
  bad "explicit speaking allocation overrun"
else
  ok "explicit speaking allocation blocks overruns"
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
MISSING_CLICK=$(python3 scripts/check_script.py tests/_missing-click-script.tex \
    --deck tests/script-sync/mini-deck.tex --slot-minutes 3 --json 2>/dev/null | python3 -c '
import json,sys
r=json.load(sys.stdin)
print("OK" if any("semantic builds require" in f for f in r["findings"])
      else "MISSED")')
rm -f tests/_missing-click-script.tex
[ "$MISSING_CLICK" = "OK" ] && ok "semantic build requires ordered click markers" \
                                || bad "missing-click regression"

MISSING_QA=$(python3 scripts/check_script.py tests/script-sync/missing-qa-script.tex \
    --deck tests/script-sync/mini-deck.tex --slot-minutes 3 --json 2>/dev/null | python3 -c '
import json,sys
r=json.load(sys.stdin)
print("OK" if not any("appendix frame has no Q&A block" in f
                      for f in r["findings"])
      else "REJECTED")')
[ "$MISSING_QA" = "OK" ] && ok "Q&A may cover selected high-probability backups" \
                             || bad "optional Q&A regression"

if python3 scripts/check_script.py tests/script-sync/good-script.tex \
     --deck tests/script-sync/mini-deck.tex --slot-minutes 2 --wpm 0 >/dev/null 2>&1; then
  bad "nonpositive script timing input"
else
  ok "nonpositive script timing input is rejected"
fi

if python3 scripts/compile_deck.py tests/interface-test.tex --passes 0 \
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

echo
echo "$PASS passed, $FAIL failed"
exit $((FAIL > 0))
