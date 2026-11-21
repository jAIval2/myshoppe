#!/bin/bash
# The plate is what its source makes (StepA step 1): rebuild every plate from its source (source.png + tools/annotate_<view>.py, or
# the torso's imported data until StepA step 2) into a scratch copy, and compare base.jpg and plate.dat byte for byte.
# Read-only for the real plates.
# usage: tools/rebuild_check.sh [plate ...]        (default: every folder in assets/plates that has a source.png)
set -u
cd "$(dirname "$0")/.."
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
plates=("$@"); [ ${#plates[@]} -eq 0 ] && plates=($(cd assets/plates && for d in */; do [ -f "$d/source.png" ] && echo "${d%/}"; done))
fail=0
for p in "${plates[@]}"; do
  mkdir -p "$TMP/$p"
  for f in source.png base.jpg plate.dat; do [ -f "assets/plates/$p/$f" ] && cp "assets/plates/$p/$f" "$TMP/$p/$f"; done
  python3 -W ignore tools/make_plate.py "$TMP/$p" --no-check >/dev/null || { echo "FAIL  $p: make_plate.py error"; fail=1; continue; }
  for f in base.jpg plate.dat; do
    if cmp -s "assets/plates/$p/$f" "$TMP/$p/$f"; then echo "same  $p/$f"; else echo "DIFF  $p/$f"; fail=1; fi
  done
done
[ $fail -eq 0 ] && echo "ALL IDENTICAL" || echo "SOME DIFFER"
exit $fail
