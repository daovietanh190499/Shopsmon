"""Static bilingual site generator for shopsmon.com (no dependencies).
Run: python _src/build.py
- Vietnamese (default) lives at the site root; English lives under /en/.
- Blog posts are stored as _src/content/<slug>.<lang>.html with placeholders @@EMAIL@@ and @@L@@ (language URL prefix).
"""
import html
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from news_data import NEWS, CATS  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONTENT = os.path.join(os.path.dirname(__file__), "content")
SITE = "https://shopsmon.com"
EMAIL = "agent.distributed.virtual@gmail.com"
TODAY = "2026-11-05"
LANGS = ("vi", "en")

PAGES = []  # canonical (vi) paths, each has an /en/ twin

NAV = [
    ("/", {"vi": "Trang chủ", "en": "Home"}),
    ("/services.html", {"vi": "Dịch vụ", "en": "Services"}),
    ("/portfolio.html", {"vi": "Portfolio", "en": "Portfolio"}),
    ("/blog/", {"vi": "Blog", "en": "Blog"}),
    ("/news/", {"vi": "Tin tức", "en": "News"}),
    ("/contact.html", {"vi": "Liên hệ", "en": "Contact"}),
]

# Blog post registry (newest first). Body: content/<slug>.<lang>.html
POSTS = [
    dict(slug="int8-quantization", date="2026-11-05", min=12, aff="iot",
         og="/assets/img/blog/int8-quantization-cover.png",
         tag={"vi": "IoT / AIoT", "en": "IoT / AIoT"},
         title={"vi": "Lượng tử hoá int8 cho edge AI: từ công thức đến sai số đo được",
                "en": "Int8 quantization for edge AI: from the formula to measured error"},
         summary={"vi": "Bộ lượng tử hoá affine, phép tính số nguyên của một tầng dense, và thí nghiệm trên 12 seed: int8 per-tensor và per-channel so với số thực, rồi hạ xuống 2 bit.",
                  "en": "The affine quantizer, the integer arithmetic of a dense layer, and a 12-seed experiment: per-tensor and per-channel int8 against floating point, then down to 2 bits."},
         seo_title={"vi": "Lượng tử hoá int8 cho edge AI: công thức và sai số đo được | Shopsmon",
                    "en": "Int8 quantization for edge AI: formula and measured error | Shopsmon"},
         seo_desc={"vi": "Dẫn xuất lượng tử hoá int8 (affine, per-channel), phép tính số nguyên và thí nghiệm NumPy 12 seed đo độ chính xác, SQNR và kích thước mô hình khi giảm số bit.",
                   "en": "Derivation of int8 quantization (affine, per-channel), the integer arithmetic and a 12-seed NumPy experiment measuring accuracy, SQNR and model size as bits are removed."}),
    dict(slug="gd-conditioning", date="2026-11-04", min=13, aff="ml-books",
         tag={"vi": "Khoa học dữ liệu", "en": "Data science"},
         title={"vi": "Gradient descent và số điều kiện: vì sao bình phương tối thiểu chạy chậm",
                "en": "Gradient descent and the condition number: why least squares gets slow"},
         summary={"vi": "Tốc độ hội tụ (κ−1)/(κ+1) dẫn xuất trong năm dòng, so sánh với conjugate gradient, và thí nghiệm cho thấy chuẩn hoá đặc trưng đổi hàng triệu vòng lặp thành bốn.",
                  "en": "The (κ−1)/(κ+1) convergence rate derived in five lines, a comparison with conjugate gradient, and an experiment where standardising features turns millions of iterations into four."},
         seo_title={"vi": "Gradient descent và số điều kiện: chuẩn hoá đặc trưng | Shopsmon",
                    "en": "Gradient descent and the condition number: why standardise features | Shopsmon"},
         seo_desc={"vi": "Dẫn xuất tốc độ hội tụ của gradient descent trên hàm bậc hai, so sánh với conjugate gradient và đo tác động của chuẩn hoá đặc trưng lên bài hồi quy, kèm code NumPy.",
                   "en": "Derivation of gradient descent's convergence rate on a quadratic, comparison with conjugate gradient and a measured effect of feature standardisation on a regression, with NumPy code."}),
    dict(slug="zhang-calibration", date="2026-11-04", min=15, aff="calib",
         tag={"vi": "Tái tạo 3D", "en": "3D reconstruction"},
         title={"vi": "Hiệu chuẩn camera bằng bàn cờ: phương pháp Zhang",
                "en": "Camera calibration from a chessboard: Zhang's method"},
         summary={"vi": "Một mẫu phẳng cho ra ma trận nội tại theo công thức đóng, vì sao cần ít nhất 3 góc nhìn, và thí nghiệm Monte-Carlo về nhiễu và số ảnh.",
                  "en": "How a planar pattern yields the intrinsic matrix in closed form, why at least three views are needed, and a Monte-Carlo experiment on noise and number of images."},
         seo_title={"vi": "Hiệu chuẩn camera Zhang: ma trận nội tại từ bàn cờ | Shopsmon",
                    "en": "Zhang camera calibration: intrinsic matrix from a chessboard | Shopsmon"},
         seo_desc={"vi": "Dẫn xuất phương pháp hiệu chuẩn camera của Zhang (homography, ràng buộc trên B, SVD, công thức đóng), kèm code NumPy và thí nghiệm về nhiễu và số góc nhìn.",
                   "en": "Derivation of Zhang's camera calibration (homography, constraints on B, SVD, closed form), with NumPy code and an experiment on noise and the number of views."}),
    dict(slug="eight-point-normalization", date="2026-11-04", min=14,
         tag={"vi": "Tái tạo 3D", "en": "3D reconstruction"},
         title={"vi": "Thuật toán 8 điểm và vì sao chuẩn hoá toạ độ lại quan trọng",
                "en": "The eight-point algorithm and why normalisation matters"},
         summary={"vi": "Ước lượng ma trận cơ bản bằng SVD, vì sao toạ độ pixel thô làm bài toán điều kiện kém, và thí nghiệm số về chuẩn hoá Hartley.",
                  "en": "Estimating the fundamental matrix with an SVD, why raw pixel coordinates make the problem ill-conditioned, and a numerical experiment on Hartley normalisation."},
         seo_title={"vi": "Thuật toán 8 điểm & chuẩn hoá Hartley: ma trận cơ bản | Shopsmon",
                    "en": "Eight-point algorithm & Hartley normalisation explained | Shopsmon"},
         seo_desc={"vi": "Dẫn xuất thuật toán 8 điểm ước lượng ma trận cơ bản, giải thích điều kiện số và chuẩn hoá Hartley, kèm code NumPy, hình minh hoạ và thí nghiệm tái lập được.",
                   "en": "Derivation of the eight-point algorithm for the fundamental matrix, conditioning and Hartley normalisation, with NumPy code, figures and a reproducible experiment."}),
    dict(slug="triangulation-dlt", date="2026-11-04", min=12,
         tag={"vi": "Tái tạo 3D", "en": "3D reconstruction"},
         title={"vi": "Tam giác hoá (triangulation): từ hai góc nhìn đến một điểm 3D",
                "en": "Triangulation: from two views to a 3D point"},
         summary={"vi": "Vì sao hai tia nhiễu không bao giờ cắt nhau, DLT giải bài toán bằng SVD ra sao, và thí nghiệm số về việc baseline quyết định độ chính xác.",
                  "en": "Why two noisy rays never intersect, how the Direct Linear Transform solves it with an SVD, and a numerical experiment on how camera baseline controls accuracy."},
         seo_title={"vi": "Tam giác hoá DLT: từ hai góc nhìn đến điểm 3D | Shopsmon",
                    "en": "Triangulation: from two views to a 3D point (DLT explained) | Shopsmon"},
         seo_desc={"vi": "Dẫn xuất tam giác hoá tuyến tính (DLT) cho hai góc nhìn, kèm code NumPy, hình minh hoạ và thí nghiệm cho thấy baseline quyết định độ chính xác 3D.",
                   "en": "Derivation of linear triangulation (DLT) for two views, with NumPy code, figures and an experiment showing how camera baseline controls 3D accuracy."}),
]


def pth(L, path):
    """URL path of page `path` (given as the Vietnamese/canonical path) in language L."""
    if L == "vi":
        return path
    return "/en" + path


def layout(L, path, title, desc, body, active="", og_image="/assets/img/og.png", extra_head="", extra_body="", register=True):
    t = lambda vi, en: vi if L == "vi" else en
    url = SITE + pth(L, path)
    other = "en" if L == "vi" else "vi"
    nav = "".join(
        f'<a href="{pth(L, h)}"{" class=active" if h == active else ""}>{lbl[L]}</a>' for h, lbl in NAV)
    lang_switch = (
        f'<span class="langsw" role="group" aria-label="Language">'
        + (f'<span>VI</span><a href="{pth("en", path)}" hreflang="en" lang="en" onclick="try{{localStorage.setItem(\'lang\',\'en\')}}catch(e){{}}">EN</a>' if L == "vi"
           else f'<a href="{pth("vi", path)}" hreflang="vi" lang="vi" onclick="try{{localStorage.setItem(\'lang\',\'vi\')}}catch(e){{}}">VI</a><span>EN</span>')
        + '</span>')
    theme_label = t("Đổi giao diện sáng/tối", "Toggle light/dark theme")
    html = f"""<!doctype html>
<html lang="{L}" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="vi" href="{SITE}{pth('vi', path)}">
<link rel="alternate" hreflang="en" href="{SITE}{pth('en', path)}">
<link rel="alternate" hreflang="x-default" href="{SITE}{pth('vi', path)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Shopsmon">
<meta property="og:locale" content="{t('vi_VN', 'en_US')}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}{og_image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<script>
(function(){{var d=document.documentElement;try{{var th=localStorage.getItem('theme');if(th==='dark'||th==='light')d.setAttribute('data-theme',th);
var pref=localStorage.getItem('lang');if(pref&&pref!==d.lang){{var a=document.querySelector('link[rel=alternate][hreflang='+pref+']');if(a){{location.replace(new URL(a.href).pathname+location.search+location.hash);}}}}}}catch(e){{}}}})();
</script>
<link rel="stylesheet" href="/assets/css/style.css">
{extra_head}
</head>
<body>
<header class="site"><div class="wrap">
<a class="logo" href="{pth(L, '/')}">shops<span>mon</span></a>
<div class="right"><nav>{nav}</nav>{lang_switch}<button type="button" class="ctrl" id="themeBtn" aria-label="{theme_label}" title="{theme_label}">&#9790;</button></div>
</div></header>
<main>
{body}
</main>
<footer class="site"><div class="wrap">
<div>&copy; 2026 Shopsmon &middot; {t('Freelance AI &amp; kỹ thuật 3D', 'Freelance AI &amp; 3D engineering')} &middot; <a href="{pth(L, '/privacy.html')}">{t('Chính sách bảo mật', 'Privacy Policy')}</a></div>
<div><a href="https://www.facebook.com/profile.php?id=61596328016181" rel="noopener" target="_blank">Facebook</a> &middot; <a href="mailto:{EMAIL}">{EMAIL}</a></div>
<div class="fine">{t('Một số liên kết sản phẩm có thể mang lại hoa hồng cho Shopsmon.', 'Some product links may earn Shopsmon a commission.')}</div>
</div></footer>
<script>
(function(){{var d=document.documentElement,b=document.getElementById('themeBtn');
function sync(){{b.innerHTML=d.getAttribute('data-theme')==='dark'?'&#9728;':'&#9790;';}}
sync();b.addEventListener('click',function(){{var n=d.getAttribute('data-theme')==='dark'?'light':'dark';d.setAttribute('data-theme',n);try{{localStorage.setItem('theme',n)}}catch(e){{}}sync();}});}})();
</script>
{extra_body}
</body>
</html>
"""
    out = os.path.join(ROOT, pth(L, path).lstrip("/"))
    if path.endswith("/"):
        out = os.path.join(out, "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    if register and L == "vi":
        PAGES.append((path, TODAY))


def cta_btns(L):
    t = lambda vi, en: vi if L == "vi" else en
    subj = t("Y%C3%AAu%20c%E1%BA%A7u%20d%E1%BB%B1%20%C3%A1n%20-%20Shopsmon", "Project%20inquiry%20-%20Shopsmon")
    return (f'<a class="btn primary" href="mailto:{EMAIL}?subject={subj}">{t("Nhận báo giá miễn phí", "Get a free quote")}</a>'
            f'<a class="btn ghost" href="{pth(L, "/portfolio.html")}">{t("Xem portfolio", "See portfolio")}</a>')


def post_cards(L, limit=None, tag_en=None):
    items = [p for p in POSTS if not tag_en or p["tag"]["en"] == tag_en]
    items = items[:limit] if limit else items
    out = ""
    for p in items:
        out += (f'<a class="card" href="{pth(L, "/blog/" + p["slug"] + ".html")}"><span class="tag">{p["tag"][L]} &middot; {p["date"]}</span>'
                f'<h3>{p["title"][L]}</h3><p>{p["summary"][L]}</p></a>')
    return out


import json  # noqa: E402
try:
    with open(os.path.join(os.path.dirname(__file__), "news_images.json"), encoding="utf-8") as _f:
        NEWS_IMG = json.load(_f)  # slug -> {credit, image_url}: lead image taken from the source article
except FileNotFoundError:
    NEWS_IMG = {}

# Shopee Affiliate links (owner's account; collected 2026-11-04, see states/affiliate.md). `price` is the listing price seen that day.
AFF = {
    "agent-combo": dict(link="https://s.shopee.vn/LoX19EmMH", price="₫249.000",
                        vi="Combo 2 sách: AI Agent thực chiến &amp; AI Agent ứng dụng", en="2-book combo (Vietnamese): AI Agent in practice &amp; Applied AI Agents"),
    "ml-systems": dict(link="https://s.shopee.vn/LoX0mfWy1", price="₫371.250",
                       vi="Thiết kế hệ thống học máy (Designing Machine Learning Systems, bản tiếng Việt)", en="Designing Machine Learning Systems (Vietnamese edition)"),
    "python-adv": dict(link="https://s.shopee.vn/8fTew5J4vr", price="₫289.000",
                       vi="Đường vào lập trình Python nâng cao", en="Advanced Python programming (Vietnamese book)"),
    "agent-book": dict(link="https://s.shopee.vn/7puXwtWBxq", price="₫179.000",
                       vi="Thiết lập cỗ máy xây kênh tự động 24/24 từ trợ lý AI và AI Agent", en="Setting up a 24/7 automated channel with AI assistants and AI agents (Vietnamese book)"),
    "esp32-ai": dict(link="https://s.shopee.vn/AUvJ7Ugukh", price="₫105.000",
                     vi="Bo mạch ESP32-S3 MINI Xiaozhi AI &ndash; robot thoại, màn hình OLED 0,96 inch", en="ESP32-S3 MINI Xiaozhi AI board &ndash; voice robot, 0.96&quot; OLED"),
    "esp32-n16r8": dict(link="https://s.shopee.vn/3B8iO1zd11", price="₫190.000",
                        vi="ESP32-S3 N16R8 Wi-Fi/Bluetooth 5.0, Flash 16 MB + PSRAM 8 MB (board AI/IoT)", en="ESP32-S3 N16R8 Wi-Fi/Bluetooth 5.0, 16 MB flash + 8 MB PSRAM (AI/IoT dev board)"),
    "sht40": dict(link="https://s.shopee.vn/4qGwN7QQYU", price="₫123.640",
                  vi="Mô-đun cảm biến nhiệt độ &amp; độ ẩm SHT40/SHT41/SHT45", en="SHT40/SHT41/SHT45 temperature &amp; humidity sensor module"),
    "lora": dict(link="https://s.shopee.vn/1W0UP1IIvG", price="₫322.300",
                 vi="Mô-đun LoRa SX1262 giao tiếp UART (DX-LR30)", en="LoRa SX1262 UART module (DX-LR30)"),
    "sonoff-zb": dict(link="https://s.shopee.vn/7fb7kNXg67", price="₫504.900",
                      vi="SONOFF ZB Bridge-P &ndash; cầu nối Zigbee 3.0 cho smart home", en="SONOFF ZB Bridge-P &ndash; Zigbee 3.0 smart-home bridge"),
    "data-strategy": dict(link="https://s.shopee.vn/3g4yyvPH69", price="₫169.100",
                          vi="Data Strategy &ndash; Chiến lược dữ liệu (sách tiếng Việt)", en="Data Strategy (Vietnamese edition)"),
    "webcam-fhd": dict(link="https://s.shopee.vn/8VAEjvGDOM", price="₫178.000",
                       vi="Webcam Full HD có mic cho PC/laptop", en="Full HD webcam with mic for PC/laptop"),
    "webcam-4k": dict(link="https://s.shopee.vn/40hpNfO0O7", price="₫164.000",
                      vi="Webcam 4K/2K có mic cho PC/laptop", en="4K/2K webcam with mic for PC/laptop"),
}

AFF_BOXES = {
    "agents": dict(
        title={"vi": "Đọc thêm: sách về agent LLM và hệ thống ML", "en": "Further reading: books on LLM agents and ML systems"},
        intro={"vi": "Sách tiếng Việt về agent LLM, Python và hệ thống học máy.",
               "en": "Vietnamese-language books on LLM agents, Python and machine-learning systems."},
        items=["agent-combo", "ml-systems", "python-adv", "agent-book"]),
    "iot": dict(
        title={"vi": "Linh kiện IoT / AIoT phổ biến", "en": "Common IoT / AIoT parts"},
        intro={"vi": "Board và cảm biến thường dùng để làm nguyên mẫu: ESP32-S3 chạy mô hình nhỏ, Zigbee và LoRa cho mạng cảm biến.",
               "en": "Boards and sensors commonly used for prototyping: ESP32-S3 for small models, Zigbee and LoRa for sensor networks."},
        items=["esp32-ai", "esp32-n16r8", "sht40", "lora", "sonoff-zb"]),
    "calib": dict(
        title={"vi": "Thiết bị để tự hiệu chuẩn camera", "en": "Hardware for calibrating your own camera"},
        intro={"vi": "Webcam USB và một bàn cờ in trên giấy phẳng là đủ để làm lại thí nghiệm trong bài. Nên cố định lấy nét khi chụp vì tiêu cự đổi theo lấy nét.",
               "en": "A USB webcam and a chessboard printed on flat paper are enough to repeat the experiment. Lock the focus while capturing, since focal length changes with focus."},
        items=["webcam-fhd", "webcam-4k"]),
    "ml-books": dict(
        title={"vi": "Sách để học tiếp", "en": "Further reading"},
        intro={"vi": "Sách tiếng Việt về Python, học máy và dữ liệu.",
               "en": "Vietnamese-language books on Python, machine learning and data."},
        items=["python-adv", "ml-systems", "data-strategy", "agent-combo"]),
}


def aff_box(L, key):
    t = lambda vi, en: vi if L == "vi" else en
    b = AFF_BOXES[key]
    lis = "".join(
        f'<li><a href="{AFF[i]["link"]}" rel="sponsored nofollow noopener" target="_blank">{AFF[i][L]}</a> '
        f'<span class="price">{AFF[i]["price"]}</span></li>' for i in b["items"])
    return (f'<aside class="aff-box"><h3>{b["title"][L]}</h3><p>{b["intro"][L]}</p><ul>{lis}</ul></aside>')


def sorted_news():
    return sorted(NEWS, key=lambda n: n["date"], reverse=True)


def news_url(L, n):
    return pth(L, "/news/" + n["slug"] + ".html")


def excerpt(text, limit=190):
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(",;:&") + "&hellip;"


def news_cards(L, limit=None, cat=None, featured_first=False):
    """Image cards linking to the article pages."""
    items = sorted_news()
    if cat:
        items = [n for n in items if n["cat"] == cat]
    if limit:
        items = items[:limit]
    t = lambda vi, en: vi if L == "vi" else en
    out = ""
    for n in items:
        out += (f'<a class="ncard" href="{news_url(L, n)}" data-cat="{n["cat"]}">'
                f'<img src="/assets/img/news/{n["slug"]}.jpg" width="1200" height="630" loading="lazy" alt="">'
                f'<div class="nbody"><span class="tag">{CATS[n["cat"]][L]} &middot; {n["date"]}</span>'
                f'<h3>{n["title"][L]}</h3><p>{excerpt(n["body"][L])}</p>'
                f'<span class="more">{t("Đọc tiếp", "Read more")} &rarr; <small>{n["src"]}</small></span></div></a>')
    return out


def news_article(L, n):
    t = lambda vi, en: vi if L == "vi" else en
    P = lambda x: pth(L, x)
    related = [m for m in sorted_news() if m["cat"] == n["cat"] and m["slug"] != n["slug"]][:3]
    if len(related) < 3:
        related += [m for m in sorted_news() if m["cat"] != n["cat"] and m["slug"] != n["slug"]][: 3 - len(related)]
    rel_html = "".join(
        f'<a class="ncard" href="{news_url(L, m)}"><img src="/assets/img/news/{m["slug"]}.jpg" width="1200" height="630" loading="lazy" alt="">'
        f'<div class="nbody"><span class="tag">{CATS[m["cat"]][L]} &middot; {m["date"]}</span><h3>{m["title"][L]}</h3></div></a>' for m in related)
    svc = {
        "ai": ("/solutions/llm-chatbot-agent.html", t("Cần chatbot hoặc agent LLM cho doanh nghiệp?", "Need an LLM chatbot or agent for your business?")),
        "iot": ("/solutions/custom-ai-tools.html", t("Cần công cụ AI / tự động hoá theo yêu cầu cho dự án IoT-AIoT?", "Need a custom AI / automation tool for an IoT-AIoT project?")),
        "cs": ("/solutions/custom-ai-tools.html", t("Cần công cụ AI theo yêu cầu?", "Need a custom AI tool?")),
        "hw": ("/solutions/custom-ai-tools.html", t("Cần công cụ AI theo yêu cầu?", "Need a custom AI tool?")),
        "mobile": ("/solutions/custom-ai-tools.html", t("Cần ứng dụng hoặc công cụ AI theo yêu cầu?", "Need a custom app or AI tool?")),
    }[n["cat"]]
    box = aff_box(L, n["aff"]) if n.get("aff") else ""
    cap = (f'<figcaption>{t("Ảnh", "Image")}: {NEWS_IMG[n["slug"]]["credit"]}</figcaption>' if n["slug"] in NEWS_IMG else "")
    art = f"""<article class="post newspost">
<p class="crumbs"><a href="{P('/news/')}">{t('Tin tức', 'News')}</a> &rsaquo; <a href="{P('/news/')}#{n['cat']}">{CATS[n['cat']][L]}</a></p>
<span class="tag cat-{n['cat']}">{CATS[n['cat']][L]}</span>
<h1>{n['title'][L]}</h1>
<p class="meta">{n['date']} &middot; {t('Nguồn', 'Source')}: <a href="{n['url']}" rel="noopener nofollow" target="_blank">{n['src']}</a></p>
<figure class="cover"><img src="/assets/img/news/{n['slug']}.jpg" width="1200" height="630" alt="{html.escape(html.unescape(n['title'][L]), quote=True)}">{cap}</figure>
<p class="standfirst">{n['body'][L]}</p>
<p class="srcline">{t('Nguồn', 'Source')}: <a href="{n['url']}" rel="noopener nofollow" target="_blank">{n['src']}</a></p>
{box}
<div class="cta-box"><h3 style="margin-top:0">{svc[1]}</h3><p>{t('Mô tả ngắn yêu cầu của bạn; bạn sẽ nhận câu hỏi làm rõ và đề xuất phạm vi trước khi bắt đầu.', 'Describe your need briefly; you will get clarifying questions and a scoped proposal before any work starts.')}</p>
<p><a class="btn primary" href="mailto:{EMAIL}?subject=Project%20inquiry%20-%20Shopsmon">{t('Gửi yêu cầu', 'Send a request')}</a> <a class="btn ghost" href="{P(svc[0])}">{t('Xem dịch vụ', 'See the service')}</a></p></div>
<h2>{t('Tin liên quan', 'Related news')}</h2>
<div class="newsgrid related">{rel_html}</div>
</article>"""
    layout(L, "/news/" + n["slug"] + ".html",
           f"{n['title'][L]} | Shopsmon",
           html.escape(html.unescape(excerpt(n["body"][L], 155)), quote=True),
           art, active="/news/", og_image=f"/assets/img/news/{n['slug']}.jpg")


# =============================================================== PAGES
def home(L):
    t = lambda vi, en: vi if L == "vi" else en
    P = lambda x: pth(L, x)
    body = f"""
<div class="hero"><div class="wrap">
<span class="pill">{t('Kỹ sư AI &amp; 3D freelance &middot; nhận dự án mới', 'Freelance AI &amp; 3D engineer &middot; available for new projects')}</span>
<h1>{t('Chatbot LLM, tái tạo 3D và công cụ AI theo yêu cầu &mdash; làm để dùng được ngay.', 'LLM chatbots, 3D reconstruction and custom AI tools &mdash; built to ship.')}</h1>
<p class="lead">{t('Shopsmon là studio kỹ thuật một người. Bạn mô tả vấn đề; tôi thiết kế, xây dựng và bàn giao phần mềm chạy được: agent LLM trả lời đúng câu hỏi thật, pipeline 3D biến ảnh thành hình học, và các công cụ AI gọn nhẹ cho quy trình của bạn.', 'Shopsmon is a one-person engineering studio. You describe the problem; I design, build and hand over working software: LLM agents that answer real questions, 3D pipelines that turn photos into geometry, and focused AI tools for your workflow.')}</p>
<div class="cta">{cta_btns(L)}</div>
</div></div>

<section><div class="wrap">
<h2>{t('Tôi làm gì', 'What I build')}</h2>
<p class="sub">{t('Ba dịch vụ tập trung. Mỗi dự án bắt đầu bằng một cuộc trao đổi ngắn để xác định phạm vi và báo giá cố định trước khi làm.', 'Three focused services. Each starts with a short scoping chat and a fixed-scope quote before any work begins.')}</p>
<div class="grid g3">
<div class="card"><span class="tag">LLM</span><h3>{t('Chatbot &amp; agent LLM', 'Chatbot &amp; agent development')}</h3><p>{t('Bot hỗ trợ khách hàng, trợ lý tri thức nội bộ và agent biết dùng công cụ, truy xuất trên chính tài liệu của bạn.', 'Support bots, internal knowledge assistants and tool-using agents with retrieval over your own documents.')}</p><a href="{P('/solutions/llm-chatbot-agent.html')}">{t('Tìm hiểu thêm', 'Learn more')} &rarr;</a></div>
<div class="card"><span class="tag">3D</span><h3>{t('Tái tạo 3D', '3D reconstruction')}</h3><p>{t('Hình học đa góc nhìn, pipeline kiểu photogrammetry, hiệu chuẩn camera và xử lý đám mây điểm bằng Python.', 'Multi-view geometry, photogrammetry-style pipelines, camera calibration and point-cloud processing in Python.')}</p><a href="{P('/solutions/3d-reconstruction.html')}">{t('Tìm hiểu thêm', 'Learn more')} &rarr;</a></div>
<div class="card"><span class="tag">Tools</span><h3>{t('Công cụ AI theo yêu cầu', 'Custom AI tools')}</h3><p>{t('Tự động hoá và ứng dụng nhỏ: trích xuất tài liệu, phân loại, làm sạch dữ liệu, dashboard &mdash; đo ni đóng giày theo quy trình của bạn.', 'Automations and small apps: document extraction, classification, data cleaning, dashboards &mdash; scoped to your workflow.')}</p><a href="{P('/solutions/custom-ai-tools.html')}">{t('Tìm hiểu thêm', 'Learn more')} &rarr;</a></div>
</div></div></section>

<section class="band"><div class="wrap">
<h2>{t('Một dự án diễn ra thế nào', 'How a project works')}</h2>
<p class="sub">{t('Đơn giản, minh bạch, ít rủi ro.', 'Simple, transparent, low-risk.')}</p>
<div class="grid g3 steps">
<div class="card"><h3>{t('Xác định phạm vi', 'Scope')}</h3><p>{t('Cho tôi biết mục tiêu, đầu vào, đầu ra và deadline. Tôi phản hồi bằng câu hỏi và đề xuất phạm vi cố định.', 'Tell me your goal, inputs, outputs and deadline. I reply with questions and a fixed-scope proposal.')}</p></div>
<div class="card"><h3>{t('Xây dựng &amp; demo', 'Build &amp; demo')}</h3><p>{t('Bạn thấy bản demo chạy được từ sớm để đánh giá hướng đi trước khi cam kết bản đầy đủ.', 'You see a working demo early, so you can judge the direction before committing to the full build.')}</p></div>
<div class="card"><h3>{t('Bàn giao', 'Deliver')}</h3><p>{t('Mã nguồn đầy đủ, tài liệu và buổi bàn giao. Thanh toán bằng hoá đơn PayPal.', 'Full source, documentation and a handover call. Payment via PayPal invoice.')}</p></div>
</div></div></section>

<section><div class="wrap">
<h2>{t('Đọc blog', 'Learn from the blog')}</h2>
<p class="sub">{t('Bài kỹ thuật về khoa học dữ liệu, AI, tái tạo 3D và khoa học máy tính &mdash; có công thức, hình minh hoạ và code chạy được.', 'Technical articles on data science, AI, 3D reconstruction and computer science &mdash; with equations, figures and code that runs.')}</p>
<div class="grid postlist">{post_cards(L, 3)}</div>
</div></section>

<section><div class="wrap">
<h2>{t('Tin công nghệ mới', 'Latest tech news')}</h2>
<p class="sub">{t('Điểm tin AI, LLM, chip, điện thoại&hellip; có dẫn nguồn.', 'AI, LLM, chip and smartphone headlines, with sources.')} <a href="{P('/news/')}">{t('Xem tất cả', 'See all')} &rarr;</a></p>
<div class="newsgrid">{news_cards(L, 3)}</div>
</div></section>

<section class="band"><div class="wrap" style="text-align:center">
<h2>{t('Bạn đang có dự án?', 'Have a project in mind?')}</h2>
<p class="sub" style="margin:0 auto 24px">{t('Gửi hai ba câu về điều bạn cần. Bạn sẽ nhận được phản hồi kèm câu hỏi làm rõ và đề xuất.', 'Send two or three sentences about what you need. You will get a reply with questions and a proposal.')}</p>
<div class="cta" style="justify-content:center;display:flex;gap:12px;flex-wrap:wrap">{cta_btns(L)}</div>
</div></section>
"""
    layout(L, "/",
           t("Shopsmon — Freelance chatbot LLM, tái tạo 3D & công cụ AI", "Shopsmon — Freelance LLM chatbots, 3D reconstruction & AI tools"),
           t("Kỹ sư freelance xây dựng chatbot agent LLM, pipeline tái tạo 3D và công cụ AI theo yêu cầu. Blog kỹ thuật về AI, khoa học dữ liệu và thị giác máy tính.",
             "Freelance engineer building LLM chatbot agents, 3D reconstruction pipelines and custom AI tools. Technical blog on AI, data science and computer vision."),
           body, active="/")


def services(L):
    t = lambda vi, en: vi if L == "vi" else en
    P = lambda x: pth(L, x)
    body = f"""
<div class="hero" style="padding:64px 0 32px"><div class="wrap">
<h1 style="font-size:clamp(30px,5vw,46px)">{t('Dịch vụ', 'Services')}</h1>
<p class="lead">{t('Những gì tôi có thể xây dựng cho bạn, bạn nhận được gì và tôi cần gì từ bạn.', 'What I can build for you, what you get, and what I need from you.')}</p>
</div></div>

<section id="llm"><div class="wrap">
<h2>{t('1. Chatbot &amp; agent LLM', '1. LLM chatbot &amp; agent development')}</h2>
<p class="sub">{t('Trợ lý hữu ích ngay từ ngày đầu và trung thực về những gì nó không biết.', 'Assistants that are useful on day one and honest about what they do not know.')}</p>
<div class="grid g2">
<div class="card"><h3>{t('Sản phẩm thường bàn giao', 'Typical deliverables')}</h3><ul>
<li>{t('Bot hỗ trợ khách hàng / FAQ cho web, Messenger hoặc Telegram', 'Customer-support or FAQ bot for web, Messenger or Telegram')}</li>
<li>{t('Trợ lý truy xuất (RAG) trên PDF, tài liệu hoặc wiki của bạn', 'Retrieval-augmented assistant over your PDFs, docs or wiki')}</li>
<li>{t('Agent dùng công cụ (gọi API, cơ sở dữ liệu, bảng tính của bạn)', 'Tool-using agent (calls your APIs, databases, spreadsheets)')}</li>
<li>{t('Bộ đánh giá và guardrail (từ chối, chuyển cho người thật)', 'Evaluation set and guardrails (refusals, escalation to a human)')}</li></ul></div>
<div class="card"><h3>{t('Tôi cần gì từ bạn', 'What I need from you')}</h3><ul>
<li>{t('Mục tiêu và người dùng đích', 'Goal and target users')}</li>
<li>{t('Câu hỏi mẫu và tài liệu bot cần biết', 'Sample questions and the documents the bot should know')}</li>
<li>{t('Mô hình/nhà cung cấp ưa thích và ràng buộc hosting', 'Preferred model/provider and hosting constraints')}</li>
<li>{t('Nơi bot sẽ hoạt động (website, ứng dụng chat, công cụ nội bộ)', 'Where the bot should live (site, chat app, internal tool)')}</li></ul></div>
</div>
<p style="margin-top:20px"><a href="{P('/solutions/llm-chatbot-agent.html')}">{t('Xem trang dịch vụ chatbot đầy đủ', 'Read the full chatbot service page')} &rarr;</a></p>
</div></section>

<section id="3d" class="band"><div class="wrap">
<h2>{t('2. Tái tạo 3D', '2. 3D reconstruction')}</h2>
<p class="sub">{t('Từ ảnh hoặc video đến hình học, bằng hình học đa góc nhìn cổ điển và công cụ hiện đại.', 'From images or video to geometry, using classical multi-view geometry and modern tooling.')}</p>
<div class="grid g2">
<div class="card"><h3>{t('Sản phẩm thường bàn giao', 'Typical deliverables')}</h3><ul>
<li>{t('Hiệu chuẩn camera và ước lượng tư thế', 'Camera calibration and pose estimation')}</li>
<li>{t('Pipeline structure-from-motion / tam giác hoá đa góc nhìn', 'Structure-from-motion / multi-view triangulation pipelines')}</li>
<li>{t('Làm sạch đám mây điểm, dựng mesh và script đo đạc', 'Point-cloud cleaning, meshing and measurement scripts')}</li>
<li>{t('Mã Python tái lập được kèm báo cáo kỹ thuật ngắn', 'Reproducible Python code with a short technical report')}</li></ul></div>
<div class="card"><h3>{t('Tôi cần gì từ bạn', 'What I need from you')}</h3><ul>
<li>{t('Ảnh hoặc video mẫu và kích thước vật thể/cảnh', 'Example images or video and the object/scene scale')}</li>
<li>{t('Độ chính xác yêu cầu và định dạng đầu ra (PLY, OBJ, CSV&hellip;)', 'Required accuracy and output format (PLY, OBJ, CSV&hellip;)')}</li>
<li>{t('Thông tin camera nếu có', 'Camera information if available')}</li>
<li>{t('Ràng buộc tính toán (laptop, server, GPU)', 'Compute constraints (laptop, server, GPU)')}</li></ul></div>
</div>
<p style="margin-top:20px"><a href="{P('/solutions/3d-reconstruction.html')}">{t('Xem trang dịch vụ tái tạo 3D đầy đủ', 'Read the full 3D reconstruction service page')} &rarr;</a></p>
<p style="margin-top:8px">{t('Muốn xem tôi giải thích nền tảng thế nào? Đọc', 'Want to see how I explain the fundamentals? Read')} <a href="{P('/blog/triangulation-dlt.html')}">{[x for x in POSTS if x['slug'] == 'triangulation-dlt'][0]['title'][L]}</a>.</p>
</div></section>

<section id="tools"><div class="wrap">
<h2>{t('3. Công cụ AI theo yêu cầu', '3. Custom AI tools')}</h2>
<p class="sub">{t('Phần mềm nhỏ, tập trung, loại bỏ một công việc lặp đi lặp lại.', 'Small, focused software that removes a repetitive task.')}</p>
<p><a href="{P('/solutions/custom-ai-tools.html')}">{t('Xem trang dịch vụ công cụ AI đầy đủ', 'Read the full custom AI tools page')} &rarr;</a></p>
<div class="grid g2">
<div class="card"><h3>{t('Ví dụ', 'Examples')}</h3><ul>
<li>{t('Trích xuất trường dữ liệu từ hoá đơn, biểu mẫu hoặc email vào bảng tính', 'Extract fields from invoices, forms or emails into a spreadsheet')}</li>
<li>{t('Phân loại hoặc gắn thẻ nội dung ở quy mô lớn', 'Classify or tag content at scale')}</li>
<li>{t('Script làm sạch dữ liệu và báo cáo kèm giao diện đơn giản', 'Data-cleaning and reporting scripts with a simple UI')}</li>
<li>{t('Dashboard và tự động hoá nội bộ', 'Internal dashboards and automations')}</li></ul></div>
<div class="card"><h3>{t('Cách tính giá', 'How pricing works')}</h3><p>{t('Mỗi dự án nhận báo giá theo phạm vi cố định sau một cuộc trao đổi ngắn. Bạn thanh toán bằng hoá đơn PayPal. Với dự án lớn hơn, bản demo đến trước để bạn đánh giá kết quả trước khi làm bản đầy đủ.', 'Every project gets a fixed-scope quote after a short scoping chat. You pay by PayPal invoice. For larger work, a demo comes first so you can judge the result before the full build.')}</p></div>
</div></div></section>

<section class="band"><div class="wrap" style="text-align:center"><h2>{t('Cùng xác định phạm vi dự án của bạn', 'Let&rsquo;s scope your project')}</h2>
<p class="sub" style="margin:0 auto 24px">{t('Phản hồi đầu tiên miễn phí, kèm câu hỏi và đề xuất.', 'Free first reply with questions and a proposal.')}</p>
<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">{cta_btns(L)}</div></div></section>
"""
    layout(L, "/services.html",
           t("Dịch vụ — chatbot LLM, tái tạo 3D, công cụ AI | Shopsmon", "Services — LLM chatbots, 3D reconstruction, custom AI tools | Shopsmon"),
           t("Dịch vụ freelance: phát triển chatbot và agent LLM, pipeline tái tạo 3D, công cụ AI theo yêu cầu. Báo giá phạm vi cố định, demo trước, bàn giao mã nguồn đầy đủ.",
             "Freelance services: LLM chatbot and agent development, 3D reconstruction pipelines, and custom AI tools. Fixed-scope quotes, demo first, full source delivered."),
           body, active="/services.html")


def portfolio(L):
    t = lambda vi, en: vi if L == "vi" else en
    P = lambda x: pth(L, x)
    body = f"""
<div class="hero" style="padding:64px 0 32px"><div class="wrap">
<h1 style="font-size:clamp(30px,5vw,46px)">Portfolio</h1>
<p class="lead">{t('Công việc kỹ thuật mở: mã nguồn, bài viết và thí nghiệm tái lập được.', 'Open technical work: source code, articles and reproducible experiments.')}</p>
</div></div>
<section><div class="wrap"><div class="grid g2">
<div class="card"><span class="tag">{t('Tái tạo 3D &middot; mã nguồn mở', '3D reconstruction &middot; open code')}</span><h3>{t('Thí nghiệm tam giác hoá hai góc nhìn (DLT)', 'Two-view triangulation (DLT) experiment')}</h3>
<p>{t('Bản cài đặt NumPy của tam giác hoá tuyến tính và phương pháp điểm giữa, cùng thí nghiệm tái lập được về ảnh hưởng của baseline camera đến độ chính xác 3D. Có kiểm tra tính đúng đắn với dữ liệu không nhiễu.', 'A NumPy implementation of linear triangulation and the midpoint method, with a reproducible experiment on how camera baseline affects 3D accuracy. Includes an exact noise-free sanity check.')}</p>
<p><a href="{P('/blog/triangulation-dlt.html')}">{t('Đọc bài viết', 'Read the article')}</a> &middot; <a href="/blog/code/triangulation_dlt.py">{t('Tải mã nguồn', 'Download the code')}</a></p></div>
<div class="card"><span class="tag">{t('Tái tạo 3D &middot; mã nguồn mở', '3D reconstruction &middot; open code')}</span><h3>{t('Hiệu chuẩn camera Zhang từ mẫu phẳng', 'Zhang camera calibration from a planar pattern')}</h3>
<p>{t('Cài đặt NumPy giai đoạn công thức đóng (homography, ràng buộc trên B, SVD) và thí nghiệm Monte-Carlo 3600 lần chạy về ảnh hưởng của nhiễu và số góc nhìn lên tiêu cự và điểm chính, kể cả tỉ lệ thất bại thực tế.', 'A NumPy implementation of the closed-form stage (homography, constraints on B, SVD) and a 3,600-run Monte-Carlo experiment on how noise and the number of views affect focal length and principal point, including the actual failure rate.')}</p>
<p><a href="{P('/blog/zhang-calibration.html')}">{t('Đọc bài viết', 'Read the article')}</a> &middot; <a href="/blog/code/zhang_calibration.py">{t('Tải mã nguồn', 'Download the code')}</a></p></div>
<div class="card"><span class="tag">{t('Tái tạo 3D &middot; mã nguồn mở', '3D reconstruction &middot; open code')}</span><h3>{t('Thuật toán 8 điểm: thô so với chuẩn hoá Hartley', 'Eight-point algorithm: raw vs. Hartley-normalised')}</h3>
<p>{t('Ước lượng ma trận cơ bản bằng SVD, kèm thí nghiệm tái lập được cho thấy chuẩn hoá giảm số điều kiện từ 4.6e5 xuống 18 và giảm sai số epipolar đáng kể khi có nhiễu.', 'Fundamental-matrix estimation with an SVD, plus a reproducible experiment showing that normalisation cuts the condition number from 4.6e5 to 18 and reduces epipolar error substantially under noise.')}</p>
<p><a href="{P('/blog/eight-point-normalization.html')}">{t('Đọc bài viết', 'Read the article')}</a> &middot; <a href="/blog/code/eight_point.py">{t('Tải mã nguồn', 'Download the code')}</a></p></div>
<div class="card"><span class="tag">{t('Khoa học dữ liệu &middot; mã nguồn mở', 'Data science &middot; open code')}</span><h3>{t('Gradient descent, số điều kiện và chuẩn hoá đặc trưng', 'Gradient descent, condition number and feature standardisation')}</h3>
<p>{t('So sánh gradient descent và conjugate gradient với chặn lý thuyết, và thí nghiệm hồi quy cho thấy chuẩn hoá đặc trưng giảm số điều kiện từ 3,0e5 xuống 1,09.', 'Gradient descent vs. conjugate gradient against the theoretical bounds, plus a regression experiment where standardising features cuts the condition number from 3.0e5 to 1.09.')}</p>
<p><a href="{P('/blog/gd-conditioning.html')}">{t('Đọc bài viết', 'Read the article')}</a> &middot; <a href="/blog/code/gd_conditioning.py">{t('Tải mã nguồn', 'Download the code')}</a></p></div>
<div class="card"><span class="tag">{t('LLM &middot; trang dịch vụ', 'LLM &middot; service page')}</span><h3>{t('Chatbot &amp; agent LLM', 'LLM chatbot &amp; agent development')}</h3>
<p>{t('Một dự án chatbot từ đầu đến cuối: xác định phạm vi, truy xuất trên tài liệu của bạn, đánh giá, triển khai và bàn giao.', 'What a chatbot project looks like end to end: scoping, retrieval over your documents, evaluation, deployment and handover.')}</p>
<p><a href="{P('/solutions/llm-chatbot-agent.html')}">{t('Xem trang dịch vụ', 'See the service page')}</a></p></div>
</div></div></section>
<section class="band"><div class="wrap" style="text-align:center"><h2>{t('Muốn là dự án tiêu biểu đầu tiên?', 'Want to be the first featured project?')}</h2>
<p class="sub" style="margin:0 auto 24px">{t('Khách hàng đầu tiên được tập trung phạm vi, quan tâm sát sao và mức giá hợp lý.', 'Early clients get a focused scope, close attention and a fair price.')}</p>
<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">{cta_btns(L)}</div></div></section>
"""
    layout(L, "/portfolio.html",
           t("Portfolio — công việc kỹ thuật mở | Shopsmon", "Portfolio — open technical work | Shopsmon"),
           t("Công việc kỹ thuật mở của Shopsmon: thí nghiệm tam giác hoá 3D kèm mã nguồn và tổng quan dịch vụ chatbot LLM.",
             "Open technical work from Shopsmon: 3D triangulation experiment with code, and LLM chatbot service overview."),
           body, active="/portfolio.html")


def landing(L):
    t = lambda vi, en: vi if L == "vi" else en
    body = f"""
<div class="hero"><div class="wrap">
<span class="pill">{t('Phát triển chatbot &amp; agent LLM', 'LLM chatbot &amp; agent development')}</span>
<h1>{t('Một chatbot thực sự trả lời được câu hỏi của khách hàng bạn.', 'A chatbot that actually answers your customers&rsquo; questions.')}</h1>
<p class="lead">{t('Tôi xây dựng trợ lý LLM dựa trên <em>chính</em> tài liệu và công cụ của bạn &mdash; kèm bộ đánh giá, guardrail hợp lý và bàn giao gọn gàng để bạn sở hữu kết quả.', 'I build LLM assistants grounded in <em>your</em> documents and tools &mdash; with an evaluation set, sensible guardrails and a clean handover so you own the result.')}</p>
<div class="cta">{cta_btns(L)}</div></div></div>

<section><div class="wrap"><h2>{t('Bạn nhận được gì', 'What you get')}</h2><p class="sub">{t('Một trợ lý chạy được, không phải một bộ slide.', 'A working assistant, not a slide deck.')}</p>
<div class="grid g3">
<div class="card"><h3>{t('Câu trả lời có căn cứ', 'Grounded answers')}</h3><p>{t('Truy xuất trên PDF, trang web hoặc cơ sở tri thức của bạn để câu trả lời đến từ nội dung của bạn, hiển thị nguồn khi cần.', 'Retrieval over your PDFs, web pages or knowledge base so answers come from your content, with sources shown where useful.')}</p></div>
<div class="card"><h3>{t('Dùng công cụ', 'Tool use')}</h3><p>{t('Agent có thể gọi API, truy vấn cơ sở dữ liệu hoặc cập nhật bảng tính khi câu hỏi cần dữ liệu thời gian thực.', 'The agent can call your APIs, query a database or update a spreadsheet when a question needs live data.')}</p></div>
<div class="card"><h3>{t('Guardrail &amp; chuyển tiếp', 'Guardrails &amp; escalation')}</h3><p>{t('Hành vi rõ ràng khi bot không chắc: nói thẳng và chuyển cho người thật thay vì đoán.', 'Clear behaviour when the bot is unsure: say so, and hand over to a human instead of guessing.')}</p></div>
<div class="card"><h3>{t('Bộ đánh giá', 'Evaluation set')}</h3><p>{t('Tập câu hỏi thật kèm đáp án mong đợi để đo chất lượng trước và sau mỗi thay đổi.', 'A set of real questions with expected answers so quality can be measured before and after every change.')}</p></div>
<div class="card"><h3>{t('Hoạt động ở đâu', 'Where it lives')}</h3><p>{t('Widget trên website, Facebook Messenger, Telegram hoặc công cụ nội bộ &mdash; tuỳ nơi người dùng của bạn đang dùng.', 'Website widget, Facebook Messenger, Telegram, or an internal tool &mdash; whichever your users already use.')}</p></div>
<div class="card"><h3>{t('Bàn giao đầy đủ', 'Full handover')}</h3><p>{t('Mã nguồn, ghi chú triển khai và buổi hướng dẫn. Không bị khoá nhà cung cấp.', 'Source code, deployment notes and a walkthrough call. No lock-in.')}</p></div>
</div></div></section>

<section class="band"><div class="wrap"><h2>{t('Quy trình', 'Process')}</h2><p class="sub">{t('Bốn bước, demo trước khi làm bản đầy đủ.', 'Four steps, demo before the full build.')}</p>
<div class="grid g3 steps">
<div class="card"><h3>{t('Trao đổi phạm vi', 'Scoping chat')}</h3><p>{t('Mục tiêu, người dùng, câu hỏi mẫu, tài liệu, ràng buộc, deadline.', 'Goal, users, sample questions, documents, constraints, deadline.')}</p></div>
<div class="card"><h3>{t('Báo giá cố định', 'Fixed-scope quote')}</h3><p>{t('Đề xuất bằng văn bản với sản phẩm bàn giao và tiến độ. Không có gì bắt đầu trước khi bạn đồng ý.', 'Written proposal with deliverables and timeline. Nothing starts before you agree.')}</p></div>
<div class="card"><h3>Demo</h3><p>{t('Một phiên bản chạy được có giới hạn để bạn thử với câu hỏi của riêng mình.', 'A limited working version so you can test it with your own questions.')}</p></div>
<div class="card"><h3>{t('Bàn giao cuối', 'Final delivery')}</h3><p>{t('Bản đầy đủ, tài liệu, bàn giao. Thanh toán bằng hoá đơn PayPal.', 'Full version, documentation, handover. Payment by PayPal invoice.')}</p></div>
</div></div></section>

<section><div class="wrap"><h2>{t('Phù hợp nếu&hellip;', 'Good fit if&hellip;')}</h2>
<div class="grid g2"><div class="card"><ul><li>{t('Bạn trả lời đi trả lời lại những câu hỏi giống nhau', 'You answer the same questions repeatedly')}</li><li>{t('Bạn có tài liệu hoặc FAQ để bot dựa vào', 'You have documents or FAQs the bot can rely on')}</li><li>{t('Bạn muốn thứ thiết thực trong vài tuần, không phải vài tháng', 'You want something practical in weeks, not months')}</li></ul></div>
<div class="card"><p>{t('Không phù hợp với: bot tư vấn y tế, pháp lý hoặc tài chính đòi hỏi độ chính xác được chứng nhận, hay các dự án cần kết quả được đảm bảo mà không hệ thống LLM nào có thể hứa.', 'Not a fit for: medical, legal or financial advice bots that require certified accuracy, or projects that need guaranteed outcomes that no LLM system can promise.')}</p></div></div></div></section>

<section class="band"><div class="wrap" style="text-align:center"><h2>{t('Hãy cho tôi biết bot của bạn cần làm gì', 'Tell me what your bot should do')}</h2>
<p class="sub" style="margin:0 auto 24px">{t('Hai ba câu là đủ để bắt đầu.', 'Two or three sentences are enough to start.')}</p>
<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">{cta_btns(L)}</div></div></section>
"""
    layout(L, "/solutions/llm-chatbot-agent.html",
           t("Phát triển chatbot & agent LLM cho doanh nghiệp | Shopsmon", "LLM chatbot & agent development for your business | Shopsmon"),
           t("Chatbot LLM và agent dùng công cụ dựa trên tài liệu của bạn, có đánh giá, guardrail và bàn giao mã nguồn đầy đủ. Demo trước, báo giá phạm vi cố định.",
             "Custom LLM chatbots and tool-using agents grounded in your documents, with evaluation, guardrails and full source handover. Demo first, fixed-scope quote."),
           body, active="/services.html")


def landing3d(L):
    t = lambda vi, en: vi if L == "vi" else en
    P = lambda x: pth(L, x)
    body = f"""
<div class="hero"><div class="wrap">
<span class="pill">{t('Dịch vụ tái tạo 3D', '3D reconstruction service')}</span>
<h1>{t('Từ ảnh và video đến hình học 3D đo được.', 'From photos and video to measurable 3D geometry.')}</h1>
<p class="lead">{t('Tôi xây dựng pipeline tái tạo 3D bằng Python: hiệu chuẩn camera, ước lượng tư thế, tam giác hoá, đám mây điểm và mesh &mdash; với báo cáo kỹ thuật rõ ràng về độ chính xác bạn có thể mong đợi.', 'I build 3D reconstruction pipelines in Python: camera calibration, pose estimation, triangulation, point clouds and meshes &mdash; with a clear technical report on the accuracy you can expect.')}</p>
<div class="cta">{cta_btns(L)}</div></div></div>

<section><div class="wrap"><h2>{t('Có thể làm gì', 'What it can do')}</h2><p class="sub">{t('Nền tảng là hình học đa góc nhìn cổ điển, được kiểm chứng bằng dữ liệu của bạn.', 'Built on classical multi-view geometry, validated on your own data.')}</p>
<div class="grid g3">
<div class="card"><h3>{t('Hiệu chuẩn camera', 'Camera calibration')}</h3><p>{t('Ước lượng tham số nội và méo ống kính từ ảnh bàn cờ hoặc từ chính dữ liệu của bạn, kèm sai số chiếu lại.', 'Estimate intrinsics and lens distortion from chessboard images or from your own data, with the reprojection error reported.')}</p></div>
<div class="card"><h3>{t('Hình học hai và nhiều góc nhìn', 'Two- and multi-view geometry')}</h3><p>{t('Ma trận cơ bản/cốt yếu, khôi phục tư thế camera, tam giác hoá và tinh chỉnh bằng bundle adjustment.', 'Fundamental/essential matrix, camera pose recovery, triangulation and bundle-adjustment refinement.')}</p></div>
<div class="card"><h3>{t('Đám mây điểm &amp; mesh', 'Point clouds &amp; meshes')}</h3><p>{t('Lọc nhiễu, căn chỉnh, dựng mesh và xuất PLY/OBJ/CSV để dùng trong công cụ của bạn.', 'Filtering, alignment, meshing and export to PLY/OBJ/CSV for use in your own tools.')}</p></div>
<div class="card"><h3>{t('Đo đạc', 'Measurement')}</h3><p>{t('Script đo khoảng cách, thể tích hoặc kích thước từ mô hình, kèm ước lượng độ bất định.', 'Scripts that measure distances, volumes or dimensions from the model, with an uncertainty estimate.')}</p></div>
<div class="card"><h3>{t('Báo cáo trung thực', 'Honest reporting')}</h3><p>{t('Tôi nói rõ điều gì đo được, điều gì không, và độ chính xác phụ thuộc vào baseline, độ phân giải và chất lượng ảnh thế nào.', 'I state what can and cannot be measured, and how accuracy depends on baseline, resolution and image quality.')}</p></div>
<div class="card"><h3>{t('Mã tái lập được', 'Reproducible code')}</h3><p>{t('Python sạch, có hướng dẫn chạy, để bạn tự chạy lại trên dữ liệu mới. Không bị khoá nhà cung cấp.', 'Clean Python with run instructions so you can re-run it on new data. No lock-in.')}</p></div>
</div></div></section>

<section class="band"><div class="wrap"><h2>{t('Hiểu cách tôi làm việc', 'See how I think')}</h2><p class="sub">{t('Các bài viết kỹ thuật, có công thức, hình và code chạy được, giải thích nền tảng đằng sau dịch vụ này.', 'Technical articles, with equations, figures and runnable code, explaining the fundamentals behind this service.')}</p>
<div class="grid postlist">{post_cards(L, tag_en="3D reconstruction")}</div></div></section>

<section><div class="wrap"><h2>{t('Tôi cần gì từ bạn', 'What I need from you')}</h2>
<div class="grid g2"><div class="card"><ul><li>{t('Ảnh hoặc video mẫu và kích thước vật thể/cảnh', 'Example images or video and the object/scene scale')}</li><li>{t('Độ chính xác yêu cầu và định dạng đầu ra', 'Required accuracy and output format')}</li><li>{t('Thông tin camera nếu có (model, tiêu cự, ảnh bàn cờ)', 'Camera information if available (model, focal length, chessboard images)')}</li></ul></div>
<div class="card"><p>{t('Không phù hợp với: các yêu cầu cần độ chính xác cấp trắc địa được chứng nhận, hoặc dữ liệu quá ít góc nhìn/quá mờ để tái tạo đáng tin cậy. Tôi sẽ nói thẳng điều này sau khi xem dữ liệu mẫu.', 'Not a fit for: requirements that need certified survey-grade accuracy, or data with too few views or too much blur for a reliable reconstruction. I will tell you so plainly after seeing sample data.')}</p></div></div></div></section>

<section class="band"><div class="wrap" style="text-align:center"><h2>{t('Gửi tôi vài ảnh mẫu', 'Send me a few sample photos')}</h2>
<p class="sub" style="margin:0 auto 24px">{t('Mô tả mục tiêu trong hai ba câu; tôi sẽ phản hồi với câu hỏi làm rõ và đề xuất phạm vi cố định.', 'Describe the goal in two or three sentences; I will reply with clarifying questions and a fixed-scope proposal.')}</p>
<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">{cta_btns(L)}</div></div></section>
"""
    layout(L, "/solutions/3d-reconstruction.html",
           t("Dịch vụ tái tạo 3D từ ảnh & video bằng Python | Shopsmon", "3D reconstruction from photos & video in Python | Shopsmon"),
           t("Pipeline tái tạo 3D tuỳ chỉnh: hiệu chuẩn camera, hình học đa góc nhìn, tam giác hoá, đám mây điểm và mesh, kèm báo cáo độ chính xác trung thực và mã nguồn tái lập được.",
             "Custom 3D reconstruction pipelines: camera calibration, multi-view geometry, triangulation, point clouds and meshes, with honest accuracy reporting and reproducible source code."),
           body, active="/services.html")


def landing_tools(L):
    t = lambda vi, en: vi if L == "vi" else en
    P = lambda x: pth(L, x)
    body = f"""
<div class="hero"><div class="wrap">
<span class="pill">{t('Công cụ AI theo yêu cầu', 'Custom AI tools')}</span>
<h1>{t('Một công cụ nhỏ, đúng việc, thay cho một công việc lặp đi lặp lại.', 'One small, focused tool that replaces one repetitive task.')}</h1>
<p class="lead">{t('Bạn có một quy trình tốn thời gian &mdash; đọc hoá đơn, phân loại phản hồi, làm sạch bảng dữ liệu, tổng hợp báo cáo? Tôi xây dựng công cụ AI gọn nhẹ, đo ni đóng giày cho quy trình đó, kèm cách đo xem nó có thật sự tiết kiệm thời gian không.', 'Have a time-consuming routine &mdash; reading invoices, sorting feedback, cleaning spreadsheets, compiling reports? I build lightweight AI tools tailored to that workflow, with a way to measure whether they really save time.')}</p>
<div class="cta">{cta_btns(L)}</div></div></div>

<section><div class="wrap"><h2>{t('Những loại công cụ tôi xây dựng', 'Kinds of tools I build')}</h2><p class="sub">{t('Các loại việc phù hợp.', 'The kinds of work that fit.')}</p>
<div class="grid g3">
<div class="card"><h3>{t('Trích xuất tài liệu', 'Document extraction')}</h3><p>{t('Đọc PDF, ảnh chụp hoá đơn, biểu mẫu hoặc email và đưa các trường cần thiết vào bảng tính/CSV, kèm cờ cảnh báo cho các dòng cần người kiểm tra.', 'Read PDFs, invoice photos, forms or emails and put the required fields into a spreadsheet/CSV, with flags on the rows a human should check.')}</p></div>
<div class="card"><h3>{t('Phân loại &amp; gắn thẻ', 'Classification &amp; tagging')}</h3><p>{t('Phân loại ticket, phản hồi khách hàng, đánh giá sản phẩm hoặc sản phẩm trong danh mục theo nhãn của riêng bạn, có thể kèm mức độ tin cậy.', 'Sort tickets, customer feedback, reviews or catalogue items into your own labels, optionally with a confidence score.')}</p></div>
<div class="card"><h3>{t('Làm sạch &amp; hợp nhất dữ liệu', 'Data cleaning &amp; merging')}</h3><p>{t('Chuẩn hoá tên, ngày, địa chỉ; phát hiện bản ghi trùng; hợp nhất nhiều nguồn. Mọi thay đổi được ghi log để đối chiếu.', 'Normalise names, dates and addresses; detect duplicate records; merge several sources. Every change is logged so it can be audited.')}</p></div>
<div class="card"><h3>{t('Báo cáo &amp; dashboard', 'Reports &amp; dashboards')}</h3><p>{t('Tự động tổng hợp số liệu định kỳ thành báo cáo hoặc dashboard web đơn giản, kèm phần tóm tắt bằng ngôn ngữ tự nhiên khi hữu ích.', 'Turn recurring numbers into a report or a simple web dashboard, with a natural-language summary where it helps.')}</p></div>
<div class="card"><h3>{t('Tự động hoá quy trình', 'Workflow automation')}</h3><p>{t('Nối các bước đang làm tay: đọc email, gọi API, cập nhật bảng tính, gửi thông báo &mdash; có bước xác nhận của con người ở chỗ rủi ro.', 'Connect steps you do by hand: read an email, call an API, update a sheet, send a notification &mdash; with a human approval step where it is risky.')}</p></div>
<div class="card"><h3>{t('Công cụ dòng lệnh / web nhỏ', 'Small CLI / web utilities')}</h3><p>{t('Một ứng dụng nhỏ chạy trên máy bạn hoặc một server rẻ, có hướng dẫn cài đặt và mã nguồn đầy đủ.', 'A small app that runs on your machine or a cheap server, with install instructions and full source.')}</p></div>
</div></div></section>

<section class="band"><div class="wrap"><h2>{t('Cách làm việc', 'How I work')}</h2><p class="sub">{t('Nhỏ gọn, đo được, không lock-in.', 'Small, measurable, no lock-in.')}</p>
<div class="grid g3 steps">
<div class="card"><h3>{t('Hiểu quy trình hiện tại', 'Understand the current routine')}</h3><p>{t('Bạn gửi 5&ndash;10 ví dụ thật (đã ẩn thông tin nhạy cảm) và mô tả đầu ra mong muốn.', 'You send 5&ndash;10 real examples (sensitive data removed) and describe the output you want.')}</p></div>
<div class="card"><h3>{t('Đặt tiêu chí nghiệm thu', 'Agree acceptance criteria')}</h3><p>{t('Chúng ta thống nhất cách đo: tỉ lệ đúng trên bộ ví dụ giữ lại, thời gian xử lý, số dòng cần người duyệt.', 'We agree how to measure: accuracy on held-out examples, processing time, number of rows that need review.')}</p></div>
<div class="card"><h3>{t('Demo rồi bàn giao', 'Demo, then deliver')}</h3><p>{t('Bạn thử bản demo trên dữ liệu của mình; sau khi đồng ý, bạn nhận mã nguồn, tài liệu và buổi hướng dẫn. Thanh toán bằng hoá đơn PayPal.', 'You try the demo on your own data; once you agree you get the source, documentation and a walkthrough. Payment by PayPal invoice.')}</p></div>
</div></div></section>

<section><div class="wrap"><h2>{t('Điều tôi nói thẳng từ đầu', 'What I will tell you up front')}</h2>
<div class="grid g2"><div class="card"><ul><li>{t('AI không đúng 100%: tôi đo độ chính xác trên ví dụ của bạn và thiết kế bước kiểm tra của con người.', 'AI is not 100% accurate: I measure accuracy on your examples and design the human-review step.')}</li><li>{t('Không phải việc nào cũng đáng để tự động hoá &mdash; nếu một script đơn giản là đủ, tôi sẽ nói vậy.', 'Not every task is worth automating &mdash; if a simple script is enough, I will say so.')}</li><li>{t('Dữ liệu của bạn chỉ dùng cho dự án; nếu cần gửi tới nhà cung cấp AI bên thứ ba, tôi sẽ báo trước (xem', 'Your data is used only for the project; if it must go to a third-party AI provider I will tell you first (see the')} <a href="{P('/privacy.html')}">{t('Chính sách bảo mật', 'Privacy Policy')}</a>{t(').', ').')}</li></ul></div>
<div class="card"><p>{t('Không phù hợp với: các hệ thống ra quyết định tự động về y tế, pháp lý, tín dụng hoặc việc làm mà không có con người giám sát; hoặc các dự án cần kết quả được đảm bảo.', 'Not a fit for: automated decisions on health, legal, credit or employment matters without human oversight, or projects that need guaranteed outcomes.')}</p>
<p>{t('Quan tâm đến phần kỹ thuật nền tảng? Đọc blog:', 'Curious about the engineering underneath? Read the blog:')} <a href="{P('/blog/')}">{t('các bài về AI, dữ liệu và 3D', 'articles on AI, data and 3D')}</a>.</p></div></div></div></section>

<section class="band"><div class="wrap" style="text-align:center"><h2>{t('Mô tả công việc bạn muốn bớt đi', 'Describe the task you want gone')}</h2>
<p class="sub" style="margin:0 auto 24px">{t('Hai ba câu là đủ để tôi phản hồi với câu hỏi và đề xuất phạm vi cố định.', 'Two or three sentences are enough for me to reply with questions and a fixed-scope proposal.')}</p>
<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">{cta_btns(L)}</div></div></section>
"""
    layout(L, "/solutions/custom-ai-tools.html",
           t("Công cụ AI theo yêu cầu: trích xuất, phân loại, tự động hoá | Shopsmon", "Custom AI tools: extraction, classification, automation | Shopsmon"),
           t("Xây dựng công cụ AI gọn nhẹ cho quy trình của bạn: trích xuất tài liệu, phân loại, làm sạch dữ liệu, báo cáo và tự động hoá. Đo độ chính xác trên dữ liệu của bạn, demo trước, bàn giao mã nguồn.",
             "Lightweight custom AI tools for your workflow: document extraction, classification, data cleaning, reporting and automation. Accuracy measured on your data, demo first, source handed over."),
           body, active="/services.html")


def contact(L):
    t = lambda vi, en: vi if L == "vi" else en
    subj = t("Y%C3%AAu%20c%E1%BA%A7u%20d%E1%BB%B1%20%C3%A1n%20-%20Shopsmon", "Project%20inquiry%20-%20Shopsmon")
    body = f"""
<div class="hero" style="padding:64px 0 32px"><div class="wrap">
<h1 style="font-size:clamp(30px,5vw,46px)">{t('Liên hệ', 'Contact')}</h1>
<p class="lead">{t('Hãy cho tôi biết bạn cần gì. Bạn sẽ nhận được phản hồi kèm câu hỏi làm rõ và, khi phù hợp, báo giá phạm vi cố định.', 'Tell me what you need. You will get a reply with clarifying questions and, where it makes sense, a fixed-scope quote.')}</p>
</div></div>
<section><div class="wrap"><div class="grid g2">
<div class="card"><h3>Email</h3><p><a href="mailto:{EMAIL}?subject={subj}">{EMAIL}</a></p>
<p>{t('Vui lòng nêu: mục tiêu, đầu vào và đầu ra mong muốn, deadline (nếu có) và ngân sách dự kiến.', 'Please include: your goal, what goes in and what should come out, any deadline, and your rough budget.')}</p></div>
<div class="card"><h3>Facebook Messenger</h3><p>{t('Bạn cũng có thể nhắn tin cho Facebook Page của Shopsmon. Thông tin chi tiết có trong các bài đăng của trang.', 'You can also message the Shopsmon Facebook Page. Details are shared in the page posts.')}</p></div>
</div>
<div class="card" style="margin-top:20px"><h3>{t('Điều gì xảy ra tiếp theo', 'What happens next')}</h3><ul><li>{t('Tôi phản hồi bằng các câu hỏi để làm rõ phạm vi.', 'I reply with questions to clarify the scope.')}</li><li>{t('Tôi gửi đề xuất bằng văn bản kèm giá và tiến độ.', 'I send a written proposal with price and timeline.')}</li><li>{t('Công việc bắt đầu sau khi bạn đồng ý. Thanh toán bằng hoá đơn PayPal.', 'Work starts after you agree. Payment is by PayPal invoice.')}</li></ul></div>
<p class="sub" style="margin-top:20px">{t('Thông tin bạn gửi được xử lý theo', 'Information you send is handled according to the')} <a href="{pth(L, '/privacy.html')}">{t('Chính sách bảo mật', 'Privacy Policy')}</a>.</p>
</div></section>
"""
    layout(L, "/contact.html",
           t("Liên hệ Shopsmon — bắt đầu dự án của bạn", "Contact Shopsmon — start your project"),
           t("Liên hệ Shopsmon để trao đổi về dự án chatbot LLM, tái tạo 3D hoặc công cụ AI.", "Contact Shopsmon to discuss an LLM chatbot, 3D reconstruction or custom AI tool project."),
           body, active="/contact.html")


def news_index(L):
    t = lambda vi, en: vi if L == "vi" else en
    items = sorted_news()
    top = items[0]
    rest = "".join(
        f'<a class="ncard" href="{news_url(L, n)}" data-cat="{n["cat"]}">'
        f'<img src="/assets/img/news/{n["slug"]}.jpg" width="1200" height="630" loading="lazy" alt="">'
        f'<div class="nbody"><span class="tag">{CATS[n["cat"]][L]} &middot; {n["date"]}</span>'
        f'<h3>{n["title"][L]}</h3><p>{excerpt(n["body"][L])}</p>'
        f'<span class="more">{t("Đọc tiếp", "Read more")} &rarr; <small>{n["src"]}</small></span></div></a>' for n in items[1:])
    feat = (f'<a class="featured" href="{news_url(L, top)}" data-cat="{top["cat"]}"><img src="/assets/img/news/{top["slug"]}.jpg" width="1200" height="630" alt="">'
            f'<div class="nbody"><span class="tag">{t("Nổi bật", "Top story")} &middot; {CATS[top["cat"]][L]} &middot; {top["date"]}</span>'
            f'<h2>{top["title"][L]}</h2><p>{excerpt(top["body"][L], 260)}</p><span class="more">{t("Đọc tiếp", "Read more")} &rarr; <small>{top["src"]}</small></span></div></a>')
    chips = (f'<button type="button" class="pill chip on" data-f="all">{t("Tất cả", "All")}</button> ' +
             "".join(f'<button type="button" class="pill chip" data-f="{k}">{v[L]}</button> ' for k, v in CATS.items()))
    body = f"""
<div class="hero" style="padding:56px 0 20px"><div class="wrap">
<h1 style="font-size:clamp(30px,5vw,46px)">{t('Tin tức công nghệ', 'Tech news')}</h1>
<p class="lead">{t('AI, LLM, IoT &amp; AIoT, hệ thống máy tính, khoa học máy tính &amp; dữ liệu, điện thoại thông minh.', 'AI, LLMs, IoT &amp; AIoT, computer systems, computer science &amp; data, and smartphones.')}</p>
<p class="meta">{t('Cập nhật', 'Updated')}: {TODAY}</p>
</div></div>
<section style="padding-top:20px"><div class="wrap">
{feat}
<div class="chips" role="group" aria-label="{t('Lọc theo chủ đề', 'Filter by topic')}">{chips}</div>
<div class="newsgrid" id="newsgrid">{rest}</div>
</div></section>
<script>
(function(){{var chips=document.querySelectorAll('.chip'),cards=document.querySelectorAll('#newsgrid .ncard'),feat=document.querySelector('.featured');
function apply(f){{chips.forEach(function(c){{c.classList.toggle('on',c.getAttribute('data-f')===f)}});
cards.forEach(function(c){{c.style.display=(f==='all'||c.getAttribute('data-cat')===f)?'':'none'}});
if(feat){{feat.style.display=(f==='all'||feat.getAttribute('data-cat')===f)?'':'none'}}}}
chips.forEach(function(c){{c.addEventListener('click',function(){{apply(c.getAttribute('data-f'));}})}});
var h=(location.hash||'').slice(1);if(h&&document.querySelector('.chip[data-f="'+h+'"]'))apply(h);}})();
</script>
"""
    layout(L, "/news/",
           t("Tin tức công nghệ: AI, LLM, IoT, chip, điện thoại | Shopsmon", "Tech news: AI, LLM, IoT, chips, smartphones | Shopsmon"),
           t("Điểm tin công nghệ mới nhất về AI, LLM, IoT/AIoT, hệ thống máy tính, khoa học máy tính, dữ liệu và điện thoại thông minh, kèm nguồn gốc và hình minh hoạ.",
             "Latest tech news on AI, LLMs, IoT/AIoT, computer systems, computer science, data and smartphones, with original sources and illustrations."),
           body, active="/news/", og_image=f"/assets/img/news/{top['slug']}.jpg")


def blog_index(L):
    t = lambda vi, en: vi if L == "vi" else en
    body = f"""
<div class="hero" style="padding:64px 0 24px"><div class="wrap">
<h1 style="font-size:clamp(30px,5vw,46px)">Blog</h1>
<p class="lead">{t('Khoa học dữ liệu, AI, tái tạo 3D và khoa học máy tính &mdash; được giải thích bằng công thức, hình minh hoạ và code chạy được.', 'Data science, AI, 3D reconstruction and computer science &mdash; explained with equations, figures and code that runs.')}</p>
</div></div>
<section><div class="wrap"><div class="grid postlist">{post_cards(L)}</div></div></section>
"""
    layout(L, "/blog/",
           t("Blog — AI, khoa học dữ liệu & tái tạo 3D | Shopsmon", "Blog — AI, data science & 3D reconstruction | Shopsmon"),
           t("Bài viết kỹ thuật về AI, khoa học dữ liệu, tái tạo 3D và khoa học máy tính, có công thức, hình minh hoạ và code chạy được.",
             "Technical articles on AI, data science, 3D reconstruction and computer science with equations, figures and runnable code."),
           body, active="/blog/")


KATEX_HEAD = """<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">"""
KATEX_BODY = """<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script>
window.addEventListener('load',function(){
  renderMathInElement(document.body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'\\\\(',right:'\\\\)',display:false}]});
  if(window.hljs){document.querySelectorAll('pre code').forEach(function(b){hljs.highlightElement(b)});}
});
</script>"""


def blog_post(L, p):
    with open(os.path.join(CONTENT, f"{p['slug']}.{L}.html"), encoding="utf-8") as f:
        art = f.read()
    art = art.replace("@@EMAIL@@", EMAIL).replace("@@L@@", "" if L == "vi" else "/en")
    if p.get("aff"):
        i = art.rfind("</article>")
        art = art[:i] + aff_box(L, p["aff"]) + art[i:]
    layout(L, "/blog/" + p["slug"] + ".html", p["seo_title"][L], p["seo_desc"][L], art,
           active="/blog/", og_image=p.get("og") or (f"/assets/img/blog/{p['slug']}-cover.png" if os.path.exists(os.path.join(ROOT, "assets", "img", "blog", p["slug"] + "-cover.png")) else "/assets/img/og.png"), extra_head=KATEX_HEAD, extra_body=KATEX_BODY)


# ---------------------------------------------------------------- PRIVACY POLICY
def privacy(L):
    t = lambda vi, en: vi if L == "vi" else en
    if L == "vi":
        art = f"""<article class="post">
<h1>Chính sách bảo mật</h1>
<p class="meta">Cập nhật lần cuối: {TODAY}</p>
<p>Chính sách này giải thích Shopsmon (<a href="https://shopsmon.com">shopsmon.com</a>, một dịch vụ freelance cá nhân về chatbot LLM, tái tạo 3D và công cụ AI) thu thập, sử dụng và bảo vệ thông tin của bạn như thế nào khi bạn truy cập website hoặc liên hệ để thuê dịch vụ.</p>

<h2>1. Thông tin chúng tôi thu thập</h2>
<ul>
<li><strong>Thông tin bạn chủ động gửi</strong> qua email hoặc Facebook Messenger: tên, địa chỉ email, mô tả dự án, tệp hoặc dữ liệu bạn chia sẻ để đánh giá yêu cầu.</li>
<li><strong>Thông tin thanh toán:</strong> khi bạn thanh toán, giao dịch được xử lý bởi PayPal. Chúng tôi nhận thông tin giao dịch từ PayPal (tên, email, số tiền, mã giao dịch) nhưng <strong>không bao giờ nhìn thấy số thẻ hay thông tin đăng nhập PayPal của bạn</strong>.</li>
<li><strong>Dữ liệu kỹ thuật:</strong> website là trang tĩnh chạy trên GitHub Pages. Nhà cung cấp hosting có thể ghi nhận địa chỉ IP và thông tin yêu cầu theo chính sách riêng của họ. Chúng tôi không tự vận hành hệ thống phân tích hay theo dõi.</li>
<li><strong>Lưu trữ trên trình duyệt:</strong> website dùng <code>localStorage</code> của trình duyệt chỉ để ghi nhớ lựa chọn ngôn ngữ và giao diện sáng/tối của bạn. Dữ liệu này nằm trên thiết bị của bạn, không được gửi cho chúng tôi. Website không đặt cookie quảng cáo hay cookie theo dõi.</li>
</ul>

<h2>2. Dịch vụ của bên thứ ba</h2>
<ul>
<li><strong>GitHub Pages</strong> (lưu trữ website).</li>
<li><strong>jsDelivr và cdnjs (Cloudflare)</strong>: các trang blog tải thư viện hiển thị công thức (KaTeX) và tô màu code (highlight.js) từ các CDN này; khi đó CDN nhận địa chỉ IP và thông tin trình duyệt của bạn.</li>
<li><strong>Google (Gmail)</strong>: trao đổi qua email.</li>
<li><strong>Meta (Facebook, Messenger)</strong>: nếu bạn tương tác với Facebook Page của Shopsmon, Meta xử lý dữ liệu theo chính sách của Meta.</li>
<li><strong>Shopee (liên kết affiliate)</strong>: một số trang có liên kết tiếp thị liên kết (affiliate) tới Shopee Việt Nam. Khi bạn bấm vào, Shopee và chương trình Shopee Affiliate có thể đặt cookie và ghi nhận lượt giới thiệu theo chính sách của họ; Shopsmon không nhận được thông tin cá nhân của bạn từ việc này và có thể nhận hoa hồng nếu bạn mua hàng.</li>
<li><strong>PayPal</strong>: thanh toán và hoá đơn.</li>
</ul>
<p>Mỗi bên có chính sách bảo mật riêng; chúng tôi khuyến khích bạn đọc chúng. Chúng tôi không bán hay cho thuê thông tin cá nhân của bạn.</p>

<h2>3. Mục đích sử dụng</h2>
<ul>
<li>Trả lời yêu cầu, báo giá và trao đổi về dự án.</li>
<li>Thực hiện và bàn giao dự án bạn đã đồng ý, xuất hoá đơn và nhận thanh toán.</li>
<li>Đáp ứng nghĩa vụ kế toán, pháp lý và bảo vệ quyền lợi hợp pháp.</li>
<li>Cải thiện nội dung website (không dựa trên theo dõi cá nhân).</li>
</ul>
<p>Cơ sở xử lý: sự đồng ý của bạn khi bạn chủ động liên hệ, việc thực hiện hợp đồng/dịch vụ bạn yêu cầu, và lợi ích hợp pháp trong việc vận hành dịch vụ.</p>

<h2>4. Dữ liệu dự án và AI</h2>
<p>Dữ liệu bạn cung cấp cho một dự án chỉ được dùng để thực hiện dự án đó. Nếu việc thực hiện đòi hỏi gửi dữ liệu của bạn tới một nhà cung cấp AI bên thứ ba, chúng tôi sẽ thông báo cho bạn trước khi làm. Vui lòng không gửi dữ liệu nhạy cảm (ví dụ thông tin y tế, mật khẩu, khoá API) nếu chưa thoả thuận cách xử lý.</p>

<h2>5. Thời gian lưu trữ</h2>
<p>Thư từ và dữ liệu dự án được lưu trong thời gian cần thiết để thực hiện dự án, hỗ trợ sau bàn giao và đáp ứng nghĩa vụ kế toán/pháp lý. Bạn có thể yêu cầu xoá dữ liệu bất cứ lúc nào (trừ phần chúng tôi buộc phải giữ theo quy định).</p>

<h2>6. Bảo mật</h2>
<p>Chúng tôi áp dụng các biện pháp hợp lý để bảo vệ thông tin (tài khoản có xác thực, không chia sẻ thông tin đăng nhập, chỉ truy cập dữ liệu khi cần). Tuy nhiên không có hệ thống truyền tải hay lưu trữ nào an toàn tuyệt đối.</p>

<h2>7. Quyền của bạn</h2>
<p>Bạn có quyền yêu cầu truy cập, chỉnh sửa, xoá dữ liệu cá nhân của mình, rút lại sự đồng ý hoặc phản đối việc xử lý, trong phạm vi pháp luật áp dụng cho bạn. Hãy liên hệ qua email bên dưới.</p>

<h2>8. Trẻ em</h2>
<p>Dịch vụ hướng tới doanh nghiệp và người trưởng thành, không dành cho trẻ em dưới 16 tuổi.</p>

<h2>9. Thay đổi chính sách</h2>
<p>Chúng tôi có thể cập nhật chính sách này; ngày cập nhật được ghi ở đầu trang. Việc tiếp tục sử dụng website sau khi cập nhật nghĩa là bạn chấp nhận phiên bản mới.</p>

<h2>10. Liên hệ</h2>
<p>Mọi câu hỏi hoặc yêu cầu về dữ liệu cá nhân: <a href="mailto:{EMAIL}?subject=Privacy">{EMAIL}</a>.</p>
</article>"""
    else:
        art = f"""<article class="post">
<h1>Privacy Policy</h1>
<p class="meta">Last updated: {TODAY}</p>
<p>This policy explains how Shopsmon (<a href="https://shopsmon.com">shopsmon.com</a>, an individual freelance service for LLM chatbots, 3D reconstruction and custom AI tools) collects, uses and protects your information when you visit the website or contact me about a project.</p>

<h2>1. Information we collect</h2>
<ul>
<li><strong>Information you send voluntarily</strong> by email or Facebook Messenger: name, email address, project description, and any files or data you share so a request can be evaluated.</li>
<li><strong>Payment information:</strong> payments are processed by PayPal. We receive transaction details from PayPal (name, email, amount, transaction ID) but <strong>never see your card number or PayPal login credentials</strong>.</li>
<li><strong>Technical data:</strong> the website is static and hosted on GitHub Pages. The hosting provider may log IP addresses and request details under its own policy. We do not run our own analytics or tracking.</li>
<li><strong>Browser storage:</strong> the website uses the browser&rsquo;s <code>localStorage</code> only to remember your language and light/dark theme choice. This stays on your device and is not sent to us. The site sets no advertising or tracking cookies.</li>
</ul>

<h2>2. Third-party services</h2>
<ul>
<li><strong>GitHub Pages</strong> (website hosting).</li>
<li><strong>jsDelivr and cdnjs (Cloudflare)</strong>: blog pages load the math rendering library (KaTeX) and the code highlighter (highlight.js) from these CDNs, which then receive your IP address and browser details.</li>
<li><strong>Google (Gmail)</strong>: email correspondence.</li>
<li><strong>Meta (Facebook, Messenger)</strong>: if you interact with the Shopsmon Facebook Page, Meta processes your data under its own policy.</li>
<li><strong>Shopee (affiliate links)</strong>: some pages contain affiliate links to Shopee Vietnam. When you click one, Shopee and its affiliate programme may set cookies and record the referral under their own policies; Shopsmon receives no personal information from this and may earn a commission if you buy.</li>
<li><strong>PayPal</strong>: payments and invoices.</li>
</ul>
<p>Each of these has its own privacy policy, which we encourage you to read. We do not sell or rent your personal information.</p>

<h2>3. How we use information</h2>
<ul>
<li>To answer enquiries, prepare quotes and discuss projects.</li>
<li>To carry out and deliver projects you agreed to, issue invoices and receive payment.</li>
<li>To meet accounting and legal obligations and protect legitimate interests.</li>
<li>To improve website content (not based on individual tracking).</li>
</ul>
<p>Legal bases: your consent when you contact us, performance of the service you request, and our legitimate interest in operating the service.</p>

<h2>4. Project data and AI</h2>
<p>Data you provide for a project is used only to carry out that project. If doing the work requires sending your data to a third-party AI provider, I will tell you before doing so. Please do not send sensitive data (for example medical information, passwords, API keys) unless we have agreed how it will be handled.</p>

<h2>5. Retention</h2>
<p>Correspondence and project data are kept as long as needed to deliver the project, provide post-delivery support and meet accounting or legal obligations. You can ask for deletion at any time (except for data we are legally required to keep).</p>

<h2>6. Security</h2>
<p>We take reasonable measures to protect information (authenticated accounts, no sharing of credentials, access to data only when needed). No method of transmission or storage is completely secure, however.</p>

<h2>7. Your rights</h2>
<p>Subject to the law that applies to you, you may request access to, correction or deletion of your personal data, withdraw consent, or object to processing. Contact us at the email below.</p>

<h2>8. Children</h2>
<p>The service is aimed at businesses and adults and is not intended for children under 16.</p>

<h2>9. Changes to this policy</h2>
<p>We may update this policy; the date at the top shows the latest revision. Continued use of the website after an update means you accept the new version.</p>

<h2>10. Contact</h2>
<p>Questions or requests about personal data: <a href="mailto:{EMAIL}?subject=Privacy">{EMAIL}</a>.</p>
</article>"""
    layout(L, "/privacy.html",
           t("Chính sách bảo mật | Shopsmon", "Privacy Policy | Shopsmon"),
           t("Chính sách bảo mật của Shopsmon: thông tin thu thập, dịch vụ bên thứ ba, lưu trữ trên trình duyệt và quyền của bạn.",
             "Shopsmon privacy policy: what information is collected, third-party services, browser storage and your rights."),
           art)


# =============================================================== BUILD
import make_covers  # noqa: E402
make_covers.main()  # draws any missing news cover (deterministic per slug)

for L in LANGS:
    home(L)
    services(L)
    portfolio(L)
    landing(L)
    landing3d(L)
    landing_tools(L)
    contact(L)
    blog_index(L)
    news_index(L)
    for n in NEWS:
        news_article(L, n)
    privacy(L)
    for p in POSTS:
        blog_post(L, p)

with open(os.path.join(ROOT, "404.html"), "w", encoding="utf-8", newline="\n") as f:
    f.write("""<!doctype html><html lang="vi" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>404 | Shopsmon</title><script>try{var t=localStorage.getItem('theme');if(t==='dark')document.documentElement.setAttribute('data-theme','dark')}catch(e){}</script><link rel="stylesheet" href="/assets/css/style.css"></head><body><div class="wrap" style="padding:120px 20px;text-align:center"><h1>404 &mdash; Không tìm thấy trang / Page not found</h1><p><a class="btn primary" href="/">Về trang chủ</a> <a class="btn ghost" href="/en/">Back to home (EN)</a></p></div></body></html>""")

with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8", newline="\n") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n')
    for p, d in PAGES:
        for L in LANGS:
            f.write(f'  <url><loc>{SITE}{pth(L, p)}</loc><lastmod>{d}</lastmod>'
                    f'<xhtml:link rel="alternate" hreflang="vi" href="{SITE}{pth("vi", p)}"/>'
                    f'<xhtml:link rel="alternate" hreflang="en" href="{SITE}{pth("en", p)}"/></url>\n')
    f.write("</urlset>\n")
with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8", newline="\n") as f:
    f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
open(os.path.join(ROOT, ".nojekyll"), "w").close()

os.makedirs(os.path.join(ROOT, "assets", "img"), exist_ok=True)
with open(os.path.join(ROOT, "assets", "img", "favicon.svg"), "w", encoding="utf-8") as f:
    f.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#6ea8ff"/><stop offset="1" stop-color="#8b7bff"/></linearGradient></defs><rect width="64" height="64" rx="14" fill="#0b1020"/><text x="32" y="43" font-family="Arial" font-weight="800" font-size="34" text-anchor="middle" fill="url(#g)">S</text></svg>')
print("built", len(PAGES), "pages x", len(LANGS), "languages")
