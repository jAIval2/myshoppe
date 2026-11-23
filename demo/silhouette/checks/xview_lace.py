"""The lace on every trim of every view, and across views (StepC). Numbers only, from the plates and the lace sidecars.

usage: python3 silhouette/checks/xview_lace.py [lace ...]          (default: every lace in assets/swatches)

Per lace and view, each trim: its cloth length L (plate.dat decisions.trims.<t>.lengthCm), the lace's repeat r (cm: periodRatio x
widthMm), its anchor, and what the page's fit does with it (testing.html laceFit): a centred motif at the centre front (anchor cf), or
n whole repeats scaled by fit = L / (n r) when that stays within the limit (5 %, 10 % on a trim shorter than 3 repeats).
Across views: the trims with the same group and anchor in two views must start the lace at the same phase (by construction: the
anchor is a garment point, StepB) and, where the photos agree, have the same count of whole repeats.
"""
import glob, json, os, sys

sys.path[:0] = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pipeline")]
import platedat

DEMO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VIEWS = ("torso", "neck", "sleeve", "hem")


def fit_of(L, r, anchor):
    if anchor == "cf": return {"rule": "centred", "n": None, "fit": 1.0}
    lim = 0.10 if L < 3 * r else 0.05
    n = max(1, round(L / r))
    f = L / (n * r)
    return {"rule": "whole", "n": n, "fit": round(f, 4)} if abs(f - 1) <= lim else {"rule": "kept", "n": round(L / r, 2), "fit": 1.0}


def main(a):
    laces = a or sorted(os.path.basename(p)[5:-5] for p in glob.glob(os.path.join(DEMO, "assets", "swatches", "lace-*.json")))
    plates = {v: platedat.read(os.path.join(DEMO, "assets", "plates", f"{v}-straight")) for v in VIEWS}
    for ln in laces:
        m = json.load(open(os.path.join(DEMO, "assets", "swatches", f"lace-{ln}.json")))
        W = m.get("widthMm", 30.0) / 10
        if m.get("mirror") or not m.get("periodRatio"):
            print(f"{ln:10} width {W * 10:5.1f} mm ({m.get('widthSrc', 'assumed')}): no repeat (mirrored), no fit"); continue
        r = m["periodRatio"] * W
        print(f"{ln:10} width {W * 10:5.1f} mm ({m.get('widthSrc', 'assumed')}), repeat {r:.2f} cm")
        groups = {}
        for v, P in plates.items():
            D = P.get("decisions", {}).get("trims", {})
            for tn, t in sorted(P["trims"].items()):
                L = D.get(tn, {}).get("lengthCm")
                if L is None: continue
                f = fit_of(L, r, t.get("anchor", "cf"))
                live = " (live: the page's own length)" if t.get("live") else ""
                n = "" if f["n"] is None else (f"n {f['n']}" if f["rule"] == "whole" else f"L/r {f['n']} (scale kept, a motif cut)")
                print(f"   {v:6} {tn:7} {t.get('group', '?'):6} L {L:6.1f} cm  anchor {t.get('anchor', 'cf'):4} {f['rule']:8} {n:28} fit {f['fit']}{live}")
                groups.setdefault((t.get("group"), t.get("anchor", "cf")), []).append((v, tn, f))
        for (g, an), lst in sorted(groups.items()):
            views = {v for v, _, _ in lst}
            if len(views) < 2: continue
            ns = sorted({str(f["n"]) for _, _, f in lst if f["rule"] == "whole"})
            print(f"   across {g}/{an}: phase at the anchor equal by construction; whole counts {', '.join(ns) or '-'}"
                  + ("  (differ: the photos' lengths differ, accepted in StepB)" if len(ns) > 1 else ""))


if __name__ == "__main__":
    main(sys.argv[1:])
