#!/bin/bash
# Regression check after a change to tools/make_plate.py: rebuild every plate into a scratch copy
# and compare the shipped maps byte for byte (plate.md step 5). Read-only for the real plates.
# usage: tools/rebuild_check.sh [plate ...]        (default: every folder in assets/plates)
set -u
cd "$(dirname "$0")/.."
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
plates=("$@"); [ ${#plates[@]} -eq 0 ] && plates=($(ls assets/plates))
fail=0
for p in "${plates[@]}"; do
  cp -R "assets/plates/$p" "$TMP/$p"
  python3 -W ignore tools/make_plate.py "$TMP/$p" >/dev/null || { echo "FAIL  $p: make_plate.py error"; fail=1; continue; }
  for f in id.png uv.png uv_trim.png shade.png plate.json; do
    if cmp -s "assets/plates/$p/$f" "$TMP/$p/$f"; then echo "same  $p/$f"; else echo "DIFF  $p/$f"; fail=1; fi
  done
done
[ $fail -eq 0 ] && echo "ALL IDENTICAL" || echo "SOME DIFFER"
exit $fail
