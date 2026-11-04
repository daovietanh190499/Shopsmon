"""Static site generator for shopsmon.com (no dependencies). Run: python _src/build.py"""
import os, datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITE = "https://shopsmon.com"
EMAIL = "agent.distributed.virtual@gmail.com"
TODAY = "2026-11-04"

NAV = [("/", "Home"), ("/services.html", "Services"), ("/portfolio.html", "Portfolio"),
       ("/blog/", "Blog"), ("/contact.html", "Contact")]

PAGES = []  # (url, lastmod)


def layout(path, title, desc, body, active="", og_image="/assets/img/og.png", extra_head="", extra_body=""):
    url = SITE + path
    nav = "".join(f'<a href="{h}"{" class=active" if h == active else ""}>{t}</a>' for h, t in NAV)
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Shopsmon">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}{og_image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/css/style.css">
{extra_head}
</head>
<body>
<header class="site"><div class="wrap">
<a class="logo" href="/">shops<span>mon</span></a>
<nav>{nav}</nav>
</div></header>
<main>
{body}
</main>
<footer class="site"><div class="wrap">
<div>&copy; 2026 Shopsmon &middot; Freelance AI &amp; 3D engineering</div>
<div><a href="mailto:{EMAIL}">{EMAIL}</a></div>
</div></footer>
{extra_body}
</body>
</html>
"""
    out = os.path.join(ROOT, path.lstrip("/"))
    if path.endswith("/"):
        out = os.path.join(out, "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    PAGES.append((path, TODAY))


CTA_BTNS = f'<a class="btn primary" href="mailto:{EMAIL}?subject=Project%20inquiry%20-%20Shopsmon">Get a free quote</a><a class="btn ghost" href="/portfolio.html">See portfolio</a>'

# ---------------------------------------------------------------- HOME
home = f"""
<div class="hero"><div class="wrap">
<span class="pill">Freelance AI &amp; 3D engineer &middot; available for new projects</span>
<h1>LLM chatbots, 3D reconstruction and custom AI tools &mdash; built to ship.</h1>
<p class="lead">Shopsmon is a one-person engineering studio. You describe the problem; I design, build and hand over working software: LLM agents that answer real questions, 3D pipelines that turn photos into geometry, and focused AI tools for your workflow.</p>
<div class="cta">{CTA_BTNS}</div>
</div></div>

<section><div class="wrap">
<h2>What I build</h2>
<p class="sub">Three focused services. Each starts with a short scoping chat and a fixed-scope quote before any work begins.</p>
<div class="grid g3">
<div class="card"><span class="tag">LLM</span><h3>Chatbot &amp; agent development</h3><p>Support bots, internal knowledge assistants and tool-using agents with retrieval over your own documents.</p><a href="/solutions/llm-chatbot-agent.html">Learn more &rarr;</a></div>
<div class="card"><span class="tag">3D</span><h3>3D reconstruction</h3><p>Multi-view geometry, photogrammetry-style pipelines, camera calibration and point-cloud processing in Python.</p><a href="/services.html#3d">Learn more &rarr;</a></div>
<div class="card"><span class="tag">Tools</span><h3>Custom AI tools</h3><p>Automations and small apps: document extraction, classification, data cleaning, dashboards &mdash; scoped to your workflow.</p><a href="/services.html#tools">Learn more &rarr;</a></div>
</div></div></section>

<section class="band"><div class="wrap">
<h2>How a project works</h2>
<p class="sub">Simple, transparent, low-risk.</p>
<div class="grid g3 steps">
<div class="card"><h3>Scope</h3><p>Tell me your goal, inputs, outputs and deadline. I reply with questions and a fixed-scope proposal.</p></div>
<div class="card"><h3>Build &amp; demo</h3><p>You see a working demo early, so you can judge the direction before committing to the full build.</p></div>
<div class="card"><h3>Deliver</h3><p>Full source, documentation and a handover call. Payment via PayPal invoice.</p></div>
</div></div></section>

<section><div class="wrap">
<h2>Learn from the blog</h2>
<p class="sub">Technical articles on data science, AI, 3D reconstruction and computer science &mdash; with equations, figures and code that runs.</p>
<div class="grid postlist"><a class="card" href="/blog/triangulation-dlt.html"><span class="tag">3D reconstruction</span><h3>Triangulation: from two views to a 3D point</h3><p>The pinhole model, the Direct Linear Transform, and a numerical experiment on how baseline controls accuracy.</p></a></div>
</div></section>

<section class="band"><div class="wrap" style="text-align:center">
<h2>Have a project in mind?</h2>
<p class="sub" style="margin:0 auto 24px">Send two or three sentences about what you need. You will get a reply with questions and a proposal.</p>
<div class="cta" style="justify-content:center;display:flex;gap:12px;flex-wrap:wrap">{CTA_BTNS}</div>
</div></section>
"""
layout("/", "Shopsmon — Freelance LLM chatbots, 3D reconstruction & AI tools",
       "Freelance engineer building LLM chatbot agents, 3D reconstruction pipelines and custom AI tools. Technical blog on AI, data science and computer vision.",
       home, active="/")

# ---------------------------------------------------------------- SERVICES
services = f"""
<div class="hero" style="padding:64px 0 32px"><div class="wrap">
<h1 style="font-size:clamp(30px,5vw,46px)">Services</h1>
<p class="lead">What I can build for you, what you get, and what I need from you.</p>
</div></div>

<section id="llm"><div class="wrap">
<h2>1. LLM chatbot &amp; agent development</h2>
<p class="sub">Assistants that are useful on day one and honest about what they do not know.</p>
<div class="grid g2">
<div class="card"><h3>Typical deliverables</h3><ul><li>Customer-support or FAQ bot for web, Messenger or Telegram</li><li>Retrieval-augmented assistant over your PDFs, docs or wiki</li><li>Tool-using agent (calls your APIs, databases, spreadsheets)</li><li>Evaluation set and guardrails (refusals, escalation to a human)</li></ul></div>
<div class="card"><h3>What I need from you</h3><ul><li>Goal and target users</li><li>Sample questions and the documents the bot should know</li><li>Preferred model/provider and hosting constraints</li><li>Where the bot should live (site, chat app, internal tool)</li></ul></div>
</div>
<p style="margin-top:20px"><a href="/solutions/llm-chatbot-agent.html">Read the full chatbot service page &rarr;</a></p>
</div></section>

<section id="3d" class="band"><div class="wrap">
<h2>2. 3D reconstruction</h2>
<p class="sub">From images or video to geometry, using classical multi-view geometry and modern tooling.</p>
<div class="grid g2">
<div class="card"><h3>Typical deliverables</h3><ul><li>Camera calibration and pose estimation</li><li>Structure-from-motion / multi-view triangulation pipelines</li><li>Point-cloud cleaning, meshing and measurement scripts</li><li>Reproducible Python code with a short technical report</li></ul></div>
<div class="card"><h3>What I need from you</h3><ul><li>Example images or video and the object/scene scale</li><li>Required accuracy and output format (PLY, OBJ, CSV&hellip;)</li><li>Camera information if available</li><li>Compute constraints (laptop, server, GPU)</li></ul></div>
</div>
<p style="margin-top:20px">Want to see how I explain the fundamentals? Read <a href="/blog/triangulation-dlt.html">Triangulation: from two views to a 3D point</a>.</p>
</div></section>

<section id="tools"><div class="wrap">
<h2>3. Custom AI tools</h2>
<p class="sub">Small, focused software that removes a repetitive task.</p>
<div class="grid g2">
<div class="card"><h3>Examples</h3><ul><li>Extract fields from invoices, forms or emails into a spreadsheet</li><li>Classify or tag content at scale</li><li>Data-cleaning and reporting scripts with a simple UI</li><li>Internal dashboards and automations</li></ul></div>
<div class="card"><h3>How pricing works</h3><p>Every project gets a fixed-scope quote after a short scoping chat. You pay by PayPal invoice. For larger work, a demo comes first so you can judge the result before the full build.</p></div>
</div></div></section>

<section class="band"><div class="wrap" style="text-align:center"><h2>Let&rsquo;s scope your project</h2>
<p class="sub" style="margin:0 auto 24px">Free first reply with questions and a proposal.</p>
<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">{CTA_BTNS}</div></div></section>
"""
layout("/services.html", "Services — LLM chatbots, 3D reconstruction, custom AI tools | Shopsmon",
       "Freelance services: LLM chatbot and agent development, 3D reconstruction pipelines, and custom AI tools. Fixed-scope quotes, demo first, full source delivered.",
       services, active="/services.html")

# ---------------------------------------------------------------- PORTFOLIO
portfolio = f"""
<div class="hero" style="padding:64px 0 32px"><div class="wrap">
<h1 style="font-size:clamp(30px,5vw,46px)">Portfolio</h1>
<p class="lead">Shopsmon is a new studio, so this page shows open technical work you can inspect, not client logos. As client projects are completed (with permission), they will be added here.</p>
</div></div>
<section><div class="wrap"><div class="grid g2">
<div class="card"><span class="tag">3D reconstruction &middot; open code</span><h3>Two-view triangulation (DLT) experiment</h3>
<p>A NumPy implementation of linear triangulation and the midpoint method, with a reproducible experiment on how camera baseline affects 3D accuracy. Includes an exact noise-free sanity check.</p>
<p><a href="/blog/triangulation-dlt.html">Read the article</a> &middot; <a href="/blog/code/triangulation_dlt.py">Download the code</a></p></div>
<div class="card"><span class="tag">LLM &middot; service page</span><h3>LLM chatbot &amp; agent development</h3>
<p>What a chatbot project looks like end to end: scoping, retrieval over your documents, evaluation, deployment and handover.</p>
<p><a href="/solutions/llm-chatbot-agent.html">See the service page</a></p></div>
</div></div></section>
<section class="band"><div class="wrap" style="text-align:center"><h2>Want to be the first featured project?</h2>
<p class="sub" style="margin:0 auto 24px">Early clients get a focused scope, close attention and a fair price.</p>
<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">{CTA_BTNS}</div></div></section>
"""
layout("/portfolio.html", "Portfolio — open technical work | Shopsmon",
       "Open technical work from Shopsmon: 3D triangulation experiment with code, and LLM chatbot service overview.",
       portfolio, active="/portfolio.html")

# ---------------------------------------------------------------- PRODUCT / SERVICE LANDING
landing = f"""
<div class="hero"><div class="wrap">
<span class="pill">LLM chatbot &amp; agent development</span>
<h1>A chatbot that actually answers your customers&rsquo; questions.</h1>
<p class="lead">I build LLM assistants grounded in <em>your</em> documents and tools &mdash; with an evaluation set, sensible guardrails and a clean handover so you own the result.</p>
<div class="cta">{CTA_BTNS}</div></div></div>

<section><div class="wrap"><h2>What you get</h2><p class="sub">A working assistant, not a slide deck.</p>
<div class="grid g3">
<div class="card"><h3>Grounded answers</h3><p>Retrieval over your PDFs, web pages or knowledge base so answers come from your content, with sources shown where useful.</p></div>
<div class="card"><h3>Tool use</h3><p>The agent can call your APIs, query a database or update a spreadsheet when a question needs live data.</p></div>
<div class="card"><h3>Guardrails &amp; escalation</h3><p>Clear behaviour when the bot is unsure: say so, and hand over to a human instead of guessing.</p></div>
<div class="card"><h3>Evaluation set</h3><p>A set of real questions with expected answers so quality can be measured before and after every change.</p></div>
<div class="card"><h3>Where it lives</h3><p>Website widget, Facebook Messenger, Telegram, or an internal tool &mdash; whichever your users already use.</p></div>
<div class="card"><h3>Full handover</h3><p>Source code, deployment notes and a walkthrough call. No lock-in.</p></div>
</div></div></section>

<section class="band"><div class="wrap"><h2>Process</h2><p class="sub">Four steps, demo before the full build.</p>
<div class="grid g3 steps">
<div class="card"><h3>Scoping chat</h3><p>Goal, users, sample questions, documents, constraints, deadline.</p></div>
<div class="card"><h3>Fixed-scope quote</h3><p>Written proposal with deliverables and timeline. Nothing starts before you agree.</p></div>
<div class="card"><h3>Demo</h3><p>A limited working version so you can test it with your own questions.</p></div>
<div class="card"><h3>Final delivery</h3><p>Full version, documentation, handover. Payment by PayPal invoice.</p></div>
</div></div></section>

<section><div class="wrap"><h2>Good fit if&hellip;</h2>
<div class="grid g2"><div class="card"><ul><li>You answer the same questions repeatedly</li><li>You have documents or FAQs the bot can rely on</li><li>You want something practical in weeks, not months</li></ul></div>
<div class="card"><p>Not a fit for: medical, legal or financial advice bots that require certified accuracy, or projects that need guaranteed outcomes that no LLM system can promise.</p></div></div></div></section>

<section class="band"><div class="wrap" style="text-align:center"><h2>Tell me what your bot should do</h2>
<p class="sub" style="margin:0 auto 24px">Two or three sentences are enough to start.</p>
<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">{CTA_BTNS}</div></div></section>
"""
layout("/solutions/llm-chatbot-agent.html", "LLM chatbot & agent development for your business | Shopsmon",
       "Custom LLM chatbots and tool-using agents grounded in your documents, with evaluation, guardrails and full source handover. Demo first, fixed-scope quote.",
       landing, active="/services.html")

# ---------------------------------------------------------------- CONTACT
contact = f"""
<div class="hero" style="padding:64px 0 32px"><div class="wrap">
<h1 style="font-size:clamp(30px,5vw,46px)">Contact</h1>
<p class="lead">Tell me what you need. You will get a reply with clarifying questions and, where it makes sense, a fixed-scope quote.</p>
</div></div>
<section><div class="wrap"><div class="grid g2">
<div class="card"><h3>Email</h3><p><a href="mailto:{EMAIL}?subject=Project%20inquiry%20-%20Shopsmon">{EMAIL}</a></p>
<p>Please include: your goal, what goes in and what should come out, any deadline, and your rough budget.</p></div>
<div class="card"><h3>Facebook Messenger</h3><p>You can also message the Shopsmon Facebook Page. Details are shared in the page posts.</p></div>
</div>
<div class="card" style="margin-top:20px"><h3>What happens next</h3><ul><li>I reply with questions to clarify the scope.</li><li>I send a written proposal with price and timeline.</li><li>Work starts after you agree. Payment is by PayPal invoice.</li></ul></div>
</div></section>
"""
layout("/contact.html", "Contact Shopsmon — start your project",
       "Contact Shopsmon to discuss an LLM chatbot, 3D reconstruction or custom AI tool project.", contact, active="/contact.html")

# ---------------------------------------------------------------- BLOG INDEX
blog_index = f"""
<div class="hero" style="padding:64px 0 24px"><div class="wrap">
<h1 style="font-size:clamp(30px,5vw,46px)">Blog</h1>
<p class="lead">Data science, AI, 3D reconstruction and computer science &mdash; explained with equations, figures and code that runs.</p>
</div></div>
<section><div class="wrap"><div class="grid postlist">
<a class="card" href="/blog/triangulation-dlt.html"><span class="tag">3D reconstruction &middot; 2026-11-04</span><h3>Triangulation: from two views to a 3D point</h3>
<p>Why two noisy rays never intersect, how the Direct Linear Transform solves it with an SVD, and a numerical experiment on how camera baseline controls accuracy.</p></a>
</div></div></section>
"""
layout("/blog/", "Blog — AI, data science & 3D reconstruction | Shopsmon",
       "Technical articles on AI, data science, 3D reconstruction and computer science with equations, figures and runnable code.",
       blog_index, active="/blog/")

# ---------------------------------------------------------------- BLOG POST
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

post = f"""
<article class="post">
<p class="meta"><a href="/blog/">&larr; Blog</a> &middot; 2026-11-04 &middot; 3D reconstruction &middot; ~12 min read</p>
<h1>Triangulation: from two views to a 3D point</h1>
<p class="meta">Pinhole camera, the Direct Linear Transform (DLT), and a numerical experiment on baseline vs. accuracy.</p>

<h2>1. Context</h2>
<p>Every 3D reconstruction pipeline built from images &mdash; structure from motion, photogrammetry, stereo &mdash; eventually asks the same question: <em>given where a point appears in two or more images, and given the cameras, where is it in 3D?</em> Answering it is called <strong>triangulation</strong>. It is the &ldquo;recover the point&rdquo; step once the cameras are known (or estimated).</p>
<p>In a perfect world the answer is just the intersection of two rays. In real images, pixel coordinates are noisy, the two rays are <em>skew</em> and almost never meet, and we need a principled way to pick the best point. This article derives the standard linear solution, implements it, and tests how it behaves.</p>

<h2>2. The pinhole camera</h2>
<p>A 3D point in homogeneous coordinates \\(\\mathbf{{X}}=(X,Y,Z,1)^\\top\\) is projected to the image point \\(\\mathbf{{x}}=(u,v,1)^\\top\\) by a \\(3\\times4\\) camera matrix \\(P\\):</p>
$$\\lambda\\,\\mathbf{{x}} = P\\,\\mathbf{{X}},\\qquad P = K\\,[\\,R \\mid \\mathbf{{t}}\\,],\\qquad K=\\begin{{bmatrix}} f_x & 0 & c_x\\\\ 0 & f_y & c_y\\\\ 0&0&1\\end{{bmatrix}}$$
<p>Here \\(K\\) holds the intrinsics (focal lengths \\(f_x,f_y\\) in pixels and principal point \\((c_x,c_y)\\)), and \\([R\\mid\\mathbf t]\\) are the extrinsics: the rotation and translation from world to camera coordinates. The scalar \\(\\lambda\\) is the unknown projective depth. The symbol \\(\\simeq\\) is often used for &ldquo;equal up to scale&rdquo;.</p>

<h2>3. Why the rays do not meet</h2>
<p>Each observed pixel defines a ray from the camera centre. With exact data the two rays intersect at the true point \\(\\mathbf X\\). With noisy pixels, the rays in 3D are generally <em>skew</em> &mdash; they pass each other without touching. The top-down view below is a 2D slice, where two lines always cross, so it only shows the other half of the story: noise moves the crossing point away from the truth, mostly along the viewing direction (depth).</p>
<figure><img src="/assets/img/blog/triangulation-geometry.svg" alt="Two cameras and their rays toward a point; dashed perturbed rays cross at a displaced estimate" width="640" height="540">
<figcaption>Figure 1. Top-down 2D slice (x vs. depth z). Solid rays meet at the true point; the dashed rays, perturbed by about 1&ndash;1.5 degrees to mimic image noise, cross at a displaced estimate (orange cross). In full 3D such rays would not even cross.</figcaption></figure>
<p>We therefore need a criterion for the &ldquo;best&rdquo; point. Two natural choices are (a) an <strong>algebraic</strong> criterion that leads to a linear system, and (b) the <strong>geometric reprojection error</strong>.</p>

<h2>4. Linear triangulation (DLT)</h2>
<p>The relation \\(\\lambda\\mathbf x=P\\mathbf X\\) says \\(\\mathbf x\\) and \\(P\\mathbf X\\) are parallel, so their cross product vanishes:</p>
$$\\mathbf{{x}}\\times(P\\mathbf{{X}})=\\mathbf 0 .$$
<p>Let \\(\\mathbf p_i^\\top\\) be the \\(i\\)-th row of \\(P\\) and \\(\\mathbf x=(u,v,1)^\\top\\). Expanding the cross product gives three equations, only two of which are linearly independent:</p>
$$u\\,\\mathbf p_3^\\top\\mathbf X-\\mathbf p_1^\\top\\mathbf X=0,\\qquad v\\,\\mathbf p_3^\\top\\mathbf X-\\mathbf p_2^\\top\\mathbf X=0 .$$
<p>With two views \\((P,\\mathbf x=(u,v,1)^\\top)\\) and \\((P',\\mathbf x'=(u',v',1)^\\top)\\) we stack four equations into \\(A\\mathbf X=\\mathbf 0\\):</p>
$$A=\\begin{{bmatrix}} u\\,\\mathbf p_3^\\top-\\mathbf p_1^\\top\\\\ v\\,\\mathbf p_3^\\top-\\mathbf p_2^\\top\\\\ u'\\,\\mathbf p_3'^\\top-\\mathbf p_1'^\\top\\\\ v'\\,\\mathbf p_3'^\\top-\\mathbf p_2'^\\top\\end{{bmatrix}}\\in\\mathbb R^{{4\\times4}} .$$
<p>Because \\(\\mathbf X\\) is homogeneous we only know it up to scale, so we solve</p>
$$\\hat{{\\mathbf X}}=\\arg\\min_{{\\|\\mathbf X\\|=1}}\\ \\|A\\mathbf X\\|^2 ,$$
<p>whose solution is the right singular vector of \\(A\\) associated with the smallest singular value. If \\(A=U\\Sigma V^\\top\\), then \\(\\hat{{\\mathbf X}}\\) is the last column of \\(V\\). Finally we dehomogenise: \\((X,Y,Z)=(\\hat X_1,\\hat X_2,\\hat X_3)/\\hat X_4\\).</p>
<div class="callout"><strong>Algebraic vs. geometric.</strong> The DLT minimises \\(\\|A\\mathbf X\\|\\), a quantity without direct geometric meaning in the image. The quantity we usually care about is the <em>reprojection error</em>
$$E(\\mathbf X)=\\big\\|\\mathbf x-\\pi(P\\mathbf X)\\big\\|^2+\\big\\|\\mathbf x'-\\pi(P'\\mathbf X)\\big\\|^2,\\qquad \\pi\\big((a,b,c)^\\top\\big)=(a/c,\\;b/c)^\\top ,$$
which is the maximum-likelihood criterion under independent Gaussian pixel noise. Hartley and Sturm (1997) give a non-iterative solution for the two-view case that finds the global minimum of this error; the linear DLT result is often used as an initial guess or when speed matters.</div>

<h2>5. Implementation</h2>
<p>Below is the core of the implementation (NumPy). The <a href="/blog/code/triangulation_dlt.py">complete script</a>, including the experiment and the figures in this article, is downloadable.</p>
<pre><code class="language-python">import numpy as np

def triangulate_dlt(P1, P2, x1, x2):
    \"\"\"Homogeneous linear triangulation: solve A X = 0 by SVD.\"\"\"
    A = np.vstack([
        x1[0] * P1[2] - P1[0],
        x1[1] * P1[2] - P1[1],
        x2[0] * P2[2] - P2[0],
        x2[1] * P2[2] - P2[1],
    ])
    _, _, Vt = np.linalg.svd(A)
    X = Vt[-1]              # right singular vector of the smallest singular value
    return X[:3] / X[3]     # dehomogenise
</code></pre>
<p>For comparison I also implemented the <strong>midpoint method</strong>: back-project both pixels to rays \\(\\mathbf c_i+s_i\\mathbf d_i\\), find \\((s_1,s_2)\\) minimising the distance between the rays, and return the midpoint of that shortest segment.</p>

<h3>Sanity check</h3>
<p>Before trusting any numbers, I triangulated a point from <em>noise-free</em> projections. The reconstruction error was <code>1.13e-15</code> (floating-point round-off), as it must be when the rays intersect exactly.</p>

<h2>6. Experiment: how does baseline affect accuracy?</h2>
<p><strong>Setup (synthetic, fully reproducible).</strong> Intrinsics \\(f_x=f_y=800\\) px, principal point \\((320,240)\\). Two cameras placed symmetrically on the x-axis at \\(\\pm b/2\\), both looking at \\((0,0,5)\\). Random 3D points with \\(x,y\\in[-1,1]\\), \\(z\\in[4,6]\\). Each projection receives independent Gaussian noise with \\(\\sigma=0.5\\) px. For each baseline \\(b\\) I triangulate 2000 points (NumPy random seed 7) and report the <em>median</em> Euclidean 3D error, in the same units as the scene.</p>
<table>
<thead><tr><th>Baseline b</th><th>DLT median error</th><th>Midpoint median error</th></tr></thead>
<tbody>
<tr><td>0.10</td><td>0.1492</td><td>0.1489</td></tr>
<tr><td>0.20</td><td>0.0789</td><td>0.0792</td></tr>
<tr><td>0.50</td><td>0.0295</td><td>0.0294</td></tr>
<tr><td>1.00</td><td>0.0155</td><td>0.0155</td></tr>
<tr><td>2.00</td><td>0.0083</td><td>0.0084</td></tr>
</tbody></table>
<figure><img src="/assets/img/blog/triangulation-error.svg" alt="Log-log plot of median 3D error versus baseline for DLT and midpoint triangulation" width="640" height="420">
<figcaption>Figure 2. Median 3D error vs. baseline (log&ndash;log). Output of the script in this article.</figcaption></figure>

<h3>What the numbers say</h3>
<ul>
<li><strong>Baseline dominates accuracy.</strong> Increasing the baseline 20&times; (0.1 &rarr; 2.0) reduced the median error by about 18&times; (0.149 &rarr; 0.0083), i.e. roughly inversely proportional to the baseline in this regime.</li>
<li><strong>This matches the rectified-stereo intuition.</strong> For two parallel cameras with focal length \\(f\\) and baseline \\(B\\), depth is \\(Z=fB/d\\) where \\(d\\) is the disparity. Differentiating, a disparity error \\(\\delta d\\) produces a depth error \\(\\delta Z\\approx \\dfrac{{Z^2}}{{fB}}\\,\\delta d\\): depth error grows with the square of the distance and shrinks with the baseline.</li>
<li><strong>In this setup DLT and midpoint are practically identical.</strong> The two methods differ by less than 1% at every baseline. This experiment (small noise, well-conditioned geometry, both cameras looking at the scene centre) is simply not one that separates them. I make no claim about other regimes; for a systematic comparison of methods see Hartley &amp; Sturm (1997).</li>
</ul>
<p><strong>Limitations.</strong> The data are synthetic, noise is Gaussian and isotropic, camera calibration is assumed exact, and I did not compare against the optimal (minimum reprojection error) method. Real pipelines add lens distortion, outlier matches and calibration error &mdash; each of which needs its own treatment (robust estimation, bundle adjustment).</p>

<h2>7. Practical takeaways</h2>
<ol>
<li>Use as large a baseline as the matching algorithm tolerates: it directly reduces depth uncertainty.</li>
<li>Check your code with noise-free data first; it should reproduce the point to round-off.</li>
<li>Treat DLT as a fast, solid initial estimate; refine by minimising reprojection error when accuracy matters.</li>
<li>Always report the metric you actually care about (reprojection error, 3D error) &mdash; they are not the same as the algebraic residual.</li>
</ol>

<div class="cta-box"><strong>Need 3D reconstruction, a chatbot agent or a custom AI tool?</strong><br>
I build these as a freelancer. Describe your project in a few sentences and I will reply with questions and a fixed-scope quote.<br><br>
<a class="btn primary" href="mailto:{EMAIL}?subject=3D%20reconstruction%20project">Ask for a quote</a> <a class="btn ghost" href="/services.html">See services</a></div>

<h2>References</h2>
<ol class="refs">
<li>R. Hartley and A. Zisserman. <em>Multiple View Geometry in Computer Vision</em>, 2nd ed. Cambridge University Press, 2004. ISBN 978-0-521-54051-3. (Chapter 12, &ldquo;Structure computation&rdquo;.) <a href="https://www.cambridge.org/9780521540513">Publisher page</a>.</li>
<li>R. I. Hartley and P. Sturm. &ldquo;Triangulation.&rdquo; <em>Computer Vision and Image Understanding</em> 68(2):146&ndash;157, November 1997. <a href="https://doi.org/10.1006/cviu.1997.0547">doi:10.1006/cviu.1997.0547</a>.</li>
</ol>
<p class="meta">Code: <a href="/blog/code/triangulation_dlt.py">triangulation_dlt.py</a> (Python 3.12, NumPy, Matplotlib). All numbers in Section 6 are the output of this script.</p>
</article>
"""
layout("/blog/triangulation-dlt.html", "Triangulation: from two views to a 3D point (DLT explained) | Shopsmon",
       "Derivation of linear triangulation (DLT) for two views, with NumPy code, figures and an experiment showing how camera baseline controls 3D accuracy.",
       post, active="/blog/", og_image="/assets/img/og.png",
       extra_head=KATEX_HEAD, extra_body=KATEX_BODY)

# ---------------------------------------------------------------- 404, sitemap, robots, assets
with open(os.path.join(ROOT, "404.html"), "w", encoding="utf-8", newline="\n") as f:
    f.write("""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Page not found | Shopsmon</title><link rel="stylesheet" href="/assets/css/style.css"></head><body><div class="wrap" style="padding:120px 20px;text-align:center"><h1>404 &mdash; page not found</h1><p><a class="btn primary" href="/">Back to Shopsmon</a></p></div></body></html>""")

with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8", newline="\n") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    for p, d in PAGES:
        f.write(f"  <url><loc>{SITE}{p}</loc><lastmod>{d}</lastmod></url>\n")
    f.write("</urlset>\n")
with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8", newline="\n") as f:
    f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
open(os.path.join(ROOT, ".nojekyll"), "w").close()

os.makedirs(os.path.join(ROOT, "assets", "img"), exist_ok=True)
with open(os.path.join(ROOT, "assets", "img", "favicon.svg"), "w", encoding="utf-8") as f:
    f.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#6ea8ff"/><stop offset="1" stop-color="#8b7bff"/></linearGradient></defs><rect width="64" height="64" rx="14" fill="#0b1020"/><text x="32" y="43" font-family="Arial" font-weight="800" font-size="34" text-anchor="middle" fill="url(#g)">S</text></svg>')
print("built", len(PAGES), "pages")
