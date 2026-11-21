/*
  maps.js — builds the plate maps on the GPU from the curves (numeric.md steps 2-4). Needs plate.js.
  A classic script: window.Maps.

  The main shader of testing.html reads data textures (id, uv, uv_trim, shade). Here they are DRAWN, once per view load,
  into offscreen RGBA8 textures from triangle meshes calculated by plate.js, with the same 12-bit packing as the PNGs of
  tools/make_plate.py. The main shader does not change.

  Step 2: id.png R (zone) and B (neck area), and uv.png. Step 3: id G (trims) and uv_trim.png, from ribbons along the trim
  centre lines. If an `idImage` is passed in, its G channel is kept instead (the PNG) and the trims are not drawn.

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
  const FS = `#version 300 es
  precision highp float;
  precision highp int;
  in vec2 vUV;
  uniform sampler2D uMask;  // unit 14: the garment (id R > 0), copied from the id once the zones are drawn (trims, step 3)
  uniform float uTestMask;  // 1 = draw only where the garment is (the inner part of a trim strip)
  uniform float uMode;      // 0 = a constant colour (id), 1 = the 12-bit packed (u, v) in cm (uv)
  uniform vec4  uCol;
  uniform float uRange;     // UV range in cm (the plate's uvRangeCm)
  out vec4 outColor;
  void main() {
    if (uTestMask > 0.5 && texelFetch(uMask, ivec2(gl_FragCoord.xy), 0).r == 0.0) discard;
    if (uMode < 0.5) { outColor = uCol; return; }
    int a = int(clamp(floor(vUV.x / uRange * 4095.0 + 0.5), 0.0, 4095.0));
    int b = int(clamp(floor(vUV.y / uRange * 4095.0 + 0.5), 0.0, 4095.0));
    outColor = vec4(float(a >> 4), float(b >> 4), float(((a & 15) << 4) | (b & 15)), 255.0) / 255.0;
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

  // one vertex buffer + one index buffer for a zone grid (x, y, u, v) / for a polygon fan (u, v = 0)
  function gridBuffers(gl, v64, ns, nt) {
    const vb = gl.createBuffer(), ib = gl.createBuffer(), v = new Float32Array(v64), idx = new Uint32Array(ns * nt * 6);
    let o = 0;
    for (let j = 0; j < nt; j++)
      for (let i = 0; i < ns; i++) {
        const a = j * (ns + 1) + i, b = a + 1, c = a + ns + 1, d = c + 1;
        idx[o++] = a; idx[o++] = b; idx[o++] = c; idx[o++] = b; idx[o++] = d; idx[o++] = c;
      }
    gl.bindBuffer(gl.ARRAY_BUFFER, vb); gl.bufferData(gl.ARRAY_BUFFER, v, gl.STATIC_DRAW);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, idx, gl.STATIC_DRAW);
    return { vb, ib, count: idx.length };
  }
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
    build(gl, { plate, Z, idImage, photo, cell }) -> { id, uv, uvt, shade, ms }
      plate   the plate header (Plate.parseDat: viewBox, uvRangeCm, neck{rect, edge})
      Z       the zone data (Plate.parseDat), prepared by Plate.prepare (tuck applied)
      sync    test: wait for the GPU with a 1 px readback before ms is taken (gl.finish() does not always wait): the true cost of the build
      photo   optional: the decoded base.jpg (an ImageBitmap): with it, and with EXT_color_buffer_float, the shade is built too (step 4)
      idImage optional: the PNG of id.png (an ImageBitmap). With it the trims (G) are the PNG's and uvt is not built
      cell    px per grid cell of the meshes (default 4)
      idOff   [x, y] px added to the positions of the id and the coverage of every map (default 0, 0: found by tools/map_diff.py
              against id.png, 0 px of its 1 px edge band is missed)
      grow    px: the plate maker paints each quad with an outline, so a zone is about 0.4-0.5 px larger than its exact shape on every
              side (tools/map_diff.py: 1401 px of 583127 on the torso plate). The zone is drawn 5 times, shifted by +-grow in x and y (0.5: 0.4 leaves a few single-pixel gaps on seams: neck plate, 17 px).
      uvOff   the same for the VALUES of uv: the plate maker paints each 1 px quad with its value after the later quads have
              overwritten the earlier ones, so a pixel shows the surface about 1 px further on in u and in v. Found by tools/
              map_diff.py: the signed mean of PNG - built is 0 at (-0.5, -0.5). The uv is drawn twice: first at idOff (so that
              every pixel that has a zone has a uv), then at uvOff (the precise values).
    id: the id texture (R zone, G trim, B neck area); uv: the packed fabric coordinates; uvt: the packed trim coordinates (u cm along,
    v 0..1 over vMax). All RGBA8, NEAREST.
  */
  function build(gl, { plate, Z, idImage = null, photo = null, sync = false, cell = 4, idOff = [0, 0], uvOff = [-0.5, -0.5], grow = 0.5 }) {
    const t0 = performance.now();
    const [W, H] = plate.viewBox;
    // ---- keep the state of the page: the program, the vertex array, the bound buffers, the viewport, the texture unit
    const saved = {
      prog: gl.getParameter(gl.CURRENT_PROGRAM), vao: gl.getParameter(gl.VERTEX_ARRAY_BINDING), vp: gl.getParameter(gl.VIEWPORT),
      active: gl.getParameter(gl.ACTIVE_TEXTURE), fb: gl.getParameter(gl.FRAMEBUFFER_BINDING), cm: gl.getParameter(gl.COLOR_WRITEMASK),
    };
    gl.activeTexture(gl.TEXTURE0 + 15);                      // scratch unit: the page's units 0-7 stay bound
    const prog = gl.createProgram();
    gl.attachShader(prog, compile(gl, gl.VERTEX_SHADER, VS));
    gl.attachShader(prog, compile(gl, gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error("maps.js: " + gl.getProgramInfoLog(prog));
    gl.useProgram(prog);
    const U = (n) => gl.getUniformLocation(prog, n);
    gl.uniform2f(U("uPlate"), W, H);
    const setOff = (o) => gl.uniform2f(U("uOff"), o[0], o[1]);
    setOff(idOff);
    gl.uniform1f(U("uRange"), plate.uvRangeCm);
    const vao = gl.createVertexArray();
    gl.bindVertexArray(vao);
    gl.enableVertexAttribArray(0); gl.enableVertexAttribArray(1);
    const attrib = () => { gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 16, 0); gl.vertexAttribPointer(1, 2, gl.FLOAT, false, 16, 8); };

    const idTex = dataTexture(gl, W, H, idImage), uvTex = dataTexture(gl, W, H, null);
    const rb = gl.createRenderbuffer();                      // the stencil, shared by both targets
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

    // fill a polygon (or two) into the stencil, bit 0, even-odd; then draw `fn` where it is set; then clear the stencil
    const SHIFTS = grow > 0 ? [[0, 0], [grow, 0], [-grow, 0], [0, grow], [0, -grow]] : [[0, 0]];
    const shifted = (sh) => [idOff[0] + sh[0], idOff[1] + sh[1]];
    const stencilPolys = (polys, off = idOff) => {
      setOff(off);
      gl.enable(gl.STENCIL_TEST);
      gl.colorMask(false, false, false, false);
      gl.stencilMask(1); gl.stencilFunc(gl.ALWAYS, 0, 1); gl.stencilOp(gl.KEEP, gl.KEEP, gl.INVERT);
      for (const f of polys) { gl.bindBuffer(gl.ARRAY_BUFFER, f.vb); attrib(); gl.drawArrays(gl.TRIANGLE_FAN, 0, f.count); }
      gl.stencilFunc(gl.EQUAL, 1, 1); gl.stencilOp(gl.KEEP, gl.KEEP, gl.KEEP);
    };
    const stencilDone = () => { gl.stencilMask(1); gl.clear(gl.STENCIL_BUFFER_BIT); gl.disable(gl.STENCIL_TEST); };   // bit 1 (occluders) stays
    const drawGrid = (g, offs = [idOff]) => {
      gl.bindBuffer(gl.ARRAY_BUFFER, g.vb); attrib(); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, g.ib);
      for (const o of offs) { setOff(o); gl.drawElements(gl.TRIANGLES, g.count, gl.UNSIGNED_INT, 0); }
      setOff(idOff);
    };

    // id: R and B start at 0 (G stays: it is the PNG's trims)
    gl.bindFramebuffer(gl.FRAMEBUFFER, idFbo);
    gl.colorMask(true, false, true, false); gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT | gl.STENCIL_BUFFER_BIT);
    gl.bindFramebuffer(gl.FRAMEBUFFER, uvFbo);
    gl.colorMask(true, true, true, true); gl.clear(gl.COLOR_BUFFER_BIT | gl.STENCIL_BUFFER_BIT);

    const ZONE_ID = { front: 1, "sleeve-l": 2, "sleeve-r": 3, back: 4, "back-l": 5 };
    const rect = plate.neck && plate.neck.rect, dip = plate.neck && plate.neck.edge;
    const buffers = [];
    for (const [name, zone] of Object.entries(Z.zones).sort((a, b) => a[1].order - b[1].order)) {
      const par = root.Plate.zoneParams(name, zone, Z, cell);
      const g = gridBuffers(gl, root.Plate.zoneVertices(zone, par), par.ns, par.nt);
      const outline = fanBuffer(gl, zone.outline);
      buffers.push(g.vb, g.ib, outline.vb);
      const neckZone = name === "front" && rect && dip;
      // every pass of this zone (the stencil fans, the grid, the stencil clears) only inside the box of its outline + 2 px (+ grow)
      const xs = zone.outline.map((p) => p[0]), ys = zone.outline.map((p) => p[1]), pad = 3;
      const zx0 = Math.max(0, Math.floor(Math.min(...xs) - pad)), zy0 = Math.max(0, Math.floor(Math.min(...ys) - pad));
      const zx1 = Math.min(W, Math.ceil(Math.max(...xs) + pad)), zy1 = Math.min(H, Math.ceil(Math.max(...ys) + pad));
      gl.enable(gl.SCISSOR_TEST); gl.scissor(zx0, zy0, zx1 - zx0, zy1 - zy0);

      // id: zone number in R inside (grid ∩ outline), B = 0 there (a later zone clears the neck area of an earlier one)
      gl.bindFramebuffer(gl.FRAMEBUFFER, idFbo);
      gl.uniform1f(U("uMode"), 0);
      gl.uniform4f(U("uCol"), ZONE_ID[name] / 255, 0, 0, 1);
      for (const sh of SHIFTS) {
        stencilPolys([outline], shifted(sh));
        gl.colorMask(true, false, true, false);
        drawGrid(g, [shifted(sh)]);
        stencilDone();
      }
      // uv: the same coverage with approximate values, then the precise values inside the exact shape
      gl.bindFramebuffer(gl.FRAMEBUFFER, uvFbo);
      gl.uniform1f(U("uMode"), 1);
      for (const sh of SHIFTS) {
        stencilPolys([outline], shifted(sh));
        gl.colorMask(true, true, true, true);
        drawGrid(g, [shifted(sh)]);
        stencilDone();
      }
      stencilPolys([outline]);
      gl.colorMask(true, true, true, true);
      drawGrid(g, [uvOff]);
      stencilDone();

      if (neckZone) {
        const [x0, y0, x1, y1] = rect, dipFan = fanBuffer(gl, dip);
        buffers.push(dipFan.vb);
        gl.enable(gl.SCISSOR_TEST);
        gl.scissor(x0, y0, x1 - x0, y1 - y0);
        // uv: the WHOLE grid inside the neck rectangle (the dip too)
        gl.bindFramebuffer(gl.FRAMEBUFFER, uvFbo);
        gl.colorMask(true, true, true, true);
        drawGrid(g, [idOff, uvOff]);
        // id B = 1: grid ∩ rect ∩ (outline ∪ dip)
        gl.bindFramebuffer(gl.FRAMEBUFFER, idFbo);
        gl.uniform1f(U("uMode"), 0);
        gl.uniform4f(U("uCol"), 0, 0, 1 / 255, 1);
        for (const sh of SHIFTS) {
          stencilPolys([outline, dipFan], shifted(sh));
          gl.colorMask(false, false, true, false);
          drawGrid(g, [shifted(sh)]);
          stencilDone();
        }
        gl.scissor(zx0, zy0, zx1 - zx0, zy1 - zy0);
      }
      gl.disable(gl.SCISSOR_TEST);
    }
    // ---- trims (step 3): ribbons along the centre lines, back to front in the order of the plate (a later trim overwrites)
    let uvtTex = null, maskTex = null, uvtFbo = null;
    const trimList = idImage || !Z.trims ? [] : Object.entries(Z.trims);
    if (trimList.length) {
      // the garment: every pixel that has a zone. The inner part of a strip is drawn only there (a sampler, not the id: no feedback)
      gl.activeTexture(gl.TEXTURE0 + 14);
      maskTex = dataTexture(gl, W, H, null);
      gl.bindFramebuffer(gl.FRAMEBUFFER, idFbo);
      gl.copyTexSubImage2D(gl.TEXTURE_2D, 0, 0, 0, 0, 0, W, H);
      gl.uniform1i(U("uMask"), 14);
      gl.activeTexture(gl.TEXTURE0 + 15);
      uvtTex = dataTexture(gl, W, H, null);
      uvtFbo = fbo(uvtTex);
      gl.bindFramebuffer(gl.FRAMEBUFFER, uvtFbo);
      gl.colorMask(true, true, true, true); gl.clear(gl.COLOR_BUFFER_BIT);
      // objects in front (the mannequin arm): the overhang of a strip is not drawn there. Stencil bit 1, even-odd.
      if (Z.occluders && Z.occluders.length) {
        gl.enable(gl.STENCIL_TEST);
        gl.colorMask(false, false, false, false);
        gl.stencilMask(2); gl.stencilFunc(gl.ALWAYS, 0, 2); gl.stencilOp(gl.KEEP, gl.KEEP, gl.INVERT);
        setOff(idOff);
        for (const poly of Z.occluders) { const f = fanBuffer(gl, poly); buffers.push(f.vb); gl.bindBuffer(gl.ARRAY_BUFFER, f.vb); attrib(); gl.drawArrays(gl.TRIANGLE_FAN, 0, f.count); }
        gl.disable(gl.STENCIL_TEST);
      }
      // The plate maker paints a strip quad after quad, along and then across, each with an outline: a pixel on the border of two
      // quads shows the later one. So its u runs ahead of the exact value along the strip, and its v across it, by half a quad:
      // tools/map_diff.py, all 6 trims of the torso plate, whatever the direction of the strip on the screen: +0.5 px in both.
      // (halfway step 5 found 0.95 px for u: it measured against a shader convention in which a pixel sits half a px earlier.)
      const TRIM_BIAS_PX = 0.5, TRIM_V_BIAS_PX = 0.5;
      const trimShifts = grow > 0 ? [[grow, 0], [-grow, 0], [0, grow], [0, -grow], [0, 0]] : [[0, 0]];   // the centre copy last: its values win
      for (const [name, trim] of trimList) {
        const info = plate.trims[name];
        if (!info || info.side === undefined) throw new Error(`maps.js: the plate has no side for trim ${name}`);
        const par = root.Plate.trimParams(name, trim, Z);
        const tri = root.Plate.trimTriangles(trim, par, info.side, (TRIM_BIAS_PX * plate.mmPerPx) / 10, plate.uvRangeCm, TRIM_V_BIAS_PX / (par.vmax * 2 * par.half));
        const parts = [[tri.inner, true]];
        if (tri.outer) parts.push([tri.outer, false]);
        const bufs = parts.map(([arr, inner]) => { const vb = gl.createBuffer(); buffers.push(vb); gl.bindBuffer(gl.ARRAY_BUFFER, vb); gl.bufferData(gl.ARRAY_BUFFER, arr, gl.STATIC_DRAW); return { vb, n: arr.length / 4, inner }; });
        {
          const half = (trim.widthMm / plate.mmPerPx) * (par.vmax + 1), cx = trim.centre.map((p) => p[0]), cy = trim.centre.map((p) => p[1]);
          const x0 = Math.max(0, Math.floor(Math.min(...cx) - half)), y0 = Math.max(0, Math.floor(Math.min(...cy) - half));
          gl.enable(gl.SCISSOR_TEST); gl.scissor(x0, y0, Math.min(W, Math.ceil(Math.max(...cx) + half)) - x0, Math.min(H, Math.ceil(Math.max(...cy) + half)) - y0);
        }
        const draw = (sh) => {
          setOff([idOff[0] + sh[0], idOff[1] + sh[1]]);
          for (const b of bufs) {
            gl.bindBuffer(gl.ARRAY_BUFFER, b.vb); attrib();
            gl.uniform1f(U("uTestMask"), b.inner ? 1 : 0);        // inner: on the garment only; overhang: anywhere but behind an occluder
            if (b.inner) gl.disable(gl.STENCIL_TEST);
            else { gl.enable(gl.STENCIL_TEST); gl.stencilMask(0); gl.stencilFunc(gl.EQUAL, 0, 2); gl.stencilOp(gl.KEEP, gl.KEEP, gl.KEEP); }
            gl.drawArrays(gl.TRIANGLES, 0, b.n);
          }
          gl.disable(gl.STENCIL_TEST);
        };
        gl.bindFramebuffer(gl.FRAMEBUFFER, idFbo);               // id G = the trim number
        gl.uniform1f(U("uMode"), 0); gl.uniform4f(U("uCol"), 0, info.id / 255, 0, 1);
        gl.colorMask(false, true, false, false);
        for (const sh of trimShifts) draw(sh);
        gl.bindFramebuffer(gl.FRAMEBUFFER, uvtFbo);              // uv_trim: u cm along, v 0..1 over vMax
        gl.uniform1f(U("uMode"), 1);
        gl.colorMask(true, true, true, true);
        for (const sh of trimShifts) draw(sh);                   // the shifted copies first, the centre copy last: its values win
      }
      gl.disable(gl.SCISSOR_TEST);
      gl.uniform1f(U("uTestMask"), 0);
    }
    gl.finish();

    // ---- shade (step 4), from the photo
    let shadeTex = null;
    if (photo && !idImage && plate.shadeMedian) {
      shadeTex = shadePasses(gl, { W, H, plate, Z, photo, idTex, rb });
      gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      gl.bindVertexArray(vao);
      gl.activeTexture(gl.TEXTURE0 + 15);
    }

    if (sync) { gl.bindFramebuffer(gl.FRAMEBUFFER, idFbo); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4)); }

    // ---- release the scratch objects and give the state back
    for (const b of buffers) gl.deleteBuffer(b);
    gl.deleteFramebuffer(idFbo); gl.deleteFramebuffer(uvFbo); if (uvtFbo) gl.deleteFramebuffer(uvtFbo); gl.deleteRenderbuffer(rb);
    if (maskTex) gl.deleteTexture(maskTex);
    gl.deleteVertexArray(vao); gl.deleteProgram(prog);
    gl.bindFramebuffer(gl.FRAMEBUFFER, saved.fb);
    gl.colorMask(...saved.cm);
    gl.viewport(...saved.vp);
    gl.bindVertexArray(saved.vao);
    gl.useProgram(saved.prog);
    gl.bindTexture(gl.TEXTURE_2D, null);
    gl.activeTexture(gl.TEXTURE0 + 14); gl.bindTexture(gl.TEXTURE_2D, null);
    gl.activeTexture(saved.active);
    return { id: idTex, uv: uvTex, uvt: uvtTex, shade: shadeTex, ms: performance.now() - t0 };
  }

  // read a texture back as an RGBA8 PNG data URL (tests only: tools/map_diff.py)
  function readPNG(gl, tex, w, h) {
    const f = gl.createFramebuffer(), px = new Uint8ClampedArray(w * h * 4), prev = gl.getParameter(gl.FRAMEBUFFER_BINDING);
    gl.bindFramebuffer(gl.FRAMEBUFFER, f);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, px);
    gl.bindFramebuffer(gl.FRAMEBUFFER, prev);
    gl.deleteFramebuffer(f);
    for (let i = 3; i < px.length; i += 4) px[i] = 255;       // alpha is not used by the maps; a 2D canvas would premultiply it away
    const c = document.createElement("canvas");
    c.width = w; c.height = h;
    c.getContext("2d").putImageData(new ImageData(px, w, h), 0, 0);
    return c.toDataURL("image/png");
  }

  root.Maps = { build, readPNG };
})(typeof window !== "undefined" ? window : globalThis);
