"""Generate original cover illustrations for news articles (1200x630 JPEG) with matplotlib.
No stock photos / no third-party artwork: every image is drawn here, deterministic per slug.
Run: python _src/make_covers.py   (called automatically by build.py when a cover is missing)
"""
import hashlib
import io
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle, Arc  # noqa: E402
from PIL import Image  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from news_data import NEWS  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "assets", "img", "news")
W, H = 1200, 630

PALETTE = {  # (bg1, bg2, accent, accent2)
    "ai": ("#1b1464", "#5b2bd9", "#ff8bd5", "#8fe3ff"),
    "iot": ("#04363d", "#0a8f7a", "#b7ff6b", "#7ff0ff"),
    "cs": ("#0b2a5c", "#1777d1", "#8fe3ff", "#ffe08a"),
    "hw": ("#3b1405", "#d9560b", "#ffd36b", "#fff1c9"),
    "mobile": ("#07204a", "#2a7bff", "#9ad8ff", "#ffffff"),
}


def rng_for(slug):
    return np.random.default_rng(int(hashlib.sha256(slug.encode()).hexdigest()[:8], 16))


def hex2rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)]) / 255.0


def gradient(ax, c1, c2):
    x = np.linspace(0, 1, 256)
    xx, yy = np.meshgrid(x, x)
    t = (0.65 * xx + 0.35 * (1 - yy))[..., None]
    img = hex2rgb(c1) * (1 - t) + hex2rgb(c2) * t
    ax.imshow(img, extent=[0, W, 0, H], origin="lower", aspect="auto", zorder=0)


def glow(ax, x, y, r, color, alpha=0.25, n=6):
    for i in range(n, 0, -1):
        ax.add_patch(Circle((x, y), r * i / n * 2.2, color=color, alpha=alpha / n, lw=0, zorder=2))


def motif_ai(ax, rng, a, b):
    layers = [4, 6, 7, 6, 3]
    xs = np.linspace(170, W - 170, len(layers))
    pts = []
    for lx, n in zip(xs, layers):
        ys = np.linspace(110, H - 110, n) + rng.normal(0, 6, n)
        pts.append([(lx + rng.normal(0, 8), y) for y in ys])
    for l1, l2 in zip(pts[:-1], pts[1:]):
        for (x1, y1) in l1:
            for (x2, y2) in l2:
                if rng.random() < 0.65:
                    ax.plot([x1, x2], [y1, y2], color="white", alpha=0.10 + 0.20 * rng.random(), lw=1.0, zorder=3)
    for li, layer in enumerate(pts):
        for (x, y) in layer:
            col = a if rng.random() < 0.5 else b
            glow(ax, x, y, 11, col, 0.35)
            ax.add_patch(Circle((x, y), 9, color=col, zorder=5))
            ax.add_patch(Circle((x, y), 4, color="white", alpha=0.9, zorder=6))


def motif_iot(ax, rng, a, b):
    cx, cy = W * 0.5, H * 0.5
    for r in (90, 170, 250, 330):
        ax.add_patch(Circle((cx, cy), r, fill=False, ec="white", alpha=0.12, lw=1.5, zorder=2))
    nodes = []
    for ring, (r, n) in enumerate([(170, 6), (250, 9), (330, 12)]):
        off = rng.random() * 6.28
        for k in range(n):
            ang = off + 2 * np.pi * k / n + rng.normal(0, 0.05)
            nodes.append((cx + r * np.cos(ang) * 1.45, cy + r * np.sin(ang) * 0.82, ring))
    nodes = [(x, y, rg) for x, y, rg in nodes if 40 < x < W - 40 and 30 < y < H - 30]
    for (x, y, rg) in nodes:
        ax.plot([cx, x], [cy, y], color="white", alpha=0.12, lw=1.2, zorder=3)
    for i, (x1, y1, r1) in enumerate(nodes):
        for (x2, y2, r2) in nodes[i + 1:]:
            if np.hypot(x1 - x2, y1 - y2) < 150 and rng.random() < 0.6:
                ax.plot([x1, x2], [y1, y2], color=b, alpha=0.35, lw=1.4, zorder=3)
    glow(ax, cx, cy, 34, a, 0.55)
    ax.add_patch(FancyBboxPatch((cx - 34, cy - 34), 68, 68, boxstyle="round,pad=0,rounding_size=14", fc=a, ec="white", lw=3, zorder=6))
    for ang in range(0, 360, 90):
        for dist in (50, 66):
            ax.add_patch(Arc((cx, cy), dist * 2, dist * 2, theta1=ang + 20, theta2=ang + 70, color="white", lw=2, alpha=0.8, zorder=6))
    for (x, y, rg) in nodes:
        col = a if rg == 0 else b
        s = 8 + (2 - rg) * 3
        ax.add_patch(Rectangle((x - s, y - s), 2 * s, 2 * s, fc=col, ec="white", lw=1.6, zorder=5, alpha=0.95))


def motif_cs(ax, rng, a, b):
    n = 14
    xs = np.linspace(110, W - 110, n)
    base = 90
    hs = 90 + 330 * (0.25 + 0.75 * np.abs(np.sin(np.linspace(0.3, 2.8, n) + rng.random())) * (0.6 + 0.4 * rng.random(n)))
    for x, h in zip(xs, hs):
        ax.add_patch(FancyBboxPatch((x - 24, base), 48, h, boxstyle="round,pad=0,rounding_size=8", fc="white", alpha=0.14, zorder=3, lw=0))
        ax.add_patch(FancyBboxPatch((x - 24, base), 48, h * 0.55, boxstyle="round,pad=0,rounding_size=8", fc=a, alpha=0.5, zorder=4, lw=0))
    curve_x = np.linspace(80, W - 80, 200)
    curve_y = 150 + 300 * (1 / (1 + np.exp(-(curve_x - W * (0.4 + 0.2 * rng.random())) / 120))) + 25 * np.sin(curve_x / 60)
    ax.plot(curve_x, curve_y, color=b, lw=5, zorder=6, solid_capstyle="round")
    ax.plot(curve_x, curve_y, color="white", lw=1.6, zorder=7, alpha=0.9)
    for _ in range(60):
        px, py = rng.uniform(80, W - 80), rng.uniform(120, H - 90)
        ax.add_patch(Circle((px, py), rng.uniform(2.5, 6), color="white", alpha=rng.uniform(0.25, 0.7), zorder=5, lw=0))
    for i in range(1, 6):
        ax.plot([80, W - 80], [base + i * 80, base + i * 80], color="white", alpha=0.08, lw=1, zorder=2)


def motif_hw(ax, rng, a, b):
    cx, cy, s = W * 0.5, H * 0.5, 130
    # traces
    for side in range(4):
        for k in range(9):
            off = -s + 22 + k * (2 * s - 44) / 8
            length = rng.uniform(110, 330)
            if side == 0:
                p = [(cx + off, cy + s), (cx + off, cy + s + 40), (cx + off + rng.choice([-1, 1]) * 40, cy + s + 40 + length * 0.5)]
            elif side == 1:
                p = [(cx + off, cy - s), (cx + off, cy - s - 40), (cx + off + rng.choice([-1, 1]) * 40, cy - s - 40 - length * 0.5)]
            elif side == 2:
                p = [(cx - s, cy + off), (cx - s - 40, cy + off), (cx - s - 40 - length * 1.2, cy + off + rng.choice([-1, 1]) * 40)]
            else:
                p = [(cx + s, cy + off), (cx + s + 40, cy + off), (cx + s + 40 + length * 1.2, cy + off + rng.choice([-1, 1]) * 40)]
            xs, ys = zip(*p)
            ax.plot(xs, ys, color=a, alpha=0.55, lw=3, zorder=3, solid_capstyle="round")
            ax.add_patch(Circle(p[-1], 6, color=b, zorder=4, alpha=0.9))
    glow(ax, cx, cy, 120, a, 0.45)
    ax.add_patch(FancyBboxPatch((cx - s, cy - s), 2 * s, 2 * s, boxstyle="round,pad=0,rounding_size=22", fc="#16110f", ec=b, lw=4, zorder=6))
    ax.add_patch(FancyBboxPatch((cx - s + 26, cy - s + 26), 2 * s - 52, 2 * s - 52, boxstyle="round,pad=0,rounding_size=12", fc="none", ec=a, lw=2, zorder=7, alpha=0.9))
    for i in range(4):
        for j in range(4):
            ax.add_patch(Rectangle((cx - 72 + i * 38, cy - 72 + j * 38), 28, 28, fc=a if rng.random() < 0.5 else b, alpha=0.35 + 0.5 * rng.random(), zorder=8, lw=0))


def motif_mobile(ax, rng, a, b):
    cx, cy = W * 0.5, H * 0.46
    for r in (120, 200, 280, 360):
        ax.add_patch(Arc((cx, H * 0.1), r * 2, r * 2, theta1=35, theta2=145, color="white", alpha=0.35 - r / 1400, lw=3, zorder=2))
    for dx, scale, alpha in [(-250, 0.8, 0.55), (250, 0.8, 0.55), (0, 1.0, 1.0)]:
        w, h = 190 * scale, 400 * scale
        x0, y0 = cx + dx - w / 2, cy - h / 2
        glow(ax, cx + dx, cy, 90 * scale, a, 0.25 * alpha)
        ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle="round,pad=0,rounding_size=28", fc="#0a1226", ec="white", lw=4, alpha=alpha, zorder=5))
        ax.add_patch(FancyBboxPatch((x0 + 12, y0 + 12), w - 24, h - 24, boxstyle="round,pad=0,rounding_size=20", fc=a, alpha=0.18 * alpha + 0.05, zorder=6, lw=0))
        for k in range(4):
            bw = (w - 60) * (0.5 + 0.5 * rng.random())
            ax.add_patch(FancyBboxPatch((x0 + 30, y0 + h - 70 - k * 44 * scale), bw, 14 * scale, boxstyle="round,pad=0,rounding_size=6", fc="white", alpha=0.55 * alpha, zorder=7, lw=0))
        ax.add_patch(Circle((cx + dx, y0 + h - 30 * scale), 7 * scale, fc=b, alpha=alpha, zorder=7))


MOTIFS = {"ai": motif_ai, "iot": motif_iot, "cs": motif_cs, "hw": motif_hw, "mobile": motif_mobile}


def render(slug, cat):
    c1, c2, a, b = PALETTE[cat]
    rng = rng_for(slug)
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")
    gradient(ax, c1, c2)
    MOTIFS[cat](ax, rng, a, b)
    ax.text(40, 34, "shopsmon", color="white", alpha=0.85, fontsize=17, fontweight="bold", va="center", zorder=20)
    ax.text(W - 40, 34, "illustration", color="white", alpha=0.45, fontsize=12, va="center", ha="right", zorder=20)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("RGB")
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, slug + ".jpg")
    img.save(path, "JPEG", quality=84, optimize=True, progressive=True)
    return path


def main(force=False):
    made = []
    for n in NEWS:
        p = os.path.join(OUT, n["slug"] + ".jpg")
        if force or not os.path.exists(p):
            made.append(render(n["slug"], n["cat"]))
    return made


if __name__ == "__main__":
    for p in main(force="--force" in sys.argv):
        print(p, os.path.getsize(p))
