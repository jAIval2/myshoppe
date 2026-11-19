/*
  maps.js — builds the plate maps on the GPU from the curves (numeric.md steps 2-4). Needs plate.js.
  A classic script: window.Maps.

  The main shader of testing.html reads data textures (id, uv, uv_trim, shade). Here they are DRAWN, once per view load,
  into offscreen RGBA8 textures from triangle meshes calculated by plate.js, with the same 12-bit packing as the PNGs of
  tools/make_plate.py. The main shader does not change.

  Step 2: id.png R (zone) and B (neck area), and uv.png. Everything else of id (G, the trim) is taken from the image that
  is passed in (the PNG, until step 3).

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
  uniform float uMode;      // 0 = a constant colour (id), 1 = the 12-bit packed (u, v) in cm (uv)
  uniform vec4  uCol;
  uniform float uRange;     // UV range in cm (plate.json uvRangeCm)
  out vec4 outColor;
  void main() {
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

  /*
    build(gl, { plate, Z, idImage, cell }) -> { id, uv, ms }
      plate   plate.json (viewBox, uvRangeCm, neck{rect, edge})
      Z       zones.json, prepared by Plate.prepare (tuck applied)
      idImage the PNG of id.png (an ImageBitmap): its G channel (the trims) is kept until step 3 draws it too
      cell    px per grid cell of the meshes (default 4)
      idOff   [x, y] px added to the positions of the id and the coverage of every map (default 0, 0: found by tools/map_diff.py
              against id.png, 0 px of its 1 px edge band is missed)
      grow    px: the plate maker paints each quad with an outline, so a zone is about 0.4 px larger than its exact shape on every
              side (tools/map_diff.py: 1401 px of 583127 on the torso plate). The zone is drawn 5 times, shifted by +-grow in x and y.
      uvOff   the same for the VALUES of uv: the plate maker paints each 1 px quad with its value after the later quads have
              overwritten the earlier ones, so a pixel shows the surface about 1 px further on in u and in v. Found by tools/
              map_diff.py: the signed mean of PNG - built is 0 at (-0.5, -0.5). The uv is drawn twice: first at idOff (so that
              every pixel that has a zone has a uv), then at uvOff (the precise values).
    id: the id texture (R zone, G from idImage, B neck area); uv: the packed fabric coordinates. Both RGBA8, NEAREST.
  */
  function build(gl, { plate, Z, idImage, cell = 4, idOff = [0, 0], uvOff = [-0.5, -0.5], grow = 0.4 }) {
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
    const stencilDone = () => { gl.stencilMask(0xff); gl.clear(gl.STENCIL_BUFFER_BIT); gl.disable(gl.STENCIL_TEST); };
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
        gl.disable(gl.SCISSOR_TEST);
      }
    }
    gl.finish();

    // ---- release the scratch objects and give the state back
    for (const b of buffers) gl.deleteBuffer(b);
    gl.deleteFramebuffer(idFbo); gl.deleteFramebuffer(uvFbo); gl.deleteRenderbuffer(rb);
    gl.deleteVertexArray(vao); gl.deleteProgram(prog);
    gl.bindFramebuffer(gl.FRAMEBUFFER, saved.fb);
    gl.colorMask(...saved.cm);
    gl.viewport(...saved.vp);
    gl.bindVertexArray(saved.vao);
    gl.useProgram(saved.prog);
    gl.bindTexture(gl.TEXTURE_2D, null);
    gl.activeTexture(saved.active);
    return { id: idTex, uv: uvTex, ms: performance.now() - t0 };
  }

  // read a texture back as an RGBA8 PNG data URL (tests only: tools/map_diff.py)
  function readPNG(gl, tex, w, h) {
    const f = gl.createFramebuffer(), px = new Uint8ClampedArray(w * h * 4), prev = gl.getParameter(gl.FRAMEBUFFER_BINDING);
    gl.bindFramebuffer(gl.FRAMEBUFFER, f);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, px);
    gl.bindFramebuffer(gl.FRAMEBUFFER, prev);
    gl.deleteFramebuffer(f);
    const c = document.createElement("canvas");
    c.width = w; c.height = h;
    c.getContext("2d").putImageData(new ImageData(px, w, h), 0, 0);
    return c.toDataURL("image/png");
  }

  root.Maps = { build, readPNG };
})(typeof window !== "undefined" ? window : globalThis);
