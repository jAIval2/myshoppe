// StepA step 4: plate.js frameUV() against tools/plateframe.py uv(), at the points of
//   python3 tools/plateframe.py --samples <plate-dir> <samples.json>
// usage: node tools/frame_check.mjs <plate-dir> <samples.json>        pass: every |du|, |dv| <= 1e-4 cm; exit code 0
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
const Plate = createRequire(import.meta.url)("../plate.js");
const [dir, samples] = process.argv.slice(2);
if (!dir || !samples) { console.error("usage: node tools/frame_check.mjs <plate-dir> <samples.json>"); process.exit(2); }
const buf = readFileSync(`${dir}/plate.dat`);
const { zones: Z } = Plate.parseDat(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength));
const S = JSON.parse(readFileSync(samples, "utf8"));
let du = 0, dv = 0, n = 0;
for (const [zn, x, y, u, v] of S.points) {
  const [ju, jv] = Plate.frameUV(Z.zones[zn].frame, Z.mmPerPx, x, y);
  du = Math.max(du, Math.abs(ju - u)); dv = Math.max(dv, Math.abs(jv - v)); n++;
}
const ok = du <= 1e-4 && dv <= 1e-4;
console.log(`${ok ? "PASS" : "FAIL"}  ${dir}: ${n} points, max |du| ${du.toExponential(2)} cm, |dv| ${dv.toExponential(2)} cm (limit 1e-4)`);
process.exit(ok ? 0 : 1);
