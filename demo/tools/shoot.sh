#!/bin/bash
# Headless screenshots of testing.html at 1x and 2x, plus the stat line.
# usage: tools/shoot.sh <out-dir> [port]
set -e
OUT="${1:?out dir}"; PORT="${2:-8765}"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$OUT"
python3 -m http.server "$PORT" --directory "$ROOT" >/dev/null 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null' EXIT
sleep 1
URL="http://localhost:$PORT/testing.html${QUERY}"
FLAGS=(--headless=new --disable-gpu-vsync --use-angle=swiftshader --enable-unsafe-swiftshader
       --hide-scrollbars --virtual-time-budget=15000)
run() { perl -e 'alarm 100; exec @ARGV' "$@"; }
run "$CHROME" "${FLAGS[@]}" --window-size=900,760  --force-device-scale-factor=1 --screenshot="$OUT/shot-1x.png" "$URL" >/dev/null 2>&1
run "$CHROME" "${FLAGS[@]}" --window-size=1400,1800 --force-device-scale-factor=2 --screenshot="$OUT/shot-2x.png" "$URL" >/dev/null 2>&1
run "$CHROME" "${FLAGS[@]}" --window-size=1400,1800 --force-device-scale-factor=2 --dump-dom "$URL" 2>/dev/null \
  | grep -o 'Load [^<]*' | head -1 > "$OUT/stat.txt" || true
echo "saved to $OUT:"; ls -la "$OUT"; cat "$OUT/stat.txt"
