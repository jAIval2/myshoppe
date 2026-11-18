"""Numbers for one run. usage: metrics.py <run-dir> [plate-dir]
Block ratio: share of garment pixels (fabric UV) equal to the pixel on the right, read from uv.png."""
import json, os, sys
from PIL import Image, ImageFilter, ImageChops, ImageStat
run = sys.argv[1]
plate = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "assets/plates/torso-straight")
uv = Image.open(f"{plate}/uv.png").convert("RGB"); idm = Image.open(f"{plate}/id.png").convert("RGB")
W, H = uv.size
up, ip = uv.load(), idm.load()
same = tot = 0
for y in range(H):
    for x in range(W - 1):
        if ip[x, y][0] and ip[x + 1, y][0] and not ip[x, y][1] and not ip[x + 1, y][1]:
            tot += 1
            same += up[x, y] == up[x + 1, y]
res = {"block_ratio": round(same / tot, 3)}
b = Image.open(f"{run}/crops/bodice-centre.png").convert("L").filter(ImageFilter.FIND_EDGES)
res["sharpness_bodice"] = round(ImageStat.Stat(b).var[0], 1)
if os.path.exists(f"{run}/stat.txt"): res["stat"] = open(f"{run}/stat.txt").read().strip()
sizes = {f: os.path.getsize(f"{plate}/{f}") for f in ("id.png", "uv.png", "uv_trim.png", "shade.png")}
res["plate_data_kb"] = round(sum(sizes.values()) / 1024)
sw = os.path.join(plate, "../../swatches")
res["swatch_kb"] = {f: round(os.path.getsize(f"{sw}/{f}") / 1024) for f in sorted(os.listdir(sw))}
print(json.dumps(res, indent=1))
