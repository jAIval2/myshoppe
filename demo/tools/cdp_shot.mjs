// Headless Chrome through the DevTools protocol (no libraries; Node >= 22 has WebSocket).
// Saves the WebGL CANVAS itself (toDataURL: exact pixels, no page chrome) and every console error, for each query.
// Better than a screenshot: it waits until the page says the frame is drawn, and the shader compile log is captured.
//
// usage: node tools/cdp_shot.mjs <out-dir> <port> [--dpr 2] [--win 900x760] [--eval "<js>"] "<query>" ["<query>" ...]
//   --eval: JavaScript run in the page after the first frame (may return a Promise); its JSON result goes to log.json.
//           The page exposes window.__studio (see testing.html) for tests: setNeck(), state, timings.
//   --page: also a screenshot of the whole page (page-<i>.png: the SVG handles, the panel)
//   writes <out>/canvas-<i>.png and <out>/log.json  ({ query, errors, stat, result })
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync, mkdirSync, rmSync, readFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const args = process.argv.slice(2);
const opt = { dpr: 2, win: "900x760", eval: null, budget: 120000 };
const pos = [];
for (let i = 0; i < args.length; i++) {
  if (args[i] === "--dpr") opt.dpr = parseFloat(args[++i]);
  else if (args[i] === "--win") opt.win = args[++i];
  else if (args[i] === "--eval") opt.eval = args[++i];
  else if (args[i] === "--budget") opt.budget = parseInt(args[++i]);
  else if (args[i] === "--input") opt.input = JSON.parse(args[++i]);
  else if (args[i] === "--page") opt.page = true;
  else pos.push(args[i]);
}
// the 8 fixed review queries of the polish plan (tools/polish_metrics.py QUERIES); "--polish [extra]" appends extra to each
const POLISH = ["view=torso&fabric=sage&lace=pearl", "view=torso&fabric=mocha&lace=geometric", "view=neck&fabric=mustard&lace=leaf",
  "view=neck&fabric=mocha&lace=fine", "view=sleeve&fabric=sage&lace=geometric", "view=hem&fabric=mocha&lace=geometric",
  "view=hem&fabric=mustard&lace=pearl", "view=neck&fabric=off"];
let [out, port, ...queries] = pos;
if (queries[0] === "--polish") queries = POLISH.map((q) => q + (queries[1] || ""));
if (!out || !port || !queries.length) { console.error("usage: node tools/cdp_shot.mjs <out> <port> [opts] <query> ..."); process.exit(2); }
mkdirSync(out, { recursive: true });
const [W, H] = opt.win.split("x").map(Number);
const CHROME = process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const prof = mkdtempSync(join(tmpdir(), "cdp"));
const chrome = spawn(CHROME, ["--headless=new", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--hide-scrollbars",
  "--remote-debugging-port=0", `--user-data-dir=${prof}`, `--window-size=${W},${H}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const cleanup = () => { try { chrome.kill("SIGKILL"); } catch {} try { rmSync(prof, { recursive: true, force: true }); } catch {} };
process.on("exit", cleanup);

let dport = null;
for (let i = 0; i < 100 && !dport; i++) {
  await sleep(100);
  const f = join(prof, "DevToolsActivePort");
  if (existsSync(f)) dport = readFileSync(f, "utf8").split("\n")[0];
}
if (!dport) { console.error("Chrome did not start"); process.exit(1); }
const list = await (await fetch(`http://127.0.0.1:${dport}/json/list`)).json();
const page = list.find((t) => t.type === "page");
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r, { once: true }));
let id = 0;
const pending = new Map(), listeners = [];
ws.addEventListener("message", (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) { const { res, rej } = pending.get(m.id); pending.delete(m.id); m.error ? rej(new Error(m.error.message)) : res(m.result); }
  else listeners.forEach((f) => f(m));
});
const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params })); });
const evaluate = async (expr) => {
  const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
  return r.result.value;
};

let errors = [];
listeners.push((m) => {
  if (m.method === "Runtime.consoleAPICalled" && (m.params.type === "error" || m.params.type === "warning"))
    errors.push(m.params.args.map((a) => a.value ?? a.description).join(" "));
  if (m.method === "Runtime.exceptionThrown") errors.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
});
await send("Runtime.enable");
await send("Page.enable");
await send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: opt.dpr, mobile: false });

// --input '[...]': real input events through the protocol, run after the first frame and before --eval. Steps:
//   {"m":"down|move|up", "sel":"#h-cf", "dx":0, "dy":40}   mouse; "sel" (centre of its box) is read on "down" and kept as the base
//   {"t":"start|move|end", "sel":..., "dx":.., "dy":..}      touch, same rule
//   {"k":"ArrowDown", "shift":true}                         a key to the focused element;  {"k":"Tab"} moves the focus
//   {"wait": ms}   {"js": "<code>"} (its return value goes to the list)
// The result lists, after each step, document.activeElement's id and __studio.state.neck (when present).
async function runInput(steps) {
  let base = [0, 0];
  const out = [];
  await send("Emulation.setTouchEmulationEnabled", { enabled: true, maxTouchPoints: 1 });
  const centre = async (sel) => evaluate(`(() => { const r = document.querySelector(${JSON.stringify(sel)}).getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; })()`);
  for (const s of steps) {
    if (s.wait) { await sleep(s.wait); continue; }
    if (s.js) { out.push({ js: await evaluate(`(async () => { ${s.js} })()`) }); continue; }
    if ((s.m === "down" || s.t === "start") && s.sel) base = await centre(s.sel);
    const x = base[0] + (s.dx || 0), y = base[1] + (s.dy || 0);
    if (s.m) await send("Input.dispatchMouseEvent", { type: { down: "mousePressed", move: "mouseMoved", up: "mouseReleased" }[s.m], x, y, button: "left", buttons: s.m === "up" ? 0 : 1, clickCount: 1 });
    if (s.t) await send("Input.dispatchTouchEvent", { type: { start: "touchStart", move: "touchMove", end: "touchEnd" }[s.t], touchPoints: s.t === "end" ? [] : [{ x, y, id: 1 }] });
    if (s.k) {
      const vk = { ArrowDown: 40, ArrowUp: 38, ArrowLeft: 37, ArrowRight: 39, Tab: 9, Home: 36, End: 35, PageUp: 33, PageDown: 34 }[s.k] || 0;
      for (const type of ["rawKeyDown", "keyUp"])
        await send("Input.dispatchKeyEvent", { type, key: s.k, code: s.k, windowsVirtualKeyCode: vk, modifiers: s.shift ? 8 : 0 });
    }
    await sleep(s.m === "move" || s.t === "move" ? 60 : 30);
    out.push(await evaluate(`({ step: ${JSON.stringify(JSON.stringify(s))}, focus: document.activeElement && document.activeElement.id, neck: window.__studio && window.__studio.state.neck && { d: +window.__studio.state.neck.depthMm.toFixed(1), w: +window.__studio.state.neck.widthMm.toFixed(1) } })`));
  }
  return out;
}

const log = [];
for (const [i, q] of queries.entries()) {
  errors = [];
  const url = `http://127.0.0.1:${port}/testing.html${q ? "?" + q : ""}`;
  await send("Page.navigate", { url });
  const t0 = Date.now();
  let ok = false;
  while (Date.now() - t0 < opt.budget) {
    await sleep(250);
    try {
      ok = await evaluate(`!!document.querySelector("canvas.ready") || !!document.querySelector(".stage-note.show")`);
    } catch { ok = false; }
    if (ok) break;
  }
  await sleep(400);
  const entry = { query: q, ok };
  try {
    if (opt.input) entry.input = await runInput(opt.input);
    if (opt.eval) entry.result = await evaluate(`(async () => { ${opt.eval} })()`);
    entry.note = await evaluate(`document.querySelector(".stage-note.show")?.textContent || ""`);
    entry.stat = await evaluate(`document.getElementById("stat")?.textContent || ""`);
    const data = await evaluate(`document.getElementById("stage").toDataURL("image/png")`);
    writeFileSync(join(out, `canvas-${i}.png`), Buffer.from(data.split(",")[1], "base64"));
    if (opt.page) writeFileSync(join(out, `page-${i}.png`), Buffer.from((await send("Page.captureScreenshot", { format: "png" })).data, "base64"));
  } catch (e) { entry.error = String(e.message || e); }
  entry.errors = errors;
  log.push(entry);
  console.log(`canvas-${i}.png ${ok ? "ok" : "TIMEOUT"} ${q}${errors.length ? "  ERRORS: " + errors.join(" | ").slice(0, 400) : ""}${entry.error ? "  " + entry.error : ""}`);
}
writeFileSync(join(out, "log.json"), JSON.stringify(log, null, 1));
ws.close();
cleanup();
process.exit(0);
