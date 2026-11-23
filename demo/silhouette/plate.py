"""The silhouette pipeline: one entry point (Python 3 + Pillow; Node for the page checks). Run from anywhere.

usage: python3 demo/silhouette/plate.py <command> [view] [options]

  views                          the views that have a source (silhouette/sources) and a measured view (silhouette/views)
  measure <view>                 the measured view's own checks (silhouette/views/<view>.py run alone; writes nothing)
  build <view> [--review] [--no-check]
                                 source -> assets/plates/<plate>/base.jpg + plate.dat (deterministic); --review: annotate.png,
                                 check.png and the edge crops into demo/review/<plate>/; then the plate's invariants (printed)
  check <view>                   the plate's invariants (closure, gaps, trims, landmarks, frame) and the frame parity of the page's
                                 plate.js against plateframe.py (10,000 points, 1e-4 cm)
  page-check <view> [--port 8300]
                                 the page (served from demo/ on the port) against the plate: its maps (maps_check.py) and its edges
                                 (fringe.py, edge_crops.py), into demo/review/<plate>/page/
  rebuild-check [view ...]       every plate rebuilt from its source into a scratch copy: base.jpg and plate.dat byte-identical

<view> is torso | neck | sleeve | hem, or a plate name (torso-straight). Exit code: the tool's (0 = pass).
"""
import os, subprocess, sys, tempfile

SIL = os.path.dirname(os.path.abspath(__file__))
DEMO = os.path.dirname(SIL)
PY = [sys.executable, "-W", "ignore"]


def plate_of(view):
    name = view if "-" in view else view + "-straight"
    return name, os.path.join("assets", "plates", name)


def run(cmd):
    return subprocess.run(cmd, cwd=DEMO).returncode


def views():
    return sorted(f[:-4] for f in os.listdir(os.path.join(SIL, "sources")) if f.endswith(".png"))


def main(a):
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); return 0
    cmd, rest = a[0], a[1:]
    if cmd == "views":
        print("\n".join(views())); return 0
    if cmd == "rebuild-check":
        return run([os.path.join(SIL, "checks", "rebuild_check.sh"), *[plate_of(v)[0] for v in rest]])
    if not rest:
        print(f"{cmd}: which view? ({', '.join(views())})", file=sys.stderr); return 2
    name, pd = plate_of(rest[0])
    opts = rest[1:]
    if cmd == "measure":
        own = os.path.join(SIL, "views", name.replace("-", "_") + ".py")
        return run([*PY, own if os.path.exists(own) else os.path.join(SIL, "views", name.split("-")[0] + ".py")])
    if cmd == "build":
        return run([*PY, os.path.join(SIL, "pipeline", "make_plate.py"), pd, *opts])
    if cmd == "check":
        r = run([*PY, os.path.join(SIL, "checks", "plate_invariants.py"), pd])
        with tempfile.TemporaryDirectory() as t:
            s = os.path.join(t, "samples.json")
            r |= run([*PY, os.path.join(SIL, "pipeline", "plateframe.py"), "--samples", pd, s])
            r |= run(["node", os.path.join(SIL, "checks", "frame_check.mjs"), pd, s])
        return r
    if cmd == "page-check":
        port = opts[opts.index("--port") + 1] if "--port" in opts else "8300"
        out = os.path.join("review", name, "page")
        view = name.split("-")[0]
        shot = ["node", os.path.join(SIL, "checks", "cdp_shot.mjs")]
        r = run([*shot, out + "/maps", port, "--eval", "return window.__studio.readMapsRaw()", f"view={view}&fabric=sage"])
        r |= run([*PY, os.path.join(SIL, "checks", "maps_check.py"), pd, out + "/maps/log.json"])
        q = [f"view={view}&fabric={f}&trims=none&stage=600" for f in ("mocha", "off")]
        r |= run([*shot, out + "/edges", port, "--dpr", "2", *q])
        e = out + "/edges"
        r |= run([*PY, os.path.join(SIL, "checks", "fringe.py"), e + "/canvas-0.png", pd, "--photo", e + "/canvas-1.png"])
        r |= run([*PY, os.path.join(SIL, "checks", "edge_crops.py"), e + "/canvas-0.png", pd, out + "/crops.png", "--photo", e + "/canvas-1.png"])
        return r
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
