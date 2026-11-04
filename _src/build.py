"""Static bilingual site generator for shopsmon.com (no dependencies).
Run: python _src/build.py
- Vietnamese (default) lives at the site root; English lives under /en/.
- Blog posts are stored as _src/content/<slug>.<lang>.html with placeholders @@EMAIL@@ and @@L@@ (language URL prefix).
"""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONTENT = os.path.join(os.path.dirname(__file__), "content")
SITE = "https://shopsmon.com"
EMAIL = "agent.distributed.virtual@gmail.com"
TODAY = "2026-11-04"
LANGS = ("vi", "en")

PAGES = []  # canonical (vi) paths, each has an /en/ twin

NAV = [
    ("/", {"vi": "Trang chủ", "en": "Home"}),
    ("/services.html", {"vi": "Dịch vụ", "en": "Services"}),
    ("/portfolio.html", {"vi": "Portfolio", "en": "Portfolio"}),
    ("/blog/", {"vi": "Blog", "en": "Blog"}),
    ("/contact.html", {"vi": "Liên hệ", "en": "Contact"}),
]

# Blog post registry (newest first). Body: content/<slug>.<lang>.html
POSTS = [
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
<div><a href="mailto:{EMAIL}">{EMAIL}</a></div>
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


def post_cards(L, limit=None):
    items = POSTS[:limit] if limit else POSTS
    out = ""
    for p in items:
        out += (f'<a class="card" href="{pth(L, "/blog/" + p["slug"] + ".html")}"><span class="tag">{p["tag"][L]} &middot; {p["date"]}</span>'
                f'<h3>{p["title"][L]}</h3><p>{p["summary"][L]}</p></a>')
    return out


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
<div class="card"><span class="tag">3D</span><h3>{t('Tái tạo 3D', '3D reconstruction')}</h3><p>{t('Hình học đa góc nhìn, pipeline kiểu photogrammetry, hiệu chuẩn camera và xử lý đám mây điểm bằng Python.', 'Multi-view geometry, photogrammetry-style pipelines, camera calibration and point-cloud processing in Python.')}</p><a href="{P('/services.html')}#3d">{t('Tìm hiểu thêm', 'Learn more')} &rarr;</a></div>
<div class="card"><span class="tag">Tools</span><h3>{t('Công cụ AI theo yêu cầu', 'Custom AI tools')}</h3><p>{t('Tự động hoá và ứng dụng nhỏ: trích xuất tài liệu, phân loại, làm sạch dữ liệu, dashboard &mdash; đo ni đóng giày theo quy trình của bạn.', 'Automations and small apps: document extraction, classification, data cleaning, dashboards &mdash; scoped to your workflow.')}</p><a href="{P('/services.html')}#tools">{t('Tìm hiểu thêm', 'Learn more')} &rarr;</a></div>
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
<p style="margin-top:20px">{t('Muốn xem tôi giải thích nền tảng thế nào? Đọc', 'Want to see how I explain the fundamentals? Read')} <a href="{P('/blog/triangulation-dlt.html')}">{[x for x in POSTS if x['slug'] == 'triangulation-dlt'][0]['title'][L]}</a>.</p>
</div></section>

<section id="tools"><div class="wrap">
<h2>{t('3. Công cụ AI theo yêu cầu', '3. Custom AI tools')}</h2>
<p class="sub">{t('Phần mềm nhỏ, tập trung, loại bỏ một công việc lặp đi lặp lại.', 'Small, focused software that removes a repetitive task.')}</p>
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
<p class="lead">{t('Shopsmon là studio mới, nên trang này giới thiệu các công việc kỹ thuật mở mà bạn có thể kiểm chứng, không phải logo khách hàng. Khi các dự án khách hàng hoàn thành (khi được cho phép), chúng sẽ được thêm vào đây.', 'Shopsmon is a new studio, so this page shows open technical work you can inspect, not client logos. As client projects are completed (with permission), they will be added here.')}</p>
</div></div>
<section><div class="wrap"><div class="grid g2">
<div class="card"><span class="tag">{t('Tái tạo 3D &middot; mã nguồn mở', '3D reconstruction &middot; open code')}</span><h3>{t('Thí nghiệm tam giác hoá hai góc nhìn (DLT)', 'Two-view triangulation (DLT) experiment')}</h3>
<p>{t('Bản cài đặt NumPy của tam giác hoá tuyến tính và phương pháp điểm giữa, cùng thí nghiệm tái lập được về ảnh hưởng của baseline camera đến độ chính xác 3D. Có kiểm tra tính đúng đắn với dữ liệu không nhiễu.', 'A NumPy implementation of linear triangulation and the midpoint method, with a reproducible experiment on how camera baseline affects 3D accuracy. Includes an exact noise-free sanity check.')}</p>
<p><a href="{P('/blog/triangulation-dlt.html')}">{t('Đọc bài viết', 'Read the article')}</a> &middot; <a href="/blog/code/triangulation_dlt.py">{t('Tải mã nguồn', 'Download the code')}</a></p></div>
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
    layout(L, "/blog/" + p["slug"] + ".html", p["seo_title"][L], p["seo_desc"][L], art,
           active="/blog/", extra_head=KATEX_HEAD, extra_body=KATEX_BODY)


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
for L in LANGS:
    home(L)
    services(L)
    portfolio(L)
    landing(L)
    contact(L)
    blog_index(L)
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
