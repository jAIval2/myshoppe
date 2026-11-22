/*
  plate.js — the plate maths of silhouette/pipeline/make_plate.py, in JavaScript (numeric.md step 1, StepA). One file, no dependencies.
  A classic script: in the page it sets window.Plate; in Node (silhouette/checks/frame_check.mjs) it is `require`d.

  Same names and same arithmetic as make_plate.py / plateframe.py / platedat.py, so that the page can calculate what the build
  calculates: resample, trimElements, trimTriangles (the trim field), offset_poly, outlineOf, frameProject, frameUV, underStrips,
  insidePoly, parseDat (plate.dat version 2).
  make_plate.py stays the reference. Decisions that it takes by searching the image (which side of a trim is the garment
  edge, the median light, the fill colours, the form patch) are NOT repeated here: they arrive as numbers (the
  decisions of plate.dat), e.g. trims[name].side.

  Python round() rounds halves to even; pyRound() does the same.
*/
(function (root) {
  "use strict";
  const STEP = 1.0;                                      // quad size in px of the plate maker

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






  // ---- trims (StepA extension, step L1): the elements of the trim field, as silhouette/pipeline/trimfield.py makes them (the same arithmetic).
  // A lace hangs on its garment edge: the line, resampled every 2 px, with smooth normals (the chord over +-30 mm) onto the zone; s =
  // the cloth length along it (cm, in the zone's fabric frame, 0 at the anchor); open ends carried on by the band. Each segment is one
  // element (part +1 inner, -1 the overhang of an edging trim): { part, a, b, na, nb, sa, sb }. maps.js draws them (TRIM_FS).
  const LACE_IN_MM = 56, LACE_OUT_MM = 8, SPACING_PX = 2, NORMAL_MM = 30;
  const S_OFF_CM = 64, T_OFF_MM = 64, SLIT_OFF_CM = { "slit-l": 32, "slit-r": 96 };
  const fround = (x) => Math.floor(x + 0.5);
  function trimAnchorS(s, uv, anchor) {
    if (anchor === "from") return 0;
    if (anchor === "to") return s[s.length - 1];
    for (let i = 0; i < s.length - 1; i++) {
      const u0 = uv[i][0], u1 = uv[i + 1][0];
      if (u0 === 0) return s[i];
      if (u0 * u1 < 0) return s[i] + ((s[i + 1] - s[i]) * u0) / (u0 - u1);
    }
    if (uv[uv.length - 1][0] === 0) return s[s.length - 1];
    const n = s.length;
    const [k, j] = Math.abs(uv[0][0]) <= Math.abs(uv[n - 1][0]) ? [0, Math.min(4, n - 1)] : [n - 1, Math.max(0, n - 5)];
    const du = uv[j][0] - uv[k][0], rate = Math.abs(du) > 1e-9 ? (s[j] - s[k]) / du : 0;
    return s[k] - uv[k][0] * rate;
  }
  function trimElements(t, F, mm) {
    const tin = LACE_IN_MM / mm, tout = t.type === "edging" ? LACE_OUT_MM / mm : 0;
    const line = t.line, L = length(line), n = Math.max(2, fround(L / SPACING_PX));
    let P = resample(line, n);
    const uv = P.map(([x, y]) => frameUV(F, mm, x, y));
    let S = [0];
    for (let i = 0; i + 1 < uv.length; i++) S.push(S[i] + Math.hypot(uv[i + 1][0] - uv[i][0], uv[i + 1][1] - uv[i][1]));
    const lengthCm = S[S.length - 1], s0 = trimAnchorS(S, uv, t.anchor || "cf");
    S = S.map((v) => v - s0);
    const k = Math.max(1, fround(NORMAL_MM / mm / (L / n)));
    let N = P.map((_, i) => {
      const a = P[Math.max(0, i - k)], b = P[Math.min(n, i + k)], tx = b[0] - a[0], ty = b[1] - a[1], l = Math.hypot(tx, ty) || 1;
      return [(-ty / l) * t.side, (tx / l) * t.side];
    });
    const ok = new Array(P.length - 1).fill(true), cut = t.cut || [], E = tin + 2;
    P = P.slice(); S = S.slice(); N = N.slice();
    for (const end of ["from", "to"]) {
      if (cut.includes(end)) continue;
      const [kk, j] = end === "from" ? [0, 1] : [P.length - 1, P.length - 2], nn = N[kk];
      let tx = nn[1], ty = -nn[0];
      if ((P[kk][0] - P[j][0]) * tx + (P[kk][1] - P[j][1]) * ty < 0) { tx = -tx; ty = -ty; }
      const d = dist(P[kk], P[j]) || 1, rate = (S[kk] - S[j]) / d;
      const q = [P[kk][0] + tx * E, P[kk][1] + ty * E], sq = S[kk] + rate * E;
      if (end === "from") { P.unshift(q); S.unshift(sq); N.unshift(nn); ok.unshift(false); }
      else { P.push(q); S.push(sq); N.push(nn); ok.push(false); }
    }
    const els = [];
    for (let j = 0; j + 1 < P.length; j++) {
      if (dist(P[j], P[j + 1]) < 1e-6) continue;
      els.push({ part: 1, a: P[j], b: P[j + 1], na: N[j], nb: N[j + 1], sa: S[j], sb: S[j + 1] });
      if (ok[j] && tout > 0) els.push({ part: -1, a: P[j], b: P[j + 1], na: N[j], nb: N[j + 1], sa: S[j], sb: S[j + 1] });
    }
    return { els, tin, tout, lengthCm };
  }
  // two triangles that hold every pixel an element accepts (1 px margin), as silhouette/pipeline/trimfield.py triangles()
  function trimTriangles(el, tin, tout) {
    const { part, a, b, na, nb } = el, L = dist(a, b), tx = (b[0] - a[0]) / L, ty = (b[1] - a[1]) / L;
    const [lo, hi] = part > 0 ? [-1, tin + 1] : [1, -(tout + 1)];
    const A0 = [a[0] - tx + na[0] * lo, a[1] - ty + na[1] * lo], B0 = [b[0] + tx + nb[0] * lo, b[1] + ty + nb[1] * lo];
    const B1 = [b[0] + tx + nb[0] * hi, b[1] + ty + nb[1] * hi], A1 = [a[0] - tx + na[0] * hi, a[1] - ty + na[1] * hi];
    return [A0, B0, B1, A0, B1, A1];
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

  // ---- plate.dat version 2 (silhouette/pipeline/platedat.py): every number of one view -> { plate, zones, P }. P is the file as written (typed
  // edges, zone outlines as chains of edges, trims, decisions); plate and zones are the shapes the map code reads: the plate header
  // (viewBox, ids, sizes, trim sides, the shade median, the neck block) and the zone data (outlines as points, frames, trims, settings),
  // exactly as silhouette/pipeline/platedat.py legacy() makes them.
  function outlineOf(P, zone) {                          // the chain of edges, a join point written once
    const out = [];
    for (const [name, d] of P.zones[zone].outline) {
      let pts = P.edges[name].points;
      if (d < 0) pts = pts.slice().reverse();
      const same = out.length && out[out.length - 1][0] === pts[0][0] && out[out.length - 1][1] === pts[0][1];
      for (let i = same ? 1 : 0; i < pts.length; i++) out.push([pts[i][0], pts[i][1]]);
    }
    if (out.length > 1 && out[0][0] === out[out.length - 1][0] && out[0][1] === out[out.length - 1][1]) out.pop();
    return out;
  }
  // ---- StepA step 4: the fabric frame (silhouette/pipeline/plateframe.py, the same arithmetic; silhouette/checks/frame_check.mjs compares the two)
  const axisNormals = new WeakMap();                     // axis -> unit vertex normals (the mean of the two segments' normals)
  function frameNormals(axis) {
    let N = axisNormals.get(axis);
    if (N) return N;
    const seg = [];
    for (let i = 0; i + 1 < axis.length; i++) { const dx = axis[i + 1][0] - axis[i][0], dy = axis[i + 1][1] - axis[i][1], L = Math.hypot(dx, dy) || 1e-9; seg.push([dy / L, -dx / L]); }
    N = axis.map((_, i) => { const ns = [i - 1, i].filter((j) => j >= 0 && j < seg.length).map((j) => seg[j]); const x = ns.reduce((a, n) => a + n[0], 0), y = ns.reduce((a, n) => a + n[1], 0), L = Math.hypot(x, y) || 1e-9; return [x / L, y / L]; });
    axisNormals.set(axis, N);
    return N;
  }
  // [s, r]: position along the axis (px) and signed distance (+ right walking down); the normal interpolated along each segment,
  // t solves (q - P(t)) x N(t) = 0: continuous across the vertices (silhouette/pipeline/plateframe.py project, the same arithmetic)
  function frameProject(axis, q) {
    const N = frameNormals(axis), n = axis.length;
    let best = null, acc = 0;
    for (let i = 0; i < n - 1; i++) {
      const a = axis[i], b = axis[i + 1], ex = b[0] - a[0], ey = b[1] - a[1], L = Math.hypot(ex, ey) || 1e-9;
      let na = N[i], nb = N[i + 1];
      if (i === 0) na = [ey / L, -ex / L];
      if (i === n - 2) nb = [ey / L, -ex / L];
      const wx = q[0] - a[0], wy = q[1] - a[1], dnx = nb[0] - na[0], dny = nb[1] - na[1];
      const A = -(ex * dny - ey * dnx), B = (wx * dny - wy * dnx) - (ex * na[1] - ey * na[0]), C = wx * na[1] - wy * na[0];
      const ts = [], disc = B * B - 4 * A * C;            // the stable roots (no cancellation when A is small)
      if (disc >= 0) {
        const qq = -0.5 * (B + (B >= 0 ? 1 : -1) * Math.sqrt(disc));
        if (Math.abs(qq) > 1e-15) ts.push(C / qq);
        if (Math.abs(A) > 1e-12) ts.push(qq / A);
      }
      const lo = i === 0 ? -Infinity : -1e-9, hi = i === n - 2 ? Infinity : 1 + 1e-9;
      for (const t of ts) {
        if (!(lo <= t && t <= hi)) continue;
        const px = a[0] + t * ex, py = a[1] + t * ey, nx = na[0] + t * dnx, ny = na[1] + t * dny, nl = Math.hypot(nx, ny) || 1e-9;
        const r = ((q[0] - px) * nx + (q[1] - py) * ny) / nl;
        if (best === null || Math.abs(r) < Math.abs(best[1]) - 1e-12) best = [acc + t * L, r];
      }
      acc += L;
    }
    if (best === null) {                                 // (not reached for a smooth axis) the nearest vertex
      let i = 0, d = Infinity;
      axis.forEach((p, k) => { const dd = (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2; if (dd < d) { d = dd; i = k; } });
      let s = 0;
      for (let k = 0; k < i; k++) s += Math.hypot(axis[k + 1][0] - axis[k][0], axis[k + 1][1] - axis[k][1]);
      best = [s, (q[0] - axis[i][0]) * N[i][0] + (q[1] - axis[i][1]) * N[i][1]];
    }
    return best;
  }
  const frameCubic = (c, t) => { t = Math.min(1, Math.max(0, t)); return c[0] + t * (c[1] + t * (c[2] + t * c[3])); };
  function frameUV(F, mm, x, y) {                        // [u, v] in cm
    const [s, r] = frameProject(F.axis, [x, y]);
    const h = Math.max(4, frameCubic(F.half[r >= 0 ? "right" : "left"], s / F.L));
    const th = (F.thetaDeg * Math.PI) / 180, st = Math.sin(th), ct = Math.cos(th), a = Math.abs(r);
    let up = a <= h ? (h / st) * Math.asin((a / h) * st) : (h / st) * th + (a - h) / ct;
    if (r < 0) up = -up;
    const sg = F.sag || {}, c = sg.c ?? 0, s1 = sg.s1 ?? F.s0;
    const w = s1 === F.s0 ? 0 : Math.min(1, Math.max(0, (s - F.s0) / (s1 - F.s0)));
    const sc = s - c * r * r * w;
    return [(up * mm) / 10, ((sc - F.s0) * mm + (F.vMm ?? 0)) / 10];
  }
  function insidePoly(pt, poly) {                        // the same even-odd test as the Python (edge pairs i - 1, i)
    let c = false;
    for (let i = 0; i < poly.length; i++) {
      const [x1, y1] = poly[(i + poly.length - 1) % poly.length], [x2, y2] = poly[i];
      if ((y1 > pt[1]) !== (y2 > pt[1]) && pt[0] < ((x2 - x1) * (pt[1] - y1)) / (y2 - y1) + x1) c = !c;
    }
    return c;
  }
  // at a seam the LOWER zone runs 6 px under the upper one (silhouette/pipeline/platedat.py under_strips): { lower zone: [strip polygons] }
  function underStrips(P) {
    const out = {}, Zs = P.zones, UNDER = 6;
    for (const e of Object.values(P.edges)) {
      if (e.type !== "seam" || e.under || !e.zones || e.zones.length !== 2) continue;
      const [a, b] = e.zones;
      if (Zs[a].order === Zs[b].order) continue;
      const [lo, up] = Zs[a].order < Zs[b].order ? [a, b] : [b, a], pts = e.points;
      if (pts.length < 2) continue;
      const upo = outlineOf(P, up);
      const normal = (i) => { const p = pts[Math.max(0, i - 1)], q = pts[Math.min(pts.length - 1, i + 1)], tx = q[0] - p[0], ty = q[1] - p[1], L = Math.hypot(tx, ty) || 1; return [-ty / L, tx / L]; };
      const m = Math.floor(pts.length / 2);
      const [nx, ny] = normal(m);
      const mid = pts.length > 2 ? [(pts[m][0] + pts[Math.max(0, m - 1)][0]) / 2, (pts[m][1] + pts[Math.max(0, m - 1)][1]) / 2] : [(pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2];
      const sgn = insidePoly([mid[0] + 2 * nx, mid[1] + 2 * ny], upo) ? 1 : -1;
      const off = pts.map((p, i) => { const [qx, qy] = normal(i); return [p[0] + sgn * qx * UNDER, p[1] + sgn * qy * UNDER]; });
      (out[lo] ||= []).push(pts.map((p) => [p[0], p[1]]).concat(off.reverse()));
    }
    return out;
  }
  function chainOf(P, ch) {                             // an occluder: a chain of edges, a join point written once, no closure
    const out = [];
    for (const [name, d] of ch) {
      let pts = P.edges[name].points;
      if (d < 0) pts = pts.slice().reverse();
      const same = out.length && out[out.length - 1][0] === pts[0][0] && out[out.length - 1][1] === pts[0][1];
      for (let i = same ? 1 : 0; i < pts.length; i++) out.push([pts[i][0], pts[i][1]]);
    }
    return out;
  }
  function parseDat(buf) {
    const dv = new DataView(buf), u8 = new Uint8Array(buf);
    if (String.fromCharCode(u8[0], u8[1], u8[2], u8[3]) !== "BSP2") throw new Error("plate.dat: not BSP2");
    const version = dv.getUint16(4, true), unit = dv.getUint16(6, true), hlen = dv.getUint32(8, true);
    if (version !== 2) throw new Error("plate.dat: version " + version);
    const head = JSON.parse(new TextDecoder().decode(u8.subarray(12, 12 + hlen)));
    let off = 12 + hlen;
    const curves = head.curves.map((n) => {
      const pts = [];
      let x = 0, y = 0;
      for (let i = 0; i < n; i++, off += 4) {
        x += dv.getInt16(off, true); y += dv.getInt16(off + 2, true);
        pts.push([(x * unit) / 1000, (y * unit) / 1000]);       // an integer / 1000: the same double as Python's x * unit / 1000
      }
      return pts;
    });
    delete head.curves;
    const walk = (v) => {
      if (Array.isArray(v)) return v.map(walk);
      if (v && typeof v === "object") {
        const k = Object.keys(v);
        if (k.length === 1 && k[0] === "@c") return curves[v["@c"]].map((p) => p.slice());
        return Object.fromEntries(k.map((key) => [key, walk(v[key])]));
      }
      return v;
    };
    const P = walk(head), D = P.decisions || {}, S = P.settings || {};
    const plate = { viewBox: P.viewBox, mmPerPx: P.mmPerPx, uvRangeCm: P.uvRangeCm ?? 128, zones: {}, trims: {} };
    for (const [n, z] of Object.entries(P.zones)) plate.zones[n] = { id: z.id, ...((D.zones || {})[n] || {}) };
    for (const [n, t] of Object.entries(P.trims || {}))
      plate.trims[n] = { id: t.id, type: t.type, ...((D.trims || {})[n] || {}), side: t.side, zone: t.zone, anchor: t.anchor || "cf" };
    for (const k of ["shadeSmoothMm", "shadeSmoothPx", "shadeSpace", "shadeEncoding", "shadeMedian", "neck"]) if (D[k] !== undefined) plate[k] = D[k];
    const Z = { view: P.view, mmPerPx: P.mmPerPx, viewBox: P.viewBox, zones: {}, trims: {} };
    for (const k of ["thetaDeg", "shadeSmoothEps", "shadeSmoothMm", "shadeSpace"]) if (S[k] !== undefined) Z[k] = S[k];
    if (P.uvRangeCm !== undefined) Z.uvRangeCm = P.uvRangeCm;
    for (const [n, z] of Object.entries(P.zones)) {
      Z.zones[n] = { order: z.order, outline: outlineOf(P, n) };
      if (z.frame && z.frame.L !== undefined) Z.zones[n].frame = z.frame;
    }
    for (const [n, strips] of Object.entries(underStrips(P))) Z.zones[n].under = strips;
    // StepA step 6: each zone's free edges, in the direction of its outline (the soft edges)
    for (const [n, z] of Object.entries(P.zones))
      Z.zones[n].freeEdges = z.outline.filter(([e]) => P.edges[e].type === "free").map(([e, d]) => (d > 0 ? P.edges[e].points : P.edges[e].points.slice().reverse()).map((p) => [p[0], p[1]]));
    if (D.uvOffsetCm) Z.uvOffsetCm = D.uvOffsetCm;
    for (const [n, t] of Object.entries(P.trims || {}))
      Z.trims[n] = Object.fromEntries(["order", "type", "line", "side", "zone", "anchor", "cut"].filter((k) => t[k] !== undefined).map((k) => [k, t[k]]));
    for (const k of ["landmarks", "stitches", "invariants"]) if (P[k] !== undefined) Z[k] = P[k];
    if (P.occluders && P.occluders.length) Z.occluders = P.occluders.map((o) => (typeof o[0][0] === "string" ? chainOf(P, o) : o));
    const cut = Object.values(P.edges).find((e) => e.type === "cut");
    if (cut) Z.neckEdge = cut.points;
    return { plate, zones: Z, P };
  }

  const Plate = { STEP, pyRound, length, resample, trimElements, trimTriangles, LACE_IN_MM, LACE_OUT_MM, S_OFF_CM, T_OFF_MM, SLIT_OFF_CM, offset_poly, outlineOf, frameProject, frameUV, underStrips, insidePoly, parseDat };
  if (typeof module !== "undefined" && module.exports) module.exports = Plate;
  else root.Plate = Plate;
})(typeof window !== "undefined" ? window : globalThis);
