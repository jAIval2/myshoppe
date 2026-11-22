/*
  maps.js — builds the plate maps on the GPU from the curves (numeric.md steps 2-4). Needs plate.js.
  A classic script: window.Maps.

  The main shader of testing.html reads data textures (id, uv, the trim fields uvt and uvts, shade). Here they are DRAWN, once per view load, into
  offscreen RGBA8 textures (StepA step 5: one exact draw for each zone and trim, the fabric frame evaluated per pixel, 16-bit packing).

  Coordinates: plate px, as make_plate.py (an integer coordinate = the centre of that pixel). Row j of a texture is plate row j
  (no flip), so the clip y is not flipped either.
*/
(function (root) {
  "use strict";
  const VS = `#version 300 es
  layout(location = 0) in vec2 aPos;
  layout(location = 1) in vec2 aUV;
  uniform vec2 uPlate;
  uniform vec2 uOff;        // plate px added to every position: an integer coordinate is the centre of that pixel (0.5, 0.5)
  out vec2 vUV;
  void main() {
    vUV = aUV;
    gl_Position = vec4((aPos.x + uOff.x) / uPlate.x * 2.0 - 1.0, (aPos.y + uOff.y) / uPlate.y * 2.0 - 1.0, 0.0, 1.0);
  }`;
  // 16-bit packing (StepA step 5): u and v / range -> 0..65535, RG = u (high, low byte), BA = v
  const PACK16 = `
  vec4 pack16(vec2 c) {
    int a = int(clamp(floor(c.x / uRange * 65535.0 + 0.5), 0.0, 65535.0));
    int b = int(clamp(floor(c.y / uRange * 65535.0 + 0.5), 0.0, 65535.0));
    return vec4(float(a >> 8), float(a & 255), float(b >> 8), float(b & 255)) / 255.0;
  }`;
  const FS = `#version 300 es
  precision highp float;
  precision highp int;
  uniform float uRange;     // UV range in cm (UV_RANGE_CM)
  ${PACK16}
  in vec2 vUV;
  uniform sampler2D uMask;  // unit 14: the garment (id R > 0), copied from the id once the zones are drawn (trims, step 3)
  uniform float uTestMask;  // 1 = draw only where the garment is (the inner part of a trim strip)
  uniform float uMode;      // 0 = a constant colour (id), 1 = the 16-bit packed (u, v) in cm (uv)
  uniform vec4  uCol;
  out vec4 outColor;
  void main() {
    if (uTestMask > 0.5 && texelFetch(uMask, ivec2(gl_FragCoord.xy), 0).r == 0.0) discard;
    if (uMode < 0.5) { outColor = uCol; return; }
    outColor = pack16(vUV);
  }`;


  // StepA step 5: the fabric frame of a zone at each pixel (Plate.frameUV / tools/plateframe.py, the same arithmetic, in float)
  const FRAME_FS = `#version 300 es
  precision highp float;
  precision highp int;
  uniform float uRange;
  ${PACK16}
  uniform float uMode;
  uniform vec4  uCol;
  uniform vec2  uAxis[33];   // the axis points
  uniform vec4  uSegN[33];   // per segment: the normals at its two ends (xy, zw)
  uniform float uCum[33];    // arc length at each point
  uniform int   uN;          // number of axis points
  uniform vec4  uHalfL, uHalfR;
  uniform float uLen, uTheta, uS0, uVmm, uSagC, uSagS1, uMm;
  uniform vec2  uUVOff;
  out vec4 outColor;
  float cubic(vec4 c, float t) { t = clamp(t, 0.0, 1.0); return c.x + t * (c.y + t * (c.z + t * c.w)); }
  void main() {
    if (uMode < 0.5) { outColor = uCol; return; }
    vec2 q = gl_FragCoord.xy - 0.5;                       // plate px: an integer coordinate is the centre of that pixel
    float bs = 0.0, br = 1e9;
    bool found = false;
    for (int i = 0; i < 32; i++) {
      if (i >= uN - 1) break;
      vec2 a = uAxis[i], e = uAxis[i + 1] - a, na = uSegN[i].xy, dn = uSegN[i].zw - na, w = q - a;
      float L = length(e);
      float A = -(e.x * dn.y - e.y * dn.x), B = (w.x * dn.y - w.y * dn.x) - (e.x * na.y - e.y * na.x), C = w.x * na.y - w.y * na.x;
      float lo = i == 0 ? -1e9 : -1e-6, hi = i == uN - 2 ? 1e9 : 1.0 + 1e-6;
      float t0 = 1e20, t1 = 1e20;                      // the stable roots (no cancellation when A is small: a near-straight segment)
      float d = B * B - 4.0 * A * C;
      if (d >= 0.0) {
        float qq = -0.5 * (B + (B >= 0.0 ? 1.0 : -1.0) * sqrt(d));
        if (abs(qq) > 1e-12) t0 = C / qq;
        if (abs(A) > 1e-9) t1 = qq / A;
      }
      for (int k = 0; k < 2; k++) {
        float t = k == 0 ? t0 : t1;
        if (t < lo || t > hi) continue;
        vec2 p = a + t * e, n = na + t * dn;
        float r = dot(q - p, n) / max(length(n), 1e-9);
        if (!found || abs(r) < abs(br)) { found = true; br = r; bs = uCum[i] + t * L; }
      }
    }
    float h = max(4.0, cubic(br >= 0.0 ? uHalfR : uHalfL, bs / uLen));
    float st = sin(uTheta), ct = cos(uTheta), ar = abs(br);
    float up = ar <= h ? (h / st) * asin(min(1.0, ar / h * st)) : (h / st) * uTheta + (ar - h) / ct;
    if (br < 0.0) up = -up;
    float wgt = uSagS1 == uS0 ? 0.0 : clamp((bs - uS0) / (uSagS1 - uS0), 0.0, 1.0);
    float sc = bs - uSagC * br * br * wgt;
    outColor = pack16(vec2(up * uMm / 10.0 + uUVOff.x, ((sc - uS0) * uMm + uVmm) / 10.0 + uUVOff.y));
  }`;


  // StepA extension, step L2: the trim field (tools/trimfield.py, the same arithmetic). One element = one segment of a trim's line
  // with the smooth normals at its two ends (flat inputs); the pixel's foot point solves (q - P(tau)) x N(tau) = 0. The element
  // accepts the pixel when 0 <= tau <= 1 and t lies in its band (inner 0..tin, outer -tout..0); the depth is |t|, so the nearest edge
  // wins. The inner part only on the trim's own zone; the overhang where there is no zone, its own, or one behind it (the stencil
  // keeps it off the objects in front). uMode 1: the field, 16-bit (u = s + uSOff cm, v = (t mm + 64) / 10 cm); 0: id G.
  const TRIM_VS = `#version 300 es
  layout(location = 0) in vec2 aPos;
  layout(location = 1) in vec4 aAB;
  layout(location = 2) in vec4 aN;
  layout(location = 3) in vec3 aSP;
  uniform vec2 uPlate;
  uniform vec2 uOff;
  flat out vec4 vAB;
  flat out vec4 vN;
  flat out vec3 vSP;
  void main() {
    vAB = aAB; vN = aN; vSP = aSP;
    gl_Position = vec4((aPos.x + uOff.x) / uPlate.x * 2.0 - 1.0, (aPos.y + uOff.y) / uPlate.y * 2.0 - 1.0, 0.0, 1.0);
  }`;
  const TRIM_FS = `#version 300 es
  precision highp float;
  precision highp int;
  uniform float uRange;
  ${PACK16}
  uniform sampler2D uMask;   // the zones (id R), copied once the zones and the soft edges are drawn
  uniform float uZone, uOrder, uTin, uTout, uMm, uSOff, uMode, uTrimId;
  uniform float uOrderOf[8]; // the order of each zone id
  flat in vec4 vAB;
  flat in vec4 vN;
  flat in vec3 vSP;
  out vec4 outColor;
  void main() {
    vec2 q = gl_FragCoord.xy - 0.5;
    int z = int(texelFetch(uMask, ivec2(gl_FragCoord.xy), 0).r * 255.0 + 0.5);
    if (vSP.z > 0.0) { if (float(z) != uZone) discard; }
    else if (!(z == 0 || float(z) == uZone || uOrderOf[z] < uOrder)) discard;
    vec2 a = vAB.xy, e = vAB.zw - vAB.xy, na = vN.xy, dn = vN.zw - vN.xy, w = q - a;
    float A = -(e.x * dn.y - e.y * dn.x), B = (w.x * dn.y - w.y * dn.x) - (e.x * na.y - e.y * na.x), C = w.x * na.y - w.y * na.x;
    float t0 = 1e20, t1 = 1e20;
    float d = B * B - 4.0 * A * C;
    if (d >= 0.0) {
      float qq = -0.5 * (B + (B >= 0.0 ? 1.0 : -1.0) * sqrt(d));
      if (abs(qq) > 1e-12) t0 = C / qq;
      if (abs(A) > 1e-9) t1 = qq / A;
    }
    bool found = false;
    float br = 0.0, bs = 0.0;
    for (int k = 0; k < 2; k++) {
      float tau = k == 0 ? t0 : t1;
      if (tau < -1e-6 || tau > 1.0 + 1e-6) continue;
      vec2 p = a + tau * e, n = na + tau * dn;
      float r = dot(q - p, n) / max(length(n), 1e-9);
      if (vSP.z > 0.0) { if (r < 0.0 || r > uTin) continue; }
      else if (r >= 0.0 || r < -uTout) continue;
      if (!found || abs(r) < abs(br)) { found = true; br = r; bs = vSP.x + (vSP.y - vSP.x) * clamp(tau, 0.0, 1.0); }
    }
    if (!found) discard;
    gl_FragDepth = abs(br) / 4096.0;
    if (uMode < 0.5) { outColor = vec4(0.0, uTrimId / 255.0, 0.0, 1.0); return; }
    outColor = pack16(vec2(bs + uSOff, (br * uMm + 64.0) / 10.0));
  }`;

  // StepA step 6: a soft free edge. vUV.x = the signed distance d to the edge in px (+ inside), from -3 to +1. id R = the zone, A =
  // (d + 3) / 4 (the coverage is clamp(0.5 + d); the shader also takes the outward direction from A's gradient). Not where the pixel,
  // or the point 1.5 or 3.5 px outward, belongs to another zone (a contour over another zone stays hard).
  const SOFT_FS = `#version 300 es
  precision highp float;
  precision highp int;
  uniform float uRange;
  uniform sampler2D uMask;
  uniform float uZone;
  in vec2 vUV;
  out vec4 outColor;
  void main() {
    if (vUV.x <= -3.0) discard;
    vec2 g = vec2(dFdx(vUV.x), dFdy(vUV.x));
    vec2 outward = length(g) > 0.0 ? -normalize(g) : vec2(0.0);
    float here = texelFetch(uMask, ivec2(gl_FragCoord.xy), 0).r;
    float there = texelFetch(uMask, ivec2(gl_FragCoord.xy + outward * 1.5), 0).r;
    float far = texelFetch(uMask, ivec2(gl_FragCoord.xy + outward * (3.5 + vUV.x)), 0).r;
    bool other = (here > 0.0 && abs(here - uZone) > 0.5 / 255.0) || (there > 0.0 && abs(there - uZone) > 0.5 / 255.0) || (far > 0.0 && abs(far - uZone) > 0.5 / 255.0);
    if (other) discard;
    outColor = vec4(uZone, 0.0, 0.0, clamp((vUV.x + 3.0) / 4.0, 0.0, 1.0));
  }`;

  function compile(gl, type, src) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error("maps.js: " + gl.getShaderInfoLog(s));
    return s;
  }

  function dataTexture(gl, w, h, img) {                     // RGBA8, NEAREST, clamped: a data texture like the PNG maps
    const t = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, t);
    if (img) {
      gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
      gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
      gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.NONE);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, img);
    } else gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, w, h, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    for (const [p, v] of [[gl.TEXTURE_MIN_FILTER, gl.NEAREST], [gl.TEXTURE_MAG_FILTER, gl.NEAREST], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]])
      gl.texParameteri(gl.TEXTURE_2D, p, v);
    return t;
  }

  // a vertex buffer for a polygon fan (u, v = 0)
  function fanBuffer(gl, poly) {
    const vb = gl.createBuffer(), v = new Float32Array(poly.length * 4);
    poly.forEach((p, i) => { v[i * 4] = p[0]; v[i * 4 + 1] = p[1]; });
    gl.bindBuffer(gl.ARRAY_BUFFER, vb); gl.bufferData(gl.ARRAY_BUFFER, v, gl.STATIC_DRAW);
    return { vb, count: poly.length };
  }

  // ---------------------------------------------------------------------------------------------------------------
  // Step 4: the shade (folds) from the photo. tools/make_plate.py does, in this order:
  //   Lum = base.convert("L") (Pillow: (299 R + 587 G + 114 B) with 16 bit fixed point and rounding), shade = Lum / median (the median
  //   is a number of the plate: decided offline), the guided filter of each zone (box windows of radius r, eps, masked by the
  //   zone; off when the plate has no shadeSmoothPx), the linear light encoding stored = sqrt(shade_lin / 2) * 255 (truncated),
  //   the value 180 (shade 1.0) outside the garment, and in the neck area the garment's shade carried 8 px outward (the dip).
  // Float textures are needed for the filter (var = s2 / n - mean^2): EXT_color_buffer_float. shadePasses() returns null without it.
  const FULL_VS = `#version 300 es
  void main() { vec2 p = vec2((gl_VertexID << 1) & 2, gl_VertexID & 2); gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0); }`;
  const SH_COMMON = `#version 300 es
  precision highp float;
  precision highp int;
  uniform sampler2D uPhotoRaw, uI, uId, uA, uB, uSrc;
  uniform ivec2 uSize;
  uniform int uZone, uR;
  uniform float uInvMed, uEps, uM255, uLinMed;
  uniform ivec4 uRect;      // neck area rectangle x0 y0 x1 y1 (x1, y1 exclusive); x0 = x1 when there is none
  out vec4 o;
  int zoneAt(ivec2 q) { return int(texelFetch(uId, q, 0).r * 255.0 + 0.5); }
  bool inside(ivec2 q) { return q.x >= 0 && q.y >= 0 && q.x < uSize.x && q.y < uSize.y; }
  bool inRect(ivec2 q) { return q.x >= uRect.x && q.x < uRect.z && q.y >= uRect.y && q.y < uRect.w; }
  `;
  const SH_FS = {
    lum: `void main() {
      ivec3 c = ivec3(texelFetch(uPhotoRaw, ivec2(gl_FragCoord.xy), 0).rgb * 255.0 + 0.5);
      int L = (c.r * 19595 + c.g * 38470 + c.b * 7471 + 32768) >> 16;
      o = vec4(float(L) * uInvMed, 0.0, 0.0, 1.0);
    }`,
    copy: `void main() { o = texelFetch(uSrc, ivec2(gl_FragCoord.xy), 0); }`,
    // (n, s1, s2) of the zone's pixels summed along x
    sumsH: `void main() {
      ivec2 p = ivec2(gl_FragCoord.xy); vec3 a = vec3(0.0);
      for (int d = -uR; d <= uR; d++) {
        ivec2 q = p + ivec2(d, 0);
        if (inside(q) && zoneAt(q) == uZone) { float v = texelFetch(uI, q, 0).r; a += vec3(1.0, v, v * v); }
      }
      o = vec4(a, 0.0);
    }`,
    // + vertically: the 2D sums; then a, b of the guided filter, times the zone mask; n is kept
    ab: `void main() {
      ivec2 p = ivec2(gl_FragCoord.xy); vec3 a = vec3(0.0);
      for (int d = -uR; d <= uR; d++) { ivec2 q = p + ivec2(0, d); if (inside(q)) a += texelFetch(uA, q, 0).rgb; }
      float n = a.x, A = 0.0, B = 0.0;
      if (zoneAt(p) == uZone && n > 0.0) {
        float I = texelFetch(uI, p, 0).r, mean = a.y / n, v = a.z / n - mean * mean;
        A = v > 0.0 ? v / (v + uEps) : 0.0;
        B = mean - A * mean;
      }
      o = vec4(A, B, n, 0.0);
    }`,
    sumsH2: `void main() {
      ivec2 p = ivec2(gl_FragCoord.xy); vec2 a = vec2(0.0);
      for (int d = -uR; d <= uR; d++) { ivec2 q = p + ivec2(d, 0); if (inside(q)) a += texelFetch(uB, q, 0).rg; }
      o = vec4(a, texelFetch(uB, p, 0).b, 0.0);
    }`,
    // + vertically, then q = (SA * I + SB) / n inside the zone (discard elsewhere: the other zones keep their own)
    guided: `void main() {
      ivec2 p = ivec2(gl_FragCoord.xy);
      if (zoneAt(p) != uZone) discard;
      vec2 a = vec2(0.0);
      for (int d = -uR; d <= uR; d++) { ivec2 q = p + ivec2(0, d); if (inside(q)) a += texelFetch(uA, q, 0).rg; }
      float n = texelFetch(uA, p, 0).b, I = texelFetch(uI, p, 0).r;
      o = vec4(n > 0.0 ? (a.x * I + a.y) / n : I, 0.0, 0.0, 1.0);
    }`,
    // the stored byte (R) and, in G, "known" for the dip fill: a garment pixel inside the neck rectangle
    enc: `void main() {
      ivec2 p = ivec2(gl_FragCoord.xy);
      float s = texelFetch(uI, p, 0).r;
      bool garment = zoneAt(p) > 0;
      float v = sqrt(pow((s * uM255 + 0.055) / 1.055, 2.4) / uLinMed / 2.0) * 255.0;
      float code = garment ? floor(clamp(v, 0.0, 255.0)) : 180.0;
      o = vec4(code / 255.0, (garment && inRect(p)) ? 1.0 : 0.0, 0.0, 1.0);
    }`,
    fill: `void main() {
      ivec2 p = ivec2(gl_FragCoord.xy); vec4 c = texelFetch(uSrc, p, 0);
      if (c.g > 0.5 || !inRect(p) || texelFetch(uId, p, 0).b == 0.0) { o = c; return; }
      float sum = 0.0, cnt = 0.0;
      for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) {
        ivec2 q = p + ivec2(dx, dy);
        if (inRect(q)) { vec4 k = texelFetch(uSrc, q, 0); if (k.g > 0.5) { sum += floor(k.r * 255.0 + 0.5); cnt += 1.0; } }
      }
      o = cnt > 0.0 ? vec4(floor(sum / cnt + 0.5) / 255.0, 1.0, 0.0, 1.0) : c;
    }`,
  };

  function shadePasses(gl, { W, H, plate, Z, photo, idTex, rb }) {
    if (!gl.getExtension("EXT_color_buffer_float") || !photo) return null;
    const progs = {};
    const prog = (k) => {
      if (progs[k]) return progs[k];
      const p = gl.createProgram();
      gl.attachShader(p, compile(gl, gl.VERTEX_SHADER, FULL_VS));
      gl.attachShader(p, compile(gl, gl.FRAGMENT_SHADER, SH_COMMON + SH_FS[k]));
      gl.linkProgram(p);
      if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error("maps.js shade " + k + ": " + gl.getProgramInfoLog(p));
      return (progs[k] = p);
    };
    const tex = (internal, format, type, filter) => {
      const t = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, internal, W, H, 0, format, type, null);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, filter); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, filter);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      return t;
    };
    const f32 = () => tex(gl.R32F, gl.RED, gl.FLOAT, gl.NEAREST), f32x4 = () => tex(gl.RGBA32F, gl.RGBA, gl.FLOAT, gl.NEAREST);
    const u8 = () => tex(gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, gl.NEAREST);
    const fb = (t) => { const f = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, f); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0); return f; };
    const fbs = [], texs = [];
    const mk = (t) => { texs.push(t); const f = fb(t); fbs.push(f); return { t, f }; };

    // the photo as bytes (not sRGB-decoded): the plate maker works on the bytes
    gl.activeTexture(gl.TEXTURE0 + 8);
    const raw = gl.createTexture(); texs.push(raw);
    gl.bindTexture(gl.TEXTURE_2D, raw);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false); gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false); gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.NONE);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, photo);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.activeTexture(gl.TEXTURE0 + 9); gl.bindTexture(gl.TEXTURE_2D, idTex);

    const vao = gl.createVertexArray(); gl.bindVertexArray(vao);
    gl.viewport(0, 0, W, H);
    gl.disable(gl.STENCIL_TEST); gl.disable(gl.SCISSOR_TEST); gl.colorMask(true, true, true, true);
    const SLOT = { uPhotoRaw: 8, uId: 9, uI: 10, uA: 11, uB: 12, uSrc: 13 };
    const run = (k, target, bind, ints = {}, floats = {}, box = null) => {     // bind: { sampler: texture }; box: [x0, y0, x1, y1] limits the pass
      const p = prog(k); gl.useProgram(p);
      const loc = (n) => gl.getUniformLocation(p, n);
      for (const [n, u] of Object.entries(SLOT)) { const l = loc(n); if (l) gl.uniform1i(l, u); }
      for (const [n, t] of Object.entries(bind)) { gl.activeTexture(gl.TEXTURE0 + SLOT[n]); gl.bindTexture(gl.TEXTURE_2D, t); }
      gl.activeTexture(gl.TEXTURE0 + 9); gl.bindTexture(gl.TEXTURE_2D, idTex);
      if (loc("uSize")) gl.uniform2i(loc("uSize"), W, H);
      if (loc("uRect")) gl.uniform4i(loc("uRect"), ...rect);
      for (const [n, v] of Object.entries(ints)) if (loc(n)) gl.uniform1i(loc(n), v);
      for (const [n, v] of Object.entries(floats)) if (loc(n)) gl.uniform1f(loc(n), v);
      gl.bindFramebuffer(gl.FRAMEBUFFER, target.f);
      if (box) { gl.enable(gl.SCISSOR_TEST); gl.scissor(box[0], box[1], box[2] - box[0], box[3] - box[1]); } else gl.disable(gl.SCISSOR_TEST);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      gl.disable(gl.SCISSOR_TEST);
    };
    const nk = plate.neck, rect = nk && nk.rect ? nk.rect : [0, 0, 0, 0];
    const med = plate.shadeMedian, m255 = med / 255;
    const sRGBtoLin = (c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
    const linMed = sRGBtoLin(m255);

    const I = mk(f32());                                      // shade as a ratio, 1.0 = the median light
    run("lum", I, { uPhotoRaw: raw }, {}, { uInvMed: 1 / med });
    let S = I;
    const r = plate.shadeSmoothPx || 0;
    if (r > 0) {                                              // the guided filter, zone by zone
      const eps = Z.shadeSmoothEps !== undefined ? Z.shadeSmoothEps : 0.006;
      const Q = mk(f32()), A = mk(f32x4()), B = mk(f32x4());
      run("copy", Q, { uSrc: I.t });
      const box = (name, pad) => {                              // the bounding box of a zone outline, grown by pad px, in the plate
        const o = Z.zones[name].outline, xs = o.map((p) => p[0]), ys = o.map((p) => p[1]);
        return [Math.max(0, Math.floor(Math.min(...xs) - pad)), Math.max(0, Math.floor(Math.min(...ys) - pad)),
                Math.min(W, Math.ceil(Math.max(...xs) + pad)), Math.min(H, Math.ceil(Math.max(...ys) + pad))];
      };
      for (const [name, zi] of Object.entries(plate.zones)) {
        const ints = { uZone: zi.id, uR: r }, floats = { uEps: eps };
        // the sums are needed where a window of the zone's pixels reaches: its box + r (+ the 2 px of the PNG's edge); the result inside the box
        const b1 = box(name, 2 * r + 4), b0 = box(name, 2);
        run("sumsH", A, { uI: I.t }, ints, {}, b1);
        run("ab", B, { uA: A.t, uI: I.t }, ints, floats, box(name, r + 4));
        run("sumsH2", A, { uB: B.t }, ints, {}, box(name, r + 4));
        run("guided", Q, { uA: A.t, uI: I.t }, ints, {}, b0);
      }
      S = Q;
    }
    const E0 = mk(u8()), E1 = mk(u8());                         // the bytes, ping-pong for the dip fill
    run("enc", E0, { uI: S.t }, {}, { uM255: m255, uLinMed: linMed });
    let cur = E0, nxt = E1;
    if (nk && nk.rect) {
      // ping-pong inside the rectangle only: copy the encoded bytes to the second target outside it once, then fill inside
      run("copy", E1, { uSrc: E0.t });
      for (let i = 0; i < 8; i++) { run("fill", nxt, { uSrc: cur.t }, {}, {}, nk.rect); [cur, nxt] = [nxt, cur]; }
    }
    gl.finish();
    // keep the result texture, free the rest. The page reads the shade with LINEAR filtering (texture()) and texelFetch.
    gl.bindTexture(gl.TEXTURE_2D, cur.t);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    for (const f of fbs) gl.deleteFramebuffer(f);
    for (const t of texs) if (t !== cur.t) gl.deleteTexture(t);
    for (const p of Object.values(progs)) gl.deleteProgram(p);
    gl.deleteVertexArray(vao);
    return cur.t;
  }

  /*
    build(gl, { plate, Z, photo, sync }) -> { id, uv, uvt, uvts, shade, ms }   (StepA steps 4-6 and the extension: exact maps)
      plate   the plate header (Plate.parseDat: viewBox, neck{rect, edge}, trims[name].side ...)
      Z       the zone data (Plate.parseDat): outlines, under-strips, frames, free edges, trims, occluders
      photo   optional: the decoded base.jpg (an ImageBitmap): with it, and with EXT_color_buffer_float, the shade is built too
      sync    test: wait for the GPU with a 1 px readback before ms is taken (gl.finish() does not always wait): the true cost
    One draw for each zone: its outline (and, at a seam, the lower zone's strip under the upper one) into the stencil, one polygon at
    a time, then one quad over the zone's box whose fragment shader evaluates the zone's fabric frame at the pixel (FRAME_FS: the
    arithmetic of Plate.frameUV); the trim field (one element per segment of each trim's line, the nearest edge wins). Exact shapes.
    id: R zone, G trim, B neck area. uv: the fabric (u, v) in cm + the view's offset, 16-bit: RG = u, BA = v, over UV_RANGE_CM.
    uvt: the trim field (u = s + 64 cm along the edge, v = (t mm from the edge + 64) / 10), the same packing; uvts: the slits' field
    (u = s + 32 for slit-l, s + 96 for slit-r). All RGBA8, NEAREST.
  */
  const UV_RANGE_CM = 128;
  const AXIS_MAX = 33;
  function build(gl, { plate, Z, photo = null, sync = false }) {
    const t0 = performance.now();
    const [W, H] = plate.viewBox;
    // ---- keep the state of the page: the program, the vertex array, the bound buffers, the viewport, the texture unit
    const saved = {
      prog: gl.getParameter(gl.CURRENT_PROGRAM), vao: gl.getParameter(gl.VERTEX_ARRAY_BINDING), vp: gl.getParameter(gl.VIEWPORT),
      active: gl.getParameter(gl.ACTIVE_TEXTURE), fb: gl.getParameter(gl.FRAMEBUFFER_BINDING), cm: gl.getParameter(gl.COLOR_WRITEMASK),
    };
    gl.activeTexture(gl.TEXTURE0 + 15);                      // scratch unit: the page's units 0-7 stay bound
    const mkProg = (fs) => {
      const p = gl.createProgram();
      gl.attachShader(p, compile(gl, gl.VERTEX_SHADER, VS));
      gl.attachShader(p, compile(gl, gl.FRAGMENT_SHADER, fs));
      gl.linkProgram(p);
      if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error("maps.js: " + gl.getProgramInfoLog(p));
      return p;
    };
    const prog = mkProg(FS), fprog = mkProg(FRAME_FS), sprog = mkProg(SOFT_FS);
    const tprog = (() => {                                   // the trim field (its own vertex shader: the element's numbers)
      const p = gl.createProgram();
      gl.attachShader(p, compile(gl, gl.VERTEX_SHADER, TRIM_VS));
      gl.attachShader(p, compile(gl, gl.FRAGMENT_SHADER, TRIM_FS));
      gl.linkProgram(p);
      if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error("maps.js: " + gl.getProgramInfoLog(p));
      return p;
    })();
    let cur = null;
    const use = (p) => { cur = p; gl.useProgram(p); };
    const U = (n) => gl.getUniformLocation(cur, n);
    for (const p of [prog, fprog, sprog, tprog]) {
      use(p);
      // an integer plate coordinate is the centre of that pixel (as Pillow draws, and as FRAME_FS evaluates: gl_FragCoord - 0.5)
      gl.uniform2f(U("uPlate"), W, H); gl.uniform2f(U("uOff"), 0.5, 0.5); gl.uniform1f(U("uRange"), UV_RANGE_CM);
    }
    use(prog);
    const vao = gl.createVertexArray();
    gl.bindVertexArray(vao);
    gl.enableVertexAttribArray(0); gl.enableVertexAttribArray(1);
    const attrib = () => { gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 16, 0); gl.vertexAttribPointer(1, 2, gl.FLOAT, false, 16, 8); };

    const idTex = dataTexture(gl, W, H, null), uvTex = dataTexture(gl, W, H, null);
    const rb = gl.createRenderbuffer();                      // the stencil, shared by the targets
    gl.bindRenderbuffer(gl.RENDERBUFFER, rb);
    gl.renderbufferStorage(gl.RENDERBUFFER, gl.DEPTH24_STENCIL8, W, H);
    const fbo = (tex) => {
      const f = gl.createFramebuffer();
      gl.bindFramebuffer(gl.FRAMEBUFFER, f);
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
      gl.framebufferRenderbuffer(gl.FRAMEBUFFER, gl.DEPTH_STENCIL_ATTACHMENT, gl.RENDERBUFFER, rb);
      if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) throw new Error("maps.js: framebuffer incomplete");
      return f;
    };
    const idFbo = fbo(idTex), uvFbo = fbo(uvTex);
    gl.viewport(0, 0, W, H);
    gl.disable(gl.DEPTH_TEST); gl.disable(gl.BLEND); gl.disable(gl.CULL_FACE);

    // a polygon into the stencil (bit 0, even-odd), then draws where it is set, then clear bit 0 (bit 1: the occluders)
    const stencilPoly = (f) => {
      gl.enable(gl.STENCIL_TEST);
      gl.colorMask(false, false, false, false);
      gl.stencilMask(1); gl.stencilFunc(gl.ALWAYS, 0, 1); gl.stencilOp(gl.KEEP, gl.KEEP, gl.INVERT);
      gl.bindBuffer(gl.ARRAY_BUFFER, f.vb); attrib(); gl.drawArrays(gl.TRIANGLE_FAN, 0, f.count);
      gl.stencilFunc(gl.EQUAL, 1, 1); gl.stencilOp(gl.KEEP, gl.KEEP, gl.KEEP);
    };
    const stencilDone = () => { gl.stencilMask(1); gl.clear(gl.STENCIL_BUFFER_BIT); gl.disable(gl.STENCIL_TEST); };
    const drawQuad = (q) => { gl.bindBuffer(gl.ARRAY_BUFFER, q.vb); attrib(); gl.drawArrays(gl.TRIANGLES, 0, 6); };
    const buffers = [];
    const quadBuffer = (x0, y0, x1, y1) => {                 // the box as two triangles (its edges on pixel borders)
      const vb = gl.createBuffer(), v = new Float32Array([x0, y0, 0, 0, x1, y0, 0, 0, x0, y1, 0, 0, x1, y0, 0, 0, x1, y1, 0, 0, x0, y1, 0, 0]);
      gl.bindBuffer(gl.ARRAY_BUFFER, vb); gl.bufferData(gl.ARRAY_BUFFER, v, gl.STATIC_DRAW); buffers.push(vb);
      return { vb };
    };

    gl.bindFramebuffer(gl.FRAMEBUFFER, idFbo);                 // id A = 1: full coverage (a soft edge writes less, step 6)
    gl.colorMask(true, true, true, true); gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT | gl.STENCIL_BUFFER_BIT);
    gl.bindFramebuffer(gl.FRAMEBUFFER, uvFbo);
    gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT | gl.STENCIL_BUFFER_BIT);

    const ZONE_ID = { front: 1, "sleeve-l": 2, "sleeve-r": 3, back: 4, "back-l": 5 };
    const rect = plate.neck && plate.neck.rect, dip = plate.neck && plate.neck.edge;
    const frameOff = Z.uvOffsetCm || [0, 0];
    const setFrame = (F) => {                                // the frame's numbers as uniforms of FRAME_FS (the end normals as Plate)
      const ax = F.axis, n = ax.length;
      if (n > AXIS_MAX) throw new Error(`maps.js: an axis of ${n} points (at most ${AXIS_MAX})`);
      const N = ax.map((_, i) => {
        const seg = [i - 1, i].filter((j) => j >= 0 && j < n - 1).map((j) => { const dx = ax[j + 1][0] - ax[j][0], dy = ax[j + 1][1] - ax[j][1], L = Math.hypot(dx, dy) || 1e-9; return [dy / L, -dx / L]; });
        const x = seg.reduce((s, q) => s + q[0], 0), y = seg.reduce((s, q) => s + q[1], 0), L = Math.hypot(x, y) || 1e-9;
        return [x / L, y / L];
      });
      const a = new Float32Array(AXIS_MAX * 2), nn = new Float32Array(AXIS_MAX * 4), cum = new Float32Array(AXIS_MAX);
      let acc = 0;
      for (let i = 0; i < n; i++) {
        a[2 * i] = ax[i][0]; a[2 * i + 1] = ax[i][1]; cum[i] = acc;
        if (i + 1 < n) {
          const dx = ax[i + 1][0] - ax[i][0], dy = ax[i + 1][1] - ax[i][1], L = Math.hypot(dx, dy) || 1e-9, own = [dy / L, -dx / L];
          const na = i === 0 ? own : N[i], nb = i + 1 === n - 1 ? own : N[i + 1];   // per segment: its two end normals
          nn[4 * i] = na[0]; nn[4 * i + 1] = na[1]; nn[4 * i + 2] = nb[0]; nn[4 * i + 3] = nb[1];
          acc += L;
        }
      }
      gl.uniform2fv(U("uAxis"), a); gl.uniform4fv(U("uSegN"), nn); gl.uniform1fv(U("uCum"), cum); gl.uniform1i(U("uN"), n);
      gl.uniform4fv(U("uHalfL"), F.half.left); gl.uniform4fv(U("uHalfR"), F.half.right);
      gl.uniform1f(U("uLen"), F.L); gl.uniform1f(U("uTheta"), (F.thetaDeg * Math.PI) / 180); gl.uniform1f(U("uS0"), F.s0);
      gl.uniform1f(U("uVmm"), F.vMm ?? 0); gl.uniform1f(U("uSagC"), (F.sag && F.sag.c) || 0); gl.uniform1f(U("uSagS1"), F.sag && F.sag.s1 !== undefined ? F.sag.s1 : F.s0);
      gl.uniform1f(U("uMm"), Z.mmPerPx); gl.uniform2f(U("uUVOff"), frameOff[0], frameOff[1]);
    };
    for (const [name, zone] of Object.entries(Z.zones).sort((a, b) => a[1].order - b[1].order)) {
      const polys = [zone.outline, ...(zone.under || [])];
      const neckZone = name === "front" && rect && dip;
      const fans = polys.map((p) => fanBuffer(gl, p));
      buffers.push(...fans.map((f) => f.vb));
      if (!zone.frame) throw new Error(`maps.js: zone ${name} has no fabric frame`);
      const xs = polys.flat().map((p) => p[0]), ys = polys.flat().map((p) => p[1]);
      let bx0 = Math.max(0, Math.floor(Math.min(...xs)) - 16), by0 = Math.max(0, Math.floor(Math.min(...ys)) - 16);
      let bx1 = Math.min(W, Math.ceil(Math.max(...xs)) + 17), by1 = Math.min(H, Math.ceil(Math.max(...ys)) + 17);
      if (neckZone) { bx0 = Math.min(bx0, rect[0]); by0 = Math.min(by0, rect[1]); bx1 = Math.max(bx1, rect[2]); by1 = Math.max(by1, rect[3]); }
      const q = quadBuffer(bx0 - 0.5, by0 - 0.5, bx1 - 0.5, by1 - 0.5);      // plate px: pixel i covers i - 0.5 .. i + 0.5
      // the zone's fabric draw (inside the current stencil and scissor): the frame evaluated per pixel
      const draw = (mode) => { use(fprog); gl.uniform1f(U("uMode"), mode); gl.uniform4f(U("uCol"), ZONE_ID[name] / 255, 0, 0, 1); setFrame(zone.frame); drawQuad(q); use(prog); };
      // id R = the zone (B = 0: a later zone clears the neck area of an earlier one), uv = its fabric coordinates; each polygon a pass
      for (const [fb, mode] of [[idFbo, 0], [uvFbo, 1]]) {
        gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
        for (const f of fans) {
          stencilPoly(f);
          gl.colorMask(true, mode === 1, true, true);        // id: R the zone, B 0, A 1 (full coverage; soft edges write less)
          draw(mode);
          stencilDone();
        }
      }
      if (neckZone) {
        const [x0, y0, x1, y1] = rect, dipFan = fanBuffer(gl, dip);
        buffers.push(dipFan.vb);
        gl.enable(gl.SCISSOR_TEST); gl.scissor(x0, y0, x1 - x0, y1 - y0);
        gl.bindFramebuffer(gl.FRAMEBUFFER, uvFbo);             // uv: the whole neck rectangle (the dip too)
        gl.colorMask(true, true, true, true);
        draw(1);
        gl.bindFramebuffer(gl.FRAMEBUFFER, idFbo);             // id B = 1: rect x (outline + dip)
        for (const f of [fans[0], dipFan]) {
          stencilPoly(f);
          gl.colorMask(false, false, true, false);
          use(prog); gl.uniform1f(U("uMode"), 0); gl.uniform4f(U("uCol"), 0, 0, 1 / 255, 1);
          drawQuad(quadBuffer(x0 - 0.5, y0 - 0.5, x1 - 0.5, y1 - 0.5));
          stencilDone();
        }
        gl.disable(gl.SCISSOR_TEST);
      }
    }
    use(prog);
    // ---- StepA step 6: soft free edges. Each zone's free edges as ribbons from 3 px out to 1 px in, carrying the signed distance d to
    // the edge (+ inside); id A = (d + 3) / 4. The shader: coverage = clamp(0.5 + d) (a 1 px ramp centred on the edge, the snapped 50 %
    // crossing of the photo), and, out to 3 px, the photo is taken 3 px beyond the edge (past the garment's own soft transition). Only
    // against the background: a pixel whose outside (1.5 or 3.5 px out) is another zone (a sleeve's edge over the body) keeps the hard
    // edge, and so do the seams, the frame and the neck cut.
    {
      gl.activeTexture(gl.TEXTURE0 + 14);
      const smask = dataTexture(gl, W, H, null);
      gl.bindFramebuffer(gl.FRAMEBUFFER, idFbo);
      gl.copyTexSubImage2D(gl.TEXTURE_2D, 0, 0, 0, 0, 0, W, H);
      gl.activeTexture(gl.TEXTURE0 + 15);
      use(sprog);
      gl.uniform1i(U("uMask"), 14);
      gl.colorMask(true, false, false, true);
      for (const [name, zone] of Object.entries(Z.zones).sort((a, b) => a[1].order - b[1].order)) {
        if (!zone.freeEdges || !zone.freeEdges.length) continue;
        const inside = (pt) => root.Plate.insidePoly ? root.Plate.insidePoly(pt, zone.outline) : false;
        const tris = [];
        for (const e of zone.freeEdges) {
          if (e.length < 2) continue;
          // the inward side: the left normal of the edge's direction, if a point 1 px along it is inside (a vote over the edge)
          let vote = 0;
          for (let i = 0; i + 1 < e.length; i += Math.max(1, Math.floor(e.length / 9))) {
            const dx = e[i + 1][0] - e[i][0], dy = e[i + 1][1] - e[i][1], L = Math.hypot(dx, dy) || 1;
            vote += inside([(e[i][0] + e[i + 1][0]) / 2 - dy / L, (e[i][1] + e[i + 1][1]) / 2 + dx / L]) ? 1 : -1;
          }
          const sg = vote >= 0 ? 1 : -1;
          for (let i = 0; i + 1 < e.length; i++) {
            const a = e[i], b = e[i + 1], dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy);
            if (L < 1e-6) continue;
            const nx = (-dy / L) * sg, ny = (dx / L) * sg, ex = (dx / L) * 0.5, ey = (dy / L) * 0.5;   // inward normal; 0.5 px past each end
            // from 3 px outside (d = -3) to 1 px inside (d = +1)
            const c = [[a[0] - ex - 3 * nx, a[1] - ey - 3 * ny, -3], [b[0] + ex - 3 * nx, b[1] + ey - 3 * ny, -3], [a[0] - ex + nx, a[1] - ey + ny, 1], [b[0] + ex + nx, b[1] + ey + ny, 1]];
            for (const k of [0, 1, 2, 1, 3, 2]) tris.push(c[k][0], c[k][1], c[k][2], 0);
          }
        }
        if (!tris.length) continue;
        const vb = gl.createBuffer(); buffers.push(vb);
        gl.bindBuffer(gl.ARRAY_BUFFER, vb); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(tris), gl.STATIC_DRAW);
        attrib();
        gl.uniform1f(U("uZone"), ZONE_ID[name] / 255);
        // A starts at 1 everywhere (the clear and the fills); MIN blending: where two segments overlap, the smaller share wins
        gl.enable(gl.BLEND); gl.blendEquationSeparate(gl.FUNC_ADD, gl.MIN); gl.blendFuncSeparate(gl.ONE, gl.ZERO, gl.ONE, gl.ONE);
        gl.drawArrays(gl.TRIANGLES, 0, tris.length / 4);
        gl.disable(gl.BLEND);
      }
      gl.deleteTexture(smask);
      use(prog);
    }
    // ---- trims (StepA extension, step L2): the trim field. The main field (every trim but the slits) into uvt and id G, the slits'
    // field into uvts; one group per zone, back to front: within a group the nearest edge wins (depth = |t|; a mitre where two trims
    // meet), a later group overwrites. The neck of a view with the live neckline is laid by the page from the live edge: not here.
    let uvtTex = null, uvtsTex = null, maskTex = null;
    const fbos = [];
    const trimList = !Z.trims ? [] : Object.entries(Z.trims).filter(([name]) => !(name === "neck" && plate.neck));
    if (trimList.length) {
      gl.activeTexture(gl.TEXTURE0 + 14);                   // the zones as they are now (the soft edges included): a sampler, no feedback
      maskTex = dataTexture(gl, W, H, null);
      gl.bindFramebuffer(gl.FRAMEBUFFER, idFbo);
      gl.copyTexSubImage2D(gl.TEXTURE_2D, 0, 0, 0, 0, 0, W, H);
      gl.activeTexture(gl.TEXTURE0 + 15);
      uvtTex = dataTexture(gl, W, H, null); uvtsTex = dataTexture(gl, W, H, null);
      const uvtFbo = fbo(uvtTex), uvtsFbo = fbo(uvtsTex);
      fbos.push(uvtFbo, uvtsFbo);
      for (const f of [uvtFbo, uvtsFbo]) { gl.bindFramebuffer(gl.FRAMEBUFFER, f); gl.colorMask(true, true, true, true); gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT); }
      // objects in front (the mannequin arm): the overhang is not drawn there. Stencil bit 1, even-odd.
      if (Z.occluders && Z.occluders.length) {
        use(prog);
        gl.enable(gl.STENCIL_TEST);
        gl.colorMask(false, false, false, false);
        gl.stencilMask(2); gl.stencilFunc(gl.ALWAYS, 0, 2); gl.stencilOp(gl.KEEP, gl.KEEP, gl.INVERT);
        for (const poly of Z.occluders) { const f = fanBuffer(gl, poly); buffers.push(f.vb); gl.bindBuffer(gl.ARRAY_BUFFER, f.vb); attrib(); gl.drawArrays(gl.TRIANGLE_FAN, 0, f.count); }
        gl.disable(gl.STENCIL_TEST);
      }
      const tvao = gl.createVertexArray();
      gl.bindVertexArray(tvao);
      for (let i = 0; i < 4; i++) gl.enableVertexAttribArray(i);
      use(tprog);
      gl.uniform1i(U("uMask"), 14);
      gl.uniform1f(U("uMm"), plate.mmPerPx);
      const order = new Float32Array(8).fill(99);
      for (const [n, z] of Object.entries(Z.zones)) order[ZONE_ID[n]] = z.order;
      gl.uniform1fv(U("uOrderOf"), order);
      // the elements of each trim: 6 vertices each, 13 floats a vertex (x y, a b, na nb, sa sb part)
      const groups = { main: new Map(), slit: new Map() };
      for (const [name, trim] of trimList) {
        const info = plate.trims[name], F = Z.zones[trim.zone].frame;
        const { els, tin, tout } = root.Plate.trimElements(trim, F, plate.mmPerPx);
        const arr = (part) => {
          const sel = els.filter((e) => e.part === part), out = new Float32Array(sel.length * 6 * 13);
          let o = 0;
          for (const el of sel) {
            const tri = root.Plate.trimTriangles(el, tin, tout);
            for (const p of tri) out.set([p[0], p[1], el.a[0], el.a[1], el.b[0], el.b[1], el.na[0], el.na[1], el.nb[0], el.nb[1], el.sa, el.sb, el.part], (o++) * 13);
          }
          const vb = gl.createBuffer(); buffers.push(vb);
          gl.bindBuffer(gl.ARRAY_BUFFER, vb); gl.bufferData(gl.ARRAY_BUFFER, out, gl.STATIC_DRAW);
          return { vb, n: sel.length * 6 };
        };
        const key = root.Plate.SLIT_OFF_CM[name] !== undefined ? "slit" : "main";
        const zid = ZONE_ID[trim.zone];
        if (!groups[key].has(zid)) groups[key].set(zid, []);
        groups[key].get(zid).push({ id: info.id, tin, tout, sOff: key === "slit" ? root.Plate.SLIT_OFF_CM[name] : root.Plate.S_OFF_CM,
                                    inner: arr(1), outer: arr(-1) });
      }
      const draw = (g, zid, mode) => {
        gl.uniform1f(U("uZone"), zid); gl.uniform1f(U("uOrder"), order[zid]); gl.uniform1f(U("uMode"), mode);
        for (const t of g) {
          gl.uniform1f(U("uTin"), t.tin); gl.uniform1f(U("uTout"), t.tout); gl.uniform1f(U("uSOff"), t.sOff); gl.uniform1f(U("uTrimId"), t.id);
          for (const [b, inner] of [[t.inner, true], [t.outer, false]]) {
            if (!b.n) continue;
            if (inner) gl.disable(gl.STENCIL_TEST);
            else { gl.enable(gl.STENCIL_TEST); gl.stencilMask(0); gl.stencilFunc(gl.EQUAL, 0, 2); gl.stencilOp(gl.KEEP, gl.KEEP, gl.KEEP); }
            gl.bindBuffer(gl.ARRAY_BUFFER, b.vb);
            gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 52, 0); gl.vertexAttribPointer(1, 4, gl.FLOAT, false, 52, 8);
            gl.vertexAttribPointer(2, 4, gl.FLOAT, false, 52, 24); gl.vertexAttribPointer(3, 3, gl.FLOAT, false, 52, 40);
            gl.drawArrays(gl.TRIANGLES, 0, b.n);
          }
        }
        gl.disable(gl.STENCIL_TEST);
      };
      gl.enable(gl.DEPTH_TEST);
      for (const [key, target] of [["main", uvtFbo], ["slit", uvtsFbo]]) {
        for (const zid of [...groups[key].keys()].sort((p, q) => order[p] - order[q])) {
          const g = groups[key].get(zid);
          gl.bindFramebuffer(gl.FRAMEBUFFER, target);
          gl.depthMask(true); gl.clearDepth(1); gl.clear(gl.DEPTH_BUFFER_BIT);
          gl.depthFunc(gl.LESS); gl.colorMask(true, true, true, true);
          draw(g, zid, 1);
          if (key === "main") {                               // id G = the trim: the same fragments again, where the depth is equal
            gl.bindFramebuffer(gl.FRAMEBUFFER, idFbo);
            gl.depthMask(false); gl.depthFunc(gl.EQUAL); gl.colorMask(false, true, false, false);
            draw(g, zid, 0);
          }
        }
      }
      gl.depthMask(true); gl.depthFunc(gl.LESS); gl.disable(gl.DEPTH_TEST);
      gl.colorMask(true, true, true, true);
      gl.bindVertexArray(vao);
      gl.deleteVertexArray(tvao);
      use(prog);
    }
    gl.finish();

    // ---- shade, from the photo
    let shadeTex = null;
    if (photo && plate.shadeMedian) {
      shadeTex = shadePasses(gl, { W, H, plate, Z, photo, idTex, rb });
      gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      gl.bindVertexArray(vao);
      gl.activeTexture(gl.TEXTURE0 + 15);
    }

    if (sync) { gl.bindFramebuffer(gl.FRAMEBUFFER, idFbo); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4)); }

    // ---- release the scratch objects and give the state back
    for (const b of buffers) gl.deleteBuffer(b);
    gl.deleteFramebuffer(idFbo); gl.deleteFramebuffer(uvFbo); for (const f of fbos) gl.deleteFramebuffer(f); gl.deleteRenderbuffer(rb);
    if (maskTex) gl.deleteTexture(maskTex);
    gl.deleteVertexArray(vao); gl.deleteProgram(prog); gl.deleteProgram(fprog); gl.deleteProgram(sprog); gl.deleteProgram(tprog);
    gl.bindFramebuffer(gl.FRAMEBUFFER, saved.fb);
    gl.colorMask(...saved.cm);
    gl.viewport(...saved.vp);
    gl.bindVertexArray(saved.vao);
    gl.useProgram(saved.prog);
    gl.bindTexture(gl.TEXTURE_2D, null);
    gl.activeTexture(gl.TEXTURE0 + 14); gl.bindTexture(gl.TEXTURE_2D, null);
    gl.activeTexture(saved.active);
    return { id: idTex, uv: uvTex, uvt: uvtTex, uvts: uvtsTex, shade: shadeTex, ms: performance.now() - t0 };
  }

  // a texture's raw RGBA bytes as base64 (tests only: tools/maps_check.py; alpha carries data since the 16-bit packing)
  function readRaw(gl, tex, w, h) {
    const f = gl.createFramebuffer(), px = new Uint8Array(w * h * 4), prev = gl.getParameter(gl.FRAMEBUFFER_BINDING);
    gl.bindFramebuffer(gl.FRAMEBUFFER, f);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, px);
    gl.bindFramebuffer(gl.FRAMEBUFFER, prev);
    gl.deleteFramebuffer(f);
    let bin = "";
    for (let i = 0; i < px.length; i += 0x8000) bin += String.fromCharCode.apply(null, px.subarray(i, i + 0x8000));
    return btoa(bin);
  }

  root.Maps = { build, readRaw, UV_RANGE_CM };
})(typeof window !== "undefined" ? window : globalThis);
