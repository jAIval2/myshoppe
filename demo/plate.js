/*
  plate.js — the plate maths of tools/make_plate.py, in JavaScript (numeric.md step 1). One file, no dependencies.
  A classic script: in the page it sets window.Plate; in Node (tools/mesh_check.mjs) it is `require`d.

  Same names and same arithmetic as make_plate.py, so that the page can calculate what the plate maker calculates:
    resample, coons, tuck, prepare (tuck applied to a copy of zones.json), zoneParams, zoneVertices,
    trimParams, trimStrip, neck_edge, offset_poly.
  make_plate.py stays the reference. Decisions that it takes by searching the image (which side of a trim is the garment
  edge, the median light, the fill colours, the form patch) are NOT repeated here: they arrive as numbers (plate.json /
  the .dat file), e.g. trims[name].side.

  Differences from Python on purpose:
  - a zone / trim vertex carries its OWN (u, v) (the value at the vertex); make_plate.py paints one constant (u, v) for each
    1 px quad (the value at the quad centre). On a mesh the GPU interpolates between the vertices; the two agree at the quad
    centres.
  - Python round() rounds halves to even; pyRound() does the same.
*/
(function (root) {
  "use strict";
  const STEP = 1.0;                                      // quad size in px of the plate maker; the page uses a coarser step
  const V_MAX_EDGING = 1.5;
  const EDGING_DEFAULT = ["hem", "cuff-l", "cuff-r"];
  const THETA_DEFAULT = { front: 60, "sleeve-l": 70, "sleeve-r": 70 };

  const pyRound = (x) => {                               // Python 3 round(): halves to the even integer
    const r = Math.round(x);
    return Math.abs(x % 1) === 0.5 && r % 2 !== 0 ? r - 1 : r;
  };
  const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);

  function length(pts) {
    let n = 0;
    for (let i = 0; i < pts.length - 1; i++) n += dist(pts[i], pts[i + 1]);
    return n;
  }

  function resample(pts, n) {                            // n + 1 points, equal arc length along the polyline
    const seg = [];
    for (let i = 0; i < pts.length - 1; i++) seg.push(dist(pts[i], pts[i + 1]));
    const total = seg.reduce((a, b) => a + b, 0) || 1;
    const out = [];
    let i = 0, acc = 0;
    for (let k = 0; k <= n; k++) {
      const target = (total * k) / n;
      while (i < seg.length - 1 && acc + seg[i] < target) { acc += seg[i]; i++; }
      let f = seg[i] ? (target - acc) / seg[i] : 0;
      f = Math.max(0, Math.min(1, f));
      out.push([pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f]);
    }
    return out;
  }

  function coons(g, ns, nt) {                            // the Coons patch of the 4 edge curves: P[j][i] = [x, y]
    const T = resample(g.top, ns), B = resample(g.bottom, ns), Lf = resample(g.left, nt), R = resample(g.right, nt);
    const c00 = [(T[0][0] + Lf[0][0]) / 2, (T[0][1] + Lf[0][1]) / 2];
    const c10 = [(T[T.length - 1][0] + R[0][0]) / 2, (T[T.length - 1][1] + R[0][1]) / 2];
    const c01 = [(B[0][0] + Lf[Lf.length - 1][0]) / 2, (B[0][1] + Lf[Lf.length - 1][1]) / 2];
    const c11 = [(B[B.length - 1][0] + R[R.length - 1][0]) / 2, (B[B.length - 1][1] + R[R.length - 1][1]) / 2];
    const P = [];
    for (let j = 0; j <= nt; j++) {
      const t = j / nt, row = [];
      for (let i = 0; i <= ns; i++) {
        const s = i / ns, pt = [];
        for (let k = 0; k < 2; k++) {
          pt.push((1 - t) * T[i][k] + t * B[i][k] + (1 - s) * Lf[j][k] + s * R[j][k]
            - ((1 - s) * (1 - t) * c00[k] + s * (1 - t) * c10[k] + (1 - s) * t * c01[k] + s * t * c11[k]));
        }
        row.push(pt);
      }
      P.push(row);
    }
    return P;
  }

  function tuck(p, t) {                                  // push a front side point outward so that the front goes UNDER the sleeves
    const [x, y] = p;
    if (Math.abs(x - t.cx) < t.centreBand) return [x, y];
    let d;
    if (y < t.tipY) d = t.tip;
    else if (y <= t.yFull) d = t.reach;
    else if (y <= t.yZero) d = t.reach + ((t.below - t.reach) * (y - t.yFull)) / (t.yZero - t.yFull);
    else d = t.below;
    return [x + (x > t.cx ? d : -d), y];
  }

  function prepare(Z) {                                  // a copy of zones.json with "tuck" applied to the front grid and outline
    const C = JSON.parse(JSON.stringify(Z));
    if (C.tuck) {
      const fz = C.zones.front;
      for (const k of ["left", "right"]) fz.grid[k] = fz.grid[k].map((p) => tuck(p, C.tuck));
      fz.outline = fz.outline.map((p) => tuck(p, C.tuck));
    }
    return C;
  }

  // ---- zones. Z is a prepared zones.json.
  function zoneParams(name, zone, Z, cell) {             // cell: px per quad (STEP = the plate maker's own grid)
    const g = zone.grid, mmpx = Z.mmPerPx;
    const th = ((Z.thetaDeg && Z.thetaDeg[name]) ?? THETA_DEFAULT[name]) * Math.PI / 180;
    if (!(th > 0)) throw new Error(`no thetaDeg for zone ${name}`);
    const wPx = zone.widthPx || (length(g.top) + length(g.bottom)) / 2;
    const hPx = (length(g.left) + length(g.right)) / 2;
    const c = cell || STEP;
    const exact = !cell || cell === STEP;
    return {
      th, wPx, hPx,
      ns: exact ? Math.max(8, pyRound(wPx / c)) : Math.max(2, Math.ceil(wPx / c)),
      nt: exact ? Math.max(8, pyRound(hPx / c)) : Math.max(2, Math.ceil(hPx / c)),
      widthCm: (((wPx * mmpx) / 10) * th) / Math.sin(th),   // unrolled cylinder
      heightCm: (hPx * mmpx) / 10,
    };
  }
  // vertices (x, y, u, v) at every grid point, row-major (nt + 1) x (ns + 1); u, v in cm (the cylinder arc along u)
  function zoneVertices(zone, par) {
    const { ns, nt, th, widthCm, heightCm } = par;
    const P = coons(zone.grid, ns, nt), out = new Float64Array((ns + 1) * (nt + 1) * 4), st = Math.sin(th);
    let o = 0;
    for (let j = 0; j <= nt; j++) {
      for (let i = 0; i <= ns; i++) {
        const arc = (Math.asin((2 * (i / ns) - 1) * st) + th) / (2 * th);
        out[o++] = P[j][i][0]; out[o++] = P[j][i][1]; out[o++] = arc * widthCm; out[o++] = (j / nt) * heightCm;
      }
    }
    return out;
  }

  // ---- trims. `side` (+1 / -1) is the normal that points to the garment edge: a number from the plate (decided offline).
  function trimParams(name, trim, Z, cell) {
    const mmpx = Z.mmPerPx, c = trim.centre;
    const type = trim.type || (EDGING_DEFAULT.includes(name) ? "edging" : "insertion");
    const vmax = type === "edging" ? V_MAX_EDGING : 1.0;
    const half = trim.widthMm / 2 / mmpx, len = length(c);
    const cl = cell || STEP;
    const n = cl === STEP ? Math.max(4, pyRound(len / STEP)) : Math.max(4, Math.ceil(len / cl));
    const stepsIn = Math.max(8, Math.ceil(2 * half));    // one step per px across the strip
    return { type, vmax, half, n, stepsIn, steps: Math.ceil(stepsIn * vmax), lenCm: (len * mmpx) / 10 };
  }
  // per segment i, per level k, 2 corners (the a end and the b end): x, y, u, v (u: cm along, v: 0..1 over vMax)
  function trimStrip(trim, par, side) {
    const { n, steps, stepsIn, vmax, half, lenCm } = par;
    const C = resample(trim.centre, n), out = new Float64Array(n * (steps + 1) * 8);
    let o = 0;
    for (let i = 0; i < n; i++) {
      const a = C[i], b = C[i + 1], tx = b[0] - a[0], ty = b[1] - a[1], ln = Math.hypot(tx, ty) || 1;
      const nx = (-ty / ln) * side, ny = (tx / ln) * side;
      for (let k = 0; k <= steps; k++) {
        const f = Math.min(vmax, k / stepsIn), v = -half + 2 * half * f;
        out[o++] = a[0] + nx * v; out[o++] = a[1] + ny * v; out[o++] = (i / n) * lenCm; out[o++] = f / vmax;
        out[o++] = b[0] + nx * v; out[o++] = b[1] + ny * v; out[o++] = ((i + 1) / n) * lenCm; out[o++] = f / vmax;
      }
    }
    return out;
  }

  // ---- the neckline
  function neck_edge(front, Z, W) {                      // the run of front-outline points BELOW the grid top, corner to corner
    const top = front.grid.top, o = front.outline;
    const topy = (x) => {
      for (let i = 0; i < top.length - 1; i++) {
        const a = top[i], b = top[i + 1];
        if (a[0] !== b[0] && Math.min(a[0], b[0]) <= x && x <= Math.max(a[0], b[0])) return a[1] + ((b[1] - a[1]) * (x - a[0])) / (b[0] - a[0]);
      }
      return null;
    };
    const below = o.map((p) => { const t = topy(p[0]); return t !== null && p[1] > t + 0.5; });
    const cfx = (Z.landmarks && Z.landmarks["cf-neck"] ? Z.landmarks["cf-neck"][0] : W / 2);
    let i = 0;
    while (i < o.length) {
      if (below[i]) {
        let j = i;
        while (j + 1 < o.length && below[j + 1]) j++;
        const xs = o.slice(i, j + 1).map((p) => p[0]);
        if (Math.min(...xs) < cfx && cfx < Math.max(...xs) && i > 0 && j + 1 < o.length) return { edge: o.slice(i - 1, j + 2).map((p) => [p[0], p[1]]), topy };
        i = j + 1;
      } else i++;
    }
    return { edge: null, topy };
  }

  function offset_poly(pts, d, away) {                   // the vertex-normal offset: d px, away from the point `away`
    return pts.map(([x, y], i) => {
      const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
      const tx = b[0] - a[0], ty = b[1] - a[1], n = Math.hypot(tx, ty) || 1;
      let nx = -ty / n, ny = tx / n;
      if ((x - away[0]) * nx + (y - away[1]) * ny < 0) { nx = -nx; ny = -ny; }
      return [x + nx * d, y + ny * d];
    });
  }

  const Plate = { STEP, pyRound, length, resample, coons, tuck, prepare, zoneParams, zoneVertices, trimParams, trimStrip, neck_edge, offset_poly };
  if (typeof module !== "undefined" && module.exports) module.exports = Plate;
  else root.Plate = Plate;
})(typeof window !== "undefined" ? window : globalThis);
