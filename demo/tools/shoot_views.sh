#!/bin/bash
# Headless screenshots of testing.html, one per query, run in parallel, plus a contact sheet of the stages.
# usage: tools/shoot_views.sh <out-dir> ["view=torso&fabric=mocha&lace=geometric" ...]
#        default queries: the four views with the default fabric and lace.
# Software rendering (SwiftShader) is slow: the close views need --virtual-time-budget of ~45 s,
# otherwise the screenshot shows the fallback photo. Load / draw times on the stat line are not real.
set -u
OUT="${1:?out dir}"; shift
QUERIES=("$@"); [ ${#QUERIES[@]} -eq 0 ] && QUERIES=("view=torso" "view=neck" "view=sleeve" "view=hem")
PORT="${PORT:-8793}"; BUDGET="${BUDGET:-45000}"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$OUT"
python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$ROOT" >/dev/null 2>&1 &
SRV=$!; trap 'kill $SRV 2>/dev/null' EXIT; sleep 1
i=0
for q in "${QUERIES[@]}"; do
  perl -e 'alarm 150; exec @ARGV' "$CHROME" --headless=new --use-angle=swiftshader --enable-unsafe-swiftshader \
    --hide-scrollbars --user-data-dir="$OUT/.profile-$i" --window-size=900,760 --virtual-time-budget="$BUDGET" \
    --screenshot="$OUT/shot-$i.png" "http://127.0.0.1:$PORT/testing.html?$q" >/dev/null 2>&1 &
  i=$((i + 1))
done
wait
rm -rf "$OUT"/.profile-*
python3 -W ignore - "$OUT" "${QUERIES[@]}" <<'EOF'
import sys
from PIL import Image
out, qs = sys.argv[1], sys.argv[2:]
ims = [Image.open(f"{out}/shot-{i}.png").crop((32, 32, 462, 605)) for i in range(len(qs))]
sheet = Image.new("RGB", (len(ims) * 440, 573), "white")
for i, im in enumerate(ims):
    sheet.paste(im, (i * 440, 0))
sheet.save(f"{out}/sheet.png")
for i, q in enumerate(qs):
    print(f"shot-{i}.png  {q}")
print(f"{out}/sheet.png")
EOF
