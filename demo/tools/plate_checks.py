"""Acceptance numbers for one plate (plate.md step 6). Read-only.

usage: python3 tools/plate_checks.py assets/plates/<plate>

Prints, with PASS / FAIL:
  grid bulge   front side edges (left, right): largest sideways bulge from the chord   <= 5 % of the edge length
               (other edges may bend on purpose: shoulder line to the neck points, sleeves along the arm)
  grain tilt   front zone: tilt of constant-U lines from the vertical                  95 % of points <= 10 deg
  UV rate      cm of fabric per plate px, along U and V, median (face-on = mmPerPx/10)  within 0.8 .. 1.6 x face-on
  block ratio  fabric UV equal to the right neighbour                                  <= 0.05
  plate data   what ships: base.jpg + plate.dat                                        <= 1.0 MB
Limits come from the plates that are good: torso (side bulge 3.9 %, tilt 10.0 deg) and neck (2.6 %, 8.7 deg).
The sleeve plate of 2026-11-18 fails here (10.7 %, 18.4 deg): its front grid edge follows the armhole bulge.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_plate

D = sys.argv[1].rstrip("/") + "/"
M = make_plate.maps_of(D)                # the maps of plate.dat, in memory (StepA step 1)
Z, P = M["zones"], M["plate"]
uv, idm = M["uv"], M["id"]
up, ip = uv.load(), idm.load()
W, H = idm.size
R = P["uvRangeCm"]
face_on = P["mmPerPx"] / 10
ok_all = True


def report(name, value, ok):
    global ok_all
    ok_all &= ok
    print(f"{'PASS' if ok else 'FAIL'}  {name:34} {value}")


def dec(p):
    return (((p[0] << 4) | (p[2] >> 4)) / 4095 * R, ((p[1] << 4) | (p[2] & 15)) / 4095 * R)


# grid bulge
for zn, zv in Z["zones"].items():
    for side, e in zv["grid"].items():
        if zn != "front" or side not in ("left", "right") or len(e) < 3:
            continue
        a, b = e[0], e[-1]
        L = math.dist(a, b)
        if L < 50:
            continue
        dev = max(abs((b[0] - a[0]) * (a[1] - p[1]) - (a[0] - p[0]) * (b[1] - a[1])) / L for p in e)
        report(f"grid bulge {zn}.{side}", f"{dev:.0f} px = {100 * dev / L:.1f} %", dev / L <= 0.05)

# grain tilt and UV rate, per zone (fabric pixels only, not under a trim)
for zn, zid in ((k, v["id"]) for k, v in P["zones"].items()):
    tilts, ru, rv = [], [], []
    for y in range(20, H - 30, 20):
        for x in range(20, W - 30, 20):
            if ip[x, y][0] != zid or ip[x, y][1] or ip[x + 12, y][0] != zid or ip[x, y + 12][0] != zid:
                continue
            u0, v0 = dec(up[x, y])
            ux, vx = dec(up[x + 12, y])
            uy, vy = dec(up[x, y + 12])
            gu = ((ux - u0) / 12, (uy - u0) / 12)          # gradient of U on the screen
            gv = ((vx - v0) / 12, (vy - v0) / 12)          # gradient of V on the screen
            nu, nv = math.hypot(*gu), math.hypot(*gv)
            if nu == 0 or nv == 0:
                continue
            ru.append(nu)
            rv.append(nv)
            # constant-U lines run along the grain; on a hanging panel they should be near vertical
            tilts.append(math.degrees(math.atan2(abs(gu[1]), abs(gu[0]))))
    if not tilts:
        continue
    tilts.sort(); ru.sort(); rv.sort()
    t95 = tilts[int(len(tilts) * 0.95)]
    if zn == "front":
        report(f"grain tilt {zn} (95 %)", f"{t95:.1f} deg (median {tilts[len(tilts) // 2]:.1f})", t95 <= 10)
    else:
        print(f"info  grain tilt {zn} (95 %)              {t95:.1f} deg (sleeves bend at the elbow: not limited)")
    mu, mv = ru[len(ru) // 2] / face_on, rv[len(rv) // 2] / face_on
    report(f"UV rate {zn} (x face-on)", f"U {mu:.2f}, V {mv:.2f}", 0.8 <= mu <= 1.6 and 0.8 <= mv <= 1.6)

# block ratio
same = tot = 0
for y in range(H):
    for x in range(W - 1):
        a, b = ip[x, y], ip[x + 1, y]
        if a[0] and b[0] and not a[1] and not b[1]:
            tot += 1
            same += up[x, y] == up[x + 1, y]
report("block ratio", f"{same / tot:.3f}", same / tot <= 0.05)

kb = sum(os.path.getsize(D + f) for f in ("base.jpg", "plate.dat")) / 1024
report("plate data", f"{kb:.0f} KB", kb <= 1024)
print("ALL PASS" if ok_all else "SOME CHECKS FAIL")
