#!/bin/bash
# Headless screenshots of testing.html, one per query, run in parallel, plus a contact sheet of the stages.
# usage: tools/shoot_views.sh <out-dir> ["view=torso&fabric=mocha&lace=geometric" ...]
#        default queries: the four views with the default fabric and lace.
# PORT must be free: two runs on the same port share (and kill) each other's server. Set PORT=<free port> when another run is active.
# Software rendering (SwiftShader) is slow: the close views need --virtual-time-budget of ~45 s,
# otherwise the screenshot shows the fallback photo. Load / draw times on the stat line are not real.
set -u
OUT="${1:?out dir}"; shift
QUERIES=("$@"); [ ${#QUERIES[@]} -eq 0 ] && QUERIES=("view=torso" "view=neck" "view=sleeve" "view=hem")
PORT="${PORT:-8793}"; BUDGET="${BUDGET:-45000}"
DPR="${DPR:-1}"; WIN="${WIN:-900,760}"        # DPR=2 for review shots of lace and shadow (screenshot is then 2x)
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$OUT"
python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$ROOT" >/dev/null 2>&1 &
SRV=$!; trap 'kill $SRV 2>/dev/null' EXIT; sleep 1
JOBS="${JOBS:-8}"; TMO="${TMO:-240}"            # JOBS = Chrome processes at a time (use 3-4 on a busy machine)
i=0; PIDS=()                                     # wait for the Chrome processes only: a bare `wait` would also wait for the server
for q in "${QUERIES[@]}"; do
  perl -e 'alarm shift; exec @ARGV' "$TMO" "$CHROME" --headless=new --use-angle=swiftshader --enable-unsafe-swiftshader \
    --hide-scrollbars --user-data-dir="$OUT/.profile-$i" --window-size="$WIN" --force-device-scale-factor="$DPR" --virtual-time-budget="$BUDGET" \
    --screenshot="$OUT/shot-$i.png" "http://127.0.0.1:$PORT/testing.html?$q" >/dev/null 2>&1 &
  PIDS+=($!); i=$((i + 1))
  if [ $((i % JOBS)) -eq 0 ]; then wait "${PIDS[@]}"; PIDS=(); fi
done
[ ${#PIDS[@]} -gt 0 ] && wait "${PIDS[@]}"
rm -rf "$OUT"/.profile-*
python3 -W ignore - "$OUT" "$DPR" "${QUERIES[@]}" <<'EOF'
import sys
from PIL import Image
out, dpr, qs = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ims = [Image.open(f"{out}/shot-{i}.png").crop((32 * dpr, 32 * dpr, 462 * dpr, 605 * dpr)) for i in range(len(qs))]
sheet = Image.new("RGB", (len(ims) * (430 * dpr + 10), 573 * dpr), "white")
for i, im in enumerate(ims):
    sheet.paste(im, (i * (430 * dpr + 10), 0))
sheet.save(f"{out}/sheet.png")
for i, q in enumerate(qs):
    print(f"shot-{i}.png  {q}")
print(f"{out}/sheet.png")
EOF
