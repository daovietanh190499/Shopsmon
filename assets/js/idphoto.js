/* Shopsmon ID photo maker — runs entirely in the browser (no upload).
 * Pipeline: decode -> face landmarks (MediaPipe Face Landmarker) -> portrait matting (MODNet, ONNX Runtime Web)
 *           -> guided-filter alpha refinement -> straighten + crop to the chosen standard size
 *           -> foreground colour estimation (blur-fusion) -> background colour -> adaptive sharpening -> export (300 DPI).
 */
(function () {
  'use strict';

  var LANG = document.documentElement.lang === 'en' ? 'en' : 'vi';
  var TXT = {
    vi: {
      loadingLib: 'Đang tải thư viện AI…', loadingModel: 'Đang tải mô hình', loadingRt: 'Đang khởi tạo mô hình…',
      detect: 'Đang nhận diện khuôn mặt…', matting: 'Đang tách nền…', refine: 'Đang tinh chỉnh viền…',
      render: 'Đang cắt và căn thẳng…', done: 'Hoàn tất', badType: 'Vui lòng chọn tệp ảnh (JPG, PNG hoặc WebP).',
      tooBig: 'Tệp lớn hơn 25 MB. Hãy chọn ảnh nhỏ hơn.', decodeErr: 'Không đọc được ảnh này.',
      noFace: 'Không tìm thấy khuôn mặt. Hãy dùng ảnh chụp chính diện, đủ sáng, thấy rõ mặt.',
      multiFace: 'Có nhiều khuôn mặt, đang dùng khuôn mặt lớn nhất.', lowRes: 'Độ phân giải khuôn mặt thấp: ảnh sẽ kém nét khi phóng to.',
      tilt: 'Đã xoay ảnh', deg: '°', err: 'Có lỗi khi xử lý', sheetN: 'ảnh/tờ', auto: 'tự động', mb: 'MB',
      size: 'Kích thước', px: 'px', sharp: 'Độ nét', head: 'Tỉ lệ đầu', edge: 'Viền', custom: 'Tùy chỉnh', retry: 'Thử lại'
    },
    en: {
      loadingLib: 'Loading AI libraries…', loadingModel: 'Downloading model', loadingRt: 'Initialising model…',
      detect: 'Detecting face…', matting: 'Removing background…', refine: 'Refining edges…',
      render: 'Cropping and straightening…', done: 'Done', badType: 'Please choose an image file (JPG, PNG or WebP).',
      tooBig: 'File is larger than 25 MB. Please choose a smaller image.', decodeErr: 'This image could not be read.',
      noFace: 'No face found. Use a front-facing, well-lit photo with the face clearly visible.',
      multiFace: 'Several faces found; using the largest one.', lowRes: 'Low face resolution: the result will look soft when enlarged.',
      tilt: 'Rotated by', deg: '°', err: 'Processing error', sheetN: 'photos/sheet', auto: 'auto', mb: 'MB',
      size: 'Size', px: 'px', sharp: 'Sharpness', head: 'Head size', edge: 'Edge', custom: 'Custom', retry: 'Retry'
    }
  }[LANG];

  var ORT_BASE = 'https://cdn.jsdelivr.net/npm/onnxruntime-web@1.20.1/dist/';
  var MP_BASE = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.21';
  var MODEL_URL = '/assets/models/modnet-fp16.onnx';
  var FACE_URL = '/assets/models/face_landmarker.task';
  var MAX_SIDE = 2000;     // working resolution cap
  var DPI = 300;

  // [id, width mm, height mm, head-height ratio (crown to chin / photo height)]
  var PRESETS = [
    ['3x4', 30, 40, 0.70], ['4x6', 40, 60, 0.72], ['2x3', 20, 30, 0.70],
    ['35x45', 35, 45, 0.75], ['2in', 50.8, 50.8, 0.60]
  ];

  var $ = function (id) { return document.getElementById(id); };
  var el = {
    drop: $('idpDrop'), file: $('idpFile'), status: $('idpStatus'), bar: $('idpBar'), barWrap: $('idpBarWrap'),
    preset: $('idpPreset'), cw: $('idpCw'), ch: $('idpCh'), customRow: $('idpCustomRow'),
    head: $('idpHead'), headV: $('idpHeadV'), sharp: $('idpSharp'), sharpV: $('idpSharpV'),
    edge: $('idpEdge'), edgeV: $('idpEdgeV'), levels: $('idpLevels'), swatches: $('idpSwatches'), color: $('idpColor'),
    out: $('idpOut'), orig: $('idpOrig'), stage: $('idpStage'), info: $('idpInfo'),
    dlPng: $('idpPng'), dlJpg: $('idpJpg'), dlSheet: $('idpSheetBtn'), sheetSel: $('idpSheetSel'), sheetCv: $('idpSheet'), sheetInfo: $('idpSheetInfo'),
    reset: $('idpReset')
  };
  if (!el.drop) return;

  // ---------------------------------------------------------------- state
  var S = null;            // per-image analysis: {src, W, H, alpha, alphaCv, face, geo}
  var libs = { ort: null, mp: null, session: null, landmarker: null, loading: null };
  var bg = '#ffffff';
  var busy = false;
  var renderTimer = null;
  var lastOut = null;      // {canvas, wmm, hmm}

  function setStatus(msg, kind) {
    el.status.textContent = msg || '';
    el.status.className = 'idp-status' + (kind ? ' ' + kind : '');
  }
  function setBar(p) {
    if (p == null) { el.barWrap.hidden = true; return; }
    el.barWrap.hidden = false; el.bar.style.width = Math.round(p * 100) + '%';
  }
  function tick() { return new Promise(function (r) { setTimeout(r, 0); }); }

  // ---------------------------------------------------------------- loading libraries / models
  function loadScript(src) {
    return new Promise(function (res, rej) {
      var s = document.createElement('script'); s.src = src; s.onload = res; s.onerror = function () { rej(new Error('load ' + src)); };
      document.head.appendChild(s);
    });
  }
  async function fetchBuf(url, label) {
    var r = await fetch(url);
    if (!r.ok) throw new Error('HTTP ' + r.status + ' ' + url);
    var total = +r.headers.get('Content-Length') || 0;
    if (!r.body || !total) { return new Uint8Array(await r.arrayBuffer()); }
    var rd = r.body.getReader(), got = 0, chunks = [];
    for (;;) {
      var x = await rd.read(); if (x.done) break;
      chunks.push(x.value); got += x.value.length;
      setStatus(label + ' ' + (got / 1048576).toFixed(1) + '/' + (total / 1048576).toFixed(1) + ' ' + TXT.mb);
      setBar(got / total);
    }
    var buf = new Uint8Array(got), o = 0;
    chunks.forEach(function (c) { buf.set(c, o); o += c.length; });
    return buf;
  }
  function ensureLibs() {
    if (libs.session && libs.landmarker) return Promise.resolve();
    if (libs.loading) return libs.loading;
    libs.loading = (async function () {
      setStatus(TXT.loadingLib); setBar(0.02);
      if (!window.ort) await loadScript(ORT_BASE + 'ort.wasm.min.js');
      libs.ort = window.ort;
      libs.ort.env.wasm.wasmPaths = ORT_BASE;
      libs.ort.env.wasm.numThreads = (self.crossOriginIsolated ? Math.min(4, navigator.hardwareConcurrency || 2) : 1);
      libs.mp = await import(MP_BASE + '/vision_bundle.mjs');
      var faceBuf = await fetchBuf(FACE_URL, TXT.loadingModel + ' (1/2)');
      var modelBuf = await fetchBuf(MODEL_URL, TXT.loadingModel + ' (2/2)');
      setStatus(TXT.loadingRt); setBar(1); await tick();
      var fileset = await libs.mp.FilesetResolver.forVisionTasks(MP_BASE + '/wasm');
      libs.landmarker = await libs.mp.FaceLandmarker.createFromOptions(fileset, {
        baseOptions: { modelAssetBuffer: faceBuf, delegate: 'CPU' },
        runningMode: 'IMAGE', numFaces: 4
      });
      libs.session = await libs.ort.InferenceSession.create(modelBuf, { executionProviders: ['wasm'], graphOptimizationLevel: 'all' });
      setBar(null);
    })();
    libs.loading.catch(function () { libs.loading = null; });
    return libs.loading;
  }

  // ---------------------------------------------------------------- image helpers
  function makeCanvas(w, h) { var c = document.createElement('canvas'); c.width = w; c.height = h; return c; }

  async function decode(file) {
    if (window.createImageBitmap) {
      try { return await createImageBitmap(file, { imageOrientation: 'from-image' }); } catch (e) { /* fall through */ }
    }
    return await new Promise(function (res, rej) {
      var u = URL.createObjectURL(file), im = new Image();
      im.onload = function () { URL.revokeObjectURL(u); res(im); };
      im.onerror = function () { URL.revokeObjectURL(u); rej(new Error('decode')); };
      im.src = u;
    });
  }

  // separable box blur (window = 2r+1, edge-normalised), Float32Array in/out
  function boxBlur(a, w, h, r) {
    if (r < 1) return a.slice();
    var tmp = new Float32Array(w * h), out = new Float32Array(w * h), x, y, i, s, n;
    for (y = 0; y < h; y++) {
      var row = y * w; s = 0; n = 0;
      for (x = 0; x <= r && x < w; x++) { s += a[row + x]; n++; }
      for (x = 0; x < w; x++) {
        tmp[row + x] = s / n;
        var add = x + r + 1, sub = x - r;
        if (add < w) { s += a[row + add]; n++; }
        if (sub >= 0) { s -= a[row + sub]; n--; }
      }
    }
    for (x = 0; x < w; x++) {
      s = 0; n = 0;
      for (y = 0; y <= r && y < h; y++) { s += tmp[y * w + x]; n++; }
      for (y = 0; y < h; y++) {
        out[y * w + x] = s / n;
        var add2 = y + r + 1, sub2 = y - r;
        if (add2 < h) { s += tmp[add2 * w + x]; n++; }
        if (sub2 >= 0) { s -= tmp[sub2 * w + x]; n--; }
      }
    }
    return out;
  }

  // gray-guide guided filter (He et al.)
  function guidedFilter(I, p, w, h, r, eps) {
    var N = w * h, i;
    var mI = boxBlur(I, w, h, r), mp = boxBlur(p, w, h, r);
    var II = new Float32Array(N), Ip = new Float32Array(N);
    for (i = 0; i < N; i++) { II[i] = I[i] * I[i]; Ip[i] = I[i] * p[i]; }
    var mII = boxBlur(II, w, h, r), mIp = boxBlur(Ip, w, h, r);
    var a = new Float32Array(N), b = new Float32Array(N);
    for (i = 0; i < N; i++) {
      var vI = mII[i] - mI[i] * mI[i], cIp = mIp[i] - mI[i] * mp[i];
      a[i] = cIp / (vI + eps); b[i] = mp[i] - a[i] * mI[i];
    }
    var ma = boxBlur(a, w, h, r), mb = boxBlur(b, w, h, r), q = new Float32Array(N);
    for (i = 0; i < N; i++) { var v = ma[i] * I[i] + mb[i]; q[i] = v < 0 ? 0 : v > 1 ? 1 : v; }
    return q;
  }

  // ---------------------------------------------------------------- analysis: face + matte
  function pickFace(res, W, H) {
    var faces = res.faceLandmarks || [];
    if (!faces.length) return null;
    var best = null, bestA = -1;
    faces.forEach(function (lm) {
      var minx = 1, maxx = 0, miny = 1, maxy = 0;
      lm.forEach(function (p) { if (p.x < minx) minx = p.x; if (p.x > maxx) maxx = p.x; if (p.y < miny) miny = p.y; if (p.y > maxy) maxy = p.y; });
      var area = (maxx - minx) * (maxy - miny);
      if (area > bestA) { bestA = area; best = lm; }
    });
    var P = function (i) { return { x: best[i].x * W, y: best[i].y * H }; };
    var mid = function (a, b) { return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 }; };
    var eyeA, eyeB; // image-left and image-right eye centres
    if (best.length >= 478) { eyeA = P(468); eyeB = P(473); }
    else { eyeA = mid(P(33), P(133)); eyeB = mid(P(362), P(263)); }
    if (eyeA.x > eyeB.x) { var t = eyeA; eyeA = eyeB; eyeB = t; }
    return { count: faces.length, eyeA: eyeA, eyeB: eyeB, chin: P(152), left: P(234), right: P(454), forehead: P(10) };
  }

  async function matteOf(srcCv, W, H) {
    var ref = 512, rw, rh;
    if (W >= H) { rh = ref; rw = Math.round(W / H * ref); } else { rw = ref; rh = Math.round(H / W * ref); }
    rw = Math.max(32, rw - rw % 32); rh = Math.max(32, rh - rh % 32);
    var small = makeCanvas(rw, rh), sctx = small.getContext('2d', { willReadFrequently: true });
    sctx.imageSmoothingQuality = 'high'; sctx.drawImage(srcCv, 0, 0, rw, rh);
    var d = sctx.getImageData(0, 0, rw, rh).data, n = rw * rh, f = new Float32Array(3 * n), i;
    for (i = 0; i < n; i++) {
      f[i] = (d[i * 4] / 255 - 0.5) / 0.5; f[n + i] = (d[i * 4 + 1] / 255 - 0.5) / 0.5; f[2 * n + i] = (d[i * 4 + 2] / 255 - 0.5) / 0.5;
    }
    var inName = libs.session.inputNames[0], outName = libs.session.outputNames[0];
    var feeds = {}; feeds[inName] = new libs.ort.Tensor('float32', f, [1, 3, rh, rw]);
    var res = await libs.session.run(feeds);
    var m = res[outName].data; // Float32 [1,1,rh,rw]
    var mc = makeCanvas(rw, rh), mctx = mc.getContext('2d'), id = mctx.createImageData(rw, rh);
    for (i = 0; i < n; i++) { var v = Math.max(0, Math.min(1, m[i])) * 255; id.data[i * 4] = id.data[i * 4 + 1] = id.data[i * 4 + 2] = v; id.data[i * 4 + 3] = 255; }
    mctx.putImageData(id, 0, 0);
    var big = makeCanvas(W, H), bctx = big.getContext('2d', { willReadFrequently: true });
    bctx.imageSmoothingQuality = 'high'; bctx.drawImage(mc, 0, 0, W, H);
    var bd = bctx.getImageData(0, 0, W, H).data, a = new Float32Array(W * H);
    for (i = 0; i < W * H; i++) a[i] = bd[i * 4] / 255;
    return a;
  }

  function refineAlpha(srcCv, alpha, W, H) {
    var d = srcCv.getContext('2d', { willReadFrequently: true }).getImageData(0, 0, W, H).data, g = new Float32Array(W * H), i;
    for (i = 0; i < W * H; i++) g[i] = (0.299 * d[i * 4] + 0.587 * d[i * 4 + 1] + 0.114 * d[i * 4 + 2]) / 255;
    var r = Math.max(3, Math.round(Math.max(W, H) / 260));
    return guidedFilter(g, alpha, W, H, r, 1e-4);
  }

  function grayCanvasFromAlpha(a, W, H) {
    var c = makeCanvas(W, H), ctx = c.getContext('2d'), id = ctx.createImageData(W, H);
    for (var i = 0; i < W * H; i++) { var v = a[i] * 255; id.data[i * 4] = id.data[i * 4 + 1] = id.data[i * 4 + 2] = v; id.data[i * 4 + 3] = 255; }
    ctx.putImageData(id, 0, 0);
    return c;
  }

  // geometry in the straightened frame (origin = eye midpoint)
  function computeGeometry(face, alphaCv, W, H) {
    var c0 = { x: (face.eyeA.x + face.eyeB.x) / 2, y: (face.eyeA.y + face.eyeB.y) / 2 };
    var dx = face.eyeB.x - face.eyeA.x, dy = face.eyeB.y - face.eyeA.y;
    var theta = Math.atan2(dy, dx), E = Math.hypot(dx, dy);
    var cs = Math.cos(theta), sn = Math.sin(theta);
    var rot = function (p) { var vx = p.x - c0.x, vy = p.y - c0.y; return { x: cs * vx + sn * vy, y: -sn * vx + cs * vy }; };
    var chinRel = rot(face.chin);
    var eyeToChin = chinRel.y;
    var xc = chinRel.x * 0.5;                       // centre between eye-midline (0) and chin
    // matte-based crown: rotate alpha into the straightened frame at half scale and scan the face column band
    var AS = 0.5, diag = Math.hypot(W, H), AW = Math.ceil(diag * AS), AH = AW;
    var ac = makeCanvas(AW, AH), actx = ac.getContext('2d', { willReadFrequently: true });
    actx.fillStyle = '#000'; actx.fillRect(0, 0, AW, AH);
    actx.imageSmoothingQuality = 'medium';
    actx.setTransform(AS * cs, -AS * sn, AS * sn, AS * cs, 0, 0);  // x' = AS(cs x + sn y), y' = AS(-sn x + cs y)
    // translate so c0 lands in the centre of the analysis canvas
    var ex = AW / 2 - AS * (cs * c0.x + sn * c0.y), ey = AH / 2 - AS * (-sn * c0.x + cs * c0.y);
    actx.setTransform(AS * cs, -AS * sn, AS * sn, AS * cs, ex, ey);
    actx.drawImage(alphaCv, 0, 0);
    actx.setTransform(1, 0, 0, 1, 0, 0);
    var data = actx.getImageData(0, 0, AW, AH).data;
    var cx = AW / 2 + xc * AS, half = Math.max(4, 1.25 * E * AS);
    var x0 = Math.max(0, Math.floor(cx - half)), x1 = Math.min(AW - 1, Math.ceil(cx + half));
    var eyeRow = Math.floor(AH / 2), crownRow = -1;
    for (var y = 0; y < eyeRow && crownRow < 0; y++) {
      var cnt = 0;
      for (var x = x0; x <= x1; x++) { if (data[(y * AW + x) * 4] > 128) { cnt++; if (cnt >= 3) break; } }
      if (cnt >= 3) crownRow = y;
    }
    var crownRel = crownRow >= 0 ? (crownRow - AH / 2) / AS : null;   // negative = above eyes
    // anthropometry: eye-to-chin is ~46% of crown-to-chin height, so the crown sits ~1.17x eye-to-chin above the eyes
    var heur = -1.17 * eyeToChin, source = 'matte';
    if (crownRel === null) { crownRel = heur; source = 'heuristic'; }
    else if (crownRel > -0.95 * eyeToChin || crownRel < -1.6 * eyeToChin) {
      // implausible matte crown (hat, tall hair, segmentation error): clamp to a plausible range
      crownRel = Math.max(-1.6 * eyeToChin, Math.min(-0.95 * eyeToChin, crownRel)); source = 'clamped';
    }
    return { c0: c0, theta: theta, E: E, xc: xc, crownRel: crownRel, chinRel: eyeToChin, headPx: eyeToChin - crownRel, crownSource: source };
  }

  // ---------------------------------------------------------------- render: crop, matting composite, sharpen
  function hexToRgb(h) { var v = parseInt(h.slice(1), 16); return [(v >> 16) & 255, (v >> 8) & 255, v & 255]; }

  function foregroundEstimate(rgb, alpha, w, h) {
    // Blur-Fusion foreground estimation (M. Forte, ICIP 2021): removes the old background colour from edge pixels
    var n = w * h, r1 = Math.max(9, Math.round(h / 14)), r2 = 3, c, i;
    function pass(F, B, r) {
      var ba = boxBlur(alpha, w, h, r), oneMinus = new Float32Array(n), inv = new Float32Array(n);
      for (i = 0; i < n; i++) inv[i] = 1 - alpha[i];
      var outF = [], outB = [];
      for (c = 0; c < 3; c++) {
        var fa = new Float32Array(n), b1a = new Float32Array(n);
        for (i = 0; i < n; i++) { fa[i] = F[c][i] * alpha[i]; b1a[i] = B[c][i] * inv[i]; }
        var bfa = boxBlur(fa, w, h, r), bb1a = boxBlur(b1a, w, h, r), nf = new Float32Array(n), nb = new Float32Array(n);
        for (i = 0; i < n; i++) {
          var bf = bfa[i] / (ba[i] + 1e-5), bb = bb1a[i] / ((1 - ba[i]) + 1e-5), a = alpha[i];
          var v = bf + a * (rgb[c][i] - a * bf - (1 - a) * bb);
          nf[i] = v < 0 ? 0 : v > 1 ? 1 : v; nb[i] = bb;
        }
        outF.push(nf); outB.push(nb);
      }
      return { F: outF, B: outB };
    }
    var p1 = pass(rgb, rgb, r1);
    return pass(p1.F, p1.B, r2).F;
  }

  function laplacianVar(gray, w, h, box) {
    var s = 0, s2 = 0, n = 0;
    for (var y = Math.max(1, box.y0); y < Math.min(h - 1, box.y1); y++) {
      for (var x = Math.max(1, box.x0); x < Math.min(w - 1, box.x1); x++) {
        var i = y * w + x, v = 4 * gray[i] - gray[i - 1] - gray[i + 1] - gray[i - w] - gray[i + w];
        s += v; s2 += v * v; n++;
      }
    }
    if (!n) return 0; var m = s / n; return s2 / n - m * m;
  }

  function currentSize() {
    var id = el.preset.value;
    if (id === 'custom') return { id: id, w: Math.max(10, Math.min(100, +el.cw.value || 35)), h: Math.max(10, Math.min(150, +el.ch.value || 45)) };
    for (var i = 0; i < PRESETS.length; i++) if (PRESETS[i][0] === id) return { id: id, w: PRESETS[i][1], h: PRESETS[i][2] };
    return { id: '3x4', w: 30, h: 40 };
  }

  function render() {
    if (!S) return;
    var sz = currentSize(), outW = Math.round(sz.w / 25.4 * DPI), outH = Math.round(sz.h / 25.4 * DPI);
    var ratio = (+el.head.value) / 100, g = S.geo;
    var scale = ratio * outH / g.headPx;
    var topMargin = outH * (1 - ratio) * 0.36;
    var cs = Math.cos(g.theta), sn = Math.sin(g.theta);
    // anchor: point on the crown-line above the face centre -> (outW/2, topMargin)
    var ux = g.xc, uy = g.crownRel;
    var P0x = g.c0.x + cs * ux - sn * uy, P0y = g.c0.y + sn * ux + cs * uy;
    var a = scale * cs, b = -scale * sn, c = scale * sn, d = scale * cs;
    var e = outW / 2 - (a * P0x + c * P0y), f = topMargin - (b * P0x + d * P0y);

    var rgbCv = makeCanvas(outW, outH), rctx = rgbCv.getContext('2d', { willReadFrequently: true });
    rctx.fillStyle = '#808080'; rctx.fillRect(0, 0, outW, outH);
    rctx.imageSmoothingQuality = 'high'; rctx.setTransform(a, b, c, d, e, f); rctx.drawImage(S.src, 0, 0);
    var aCv = makeCanvas(outW, outH), actx = aCv.getContext('2d', { willReadFrequently: true });
    actx.fillStyle = '#000'; actx.fillRect(0, 0, outW, outH);
    actx.imageSmoothingQuality = 'high'; actx.setTransform(a, b, c, d, e, f); actx.drawImage(S.alphaCv, 0, 0);

    var rd = rctx.getImageData(0, 0, outW, outH).data, ad = actx.getImageData(0, 0, outW, outH).data, n = outW * outH, i;
    var rgb = [new Float32Array(n), new Float32Array(n), new Float32Array(n)], alpha = new Float32Array(n);
    var edge = +el.edge.value, lo = Math.max(0, 0.04 + 0.07 * edge), hi = Math.min(1, 0.94 + 0.02 * edge);
    for (i = 0; i < n; i++) {
      rgb[0][i] = rd[i * 4] / 255; rgb[1][i] = rd[i * 4 + 1] / 255; rgb[2][i] = rd[i * 4 + 2] / 255;
      var v = (ad[i * 4] / 255 - lo) / (hi - lo); alpha[i] = v < 0 ? 0 : v > 1 ? 1 : v;
    }
    var F = foregroundEstimate(rgb, alpha, outW, outH);

    // optional auto-levels measured on solid subject pixels
    if (el.levels.checked) {
      var hist = new Uint32Array(256), cnt = 0;
      for (i = 0; i < n; i++) if (alpha[i] > 0.95) { hist[Math.round((0.299 * F[0][i] + 0.587 * F[1][i] + 0.114 * F[2][i]) * 255)]++; cnt++; }
      if (cnt > 200) {
        var acc = 0, p1 = 0, p99 = 255, k;
        for (k = 0; k < 256; k++) { acc += hist[k]; if (acc >= cnt * 0.01) { p1 = k; break; } }
        acc = 0; for (k = 255; k >= 0; k--) { acc += hist[k]; if (acc >= cnt * 0.01) { p99 = k; break; } }
        if (p99 - p1 > 40) {
          var sc = Math.min(1.5, 232 / (p99 - p1)), off = 10, mix = 0.6;
          for (var ch = 0; ch < 3; ch++) for (i = 0; i < n; i++) {
            var o = F[ch][i] * 255, nv = (o - p1) * sc + off; nv = o + (nv - o) * mix; F[ch][i] = Math.max(0, Math.min(255, nv)) / 255;
          }
        }
      }
    }

    // composite on the chosen background
    var bgc = hexToRgb(bg), out = makeCanvas(outW, outH), octx = out.getContext('2d', { willReadFrequently: true });
    var od = octx.createImageData(outW, outH), gray = new Float32Array(n);
    for (i = 0; i < n; i++) {
      var al = alpha[i];
      var R = F[0][i] * 255 * al + bgc[0] * (1 - al), G = F[1][i] * 255 * al + bgc[1] * (1 - al), B = F[2][i] * 255 * al + bgc[2] * (1 - al);
      od.data[i * 4] = R; od.data[i * 4 + 1] = G; od.data[i * 4 + 2] = B; od.data[i * 4 + 3] = 255;
      gray[i] = 0.299 * R + 0.587 * G + 0.114 * B;
    }

    // adaptive sharpening: suggestion from Laplacian variance of the face region (computed once per image/size)
    var faceBox = {
      x0: Math.round(outW * 0.2), x1: Math.round(outW * 0.8),
      y0: Math.round(topMargin + ratio * outH * 0.25), y1: Math.round(topMargin + ratio * outH * 0.95)
    };
    var lv = laplacianVar(gray, outW, outH, faceBox);
    var auto = lv < 25 ? 1.4 : lv < 60 ? 1.1 : lv < 140 ? 0.75 : 0.45;
    if (S.sharpAuto) { S.sharpAuto = false; el.sharp.value = Math.round(auto * 100); }
    el.sharpV.textContent = el.sharp.value + '%';
    var amount = (+el.sharp.value) / 100;
    if (amount > 0.01) {
      var sig = Math.max(0.8, outH / 520), rr = Math.max(1, Math.round(sig * 1.2));
      var chn = [new Float32Array(n), new Float32Array(n), new Float32Array(n)];
      for (i = 0; i < n; i++) { chn[0][i] = od.data[i * 4]; chn[1][i] = od.data[i * 4 + 1]; chn[2][i] = od.data[i * 4 + 2]; }
      for (var q = 0; q < 3; q++) {
        var bl = boxBlur(boxBlur(boxBlur(chn[q], outW, outH, rr), outW, outH, rr), outW, outH, rr);
        for (i = 0; i < n; i++) {
          var diff = chn[q][i] - bl[i];
          if (Math.abs(diff) < 2) diff = 0;
          var nv2 = chn[q][i] + amount * diff; od.data[i * 4 + q] = nv2 < 0 ? 0 : nv2 > 255 ? 255 : nv2;
        }
      }
    }
    octx.putImageData(od, 0, 0);

    el.out.width = outW; el.out.height = outH; el.out.getContext('2d').drawImage(out, 0, 0);
    lastOut = { canvas: out, wmm: sz.w, hmm: sz.h };
    var notes = [sz.w + '×' + sz.h + ' mm · ' + outW + '×' + outH + ' ' + TXT.px + ' · ' + DPI + ' DPI'];
    if (Math.abs(g.theta) > 0.012) notes.push(TXT.tilt + ' ' + (g.theta * 180 / Math.PI).toFixed(1) + TXT.deg);
    if (scale > 1.35) notes.push(TXT.lowRes);
    if (S.face.count > 1) notes.push(TXT.multiFace);
    el.info.textContent = notes.join(' · ');
    el.stage.hidden = false;
    [el.dlPng, el.dlJpg, el.dlSheet].forEach(function (b) { b.disabled = false; });
    drawSheet();
  }

  function scheduleRender() {
    if (!S || busy) return;
    clearTimeout(renderTimer);
    renderTimer = setTimeout(function () { try { render(); } catch (e) { setStatus(TXT.err + ': ' + e.message, 'err'); console.error(e); } }, 60);
  }

  // ---------------------------------------------------------------- print sheet
  function sheetSize() { var v = el.sheetSel.value; return v === 'a4' ? { w: 2480, h: 3508, label: 'A4' } : { w: 1200, h: 1800, label: '10×15 cm' }; }
  function drawSheet() {
    if (!lastOut) return;
    var ss = sheetSize(), pw = lastOut.canvas.width, ph = lastOut.canvas.height, gap = 18, margin = 36, best = null;
    [false, true].forEach(function (land) {
      var SW = land ? ss.h : ss.w, SH = land ? ss.w : ss.h;
      var cols = Math.floor((SW - 2 * margin + gap) / (pw + gap)), rows = Math.floor((SH - 2 * margin + gap) / (ph + gap));
      if (cols > 0 && rows > 0 && (!best || cols * rows > best.cols * best.rows)) best = { SW: SW, SH: SH, cols: cols, rows: rows };
    });
    if (!best) { el.sheetInfo.textContent = ''; return; }
    var cv = el.sheetCv; cv.width = best.SW; cv.height = best.SH;
    var ctx = cv.getContext('2d'); ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, best.SW, best.SH);
    var gw = best.cols * pw + (best.cols - 1) * gap, gh = best.rows * ph + (best.rows - 1) * gap;
    var ox = Math.round((best.SW - gw) / 2), oy = Math.round((best.SH - gh) / 2);
    for (var r = 0; r < best.rows; r++) for (var c = 0; c < best.cols; c++) {
      var x = ox + c * (pw + gap), y = oy + r * (ph + gap);
      ctx.drawImage(lastOut.canvas, x, y);
      ctx.strokeStyle = '#c8c8c8'; ctx.lineWidth = 1; ctx.strokeRect(x - 0.5, y - 0.5, pw + 1, ph + 1);
    }
    el.sheetInfo.textContent = ss.label + ' · ' + (best.cols * best.rows) + ' ' + TXT.sheetN;
  }

  // ---------------------------------------------------------------- export with DPI metadata
  var CRC_T = null;
  function crc32(buf) {
    if (!CRC_T) { CRC_T = new Uint32Array(256); for (var n = 0; n < 256; n++) { var c = n; for (var k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; CRC_T[n] = c >>> 0; } }
    var crc = 0xFFFFFFFF; for (var i = 0; i < buf.length; i++) crc = CRC_T[(crc ^ buf[i]) & 255] ^ (crc >>> 8);
    return (crc ^ 0xFFFFFFFF) >>> 0;
  }
  async function withDpi(blob, type) {
    var u = new Uint8Array(await blob.arrayBuffer());
    if (type === 'image/jpeg') {
      if (u[2] === 0xFF && u[3] === 0xE0 && u[6] === 0x4A) { // JFIF APP0: units(11) Xd(12-13) Yd(14-15)
        u[13] = 1; u[14] = DPI >> 8; u[15] = DPI & 255; u[16] = DPI >> 8; u[17] = DPI & 255;
      }
      return new Blob([u], { type: type });
    }
    // PNG: insert pHYs chunk right after IHDR (8 sig + 25 IHDR)
    var ppm = Math.round(DPI / 0.0254), chunk = new Uint8Array(21), dv = new DataView(chunk.buffer);
    dv.setUint32(0, 9); chunk.set([0x70, 0x48, 0x59, 0x73], 4); dv.setUint32(8, ppm); dv.setUint32(12, ppm); chunk[16] = 1;
    dv.setUint32(17, crc32(chunk.subarray(4, 17)));
    var res = new Uint8Array(u.length + 21); res.set(u.subarray(0, 33), 0); res.set(chunk, 33); res.set(u.subarray(33), 54);
    return new Blob([res], { type: type });
  }
  function toBlob(cv, type, q) { return new Promise(function (r) { cv.toBlob(r, type, q); }); }
  async function download(cv, type, name) {
    var blob = await withDpi(await toBlob(cv, type, 0.96), type);
    var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name;
    document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 2000);
  }
  function fname(ext, sheet) { var sz = currentSize(); return 'shopsmon-id-photo-' + sz.w + 'x' + sz.h + 'mm' + (sheet ? '-sheet' : '') + '.' + ext; }

  // ---------------------------------------------------------------- main flow
  async function handleFile(file) {
    if (busy || !file) return;
    if (!/^image\/(jpeg|png|webp)$/.test(file.type)) { setStatus(TXT.badType, 'err'); return; }
    if (file.size > 25 * 1048576) { setStatus(TXT.tooBig, 'err'); return; }
    busy = true; S = null; lastOut = null;
    [el.dlPng, el.dlJpg, el.dlSheet].forEach(function (b) { b.disabled = true; });
    try {
      var bmp;
      try { bmp = await decode(file); } catch (e) { setStatus(TXT.decodeErr, 'err'); busy = false; return; }
      var w0 = bmp.width || bmp.naturalWidth, h0 = bmp.height || bmp.naturalHeight, k = Math.min(1, MAX_SIDE / Math.max(w0, h0));
      var W = Math.max(1, Math.round(w0 * k)), H = Math.max(1, Math.round(h0 * k));
      var src = makeCanvas(W, H), sctx = src.getContext('2d', { willReadFrequently: true });
      sctx.imageSmoothingQuality = 'high'; sctx.drawImage(bmp, 0, 0, W, H);
      el.orig.width = Math.min(W, 360); el.orig.height = Math.round(H * el.orig.width / W);
      el.orig.getContext('2d').drawImage(src, 0, 0, el.orig.width, el.orig.height);
      el.stage.hidden = false;

      await ensureLibs();
      setBar(0.15); setStatus(TXT.detect); await tick();
      var res = libs.landmarker.detect(src), face = pickFace(res, W, H);
      if (!face) { setBar(null); setStatus(TXT.noFace, 'err'); busy = false; return; }
      setBar(0.3); setStatus(TXT.matting); await tick();
      var alpha = await matteOf(src, W, H);
      setBar(0.8); setStatus(TXT.refine); await tick();
      alpha = refineAlpha(src, alpha, W, H);
      var alphaCv = grayCanvasFromAlpha(alpha, W, H);
      setBar(0.92); setStatus(TXT.render); await tick();
      var geo = computeGeometry(face, alphaCv, W, H);
      S = { src: src, W: W, H: H, alpha: alpha, alphaCv: alphaCv, face: face, geo: geo, sharpAuto: true };
      busy = false;
      render();
      setBar(null); setStatus(TXT.done, 'ok');
    } catch (e) {
      console.error(e); setBar(null); setStatus(TXT.err + ': ' + (e && e.message ? e.message : e), 'err'); busy = false;
    }
  }

  // ---------------------------------------------------------------- UI wiring
  PRESETS.forEach(function (p) { /* options are rendered server-side; here we only set head-ratio defaults */ });
  function applyPresetDefaults() {
    var id = el.preset.value, r = 0.72;
    for (var i = 0; i < PRESETS.length; i++) if (PRESETS[i][0] === id) r = PRESETS[i][3];
    el.head.value = Math.round(r * 100); el.headV.textContent = el.head.value + '%';
    el.customRow.hidden = id !== 'custom';
  }
  el.preset.addEventListener('change', function () { applyPresetDefaults(); scheduleRender(); });
  [el.cw, el.ch].forEach(function (x) { x.addEventListener('input', scheduleRender); });
  el.head.addEventListener('input', function () { el.headV.textContent = el.head.value + '%'; scheduleRender(); });
  el.sharp.addEventListener('input', scheduleRender);
  el.edge.addEventListener('input', function () { el.edgeV.textContent = (+el.edge.value > 0 ? '+' : '') + el.edge.value; scheduleRender(); });
  el.levels.addEventListener('change', scheduleRender);
  el.sheetSel.addEventListener('change', drawSheet);
  el.swatches.addEventListener('click', function (ev) {
    var b = ev.target.closest('button[data-c]'); if (!b) return;
    bg = b.getAttribute('data-c'); el.color.value = bg;
    [].forEach.call(el.swatches.querySelectorAll('button'), function (x) { x.classList.toggle('on', x === b); });
    scheduleRender();
  });
  el.color.addEventListener('input', function () {
    bg = el.color.value; [].forEach.call(el.swatches.querySelectorAll('button'), function (x) { x.classList.remove('on'); }); scheduleRender();
  });
  el.file.addEventListener('change', function () { if (el.file.files[0]) handleFile(el.file.files[0]); el.file.value = ''; });
  ['dragenter', 'dragover'].forEach(function (t) { el.drop.addEventListener(t, function (e) { e.preventDefault(); el.drop.classList.add('over'); }); });
  ['dragleave', 'drop'].forEach(function (t) { el.drop.addEventListener(t, function (e) { e.preventDefault(); el.drop.classList.remove('over'); }); });
  el.drop.addEventListener('drop', function (e) { var f = e.dataTransfer && e.dataTransfer.files[0]; if (f) handleFile(f); });
  el.dlPng.addEventListener('click', function () { if (lastOut) download(lastOut.canvas, 'image/png', fname('png')); });
  el.dlJpg.addEventListener('click', function () { if (lastOut) download(lastOut.canvas, 'image/jpeg', fname('jpg')); });
  el.dlSheet.addEventListener('click', function () { if (lastOut) download(el.sheetCv, 'image/jpeg', fname('jpg', true)); });
  el.reset.addEventListener('click', function () {
    S = null; lastOut = null; el.stage.hidden = true; setStatus(''); setBar(null);
    [el.dlPng, el.dlJpg, el.dlSheet].forEach(function (b) { b.disabled = true; });
  });
  applyPresetDefaults();
  window.__idphoto = { handleFile: handleFile, state: function () { return S; }, render: render };
})();
