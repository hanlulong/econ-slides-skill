#!/usr/bin/env bash
# econ-slides test suite. Requires xelatex + python3 + pymupdf.
#   bash tests/run-tests.sh
set -u
cd "$(dirname "$0")/.."
PASS=0; FAIL=0
ok()   { echo "  PASS  $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL  $1"; FAIL=$((FAIL+1)); }

echo "== interface test deck under every theme, every engine =="
for theme in econ-slides-house econ-slides-clean econ-slides-boxed; do
  sed "1,8s/\\\\def\\\\ecoslidestheme{econ-slides-house}/\\\\def\\\\ecoslidestheme{$theme}/" \
      tests/interface-test.tex > "tests/_iface-$theme.tex"
  if python3 scripts/compile_deck.py "tests/_iface-$theme.tex" \
       --build-dir tests/build-suite >/dev/null 2>&1; then
    ok "compile interface-test [$theme]"
  else
    bad "compile interface-test [$theme]"
  fi
  rm -f "tests/_iface-$theme.tex"
done
for engine in pdflatex lualatex; do
  if python3 scripts/compile_deck.py tests/interface-test.tex \
       --engine "$engine" --build-dir tests/build-suite >/dev/null 2>&1; then
    ok "compile interface-test [$engine]"
  else
    bad "compile interface-test [$engine]"
  fi
done

echo "== handout mode (overlays must collapse, not overprint) =="
sed 's/\\documentclass\[11pt, aspectratio=169\]{beamer}/\\documentclass[11pt, aspectratio=169, handout]{beamer}/' \
    tests/interface-test.tex > tests/_handout.tex
if python3 scripts/compile_deck.py tests/_handout.tex \
     --build-dir tests/build-suite >/dev/null 2>&1; then
  # the overlay frame must collapse to ONE page in handout mode: 8 -> 7
  HPAGES=$(python3 -c "import fitz; print(fitz.open('tests/build-suite/_handout.pdf').page_count)")
  [ "$HPAGES" = "7" ] && ok "handout compiles and collapses overlays (7 pages)" \
                      || bad "handout page count $HPAGES (want 7)"
else
  bad "handout compile"
fi
rm -f tests/_handout.tex

echo "== compat adapter on stock themes =="
for stock in Madrid CambridgeUS; do
  printf '\\def\\ecoslidesstocktheme{%s}\\def\\ecoslidestheme{econ-slides-compat}\\input{interface-test.tex}\n' "$stock" \
    > "tests/_compat-$stock.tex"
  if python3 scripts/compile_deck.py "tests/_compat-$stock.tex" \
       --build-dir tests/build-suite >/dev/null 2>&1; then
    ok "compile compat [$stock]"
  else
    bad "compile compat [$stock]"
  fi
  rm -f "tests/_compat-$stock.tex"
done

echo "== templates compile under every theme =="
for tpl in paper-talk discussion; do
  for theme in econ-slides-house econ-slides-clean econ-slides-boxed; do
    sed "s/\\\\usepackage{econ-slides-[a-z]*}/\\\\usepackage{$theme}/" \
        "templates/$tpl.tex" > "tests/_swap-$tpl-$theme.tex"
    if python3 scripts/compile_deck.py "tests/_swap-$tpl-$theme.tex" \
         --build-dir tests/build-suite >/dev/null 2>&1; then
      ok "compile $tpl [$theme]"
    else
      bad "compile $tpl [$theme]"
    fi
    rm -f "tests/_swap-$tpl-$theme.tex"
  done
done

echo "== checker: clean deck scores 100 =="
python3 scripts/compile_deck.py tests/interface-test.tex \
    --build-dir tests/build-suite >/dev/null 2>&1
SCORE=$(python3 scripts/check_deck.py tests/build-suite/interface-test.pdf \
    --tex tests/interface-test.tex --log tests/build-suite/interface-test.log \
    --json 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin)['score'])")
[ "$SCORE" = "100" ] && ok "clean deck score == 100" || bad "clean deck score == $SCORE (want 100)"

echo "== checker: violations deck trips every detector =="
python3 scripts/compile_deck.py tests/violations-test.tex \
    --build-dir tests/build-suite >/dev/null 2>&1
CHECKS=$(python3 scripts/check_deck.py tests/build-suite/violations-test.pdf \
    --tex tests/violations-test.tex --log tests/build-suite/violations-test.log \
    --json 2>/dev/null | python3 -c "
import json, sys
found = {f['check'] for f in json.load(sys.stdin)['findings']}
want = {'wrapped-title', 'wrapped-bullet', 'edge-overflow', 'density',
        'overfull', 'pause-chain'}
missing = want - found
print('OK' if not missing else 'MISSING:' + ','.join(sorted(missing)))")
[ "$CHECKS" = "OK" ] && ok "all six violation detectors fire" || bad "detectors: $CHECKS"

echo
echo "$PASS passed, $FAIL failed"
exit $((FAIL > 0))
