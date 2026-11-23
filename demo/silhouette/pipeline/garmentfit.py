"""The frames fitted to the garment (StepB step 3). Pure Python, no Pillow.

Each zone's fabric frame (plateframe.py) is measured in its view: an axis, an anchor, a cylinder. Its (u, v) is the garment's only
where the view fixes it by definition. This module finds, for each zone, which of its two offsets are free and fits them so that the
view's landmarks land on the garment record's cm (garment.py):
  u   FIXED when the zone's axis starts at a landmark whose garment u on this piece is 0 (the front's axis through cf-neck: u = 0 is
      the centre front by construction); otherwise FREE: the frame's u + uMm / 10 (a shift; the axis is the zone's own midline).
  v   FIXED when the anchor is the piece's own v origin: the line through two landmarks whose garment v is 0 (the neck-point line), or
      a point whose garment (u, v) is (0, 0) with no vMm (a sleeve's shoulder point); otherwise FREE: vMm (the v at the anchor).
The fit: weighted least squares over the zone's landmarks (a landmark of the record on this piece, lying on the zone: inside it or
within 12 px of its outline): a cloth point (compare uv) gives u and v, a point of a line (a cuff) v only. Weights by the record's
source: agreed and definition 4, fitted and measured 2, assumed 1. With one parameter per axis this is a weighted mean.
A zone with no landmark is tied to a fitted zone along their shared seam. Same piece (a fold of one cloth): u and v continuous across
it. Two pieces: v equal along it (a sewn seam), u equal (the pieces equally wide there: an assumption). Without either, the zone
keeps its measured offsets.
Yaw (StepB step 4): the turn of the body that fits the zone's u landmarks best (with the u shift re-fitted at each turn when u is
free): a grid over the range theta + |yaw| <= 85 deg, then refined. It is APPLIED only when the fit is over-determined (at least
YAW_MIN_POINTS u landmarks, on both sides of the axis), the turn is over YAW_MIN_DEG and it lowers the residual; otherwise it is
reported (fit.zones.<z>.yaw: best, rms before / after, why not) and the frame keeps 0 (the arithmetic of StepA). With 3 landmarks and
the shift free the turn trades off against thetaDeg (StepB step 4: the sleeve view's front fits 10 mm rms at any theta 45-70 deg)
and can come out with the wrong sign.
The result per zone (plate.dat zones.<z>.frame: uMm, vMm; fit.zones.<z>: free, n, weights, residuals) and, for information only (the
agreed scale stays: StepB decision 2), the scale that would fit the view's landmark distances best (fit.scale).
"""
import math
import garment as GM
import plateframe

WEIGHT = {"agreed": 4.0, "definition": 4.0, "fitted": 2.0, "measured": 2.0, "assumed": 1.0}
YAW_MIN_DEG = 2.0
YAW_MIN_POINTS = 4
NEAR_PX = 12.0


def _seg_dist(p, a, b):
    ex, ey = b[0] - a[0], b[1] - a[1]
    L2 = ex * ex + ey * ey or 1e-12
    t = max(0.0, min(1.0, ((p[0] - a[0]) * ex + (p[1] - a[1]) * ey) / L2))
    return math.hypot(p[0] - a[0] - t * ex, p[1] - a[1] - t * ey)


def _inside(p, poly):
    c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > p[1]) != (y2 > p[1]) and p[0] < (x2 - x1) * (p[1] - y1) / (y2 - y1) + x1: c = not c
    return c


def on_zone(p, outline):
    return _inside(p, outline) or min(_seg_dist(p, a, b) for a, b in zip(outline, outline[1:] + outline[:1])) <= NEAR_PX


def observations(P, G, zn, outline):
    """[(landmark, has_u, u_exp, v_exp, weight, xy)] of a zone: the record's points on its piece that lie on it."""
    view, pc = P["view"], P["zones"][zn]["piece"]
    obs = []
    for lm, xy in P.get("landmarks", {}).items():
        name, line = GM.landmark(G, view, lm)
        if name:
            L = G["landmarks"][name]
            at = L.get("at", {}).get(pc)
            if L["compare"] == "none" or not at: continue
            if not on_zone(xy, outline): continue
            obs.append((f"{lm}={name}", L["compare"] == "uv", at["u"], at["v"], WEIGHT[at["src"]], xy))
        elif line:
            ln = G["lines"][line]
            if ln["piece"] != pc or not on_zone(xy, outline): continue
            obs.append((f"{lm}=line {line}", False, None, ln["v"], WEIGHT[ln["src"]], xy))
    return obs


def free_of(P, G, zn):
    """{"u": bool, "v": bool}: which offsets of the zone's frame are free (module docstring)."""
    view, pc = P["view"], P["zones"][zn]["piece"]
    F = P["zones"][zn]["frame"]
    ax, an = F.get("axisFrom"), F.get("anchor", {})

    def exp(lm):
        name, _ = GM.landmark(G, view, lm) if lm in G["views"][view]["landmarks"] else (None, None)
        return GM.expected(G, name, pc) if name else None
    u_fixed = isinstance(ax, list) and isinstance(ax[0], str) and (e := exp(ax[0])) is not None and abs(e[0]) < 1e-9
    if "line" in an:
        es = [exp(n) for n in an["line"]]
        v_fixed = all(e is not None and abs(e[1]) < 1e-9 for e in es)
    else:
        e = exp(an.get("point"))
        v_fixed = "vMm" not in an and e is not None and abs(e[0]) < 1e-9 and abs(e[1]) < 1e-9
    return {"u": not u_fixed, "v": not v_fixed}


def fit(P, outline_of):
    """Fit every zone's free offsets in place (P["zones"][z]["frame"]["uMm"], ["vMm"]); return the "fit" block of plate.dat.
    outline_of(zone) -> the zone's outline points."""
    G = GM.load(P["variant"])
    mm = P["mmPerPx"]
    res, done = {}, {}
    order = sorted(P["zones"], key=lambda n: (P["zones"][n]["order"], n))
    pending = []
    for zn in order:
        F = P["zones"][zn]["frame"]
        F.setdefault("uMm", 0.0)
        free = free_of(P, G, zn)
        obs = observations(P, G, zn, outline_of(zn))
        if not obs:
            pending.append(zn); continue
        yaw = fit_yaw(F, mm, obs, free["u"])
        du = dv = 0.0
        if free["u"]:
            ou = [(w, ue - plateframe.uv(F, mm, *xy)[0]) for _, hu, ue, _, w, xy in obs if hu]
            if ou: du = sum(w * d for w, d in ou) / sum(w for w, _ in ou)
        if free["v"]:
            ov = [(w, ve - plateframe.uv(F, mm, *xy)[1]) for _, _, _, ve, w, xy in obs]
            dv = sum(w * d for w, d in ov) / sum(w for w, _ in ov)
        F["uMm"] = round(F["uMm"] + du * 10.0, 3)
        F["vMm"] = round(F.get("vMm", 0.0) + dv * 10.0, 3)
        done[zn] = True
        res[zn] = {"free": [k for k in ("u", "v") if free[k]] + (["yaw"] if yaw and yaw["deg"] else []), "by": "landmarks", "n": len(obs),
                   **({"yaw": yaw} if yaw else {}),
                   "residualsMm": {lab: residual(F, mm, hu, ue, ve, xy) for lab, hu, ue, ve, _, xy in obs}}
    for zn in pending:                                    # tied along a shared seam to a fitted zone of another piece
        F = P["zones"][zn]["frame"]
        free = free_of(P, G, zn)
        tie = None
        for en, e in P["edges"].items():
            if e["type"] != "seam" or zn not in e.get("zones", []): continue
            other = next((z for z in e["zones"] if z != zn), None)
            if other in done:
                tie = (en, other, e["points"]); break
        if not tie:
            res[zn] = {"free": [], "by": "none (no landmark, no seam to a fitted zone): the measured offsets stay", "n": 0}
            continue
        en, other, pts = tie
        Fo = P["zones"][other]["frame"]
        d = [(plateframe.uv(Fo, mm, *p)[0] - plateframe.uv(F, mm, *p)[0], plateframe.uv(Fo, mm, *p)[1] - plateframe.uv(F, mm, *p)[1]) for p in pts]
        du = sum(x for x, _ in d) / len(d) if free["u"] else 0.0
        dv = sum(y for _, y in d) / len(d) if free["v"] else 0.0
        F["uMm"] = round(F["uMm"] + du * 10.0, 3)
        F["vMm"] = round(F.get("vMm", 0.0) + dv * 10.0, 3)
        spread = max(math.hypot((a - du) * 10, (b - dv) * 10) for a, b in d)
        same = P["zones"][other]["piece"] == P["zones"][zn]["piece"]
        how = "the same piece: u, v continuous across the fold" if same else "v equal (sewn), u equal (assumed: equal widths)"
        res[zn] = {"free": [k for k in ("u", "v") if free[k]], "by": f"seam {en} to {other}: {how}",
                   "n": len(pts), "seamSpreadMm": round(spread, 2)}
    return {"zones": res, "scale": scale_info(P, G, outline_of)}


def fit_yaw(F, mm, obs, u_free):
    """The body's turn that fits the zone's u landmarks best (module docstring); sets F["yawDeg"]; None when not identifiable."""
    pts = [(w, ue, xy) for _, hu, ue, _, w, xy in obs if hu]
    rs = [plateframe.project(F["axis"], xy)[1] for _, _, xy in pts]
    if len(pts) < 2 or not (min(rs) < 0 < max(rs)):
        F["yawDeg"] = 0.0
        return None

    def sse(deg):
        F["yawDeg"] = deg
        d = [(w, ue - plateframe.uv(F, mm, *xy)[0]) for w, ue, xy in pts]
        m = sum(w * x for w, x in d) / sum(w for w, _ in d) if u_free else 0.0
        return sum(w * (x - m) ** 2 for w, x in d)
    lim = 85.0 - F["thetaDeg"]
    grid = [k * 0.5 for k in range(int(-2 * lim), int(2 * lim) + 1)]
    best = min(grid, key=sse)
    fine = [round(best + k * 0.01, 2) for k in range(-50, 51) if abs(best + k * 0.01) <= lim]
    best = min(fine, key=sse)
    s0, s1 = sse(0.0), sse(best)
    W = sum(w for w, _, _ in pts)
    why = (f"under-determined: {len(pts)} u landmarks (at least {YAW_MIN_POINTS})" if len(pts) < YAW_MIN_POINTS
           else f"|best| <= {YAW_MIN_DEG} deg" if abs(best) <= YAW_MIN_DEG else "no gain" if s1 >= s0 else None)
    F["yawDeg"] = 0.0 if why else best
    out = {"deg": F["yawDeg"], "best": best, "rmsAt0Mm": round((s0 / W) ** 0.5 * 10, 2), "rmsAtBestMm": round((s1 / W) ** 0.5 * 10, 2)}
    if why: out["notApplied"] = why
    return out


def residual(F, mm, has_u, ue, ve, xy):
    u, v = plateframe.uv(F, mm, *xy)
    return [round((u - ue) * 10, 2) if has_u else None, round((v - ve) * 10, 2)]


def scale_info(P, G, outline_of):
    """For information (StepB decision 2: the agreed scale stays): the factor k on mmPerPx that best fits the distances between the
    view's cloth points of one piece (garment cm against the frame's cm, least squares through 0), and the mmPerPx it implies."""
    mm = P["mmPerPx"]
    num = den = 0.0
    n = 0
    for zn in P["zones"]:
        F = P["zones"][zn]["frame"]
        pts = [(plateframe.uv(F, mm, *xy), (ue, ve)) for _, hu, ue, ve, _, xy in observations(P, G, zn, outline_of(zn)) if hu]
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                dm = math.dist(pts[i][0], pts[j][0]); de = math.dist(pts[i][1], pts[j][1])
                if dm < 1.0: continue
                num += dm * de; den += dm * dm; n += 1
    if not n: return {"agreed": mm, "pairs": 0}
    k = num / den
    return {"agreed": mm, "fitted": round(mm * k, 5), "factor": round(k, 4), "pairs": n}
