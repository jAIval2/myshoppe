"""Cross-view check (StepB step 0): does one point of the cloth get one fabric (u, v) in every view? Numbers only, no render.

usage: python3 silhouette/checks/xview_check.py [--json out.json] [--limit-mm 3] [plate ...]   (default: every plate in assets/plates)

For each view, each landmark is named as a point of the garment by the garment record (StepB step 2: views.<view>.landmarks in
assets/looks/<look>.json, silhouette/pipeline/garment.py) and evaluated in the fabric frame of every zone it lies on (inside, or
within 12 px of the outline) whose piece (views.<view>.zones) the landmark is a point of (the record's "at": a seam junction is a
point of two pieces; a cuff corner only of its sleeve, though the sleeve hangs in front of the body).
"record": each view's residual against the record's value (mm): the largest |du|, |dv| over the views.
ACCEPTED: a row over the limit where every view more than the limit from the record has that landmark in its accepted list
(garment.views.<view>.acceptedResiduals: the owner's decision that the photos disagree).
A landmark is compared in one of three ways:
  uv    a cloth point (a seam junction, a neck point, a slit corner): u and v must agree;
  v     a point on a weft line (the hem, a cuff): only v is a property of the cloth there. The u of a silhouette point depends on the
        view (the edge of the visible half), so it is not compared; all points of one line are compared as one row ("<line> line");
  -     not a garment point (an image border, an elbow guess): listed, not compared.
Each row: the views' (u, v) in cm, the spread (max - min) in mm, and PASS when the spread is within --limit-mm.
"visible" = the spread of what the print shows: (u, v) + the view's packing offset (decisions.uvOffsetCm), modulo the repeat of the
fabric (30 cm, 20 cm), as the page samples it (StepB F1: the page does not take the offset out).
"""
import json, math, os, sys

sys.path[:0] = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), d) for d in ("pipeline", "checks")]
import garment as GM, platedat, plateframe

DEMO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# view landmark -> (garment landmark, mode, line).  "-l" / "-r" are the image's left and right in the front views (the wearer's right
# and left). The sleeve view shows the image-left sleeve; the hem view the image-right slit.
REPEATS = (30.0, 20.0)
ACC = {}                                              # view -> the owner's accepted residuals (filled by measure)


def seg_dist(p, a, b):
    ex, ey = b[0] - a[0], b[1] - a[1]
    L2 = ex * ex + ey * ey or 1e-12
    t = max(0.0, min(1.0, ((p[0] - a[0]) * ex + (p[1] - a[1]) * ey) / L2))
    return math.hypot(p[0] - a[0] - t * ex, p[1] - a[1] - t * ey)


def zones_of(P, p, tol=3.0):
    out = []
    for zn in P["zones"]:
        o = platedat.outline(P, zn)
        d = min(seg_dist(p, a, b) for a, b in zip(o, o[1:] + o[:1]))
        if d <= tol or platedat._inside(p, o): out.append(zn)
    return out


def measure(plates):
    rows, expect = {}, {}                             # (name, piece, mode) -> {view: (u, v, off, lm, zone)}; -> (u, v) | (None, v)
    for pd in plates:
        P = platedat.read(pd)
        view = P["view"]
        G = GM.load(P.get("garment", {}).get("look") or P["variant"])
        ACC[view] = G["views"].get(view, {}).get("acceptedResiduals", {})
        off = P.get("decisions", {}).get("uvOffsetCm", [0.0, 0.0])
        for lm, xy in P.get("landmarks", {}).items():
            name, line = GM.landmark(G, view, lm)
            if name:
                L = G["landmarks"][name]
                mode, pieces = ("-" if L["compare"] == "none" else L["compare"]), set(L.get("at", {})) or set(G["pieces"])
            elif line:
                name, mode, pieces = line + " line", "v", {G["lines"][line]["piece"]}
            else:
                name, mode, pieces = f"{lm} ({view})", "-", set(G["pieces"])
            for zn in zones_of(P, xy, 12.0):
                pc = P["zones"][zn].get("piece", zn)
                if pc not in pieces: continue
                F = P["zones"][zn].get("frame")
                if not F or "L" not in F: continue
                u, v = plateframe.uv(F, P["mmPerPx"], *xy)
                key = (name, pc, mode)
                rows.setdefault(key, {})[f"{view}:{lm}" if line else view] = (u, v, off, lm, zn)
                if line: expect[key] = (None, G["lines"][line]["v"])
                elif mode != "-": expect[key] = GM.expected(G, name, pc)
    return rows, expect


def circ(vals, R):
    """The spread of values on a circle of circumference R (the smallest arc that holds them all)."""
    xs = sorted(x % R for x in vals)
    if len(xs) < 2: return 0.0
    gaps = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)] + [xs[0] + R - xs[-1]]
    return R - max(gaps)


def table(rows, limit, expect=None):
    expect = expect or {}
    out, lines = [], []
    lines.append(f"{'landmark':22} {'piece':9} {'mode':4}  {'views: (u, v) cm':64} {'du mm':>7} {'dv mm':>7}  {'visible 30/20 cm (mm)':22} {'record mm':>12} result")
    for (name, piece, mode), per in sorted(rows.items(), key=lambda kv: (kv[0][2] == "-", kv[0][1], kv[0][0])):
        us = [r[0] for r in per.values()]; vs = [r[1] for r in per.values()]
        du = (max(us) - min(us)) * 10 if mode == "uv" else None
        dv = (max(vs) - min(vs)) * 10
        vis = {}
        for R in REPEATS:
            vu = circ([r[0] + r[2][0] for r in per.values()], R) * 10 if mode == "uv" else None
            vv = circ([r[1] + r[2][1] for r in per.values()], R) * 10
            vis[R] = (vu, vv)
        n = len(per)
        res = "-" if mode == "-" or n < 2 else ("PASS" if dv <= limit and (du is None or du <= limit) else "FAIL")
        ex = expect.get((name, piece, mode))
        rec = None
        if res == "FAIL" and ex:
            far = [(k.split(":")[0], r[3]) for k, r in per.items()
                   if max(abs(r[1] - ex[1]), abs(r[0] - ex[0]) if ex[0] is not None and mode == "uv" else 0.0) * 10 > limit]
            if far and all(lm in ACC.get(v, {}) for v, lm in far): res = "ACCEPTED"
        if ex:
            ru = max(abs(r[0] - ex[0]) for r in per.values()) * 10 if ex[0] is not None and mode == "uv" else None
            rv = max(abs(r[1] - ex[1]) for r in per.values()) * 10
            rec = (ru, rv)
        cells = "  ".join(f"{k} ({r[0]:.1f}, {r[1]:.1f})" for k, r in sorted(per.items()))
        fmt = lambda x: "" if x is None else f"{x:.1f}"
        visible = " / ".join(f"{fmt(vis[R][0])},{fmt(vis[R][1])}".strip(",") for R in REPEATS) if n >= 2 else ""
        rtxt = "" if not rec else (f"{fmt(rec[0])},{fmt(rec[1])}" if rec[0] is not None else f",{fmt(rec[1])}")
        lines.append(f"{name:22} {piece:9} {mode:4}  {cells[:64]:64} {fmt(du) if n >= 2 else '':>7} {fmt(dv) if n >= 2 and mode != '-' else '':>7}  {visible:22} {rtxt:>12} {res}")
        if len(cells) > 64: lines.append(f"{'':38}{cells[64:]}")
        out.append({"landmark": name, "piece": piece, "mode": mode, "views": {k: {"u": round(r[0], 3), "v": round(r[1], 3), "lm": r[3], "zone": r[4],
                    "offset": r[2]} for k, r in per.items()}, "duMm": du and round(du, 2), "dvMm": round(dv, 2) if mode != "-" else None,
                    "visibleMm": {str(int(R)): vis[R] for R in REPEATS}, "recordMm": rec, "result": res})
    return out, lines


def main(a):
    js = a[a.index("--json") + 1] if "--json" in a else None
    limit = float(a[a.index("--limit-mm") + 1]) if "--limit-mm" in a else 3.0
    names = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] not in ("--json", "--limit-mm"))]
    root = os.path.join(DEMO, "assets", "plates")
    plates = [p if os.path.isdir(p) else os.path.join(root, p) for p in names] or sorted(os.path.join(root, d) for d in os.listdir(root))
    rows, expect = measure(plates)
    out, lines = table(rows, limit, expect)
    print("\n".join(lines))
    nf = sum(r["result"] == "FAIL" for r in out); npass = sum(r["result"] == "PASS" for r in out)
    na = sum(r["result"] == "ACCEPTED" for r in out)
    print(f"\n{npass} PASS, {na} ACCEPTED (the owner), {nf} FAIL (limit {limit} mm)")
    if js:
        json.dump({"limitMm": limit, "rows": out}, open(js, "w"), indent=1)
    return 1 if nf else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
