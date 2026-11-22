#!/bin/bash
# The plate is what its source makes (StepA step 1): rebuild every plate from its source (silhouette/sources/<plate>.png +
# silhouette/views/<view>.py) into a scratch copy, and compare base.jpg and plate.dat byte for byte. Read-only for the real plates.
# usage: silhouette/checks/rebuild_check.sh [plate ...]        (default: every plate that has a source in silhouette/sources)
set -u
cd "$(dirname "$0")/../.."                                       # demo/
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
plates=("$@"); [ ${#plates[@]} -eq 0 ] && plates=($(cd silhouette/sources && for f in *.png; do echo "${f%.png}"; done))
fail=0
for p in "${plates[@]}"; do
  mkdir -p "$TMP/$p"
  for f in base.jpg plate.dat; do [ -f "assets/plates/$p/$f" ] && cp "assets/plates/$p/$f" "$TMP/$p/$f"; done
  python3 -W ignore silhouette/pipeline/make_plate.py "$TMP/$p" --no-check >/dev/null || { echo "FAIL  $p: make_plate.py error"; fail=1; continue; }
  for f in base.jpg plate.dat; do
    if cmp -s "assets/plates/$p/$f" "$TMP/$p/$f"; then echo "same  $p/$f"; else echo "DIFF  $p/$f"; fail=1; fi
  done
done
[ $fail -eq 0 ] && echo "ALL IDENTICAL" || echo "SOME DIFFER"
exit $fail
