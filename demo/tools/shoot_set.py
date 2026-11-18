"""Shoot a list of queries with tools/shoot_views.sh, two at a time, check that each shot is a real render (not the
fallback photo that shows while WebGL has not drawn yet), and retry a bad one. Writes <out>/shot-<i>.png.

usage: DPR=2 python3 tools/shoot_set.py <out-dir> <port> "<query>" ["<query>" ...]
       python3 tools/shoot_set.py <out-dir> <port> --polish [extra]     the 8 fixed review queries, extra appended to each
"""
import os, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from polish_metrics import QUERIES, PLATES, PLATE_OF, CANVAS_X, CANVAS_Y, CANVAS_W


def is_render(path, query):
    """The stage must differ from base.jpg: >= 0.15 % of the pixels by more than 25 levels (lace alone is enough)."""
    view = query.split("view=")[1].split("&")[0]
    im = Image.open(path).convert("L")
    k = CANVAS_W / 1200
    h = round(1600 * k) - 90
    stage = im.crop((CANVAS_X, CANVAS_Y, CANVAS_X + CANVAS_W, CANVAS_Y + h))
    base = Image.open(os.path.join(PLATES, PLATE_OF[view], "base.jpg")).convert("L").resize((CANVAS_W, round(1600 * k)), Image.BOX).crop((0, 0, CANVAS_W, h))
    d = ImageChops.difference(stage, base).point(lambda v: 255 if v > 25 else 0)
    return d.histogram()[255] / (CANVAS_W * h) >= 0.0015


def one(args):
    i, q, out, port = args
    for attempt in range(1, 4):
        tmp = tempfile.mkdtemp(prefix="shoot")
        env = dict(os.environ, PORT=str(port + i % 2), JOBS="1", DPR=os.environ.get("DPR", "2"))
        subprocess.run([os.path.join(HERE, "shoot_views.sh"), tmp, q], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        f = os.path.join(tmp, "shot-0.png")
        if os.path.exists(f) and is_render(f, q):
            shutil.move(f, os.path.join(out, f"shot-{i}.png"))
            shutil.rmtree(tmp, ignore_errors=True)
            return f"shot-{i}.png ok (attempt {attempt})  {q}"
        shutil.rmtree(tmp, ignore_errors=True)
    return f"shot-{i}.png FAILED after 3 attempts  {q}"


if __name__ == "__main__":
    out, port, rest = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
    qs = [q + (rest[1] if len(rest) > 1 else "") for q in QUERIES] if rest and rest[0] == "--polish" else rest
    os.makedirs(out, exist_ok=True)
    with ThreadPoolExecutor(2) as ex:
        for line in ex.map(one, [(i, q, out, port) for i, q in enumerate(qs)]):
            print(line, flush=True)
