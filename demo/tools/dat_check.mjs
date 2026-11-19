// numeric.md step 6: plate.dat against zones.json + plate.json. parseDat() must give back everything that the page uses, exactly
// (the coordinates of zones.json are multiples of 0.1 px; the .dat stores them as integers of 0.1 px).
//
// usage: node tools/dat_check.mjs <plate-dir> [...]      exit code 0 = every plate identical
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
const Plate = createRequire(import.meta.url)("../plate.js");

const same = (a, b, path, bad) => {
  if (typeof a === "number" && typeof b === "number") { if (a !== b) bad.push(`${path}: ${a} vs ${b}`); return; }
  if (Array.isArray(a) || Array.isArray(b)) {
    if (!Array.isArray(a) || !Array.isArray(b) || a.length !== b.length) { bad.push(`${path}: array length`); return; }
    a.forEach((x, i) => same(x, b[i], `${path}[${i}]`, bad));
    return;
  }
  if (a && typeof a === "object" && b && typeof b === "object") {
    for (const k of new Set([...Object.keys(a), ...Object.keys(b)])) same(a[k], b[k], `${path}.${k}`, bad);
    return;
  }
  if (a !== b) bad.push(`${path}: ${JSON.stringify(a)} vs ${JSON.stringify(b)}`);
};

let ok = true;
for (const dir of process.argv.slice(2)) {
  const buf = readFileSync(`${dir}/plate.dat`);
  const { plate, zones } = Plate.parseDat(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength));
  const P = JSON.parse(readFileSync(`${dir}/plate.json`, "utf8")), Z = JSON.parse(readFileSync(`${dir}/zones.json`, "utf8"));
  const bad = [];
  same(plate, P, "plate", bad);
  const want = { view: Z.view, mmPerPx: Z.mmPerPx, zones: {}, trims: {} };
  for (const k of ["thetaDeg", "tuck", "shadeSmoothEps", "shadeSmoothMm", "occluders"]) if (Z[k] !== undefined) want[k] = Z[k];
  for (const [n, z] of Object.entries(Z.zones)) want.zones[n] = { order: z.order, grid: z.grid, outline: z.outline, ...(z.widthPx !== undefined ? { widthPx: z.widthPx } : {}) };
  for (const [n, t] of Object.entries(Z.trims)) want.trims[n] = { order: t.order, widthMm: t.widthMm, centre: t.centre, ...(t.type !== undefined ? { type: t.type } : {}) };
  same(zones, want, "zones", bad);
  console.log(`${bad.length ? "FAIL" : "PASS"}  ${dir}  ${buf.length} B${bad.length ? "\n  " + bad.slice(0, 8).join("\n  ") : ""}`);
  ok &&= !bad.length;
}
process.exit(ok ? 0 : 1);
