#!/usr/bin/env bash
# Focused compile, checker, and synchronization tests for theory templates.
set -euo pipefail
cd "$(dirname "$0")/.."

build=$(mktemp -d "${TMPDIR:-/tmp}/econ-theory-tests.XXXXXX")
cleanup() {
  rm -rf "$build"
  rm -f templates/_swap-theory-*.tex
}
trap cleanup EXIT

python3 tests/theory-template-contract.py

for theme in econ-slides-house econ-slides-clean econ-slides-boxed; do
  src="templates/_swap-theory-$theme.tex"
  sed "s/\\\\usepackage{econ-slides-[a-z]*}/\\\\usepackage{$theme}/" \
      templates/theory-talk.tex > "$src"
  python3 scripts/compile_deck.py "$src" --build-dir "$build" --json \
      | python3 -c 'import json,sys
r=json.load(sys.stdin)
raise SystemExit(0 if r.get("ok") and r.get("overfull")==0 else 1)'
  stem="_swap-theory-$theme"
  python3 scripts/check_deck.py "$build/$stem.pdf" --tex "$src" \
      --log "$build/$stem.log" --json | python3 -c 'import json,sys
r=json.load(sys.stdin)
raise SystemExit(0 if r.get("verdict")=="ship" else 1)'
done

python3 scripts/compile_deck.py templates/theory-script.tex --build-dir "$build" \
    --json | python3 -c 'import json,sys
r=json.load(sys.stdin)
raise SystemExit(0 if r.get("ok") and r.get("overfull")==0 else 1)'

echo "theory template render tests: PASS"
