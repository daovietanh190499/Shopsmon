/* Shopsmon OCR - image to structured text, runs entirely in the browser (no upload).
 *
 * Engines
 *   PP-OCRv6 (default, multilingual): PaddleOCR.js (ONNX Runtime Web + OpenCV.js in a Web Worker) = text detection (PP-OCRv6 small det) +
 *              text recognition (PP-OCRv6 small rec: Latin incl. FR/DE/ES/TR/PL..., Chinese simplified + traditional, Japanese).
 *              For scripts the v6 dictionary does not contain, the matching PP-OCRv5 recogniser is loaded on demand:
 *              Korean, Cyrillic (eslav), Thai, Arabic, Devanagari (Hindi), Greek.
 *   Vietnamese: the PP-OCRv6/v5 dictionaries have no Vietnamese tone-marked letters (ả ạ ế ộ ữ ...), so a Vietnamese page is read by
 *              Tesseract.js (tessdata_best "vie"): "Document" = whole page after clean-up + deskew, "Photo" = PP-OCRv6 detection finds
 *              every line, each line is rectified and read by Tesseract. Auto language detects Vietnamese from the PP-OCRv6 output.
 *   Layout: words/lines -> segments -> columns -> tables -> paragraphs / lists / headings -> HTML, Markdown, plain text.
 */
(function () {
  'use strict';

  var LANG = document.documentElement.lang === 'en' ? 'en' : 'vi';
  var TXT = {
    vi: {
      loadingLib: 'Đang tải thư viện OCR…', loadingLang: 'Đang tải dữ liệu ngôn ngữ', loadingModel: 'Đang tải mô hình', initRt: 'Đang khởi tạo bộ nhận dạng…',
      prep: 'Đang làm sạch ảnh…', reading: 'Đang đọc chữ…', detecting: 'Đang tìm các dòng chữ…', lines: 'Đang đọc từng dòng', layout: 'Đang dựng lại bố cục…',
      done: 'Hoàn tất', badType: 'Vui lòng chọn tệp ảnh (JPG, PNG, WebP, BMP hoặc GIF).', tooBig: 'Tệp lớn hơn 25 MB. Hãy chọn ảnh nhỏ hơn.',
      decodeErr: 'Không đọc được ảnh này.', err: 'Có lỗi khi nhận dạng', empty: 'Không tìm thấy chữ trong ảnh. Thử xoay ảnh, chọn chế độ khác hoặc dùng ảnh rõ hơn.',
      lowConf: 'Độ tin cậy thấp. Hãy thử ảnh rõ hơn, chế độ "Ảnh chụp" hoặc xoay ảnh cho đúng chiều.', autoRetry: 'Độ tin cậy thấp, đang thử thêm chế độ ảnh chụp…',
      words: 'từ', linesN: 'dòng', conf: 'độ tin cậy', skew: 'đã chỉnh nghiêng', engDoc: 'Tài liệu', engPhoto: 'Ảnh chụp', copied: 'Đã sao chép', copyFail: 'Không sao chép được',
      table: 'bảng', cols: 'cột', s: 's', mb: 'MB', tableN: 'bảng', orient: 'Độ tin cậy thấp, đang thử các hướng xoay khác…', rotated: 'đã tự xoay ảnh',
      loadingRec: 'Đang tải mô hình nhận dạng', vnFound: 'Phát hiện tiếng Việt, chuyển sang bộ đọc tiếng Việt…',
      lowScript: 'Độ tin cậy thấp. Nếu chữ trong ảnh là tiếng Hàn, Nga, Thái, Ả Rập, Hindi hoặc Hy Lạp, hãy chọn đúng ngôn ngữ ở ô Ngôn ngữ.', engPP: 'PP-OCRv6', engPP5: 'PP-OCRv5'
    },
    en: {
      loadingLib: 'Loading OCR libraries…', loadingLang: 'Downloading language data', loadingModel: 'Downloading model', initRt: 'Initialising recogniser…',
      prep: 'Cleaning up the image…', reading: 'Reading text…', detecting: 'Finding text lines…', lines: 'Reading line by line', layout: 'Rebuilding layout…',
      done: 'Done', badType: 'Please choose an image file (JPG, PNG, WebP, BMP or GIF).', tooBig: 'File is larger than 25 MB. Please choose a smaller image.',
      decodeErr: 'This image could not be read.', err: 'Recognition error', empty: 'No text found. Try rotating the image, another mode, or a clearer picture.',
      lowConf: 'Low confidence. Try a clearer image, the "Photo" mode, or rotate the image upright.', autoRetry: 'Low confidence, also trying photo mode…',
      words: 'words', linesN: 'lines', conf: 'confidence', skew: 'deskewed', engDoc: 'Document', engPhoto: 'Photo', copied: 'Copied', copyFail: 'Copy failed',
      table: 'table', cols: 'cols', s: 's', mb: 'MB', tableN: 'tables', orient: 'Low confidence, trying other orientations…', rotated: 'auto-rotated',
      loadingRec: 'Downloading recognition model', vnFound: 'Vietnamese detected, switching to the Vietnamese reader…',
      lowScript: 'Low confidence. If the text is Korean, Russian, Thai, Arabic, Hindi or Greek, pick that language in the Language box.', engPP: 'PP-OCRv6', engPP5: 'PP-OCRv5'
    }
  }[LANG];

  var TESS_JS = 'https://cdn.jsdelivr.net/npm/tesseract.js@5.1.1/dist/tesseract.min.js';
  var TESS_CORE = 'https://cdn.jsdelivr.net/npm/tesseract.js-core@5.1.1/';
  var TESS_DATA = { vie: 'https://cdn.jsdelivr.net/npm/@tesseract.js-data/vie/4.0.0_best_int' };
  var PADDLE_JS = 'https://cdn.jsdelivr.net/npm/@paddleocr/paddleocr-js@0.4.2/+esm';
  var PADDLE_WORKER = 'https://cdn.jsdelivr.net/npm/@paddleocr/paddleocr-js@0.4.2/dist/assets/worker-entry-C9UNuyOJ.js';
  var DET_URL = '/assets/models/PP-OCRv6_small_det.tar';
  // recognisers (model name must equal model_name inside the tar's inference.yml); v6 first = default
  var RECS = {
    v6: { name: 'PP-OCRv6_small_rec', url: '/assets/models/PP-OCRv6_small_rec.tar', v: 6 },
    ko: { name: 'korean_PP-OCRv5_mobile_rec', url: '/assets/models/korean_PP-OCRv5_mobile_rec.tar', v: 5 },
    ru: { name: 'eslav_PP-OCRv5_mobile_rec', url: '/assets/models/eslav_PP-OCRv5_mobile_rec.tar', v: 5 },
    th: { name: 'th_PP-OCRv5_mobile_rec', url: '/assets/models/th_PP-OCRv5_mobile_rec.tar', v: 5 },
    ar: { name: 'arabic_PP-OCRv5_mobile_rec', url: '/assets/models/arabic_PP-OCRv5_mobile_rec.tar', v: 5 },
    hi: { name: 'devanagari_PP-OCRv5_mobile_rec', url: '/assets/models/devanagari_PP-OCRv5_mobile_rec.tar', v: 5 },
    el: { name: 'el_PP-OCRv5_mobile_rec', url: '/assets/models/el_PP-OCRv5_mobile_rec.tar', v: 5 }
  };
  // Vietnamese-only letters (d-stroke, horn/breve vowels, dotted/hooked tone marks): the PP-OCR dictionary drops most of them, but a few survive
  var VN_RE = /[đĐơƠưƯăĂạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼẾỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴỶỸ]/g;
  var NOSP = /[\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff\uff00-\uffef\u0e00-\u0e7f]/;   // scripts written without spaces between words
  var QS = new URLSearchParams(location.search);   // test overrides: ?ocrbackend=auto&ocrlimit=960
  var MAX_SIDE = 2600;
  var LOW_CONF = 60;

  var $ = function (id) { return document.getElementById(id); };
  var el = {
    drop: $('ocrDrop'), file: $('ocrFile'), status: $('ocrStatus'), bar: $('ocrBar'), barWrap: $('ocrBarWrap'),
    mode: $('ocrMode'), lang: $('ocrLang'), keep: $('ocrKeep'), tables: $('ocrTables'), run: $('ocrRun'), reset: $('ocrReset'),
    rotL: $('ocrRotL'), rotR: $('ocrRotR'), sampleDoc: $('ocrSampleDoc'), samplePhoto: $('ocrSamplePhoto'), prev: $('ocrPrev'),
    stage: $('ocrStage'), info: $('ocrInfo'), view: $('ocrView'), md: $('ocrMd'), json: $('ocrJson'), cv: $('ocrCanvas'),
    copy: $('ocrCopy'), dlTxt: $('ocrDlTxt'), dlMd: $('ocrDlMd'), dlJson: $('ocrDlJson'), dlCsv: $('ocrDlCsv'), tabs: $('ocrTabs')
  };
  if (!el.drop) return;

  var S = null;            // {bitmap, name, rot}
  var R = null;            // last result {blocks, md, text, json, shapes, overlay, csv}
  var busy = false;
  var tessState = { key: '', workers: [] };
  var paddle = null;       // {key, inst}
  var wkUrl = null;

  // ------------------------------------------------------------------ small helpers
  function setStatus(msg, kind) { el.status.textContent = msg || ''; el.status.className = 'idp-status' + (kind ? ' ' + kind : ''); }
  function setBar(p) {
    if (p == null) { el.barWrap.hidden = true; return; }
    el.barWrap.hidden = false; el.bar.style.width = Math.round(Math.max(0, Math.min(1, p)) * 100) + '%';
  }
  function tick() { return new Promise(function (r) { setTimeout(r, 0); }); }
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  function num(a, b) { return a - b; }
  function median(a) { if (!a.length) return 0; var b = a.slice().sort(num); return b[b.length >> 1]; }
  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }

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
      var shown = Math.min(got, total);   // Content-Length can be the compressed size while the stream is decoded
      setStatus(label + ' ' + Math.round(shown / 1048576 * 10) / 10 + ' / ' + Math.round(total / 1048576 * 10) / 10 + ' ' + TXT.mb); setBar(shown / total);
    }
    var out = new Uint8Array(got), o = 0;
    chunks.forEach(function (c) { out.set(c, o); o += c.length; });
    return out;
  }

  // ------------------------------------------------------------------ image preparation
  async function decode(file) {
    try { return await createImageBitmap(file, { imageOrientation: 'from-image' }); }
    catch (e) {
      return new Promise(function (res, rej) {
        var u = URL.createObjectURL(file), im = new Image();
        im.onload = function () { createImageBitmap(im).then(res, rej); URL.revokeObjectURL(u); };
        im.onerror = function () { rej(new Error('decode')); };
        im.src = u;
      });
    }
  }
  function drawBase(bm, rot) {
    var w = bm.width, h = bm.height, long = Math.max(w, h), sc = 1;
    if (long > MAX_SIDE) sc = MAX_SIDE / long; else if (long < 1500) sc = Math.min(2.5, 1600 / long);
    var sw = Math.round(w * sc), sh = Math.round(h * sc), swap = rot % 2 === 1;
    var c = document.createElement('canvas'); c.width = swap ? sh : sw; c.height = swap ? sw : sh;
    var x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0, 0, c.width, c.height);
    x.imageSmoothingQuality = 'high';
    x.translate(c.width / 2, c.height / 2); x.rotate(rot * Math.PI / 2); x.drawImage(bm, -sw / 2, -sh / 2, sw, sh);
    return c;
  }
  function toGray(c) {
    var d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data, n = c.width * c.height, g = new Uint8ClampedArray(n);
    for (var i = 0, j = 0; i < n; i++, j += 4) g[i] = (d[j] * 299 + d[j + 1] * 587 + d[j + 2] * 114) / 1000;
    return g;
  }
  function grayToCanvas(g, w, h) {
    var c = document.createElement('canvas'); c.width = w; c.height = h;
    var x = c.getContext('2d'), im = x.createImageData(w, h), d = im.data;
    for (var i = 0, j = 0; i < g.length; i++, j += 4) { d[j] = d[j + 1] = d[j + 2] = g[i]; d[j + 3] = 255; }
    x.putImageData(im, 0, 0); return c;
  }
  // divide by a smooth estimate of the paper brightness (block max, smoothed) to remove shadows and uneven lighting
  function flatten(g, w, h) {
    var b = Math.max(16, Math.round(Math.max(w, h) / 55)), gw = Math.ceil(w / b), gh = Math.ceil(h / b);
    var m = new Float32Array(gw * gh), by, bx, y, x;
    for (by = 0; by < gh; by++) for (bx = 0; bx < gw; bx++) {
      var mx = 0, y1 = Math.min(h, (by + 1) * b), x1 = Math.min(w, (bx + 1) * b);
      for (y = by * b; y < y1; y++) { var row = y * w; for (x = bx * b; x < x1; x++) { var v = g[row + x]; if (v > mx) mx = v; } }
      m[by * gw + bx] = mx;
    }
    for (var pass = 0; pass < 2; pass++) {
      var t = new Float32Array(m.length);
      for (by = 0; by < gh; by++) for (bx = 0; bx < gw; bx++) {
        var s = 0, c = 0;
        for (var dy = -1; dy <= 1; dy++) for (var dx = -1; dx <= 1; dx++) {
          var yy = by + dy, xx = bx + dx; if (yy < 0 || xx < 0 || yy >= gh || xx >= gw) continue; s += m[yy * gw + xx]; c++;
        }
        t[by * gw + bx] = s / c;
      }
      m = t;
    }
    var out = new Uint8ClampedArray(g.length);
    for (y = 0; y < h; y++) {
      var fy = clamp((y + 0.5) / b - 0.5, 0, gh - 1), y0 = Math.floor(fy), y1i = Math.min(gh - 1, y0 + 1), ty = fy - y0;
      for (x = 0; x < w; x++) {
        var fx = clamp((x + 0.5) / b - 0.5, 0, gw - 1), x0 = Math.floor(fx), x1i = Math.min(gw - 1, x0 + 1), tx = fx - x0;
        var bg = (m[y0 * gw + x0] * (1 - tx) + m[y0 * gw + x1i] * tx) * (1 - ty) + (m[y1i * gw + x0] * (1 - tx) + m[y1i * gw + x1i] * tx) * ty;
        var o = g[y * w + x] * 255 / Math.max(bg, 70);
        out[y * w + x] = o > 255 ? 255 : o;
      }
    }
    return out;
  }
  function stretch(g) {
    var hist = new Uint32Array(256), i; for (i = 0; i < g.length; i++) hist[g[i]]++;
    var lo = 0, hi = 255, acc = 0, a = g.length * 0.005;
    for (i = 0; i < 256; i++) { acc += hist[i]; if (acc > a) { lo = i; break; } }
    acc = 0; for (i = 255; i >= 0; i--) { acc += hist[i]; if (acc > a) { hi = i; break; } }
    if (hi - lo < 40) return g;
    var out = new Uint8ClampedArray(g.length), k = 255 / (hi - lo);
    for (i = 0; i < g.length; i++) out[i] = (g[i] - lo) * k;
    return out;
  }
  function otsu(hist, total) {
    var sum = 0, i; for (i = 0; i < 256; i++) sum += i * hist[i];
    var sb = 0, wb = 0, best = 0, th = 128;
    for (i = 0; i < 256; i++) {
      wb += hist[i]; if (!wb) continue; var wf = total - wb; if (!wf) break;
      sb += i * hist[i]; var mb = sb / wb, mf = (sum - sb) / wf, v = wb * wf * (mb - mf) * (mb - mf);
      if (v > best) { best = v; th = i; }
    }
    return th;
  }
  // projection-profile skew estimate; returns clockwise tilt of the text lines in radians
  function estimateSkew(g, w, h) {
    var f = Math.max(1, Math.max(w, h) / 800), sw = Math.round(w / f), sh = Math.round(h / f), hist = new Uint32Array(256), x, y;
    var small = new Uint8Array(sw * sh);
    for (y = 0; y < sh; y++) for (x = 0; x < sw; x++) { var v = g[Math.floor(y * f) * w + Math.floor(x * f)]; small[y * sw + x] = v; hist[v]++; }
    var th = otsu(hist, sw * sh) * 0.9, pts = [];
    for (y = 0; y < sh; y++) for (x = 0; x < sw; x++) if (small[y * sw + x] < th) pts.push(x, y);
    var step = Math.max(1, Math.floor(pts.length / 2 / 90000)), n = 0, P = [];
    for (var i = 0; i < pts.length; i += 2 * step) { P.push(pts[i], pts[i + 1]); n++; }
    if (n < 300) return 0;
    var nb = sw + sh + 4;
    function score(a) {
      var c = Math.cos(a), s = Math.sin(a), bins = new Float64Array(nb), sc = 0;
      for (var k = 0; k < P.length; k += 2) bins[Math.round(P[k + 1] * c - P[k] * s) + sw]++;
      for (var j = 0; j < nb; j++) sc += bins[j] * bins[j];
      return sc;
    }
    var best = 0, bs = score(0), a;
    for (a = -10; a <= 10; a += 0.5) { var sc0 = score(a * Math.PI / 180); if (sc0 > bs) { bs = sc0; best = a; } }
    var b2 = best;
    for (a = best - 0.5; a <= best + 0.5; a += 0.1) { var sc1 = score(a * Math.PI / 180); if (sc1 > bs) { bs = sc1; b2 = a; } }
    return b2 * Math.PI / 180;
  }
  // erase long thin dark strokes (table rules, borders) so they are not read as "|" or "_" noise
  function removeRules(g, w, h) {
    var hist = new Uint32Array(256), i, x, y;
    for (i = 0; i < g.length; i += 3) hist[g[i]]++;
    var th0 = otsu(hist, Math.ceil(g.length / 3)) * 0.9, th = th0 + (255 - th0) * 0.55, Lh = Math.max(60, Math.round(w * 0.06)), Lv = Math.max(60, Math.round(h * 0.04));
    var kill = new Uint8Array(g.length), dark = function (xx, yy) { return xx >= 0 && yy >= 0 && xx < w && yy < h && g[yy * w + xx] < th; };
    for (y = 0; y < h; y++) {
      x = 0;
      while (x < w) {
        if (g[y * w + x] >= th) { x++; continue; }
        var s = x; while (x < w && g[y * w + x] < th) x++;
        if (x - s >= Lh) {
          var up = 0, dn = 0, n = x - s, st = Math.max(1, n >> 5);
          for (var k = s, c = 0; k < x; k += st, c++) { if (dark(k, y - 7)) up++; if (dark(k, y + 7)) dn++; }
          if (up / c < 0.3 && dn / c < 0.3) for (var q = s; q < x; q++) kill[y * w + q] = 1;
        }
      }
    }
    for (x = 0; x < w; x++) {
      y = 0;
      while (y < h) {
        if (g[y * w + x] >= th) { y++; continue; }
        var s2 = y; while (y < h && g[y * w + x] < th) y++;
        if (y - s2 >= Lv) {
          var lf = 0, rt = 0, n2 = y - s2, st2 = Math.max(1, n2 >> 5), c2 = 0;
          for (var k2 = s2; k2 < y; k2 += st2, c2++) { if (dark(x - 7, k2)) lf++; if (dark(x + 7, k2)) rt++; }
          if (lf / c2 < 0.3 && rt / c2 < 0.3) for (var q2 = s2; q2 < y; q2++) kill[q2 * w + x] = 1;
        }
      }
    }
    for (i = 0; i < g.length; i++) if (kill[i]) g[i] = 255;
    return g;
  }
  function rotateCanvas(c, ang) {
    var w = c.width, h = c.height, cs = Math.abs(Math.cos(ang)), sn = Math.abs(Math.sin(ang));
    var nw = Math.round(w * cs + h * sn), nh = Math.round(w * sn + h * cs);
    var o = document.createElement('canvas'); o.width = nw; o.height = nh;
    var x = o.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0, 0, nw, nh); x.imageSmoothingQuality = 'high';
    x.translate(nw / 2, nh / 2); x.rotate(ang); x.drawImage(c, -w / 2, -h / 2); return o;
  }
  // returns {canvas (clean, gray), skew}
  function prepare(deskew) {
    var c = drawBase(S.bitmap, S.rot), w = c.width, h = c.height, g = toGray(c), i, sum = 0;
    for (i = 0; i < g.length; i += 7) sum += g[i];
    if (sum / Math.ceil(g.length / 7) < 100) for (i = 0; i < g.length; i++) g[i] = 255 - g[i];   // light text on dark background
    g = removeRules(stretch(flatten(g, w, h)), w, h);
    var out = grayToCanvas(g, w, h), skew = 0;
    if (deskew) {
      skew = estimateSkew(g, w, h);
      if (Math.abs(skew) >= 0.3 * Math.PI / 180) out = rotateCanvas(out, -skew); else skew = 0;
    }
    return { canvas: out, skew: skew };
  }

  // ------------------------------------------------------------------ engines: Tesseract
  async function loadTess() { if (!window.Tesseract) { setStatus(TXT.loadingLib); setBar(null); await loadScript(TESS_JS); } }
  async function killTess() {
    var ws = tessState.workers; tessState = { key: '', workers: [] };
    await Promise.all(ws.map(function (w) { return w.terminate().catch(function () {}); }));
  }
  async function getTess(lang, psm, n) {
    var key = lang + '|' + psm + '|' + n;
    if (tessState.key === key) return tessState.workers;
    await killTess(); await loadTess();
    setStatus(TXT.loadingLang + '…'); setBar(null);
    var logger = function (m) {
      if (m && /loading|initializ/.test(m.status || '') && typeof m.progress === 'number') {
        setStatus(TXT.loadingLang + ' (' + Math.round(m.progress * 100) + '%)'); setBar(m.progress);
      }
    };
    var ws = await Promise.all(Array.apply(null, Array(n)).map(function () {
      return Tesseract.createWorker(lang, 1, { langPath: TESS_DATA[lang], corePath: TESS_CORE, logger: logger }).then(function (w) {
        return w.setParameters({ tessedit_pageseg_mode: String(psm), preserve_interword_spaces: '1', user_defined_dpi: '300' }).then(function () { return w; });
      });
    }));
    tessState = { key: key, workers: ws };
    return ws;
  }
  function wordsOf(data) {
    var out = [];
    (data.blocks || []).forEach(function (b) { b.paragraphs.forEach(function (p) { p.lines.forEach(function (l) {
      var ws = l.words.filter(function (w) { return w.text && w.text.trim(); }).map(function (w) {
        return { t: w.text.trim(), c: w.confidence, x0: w.bbox.x0, y0: w.bbox.y0, x1: w.bbox.x1, y1: w.bbox.y1 };
      });
      if (ws.length) out.push(ws);
    }); }); });
    return out;   // array of lines, each an array of words
  }
  // join tokens with spaces, except between two characters of a script that is written without spaces
  function joinWords(ws, fmt) {
    var o = '';
    ws.forEach(function (w, i) {
      if (i && !(NOSP.test(ws[i - 1].t.slice(-1)) && NOSP.test(w.t.charAt(0)))) o += ' ';
      o += fmt ? fmt(w) : w.t;
    });
    return o;
  }
  function segFromWords(ws, ext) {
    var s = { words: ws, text: joinWords(ws), x0: 1e9, y0: 1e9, x1: -1e9, y1: -1e9, conf: 0 }, tc = 0, tw = 0;
    ws.forEach(function (w) {
      s.x0 = Math.min(s.x0, w.x0); s.y0 = Math.min(s.y0, w.y0); s.x1 = Math.max(s.x1, w.x1); s.y1 = Math.max(s.y1, w.y1);
      var l = w.t.length; tc += w.c * l; tw += l;
    });
    s.conf = tw ? tc / tw : 0;
    if (ext) for (var k in ext) s[k] = ext[k];
    return s;
  }

  async function runDocument(lang, onProg) {
    var prep = prepare(true);
    var ws = await getTess(lang, 6, 1);   // PSM 6 (uniform block): keeps lone table digits that PSM 3/11/12 drop; columns are split later from word gaps
    setStatus(TXT.reading); setBar(0);
    var w = ws[0], prog = 0;
    var data = (await w.recognize(prep.canvas, {}, { blocks: true })).data;
    onProg && onProg(1);
    var lines = wordsOf(data);
    var hMed = median([].concat.apply([], lines.map(function (l) { return l.map(function (x) { return x.y1 - x.y0; }); }))) || 20;
    var segs = [];
    lines.forEach(function (l) {
      l.sort(function (a, b) { return a.x0 - b.x0; });
      var cur = [l[0]];
      for (var i = 1; i < l.length; i++) {
        if (l[i].x0 - l[i - 1].x1 > hMed * 1.1) { segs.push(segFromWords(cur)); cur = []; }
        cur.push(l[i]);
      }
      segs.push(segFromWords(cur));
    });
    var shapes = segs.map(function (s) { return { pts: [[s.x0, s.y0], [s.x1, s.y0], [s.x1, s.y1], [s.x0, s.y1]], conf: s.conf }; });
    return { segs: segs, canvas: prep.canvas, shapes: shapes, skew: prep.skew, engine: 'doc' };
  }

  // ------------------------------------------------------------------ engines: Paddle detection + Tesseract line reading
  async function getPaddle(key) {
    key = key || 'v6';
    if (paddle && paddle.key === key) return paddle.inst;
    if (paddle) { var old = paddle.inst; paddle = null; try { await old.dispose(); } catch (e) { /* ignore */ } }
    var rc = RECS[key];
    setStatus(TXT.loadingLib); setBar(null);
    var mod = await import(PADDLE_JS);
    var det = await fetchBuf(DET_URL, TXT.loadingModel + ' (1/3)'); void det;      // warm the HTTP cache, with progress
    var rec = await fetchBuf(rc.url, TXT.loadingRec + ' (2/3)'); void rec;
    var origin = location.origin, wk = false;
    try {
      if (!wkUrl) {
        var code = await fetchBuf(PADDLE_WORKER, TXT.loadingModel + ' (3/3)');
        wkUrl = URL.createObjectURL(new Blob([code], { type: 'text/javascript' }));
      }
      var u = wkUrl;
      wk = { createWorker: function () { return new Worker(u, { type: 'module' }); } };
    } catch (e) { wk = false; }
    setStatus(TXT.initRt); setBar(null);
    var mk = function (worker) {
      return mod.PaddleOCR.create({
        worker: worker,
        textDetectionModelName: 'PP-OCRv6_small_det', textDetectionModelAsset: { url: origin + DET_URL },
        textRecognitionModelName: rc.name, textRecognitionModelAsset: { url: origin + rc.url },
        ortOptions: { backend: QS.get('ocrbackend') || 'wasm', numThreads: 1, simd: true }
      });
    };
    var inst;
    try { inst = await mk(wk); } catch (e) { inst = await mk(false); }
    paddle = { key: key, inst: inst };
    return inst;
  }
  function cropLine(src, poly) {
    var p = poly, dx = p[1][0] - p[0][0], dy = p[1][1] - p[0][1];
    var w = Math.hypot(dx, dy), h = Math.hypot(p[3][0] - p[0][0], p[3][1] - p[0][1]), ang = Math.atan2(dy, dx);
    var ph = Math.round(h * 0.2 + 4), pw = Math.round(h * 0.9 + 4);
    var sc = h < 36 ? 36 / h : h > 90 ? 64 / h : 1;
    var cw = Math.max(8, Math.round((w + 2 * pw) * sc)), ch = Math.max(8, Math.round((h + 2 * ph) * sc));
    var c = document.createElement('canvas'); c.width = cw; c.height = ch;
    var x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0, 0, cw, ch); x.imageSmoothingQuality = 'high';
    x.scale(sc, sc); x.translate(pw, ph); x.rotate(-ang); x.translate(-p[0][0], -p[0][1]); x.drawImage(src, 0, 0);
    return c;
  }
  // drop stray punctuation fragments (rule/edge residue) at both ends of a recognised line
  function trimJunk(ws) {
    var junk = /^[._\-–—|~`'"=:;,]+$/;
    while (ws.length > 1 && junk.test(ws[0].t)) ws.shift();
    while (ws.length > 1 && junk.test(ws[ws.length - 1].t)) ws.pop();
    return ws;
  }
  // Paddle's recogniser reads digits better than Tesseract on slashed-zero / monospace fonts: when both engines saw the same number of
  // digit tokens on a line, take Paddle's version of ASCII-only tokens that differ slightly (never touches Vietnamese letters).
  var ASCII_TOK = /^[0-9A-Za-z.,:%\/#+()\-]+$/;
  function rescueDigits(seg, pText, pScore) {
    if (!pText || pScore < 0.85) return;
    var pt = pText.trim().split(/\s+/).filter(function (x) { return /\d/.test(x); });
    var wi = []; seg.words.forEach(function (w, i) { if (/\d/.test(w.t)) wi.push(i); });
    if (!wi.length || pt.length !== wi.length) return;
    var changed = false;
    wi.forEach(function (i, k) {
      var w = seg.words[i], p = pt[k];
      if (p !== w.t && ASCII_TOK.test(p) && ASCII_TOK.test(w.t) && Math.abs(p.length - w.t.length) <= 1) { w.t = p; w.c = Math.max(w.c, pScore * 100); changed = true; }
    });
    if (changed) { seg.text = joinWords(seg.words); }
  }
  async function runPhoto(lang, onProg) {
    var prep = prepare(false), base = prep.canvas;
    var pd = await getPaddle('v6');
    setStatus(TXT.detecting); setBar(null); await tick();
    var bm = await createImageBitmap(base);
    var res = await pd.predict(bm, { textDetMaxSideLimit: +QS.get('ocrlimit') || 960, textDetBoxThresh: 0.5, textDetUnclipRatio: 1.7, textRecScoreThresh: 0 });
    var items = (res[0] && res[0].items || []).filter(function (it) { return it.poly && it.poly.length === 4; });
    if (!items.length) return { segs: [], canvas: base, shapes: [], skew: 0, engine: 'photo' };
    var angs = items.map(function (it) { var a = Math.atan2(it.poly[1][1] - it.poly[0][1], it.poly[1][0] - it.poly[0][0]); return a; });
    var gAng = median(angs), ca = Math.cos(-gAng), sa = Math.sin(-gAng), cx = base.width / 2, cy = base.height / 2;
    var n = Math.max(1, Math.min(3, (navigator.hardwareConcurrency || 4) - 1));
    var ws = await getTess(lang, 7, n);
    var crops = items.map(function (it) { return cropLine(base, it.poly); });
    var out = new Array(items.length), next = 0, done = 0;
    setStatus(TXT.lines + '…'); setBar(0);
    await Promise.all(ws.map(async function (w) {
      for (;;) {
        var i = next++; if (i >= crops.length) break;
        var r = (await w.recognize(crops[i], {}, { blocks: true })).data, lw = wordsOf(r);
        out[i] = trimJunk([].concat.apply([], lw));
        done++; setBar(done / crops.length); setStatus(TXT.lines + ' ' + done + '/' + crops.length); onProg && onProg(done / crops.length);
      }
    }));
    var segs = [], shapes = [];
    items.forEach(function (it, i) {
      var wl = out[i]; if (!wl || !wl.length) return;
      var rp = it.poly.map(function (q) { var x = q[0] - cx, y = q[1] - cy; return [x * ca - y * sa + cx, x * sa + y * ca + cy]; });
      var xs = rp.map(function (q) { return q[0]; }), ys = rp.map(function (q) { return q[1]; });
      var s = segFromWords(wl.map(function (w) { return { t: w.t, c: w.c, x0: 0, y0: 0, x1: 0, y1: 0 }; }));
      s.x0 = Math.min.apply(null, xs); s.x1 = Math.max.apply(null, xs); s.y0 = Math.min.apply(null, ys); s.y1 = Math.max.apply(null, ys);
      if (s.conf < 8 && s.text.length < 3) return;
      rescueDigits(s, it.text, it.score);
      segs.push(s); shapes.push({ pts: it.poly, conf: s.conf });
    });
    return { segs: segs, canvas: base, shapes: shapes, skew: gAng, engine: 'photo' };
  }

  // PP-OCR pipeline: detection + recognition in the worker. RTL (Arabic) output comes in visual order: flip it back to logical order.
  function fixRtl(t) {
    var r = t.split('').reverse().join('');
    return r.replace(/[0-9A-Za-z][0-9A-Za-z.,:%\/\-]*/g, function (m) { return m.split('').reverse().join(''); });
  }
  async function runPP(key, onProg) {
    var prep = prepare(false), base = prep.canvas;
    var pd = await getPaddle(key);
    setStatus(TXT.reading); setBar(null); await tick();
    var bm = await createImageBitmap(base);
    var res = await pd.predict(bm, { textDetMaxSideLimit: +QS.get('ocrlimit') || 1280, textDetBoxThresh: 0.5, textDetUnclipRatio: 1.7, textRecScoreThresh: 0 });
    onProg && onProg(1);
    var items = (res[0] && res[0].items || []).filter(function (it) { return it.poly && it.poly.length === 4 && it.text && it.text.trim(); });
    var eng = RECS[key].v === 6 ? 'pp6' : 'pp5';
    if (!items.length) return { segs: [], canvas: base, shapes: [], skew: 0, engine: eng, rec: key };
    var angs = items.map(function (it) { return Math.atan2(it.poly[1][1] - it.poly[0][1], it.poly[1][0] - it.poly[0][0]); });
    var gAng = median(angs), ca = Math.cos(-gAng), sa = Math.sin(-gAng), cx = base.width / 2, cy = base.height / 2;
    var segs = [], shapes = [];
    items.forEach(function (it) {
      var txt = key === 'ar' ? fixRtl(it.text.trim()) : it.text.trim();
      var c = it.score * 100;
      var rp = it.poly.map(function (q) { var x = q[0] - cx, y = q[1] - cy; return [x * ca - y * sa + cx, x * sa + y * ca + cy]; });
      var xs = rp.map(function (q) { return q[0]; }), ys = rp.map(function (q) { return q[1]; });
      var wl = txt.split(/\s+/).filter(Boolean).map(function (t) { return { t: t, c: c, x0: 0, y0: 0, x1: 0, y1: 0 }; });
      var sg = segFromWords(wl);
      sg.x0 = Math.min.apply(null, xs); sg.x1 = Math.max.apply(null, xs); sg.y0 = Math.min.apply(null, ys); sg.y1 = Math.max.apply(null, ys);
      segs.push(sg); shapes.push({ pts: it.poly, conf: c });
    });
    return { segs: segs, canvas: base, shapes: shapes, skew: gAng, engine: eng, rec: key };
  }
  function looksVietnamese(segs) {
    var t = segs.map(function (s) { return s.text; }).join(' '), m = t.match(VN_RE);
    return !!m && m.length >= 2 && (t.match(/[A-Za-z]/g) || []).length > 15;
  }

  // ------------------------------------------------------------------ layout reconstruction
  var BULLET = /^\s*([•●▪◦·*\-–—+]|\d{1,3}[.)]|[A-Za-zĐđ][.)]|\(\d{1,3}\)|[IVXivx]{1,4}[.)])\s+/;
  function nWords(s) { return s.words.length; }

  function findGutters(segs, h) {
    var minX = 1e9, maxX = -1e9;
    segs.forEach(function (s) { minX = Math.min(minX, s.x0); maxX = Math.max(maxX, s.x1); });
    var W = maxX - minX; if (W < h * 6) return [];
    var cov = new Int32Array(Math.ceil(W) + 2), narrow = 0;
    segs.forEach(function (s) {
      if (s.x1 - s.x0 > W * 0.62) return;
      narrow++;
      for (var x = Math.floor(s.x0 - minX); x <= Math.ceil(s.x1 - minX); x++) cov[x]++;
    });
    if (narrow < 6) return [];
    var g = [], start = -1, need = Math.max(1.4 * h, W * 0.02), i;
    for (i = 0; i < cov.length; i++) {
      if (cov[i] === 0) { if (start < 0) start = i; }
      else { if (start >= 0 && start > 0 && i - start >= need) g.push({ a: minX + start, b: minX + i }); start = -1; }
    }
    return g;
  }
  function buildRows(segs) {
    var sorted = segs.slice().sort(function (a, b) { return (a.y0 + a.y1) - (b.y0 + b.y1); }), rows = [];
    sorted.forEach(function (s) {
      var r = rows[rows.length - 1], cyS = (s.y0 + s.y1) / 2;
      if (r) {
        var ov = Math.min(r.y1, s.y1) - Math.max(r.y0, s.y0), mh = Math.min(r.y1 - r.y0, s.y1 - s.y0);
        if (ov > 0.5 * mh) { r.segs.push(s); r.y0 = Math.min(r.y0, s.y0); r.y1 = Math.max(r.y1, s.y1); return; }
      }
      rows.push({ segs: [s], y0: s.y0, y1: s.y1, cy: cyS });
    });
    rows.forEach(function (r) {
      r.segs.sort(function (a, b) { return a.x0 - b.x0; });
      r.cy = (r.y0 + r.y1) / 2; r.x0 = r.segs[0].x0; r.x1 = r.segs[r.segs.length - 1].x1;
    });
    return rows;
  }
  function rowWords(r) { return [].concat.apply([], r.segs.map(function (s) { return s.words; })); }
  function rowText(r) { return r.segs.map(function (s) { return s.text; }).join(' '); }

  function tryTable(rows, i, h) {
    var j = i; while (j < rows.length && rows[j].segs.length >= 2) j++;
    var run = rows.slice(i, j);
    if (run.length < 2) return null;
    var cells = []; run.forEach(function (r) { r.segs.forEach(function (s) { cells.push(s); }); });
    var avgW = cells.reduce(function (a, s) { return a + nWords(s); }, 0) / cells.length;
    var okRun = run.length >= 3 || (run.length === 2 && run[0].segs.length >= 3 && run[1].segs.length >= 3);
    if (!okRun || avgW > 6) return null;
    var sorted = cells.slice().sort(function (a, b) { return a.x0 - b.x0; }), cols = [];
    sorted.forEach(function (s) {
      var c = cols[cols.length - 1];
      if (c && s.x0 <= c.b + 0.3 * h) c.b = Math.max(c.b, s.x1); else cols.push({ a: s.x0, b: s.x1 });
    });
    if (cols.length < 2 || cols.length > 14) return null;
    var table = run.map(function (r) {
      var row = cols.map(function () { return []; });
      r.segs.forEach(function (s) {
        var mid = (s.x0 + s.x1) / 2, k = 0, best = 1e9;
        cols.forEach(function (c, ci) { var d = mid < c.a ? c.a - mid : mid > c.b ? mid - c.b : 0; if (d < best) { best = d; k = ci; } });
        row[k].push(s);
      });
      return row.map(function (cs) { return { text: cs.map(function (s) { return s.text; }).join(' '), words: [].concat.apply([], cs.map(function (s) { return s.words; })) }; });
    });
    return { block: { t: 'table', rows: table, cols: cols.length }, next: j };
  }

  function layoutColumn(segs, opts, h) {
    var rows = buildRows(segs), blocks = [], i = 0;
    var lines = [];
    function flushLines() { if (lines.length) { blocks = blocks.concat(parasFromLines(lines, h)); lines = []; } }
    while (i < rows.length) {
      if (opts.tables && rows[i].segs.length >= 2) {
        var tb = tryTable(rows, i, h);
        if (tb) { flushLines(); blocks.push(tb.block); i = tb.next; continue; }
      }
      var r = rows[i++];
      lines.push({ text: rowText(r), words: rowWords(r), x0: r.x0, x1: r.x1, y0: r.y0, y1: r.y1, cy: r.cy, h: r.y1 - r.y0, conf: r.segs.reduce(function (a, s) { return a + s.conf; }, 0) / r.segs.length });
    }
    flushLines();
    return blocks;
  }
  function parasFromLines(lines, h) {
    var tl = median(lines.map(function (l) { return l.x0; })), L = Math.min.apply(null, lines.map(function (l) { return l.x0; }));
    var xs = lines.map(function (l) { return l.x0; }).sort(num); tl = xs[Math.floor(xs.length * 0.15)];
    var xe = lines.map(function (l) { return l.x1; }).sort(num), tr = xe[Math.floor(xe.length * 0.85)] || xe[xe.length - 1];
    var tw = Math.max(1, tr - tl), pc = (tl + tr) / 2;
    var sp = []; for (var k = 1; k < lines.length; k++) sp.push(lines[k].cy - lines[k - 1].cy);
    var medSp = median(sp.filter(function (v) { return v > 0; })) || h * 1.4, medH = median(lines.map(function (l) { return l.h; })) || h;
    void L;
    function isHeading(l) {
      var letters = l.text.replace(/[^A-Za-zÀ-ỹĐđ]/g, ''), up = letters.replace(/[^A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ]/g, '');
      var centered = Math.abs((l.x0 + l.x1) / 2 - pc) < 0.1 * tw + 2 * h;
      if (l.h >= 1.3 * medH && l.words.length <= 16) return true;
      return letters.length >= 4 && up.length / letters.length >= 0.85 && l.words.length <= 14 && centered;
    }
    var blocks = [], cur = null;
    lines.forEach(function (l, idx) {
      var head = isHeading(l), bullet = BULLET.test(l.text) && !head;
      var join = false;
      if (cur && cur.t === 'p' && !head && !bullet) {
        var prev = cur.lines[cur.lines.length - 1];
        var gap = l.cy - prev.cy, full = prev.x1 >= tr - 0.12 * tw, indent = l.x0 - tl > 1.2 * h && Math.abs(l.x0 - prev.x0) > 1.2 * h;
        join = gap <= 1.5 * medSp && full && !indent && Math.abs(l.x0 - prev.x0) <= 2.5 * h;
      } else if (cur && cur.t === 'li' && !head && !bullet) {
        var pv = cur.lines[cur.lines.length - 1];
        var endsSentence = /[.!?…:;]\s*$/.test(pv.text), startsUpper = /^[A-ZÀ-ỸĐ]/.test(l.text);
        join = l.cy - pv.cy <= 1.5 * medSp && pv.x1 >= tr - 0.12 * tw && !(endsSentence && startsUpper);
      }
      if (join) { cur.lines.push(l); return; }
      cur = { t: head ? 'h' : bullet ? 'li' : 'p', lines: [l] };
      blocks.push(cur);
      void idx;
    });
    return blocks;
  }
  function layoutPage(segs, opts) {
    if (!segs.length) return [];
    var h = median(segs.map(function (s) { return s.y1 - s.y0; })) || 20, blocks = [];
    var gut = opts.tables ? findGutters(segs, h) : [];
    var avgW = segs.reduce(function (a, s) { return a + nWords(s); }, 0) / segs.length;
    if (gut.length && avgW >= 4.5) {
      var minX = Math.min.apply(null, segs.map(function (s) { return s.x0; })), maxX = Math.max.apply(null, segs.map(function (s) { return s.x1; }));
      var bounds = [minX].concat.apply([], gut.map(function (g) { return [g.a, g.b]; })).concat([maxX]);
      var ncol = gut.length + 1;
      var colOf = function (s) { var m = (s.x0 + s.x1) / 2, c = 0; gut.forEach(function (g, gi) { if (m >= g.b) c = gi + 1; }); return c; };
      var spans = function (s) { return gut.some(function (g) { return s.x0 < g.a && s.x1 > g.b; }); };
      void bounds;
      var sorted = segs.slice().sort(function (a, b) { return a.y0 - b.y0; }), band = [];
      var flushBand = function () {
        for (var c = 0; c < ncol; c++) {
          var cs = band.filter(function (s) { return colOf(s) === c; });
          if (cs.length) blocks = blocks.concat(layoutColumn(cs, opts, h));
        }
        band = [];
      };
      sorted.forEach(function (s) {
        if (spans(s)) { flushBand(); blocks = blocks.concat(layoutColumn([s], opts, h)); } else band.push(s);
      });
      flushBand();
      return blocks;
    }
    return layoutColumn(segs, opts, h);
  }

  // ------------------------------------------------------------------ output formats
  function runsHtml(words) {
    return joinWords(words, function (w) { return w.c < LOW_CONF ? '<mark class="lc" title="' + Math.round(w.c) + '%">' + esc(w.t) + '</mark>' : esc(w.t); });
  }
  function blockWords(b, keep) {
    if (keep) return b.lines.map(function (l) { return l.words; });
    return [[].concat.apply([], b.lines.map(function (l) { return l.words; }))];
  }
  function toHtml(blocks, keep) {
    var h = '', firstHead = true, inList = false;
    blocks.forEach(function (b) {
      if (b.t !== 'li' && inList) { h += '</ul>'; inList = false; }
      if (b.t === 'h') { var lv = firstHead ? 1 : 2; firstHead = false; h += '<h' + (lv + 1) + '>' + blockWords(b, false).map(runsHtml).join('') + '</h' + (lv + 1) + '>'; }
      else if (b.t === 'li') { if (!inList) { h += '<ul class="ocr-list">'; inList = true; } h += '<li>' + blockWords(b, keep).map(runsHtml).join('<br>') + '</li>'; }
      else if (b.t === 'p') h += '<p>' + blockWords(b, keep).map(runsHtml).join('<br>') + '</p>';
      else if (b.t === 'table') {
        h += '<div class="ocr-tw"><table class="spec ocr-table">';
        b.rows.forEach(function (r, ri) { h += '<tr>' + r.map(function (c) { return (ri === 0 ? '<th>' : '<td>') + runsHtml(c.words) + (ri === 0 ? '</th>' : '</td>'); }).join('') + '</tr>'; });
        h += '</table></div>';
      }
    });
    if (inList) h += '</ul>';
    return h;
  }
  function plainOf(b, keep) {
    if (keep) return b.lines.map(function (l) { return l.text; }).join('\n');
    return joinWords([].concat.apply([], b.lines.map(function (l) { return l.words; })));
  }
  function toMarkdown(blocks, keep) {
    var out = [], firstHead = true;
    blocks.forEach(function (b) {
      if (b.t === 'h') { out.push((firstHead ? '# ' : '## ') + plainOf(b, false)); firstHead = false; }
      else if (b.t === 'li') {
        var t = plainOf(b, keep), m = t.match(/^\s*(\d{1,3}[.)])\s+/);
        out.push(m ? t.replace(/^\s*(\d{1,3})[.)]\s+/, '$1. ') : '- ' + t.replace(BULLET, ''));
      } else if (b.t === 'p') out.push(plainOf(b, keep).replace(/\n/g, '  \n'));
      else if (b.t === 'table') {
        var rows = b.rows.map(function (r) { return '| ' + r.map(function (c) { return c.text.replace(/\|/g, '\\|'); }).join(' | ') + ' |'; });
        rows.splice(1, 0, '|' + b.rows[0].map(function () { return ' --- |'; }).join(''));
        out.push(rows.join('\n'));
      }
    });
    // keep consecutive list items tight
    var md = '';
    out.forEach(function (x, i) { var prevLi = i && /^(- |\d+\. )/.test(out[i - 1]), curLi = /^(- |\d+\. )/.test(x); md += (i ? (prevLi && curLi ? '\n' : '\n\n') : '') + x; });
    return md + '\n';
  }
  function toCsv(blocks) {
    var tabs = blocks.filter(function (b) { return b.t === 'table'; });
    if (!tabs.length) return '';
    var q = function (s) { return '"' + String(s).replace(/"/g, '""') + '"'; };
    return '\ufeff' + tabs.map(function (b) { return b.rows.map(function (r) { return r.map(function (c) { return q(c.text); }).join(','); }).join('\r\n'); }).join('\r\n\r\n') + '\r\n';
  }

  // ------------------------------------------------------------------ result UI
  function stats(segs) {
    var words = 0, tc = 0, tl = 0;
    segs.forEach(function (s) { s.words.forEach(function (w) { words++; tc += w.c * w.t.length; tl += w.t.length; }); });
    return { words: words, conf: tl ? tc / tl : 0 };
  }
  function quality(res) {
    var q = 0; res.segs.forEach(function (s) { s.words.forEach(function (w) { q += w.c * w.t.length; }); }); return q;
  }
  function drawOverlay(R) {
    var c = el.cv, src = R.canvas, sc = Math.min(1, 1100 / src.width);
    c.width = Math.round(src.width * sc); c.height = Math.round(src.height * sc);
    var x = c.getContext('2d'); x.drawImage(src, 0, 0, c.width, c.height);
    x.lineWidth = Math.max(1.5, 2 * Math.min(1, c.width / 900));
    R.shapes.forEach(function (s) {
      x.strokeStyle = s.conf >= 85 ? '#1f9d55' : s.conf >= LOW_CONF ? '#e0a100' : '#d62828';
      x.beginPath(); s.pts.forEach(function (p, i) { if (i) x.lineTo(p[0] * sc, p[1] * sc); else x.moveTo(p[0] * sc, p[1] * sc); }); x.closePath(); x.stroke();
    });
  }
  function showTab(name) {
    ['view', 'md', 'overlay', 'json'].forEach(function (k) {
      var pane = $('ocrPane-' + k); if (pane) pane.hidden = k !== name;
    });
    Array.prototype.forEach.call(el.tabs.querySelectorAll('button'), function (b) { b.setAttribute('aria-selected', b.dataset.t === name ? 'true' : 'false'); b.className = b.dataset.t === name ? 'on' : ''; });
  }
  var lastRes = null;
  function render(res, secs, extra) {
    lastRes = { res: res, secs: secs, extra: extra };
    var keep = el.keep.checked, opts = { tables: el.tables.checked };
    var blocks = layoutPage(res.segs, opts), st = stats(res.segs);
    el.view.innerHTML = toHtml(blocks, keep);
    var md = toMarkdown(blocks, keep);
    el.md.value = md;
    var csv = toCsv(blocks);
    var jsonObj = {
      engine: res.engine, language: el.lang.value, skewDegrees: Math.round(res.skew * 1800 / Math.PI) / 10,
      words: st.words, averageConfidence: Math.round(st.conf * 10) / 10,
      lines: res.segs.map(function (s) { return { text: s.text, confidence: Math.round(s.conf * 10) / 10, box: [Math.round(s.x0), Math.round(s.y0), Math.round(s.x1), Math.round(s.y1)] }; }),
      blocks: blocks.map(function (b) { return b.t === 'table' ? { type: 'table', rows: b.rows.map(function (r) { return r.map(function (c) { return c.text; }); }) } : { type: b.t, text: plainOf(b, false) }; })
    };
    el.json.textContent = JSON.stringify(jsonObj, null, 2);
    R = { blocks: blocks, md: md, csv: csv, json: el.json.textContent, canvas: res.canvas, shapes: res.shapes };
    drawOverlay(R);
    var nt = blocks.filter(function (b) { return b.t === 'table'; }).length;
    el.info.textContent = [
      ({ photo: TXT.engPhoto, doc: TXT.engDoc, pp6: TXT.engPP, pp5: TXT.engPP5 }[res.engine] || res.engine), res.segs.length + ' ' + TXT.linesN, st.words + ' ' + TXT.words,
      TXT.conf + ' ' + Math.round(st.conf) + '%', nt ? nt + ' ' + TXT.tableN : '',
      Math.abs(res.skew) >= 0.003 && res.engine === 'doc' ? TXT.skew + ' ' + Math.round(res.skew * 180 / Math.PI * 10) / 10 + '°' : '', secs.toFixed(1) + TXT.s, extra || ''
    ].filter(Boolean).join(' · ');
    el.dlCsv.hidden = !csv;
    el.stage.hidden = false;
    var emp = $('ocrEmpty'); if (emp) emp.hidden = true;
    return st;
  }

  // ------------------------------------------------------------------ orchestration
  // Vietnamese reader (Tesseract vie): Document / Photo / Auto, with auto-rotate
  async function runVi(mode) {
    var lang = 'vie', res, extra = '';
    if (mode === 'photo') return { res: await runPhoto(lang), extra: extra };
    res = await runDocument(lang);
    if (mode === 'auto') {
      var st = stats(res.segs), dig = 0, tot = 0;
      if (res.segs.length && st.conf < 70) {          // maybe sideways or upside down: try the other orientations
        setStatus(TXT.orient); await tick();
        var base = S.rot, best = res, bestQ = quality(res), bestRot = base;
        for (var k = 1; k <= 3; k++) {
          S.rot = (base + k) % 4;
          var rr = await runDocument(lang), qq = quality(rr);
          if (qq > bestQ * 1.3) { best = rr; bestQ = qq; bestRot = S.rot; }
        }
        S.rot = bestRot; res = best; st = stats(res.segs);
        if (bestRot !== base) { drawPrev(); extra = TXT.rotated; }
      }
      res.segs.forEach(function (s) { s.words.forEach(function (w) { tot++; if (/\d/.test(w.t)) dig++; }); });
      var digitHeavy = tot > 0 && dig / tot >= 0.15 && st.conf < 93;   // receipts, price lists: Paddle re-reads the digits
      if (st.conf < 70 || !res.segs.length || digitHeavy) {
        setStatus(TXT.autoRetry); await tick();
        var alt = await runPhoto(lang), sa = stats(alt.segs);
        if (alt.segs.length && (!res.segs.length || sa.conf > st.conf - (digitHeavy ? 2 : 0))) { res = alt; extra = 'auto'; }
      }
    }
    return { res: res, extra: extra };
  }
  // PP-OCR reader (PP-OCRv6 multilingual, or the PP-OCRv5 recogniser of one script) with auto-rotate
  async function runMulti(key) {
    var res = await runPP(key), extra = '';
    var st = stats(res.segs);
    if (!res.segs.length || st.conf < 70) {
      setStatus(TXT.orient); await tick();
      var base = S.rot, best = res, bestQ = quality(res), bestRot = base;
      for (var k = 1; k <= 3; k++) {
        S.rot = (base + k) % 4;
        var rr = await runPP(key), qq = quality(rr);
        if (qq > bestQ * 1.3) { best = rr; bestQ = qq; bestRot = S.rot; }
      }
      S.rot = bestRot; res = best;
      if (bestRot !== base) { drawPrev(); extra = TXT.rotated; }
    }
    return { res: res, extra: extra };
  }
  async function recognise() {
    if (!S || busy) return;
    busy = true; el.run.disabled = true;
    var t0 = performance.now(), lang = el.lang.value, mode = el.mode.value, hint = '';
    try {
      var out, res, extra = '';
      if (lang === 'vie') out = await runVi(mode);
      else {
        var key = RECS[lang] ? lang : 'v6';
        out = await runMulti(key);
        if (key === 'v6' && lang === 'auto') {
          if (looksVietnamese(out.res.segs)) { setStatus(TXT.vnFound); await tick(); out = await runVi(mode); out.extra = (out.extra ? out.extra + ' · ' : '') + 'vi'; }
          else if (stats(out.res.segs).conf < 65) hint = TXT.lowScript;
        }
      }
      res = out.res; extra = out.extra;
      setStatus(TXT.layout); setBar(null); await tick();
      if (!res.segs.length) { el.stage.hidden = true; var e2 = $('ocrEmpty'); if (e2) e2.hidden = false; setStatus(hint || TXT.empty, 'err'); return; }
      var st2 = render(res, (performance.now() - t0) / 1000, extra);
      showTab('view');
      setStatus(st2.conf < 65 ? (hint || TXT.lowConf) : TXT.done, st2.conf < 65 ? '' : 'ok'); setBar(null);
    } catch (e) {
      console.error(e); setStatus(TXT.err + ': ' + (e && e.message || e), 'err'); setBar(null);
    } finally { busy = false; el.run.disabled = false; }
  }
  function drawPrev() {
    var p = el.prev, bm = S.bitmap, sc = Math.min(1, 320 / Math.max(bm.width, bm.height));
    var swap = S.rot % 2 === 1, w = Math.round(bm.width * sc), h = Math.round(bm.height * sc);
    p.width = swap ? h : w; p.height = swap ? w : h;
    var x = p.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0, 0, p.width, p.height);
    x.translate(p.width / 2, p.height / 2); x.rotate(S.rot * Math.PI / 2); x.drawImage(bm, -w / 2, -h / 2, w, h);
    p.hidden = false;
  }
  async function handleFile(file, label) {
    if (!file) return;
    if (!/^image\//.test(file.type)) { setStatus(TXT.badType, 'err'); return; }
    if (file.size > 25 * 1048576) { setStatus(TXT.tooBig, 'err'); return; }
    try { S = { bitmap: await decode(file), name: label || file.name || 'image', rot: 0 }; }
    catch (e) { setStatus(TXT.decodeErr, 'err'); return; }
    el.run.disabled = false; el.rotL.disabled = el.rotR.disabled = false;
    drawPrev(); await recognise();
  }
  async function loadSample(url, name) {
    try { var r = await fetch(url); var b = await r.blob(); await handleFile(new File([b], name, { type: b.type || 'image/png' }), name); }
    catch (e) { setStatus(TXT.decodeErr, 'err'); }
  }
  function download(name, text, type) {
    var a = document.createElement('a'), u = URL.createObjectURL(new Blob([text], { type: type }));
    a.href = u; a.download = name; document.body.appendChild(a); a.click(); a.remove(); setTimeout(function () { URL.revokeObjectURL(u); }, 2000);
  }
  function baseName() { return ((S && S.name) || 'ocr').replace(/\.[^.]+$/, ''); }
  function curText() { return el.view.innerText.replace(/\n{3,}/g, '\n\n').trim() + '\n'; }

  // ------------------------------------------------------------------ events
  el.file.addEventListener('change', function () { handleFile(el.file.files[0]); el.file.value = ''; });
  ['dragenter', 'dragover'].forEach(function (ev) { el.drop.addEventListener(ev, function (e) { e.preventDefault(); el.drop.classList.add('over'); }); });
  ['dragleave', 'drop'].forEach(function (ev) { el.drop.addEventListener(ev, function (e) { e.preventDefault(); el.drop.classList.remove('over'); }); });
  el.drop.addEventListener('drop', function (e) { var f = e.dataTransfer && e.dataTransfer.files[0]; if (f) handleFile(f); });
  document.addEventListener('paste', function (e) {
    var items = (e.clipboardData && e.clipboardData.items) || [];
    for (var i = 0; i < items.length; i++) if (items[i].type.indexOf('image/') === 0) { handleFile(items[i].getAsFile(), 'clipboard.png'); break; }
  });
  el.sampleDoc.addEventListener('click', function () { loadSample('/assets/img/products/ocr-sample-doc.png', 'ocr-sample-doc.png'); });
  el.samplePhoto.addEventListener('click', function () { loadSample('/assets/img/products/ocr-sample-photo.jpg', 'ocr-sample-photo.jpg'); });
  el.run.addEventListener('click', recognise);
  function syncControls() {
    var l = el.lang.value;
    el.mode.disabled = !(l === 'auto' || l === 'vie');   // Document / Photo only matters for the Vietnamese reader
    el.view.dir = l === 'ar' ? 'rtl' : 'ltr';
  }
  el.lang.addEventListener('change', function () { syncControls(); if (S && !busy) recognise(); });
  el.mode.addEventListener('change', function () { if (S && !busy) recognise(); });
  syncControls();
  [el.keep, el.tables].forEach(function (c) { c.addEventListener('change', function () { if (R && S && !busy) rerender(); }); });
  function rerender() {
    // layout-only options: rebuild from the cached segments without running OCR again
    if (lastRes) render(lastRes.res, lastRes.secs, lastRes.extra);
  }
  el.rotL.addEventListener('click', function () { if (S && !busy) { S.rot = (S.rot + 3) % 4; drawPrev(); recognise(); } });
  el.rotR.addEventListener('click', function () { if (S && !busy) { S.rot = (S.rot + 1) % 4; drawPrev(); recognise(); } });
  el.reset.addEventListener('click', function () {
    S = null; R = null; lastRes = null; el.stage.hidden = true; el.prev.hidden = true; el.run.disabled = true; el.rotL.disabled = el.rotR.disabled = true;
    var emp = $('ocrEmpty'); if (emp) emp.hidden = false; setStatus(''); setBar(null);
  });
  el.tabs.addEventListener('click', function (e) { var b = e.target.closest('button'); if (b && b.dataset.t) showTab(b.dataset.t); });
  el.copy.addEventListener('click', function () {
    var active = el.tabs.querySelector('button.on'), t = active && active.dataset.t;
    var txt = t === 'md' ? el.md.value : t === 'json' ? el.json.textContent : curText();
    var done = function () { var o = el.copy.textContent; el.copy.textContent = TXT.copied; setTimeout(function () { el.copy.textContent = o; }, 1500); };
    (navigator.clipboard ? navigator.clipboard.writeText(txt) : Promise.reject()).then(done, function () {
      var ta = document.createElement('textarea'); ta.value = txt; document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); done(); } catch (e) { setStatus(TXT.copyFail, 'err'); } ta.remove();
    });
  });
  el.dlTxt.addEventListener('click', function () { download(baseName() + '.txt', curText(), 'text/plain;charset=utf-8'); });
  el.dlMd.addEventListener('click', function () { download(baseName() + '.md', el.md.value, 'text/markdown;charset=utf-8'); });
  el.dlJson.addEventListener('click', function () { download(baseName() + '.json', el.json.textContent, 'application/json'); });
  el.dlCsv.addEventListener('click', function () { if (R && R.csv) download(baseName() + '-tables.csv', R.csv, 'text/csv;charset=utf-8'); });
  window.addEventListener('pagehide', function () { killTess(); if (paddle) { try { paddle.inst.dispose(); } catch (e) { /* ignore */ } } });
  el.run.disabled = true; el.rotL.disabled = el.rotR.disabled = true;
  showTab('view');
  window.__ocrDebug = function () { return lastRes; };   // for automated tests
})();
