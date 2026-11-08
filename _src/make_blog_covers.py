"""Raster (PNG 1200x630) title-card covers for blog posts that have no photo, used as og:image / Facebook attachment.
Usage: python _src/make_blog_covers.py            (writes assets/img/blog/<slug>-cover.png for the slugs below)
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "img", "blog")
CARDS = {
    "triangulation-dlt": ("Triangulation (DLT)", "From two views to a 3D point  |  SVD, NumPy", "#0ea5e9"),
    "eight-point-normalization": ("Eight-point algorithm", "Why Hartley normalisation matters  |  SVD, NumPy", "#22c55e"),
    "zhang-calibration": ("Camera calibration", "Zhang's chessboard method  |  homography, SVD", "#f59e0b"),
    "gd-conditioning": ("Gradient descent & conditioning", "Why least squares gets slow  |  kappa, CG, NumPy", "#a855f7"),
    "essential-matrix": ("Essential matrix: four poses", "Decomposing E, one cheirality test  |  SVD, NumPy", "#ef4444"),
    "pca-svd": ("PCA through the SVD", "Stability and sensor data compression  |  NumPy", "#14b8a6"),
}
ONLY = set(__import__("sys").argv[1:])


def art(ax, slug, col):
    x = np.linspace(0, 1, 400)
    rng = np.random.default_rng(sum(map(ord, slug)))
    for k in range(5):
        ax.plot(x, 0.5 + 0.18 * np.sin(2 * np.pi * (k + 1) * x + k) * (1 - 0.12 * k), color=col, alpha=0.18 + 0.12 * k, lw=2)
    ax.scatter(rng.random(40), rng.random(40), s=14, color=col, alpha=0.5)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")


for slug, (title, sub, col) in CARDS.items():
    if ONLY and slug not in ONLY:
        continue
    fig = plt.figure(figsize=(12, 6.3), dpi=100)
    fig.patch.set_facecolor("#0f172a")
    ax = fig.add_axes([0.07, 0.08, 0.86, 0.48]); ax.set_facecolor("#0f172a")
    art(ax, slug, col)
    fig.text(0.07, 0.86, title, color="white", fontsize=40, fontweight="bold")
    fig.text(0.07, 0.72, sub, color="#94a3b8", fontsize=22)
    fig.text(0.93, 0.03, "shopsmon.com", color="#64748b", fontsize=16, ha="right")
    fig.savefig(os.path.join(OUT, slug + "-cover.png"), facecolor=fig.get_facecolor())
    plt.close(fig)
    print("wrote", slug)
