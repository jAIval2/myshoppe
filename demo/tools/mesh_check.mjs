// numeric.md step 1: plate.js against make_plate.py. Every vertex of every zone grid and trim strip, and the neck edge and
// its offsets, compared with the Python values.
//
// usage: python3 tools/make_plate.py <plate-dir> --dump-mesh <prefix>      (writes <prefix>.json, <prefix>.bin)
//        node tools/mesh_check.mjs <plate-dir> <prefix>
// pass: every position within 0.01 px, every u / v within 0.001 cm (v of a trim: 0.0001 of the strip), exit code 0.
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
const Plate = createRequire(import.meta.url)("../plate.js");

const [dir, prefix] = process.argv.slice(2);
if (!dir || !prefix) { console.error("usage: node tools/mesh_check.mjs <plate-dir> <prefix>"); process.exit(2); }
const datBuf = readFileSync(`${dir}/plate.dat`);
const dat = Plate.parseDat(datBuf.buffer.slice(datBuf.byteOffset, datBuf.byteOffset + datBuf.byteLength));   // plate.dat version 2 (StepA step 1)
const Z = Plate.prepare(dat.zones);
const P = dat.plate;
const meta = JSON.parse(readFileSync(`${prefix}.json`, "utf8"));
const raw = readFileSync(`${prefix}.bin`);
const bin = new Float64Array(raw.buffer, raw.byteOffset, raw.byteLength / 8);

let ok = true;
const rep = (name, n, dpos, du, dv, tol) => {
  const pass = dpos <= tol.pos && du <= tol.u && dv <= tol.v;
  ok &&= pass;
  console.log(`${pass ? "PASS" : "FAIL"}  ${name.padEnd(14)} ${String(n).padStart(8)} vertices  max |dpos| ${dpos.toExponential(2)} px  |du| ${du.toExponential(2)}  |dv| ${dv.toExponential(2)}`);
};
const cmp = (a, o, count, stride, uIdx) => {            // compare a JS Float64Array with bin[o .. o + count]
  let dp = 0, du = 0, dv = 0;
  for (let i = 0; i < count; i += stride) {
    dp = Math.max(dp, Math.abs(a[i] - bin[o + i]), Math.abs(a[i + 1] - bin[o + i + 1]));
    du = Math.max(du, Math.abs(a[i + 2] - bin[o + i + 2]));
    dv = Math.max(dv, Math.abs(a[i + 3] - bin[o + i + 3]));
  }
  return [dp, du, dv];
};

for (const [name, m] of Object.entries(meta.zones)) {
  const zone = Z.zones[name], par = Plate.zoneParams(name, zone, Z);
  if (par.ns !== m.ns || par.nt !== m.nt) { console.log(`FAIL  ${name}: grid ${par.ns}x${par.nt} vs Python ${m.ns}x${m.nt}`); ok = false; continue; }
  const v = Plate.zoneVertices(zone, par);
  if (v.length !== m.count) { console.log(`FAIL  ${name}: ${v.length} vs ${m.count} values`); ok = false; continue; }
  const [dp, du, dv] = cmp(v, m.offset, m.count, 4);
  rep(`zone ${name}`, m.count / 4, dp, Math.max(du, Math.abs(par.widthCm - m.widthCm), Math.abs(par.heightCm - m.heightCm)), dv, { pos: 0.01, u: 0.001, v: 0.001 });
}
for (const [name, m] of Object.entries(meta.trims)) {
  const trim = Z.trims[name], par = Plate.trimParams(name, trim, Z);
  if (par.n !== m.n || par.steps !== m.steps || par.vmax !== m.vmax) { console.log(`FAIL  trim ${name}: n ${par.n}/${m.n} steps ${par.steps}/${m.steps}`); ok = false; continue; }
  const side = P.trims[name].side;
  if (side !== m.side) { console.log(`FAIL  trim ${name}: plate side ${side} vs ${m.side}`); ok = false; continue; }
  const s = Plate.trimStrip(trim, par, side);
  const [dp, du, dv] = cmp(s, m.offset, m.count, 4);      // stride 4: x y u v of each corner
  rep(`trim ${name}`, m.count / 4, dp, du, dv, { pos: 0.01, u: 0.001, v: 0.0001 });
  // the two-quad ribbon of the page against the same corners of the full strip (levels 0, stepsIn, steps)
  const T = Plate.trimTriangles(trim, par, side, 0, 1);
  let rp = 0, ru = 0, rv = 0;
  const lvl = (i, k, e) => m.offset + ((i * (par.steps + 1) + k) * 2 + e) * 4;       // start of the corner (i, level k, end e) in bin
  const chk = (arr, q, i, k, e, tri) => {                 // vertex tri of quad i in arr against the strip corner
    const o = i * 24 + tri * 4, b0 = lvl(i, k, e);
    rp = Math.max(rp, Math.abs(arr[o] - bin[b0]), Math.abs(arr[o + 1] - bin[b0 + 1]));
    ru = Math.max(ru, Math.abs(arr[o + 2] - bin[b0 + 2])); rv = Math.max(rv, Math.abs(arr[o + 3] - bin[b0 + 3]));
  };
  for (let i = 0; i < par.n; i++)
    for (const [arr, k0, k1] of [[T.inner, 0, par.stepsIn], [T.outer, par.stepsIn, par.steps]]) {
      if (!arr) continue;
      // triangle order of a quad: (a,k0) (b,k0) (a,k1) | (b,k0) (b,k1) (a,k1)
      chk(arr, 0, i, k0, 0, 0); chk(arr, 0, i, k0, 1, 1); chk(arr, 0, i, k1, 0, 2); chk(arr, 0, i, k1, 1, 4);
    }
  rep(`ribbon ${name}`, par.n * (T.outer ? 8 : 4), rp, ru, rv, { pos: 0.01, u: 0.001, v: 0.0001 });
}
if (meta.neck) {                                          // the neck edge (found by outline analysis) and its offsets
  const front = Z.zones.front, W = P.viewBox[0];
  const { edge } = Plate.neck_edge(front, Z, W);
  const same = (a, b) => a.length === b.length && a.every((p, i) => Math.abs(p[0] - b[i][0]) < 0.01 && Math.abs(p[1] - b[i][1]) < 0.01);
  const e1 = same(edge, meta.neck.edge), e2 = same(edge, P.neck.edge.map((p) => p));
  const below = Plate.offset_poly(edge, meta.neck.belowD, meta.neck.away), above = Plate.offset_poly(edge, meta.neck.aboveD, meta.neck.away);
  const o1 = same(below, meta.neck.below), o2 = same(above, meta.neck.above);
  for (const [n, p] of [["neck edge", e1 && e2], ["offset below", o1], ["offset above", o2]]) { console.log(`${p ? "PASS" : "FAIL"}  ${n.padEnd(14)} ${edge.length} points`); ok &&= p; }
}
console.log(ok ? "ALL PASS" : "SOME FAIL");
process.exit(ok ? 0 : 1);
