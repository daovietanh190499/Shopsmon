"""Linear (DLT) triangulation demo for the Shopsmon blog post
"Triangulation: from two views to a 3D point".

Run:  python triangulation_dlt.py
Needs: numpy, matplotlib
Outputs: ../../assets/img/blog/triangulation-geometry.svg
         ../../assets/img/blog/triangulation-error.svg
and prints a small results table.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rng = np.random.default_rng(7)
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "img", "blog")
os.makedirs(OUT, exist_ok=True)

K = np.array([[800.0, 0, 320], [0, 800.0, 240], [0, 0, 1]])


def camera(center, look_at=np.array([0.0, 0.0, 5.0])):
    """P = K [R | t] for a camera at `center` looking at `look_at` (world y-down not enforced)."""
    z = look_at - center
    z = z / np.linalg.norm(z)
    x = np.cross(np.array([0.0, 1.0, 0.0]), z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    R = np.stack([x, y, z])          # rows = camera axes in world coords
    t = -R @ center
    return K @ np.hstack([R, t[:, None]])


def project(P, X):
    x = P @ np.append(X, 1.0)
    return x[:2] / x[2]


def triangulate_dlt(P1, P2, x1, x2):
    """Homogeneous linear triangulation: solve A X = 0 by SVD (Hartley & Zisserman, sec. 12.2)."""
    A = np.vstack([
        x1[0] * P1[2] - P1[0],
        x1[1] * P1[2] - P1[1],
        x2[0] * P2[2] - P2[0],
        x2[1] * P2[2] - P2[1],
    ])
    _, _, Vt = np.linalg.svd(A)
    X = Vt[-1]
    return X[:3] / X[3]


def triangulate_midpoint(P1, P2, x1, x2):
    """Midpoint of the shortest segment between the two back-projected rays."""
    def ray(P, x):
        M = P[:, :3]
        c = -np.linalg.solve(M, P[:, 3])
        d = np.linalg.solve(M, np.array([x[0], x[1], 1.0]))
        return c, d / np.linalg.norm(d)
    c1, d1 = ray(P1, x1)
    c2, d2 = ray(P2, x2)
    # minimise |c1 + s d1 - (c2 + t d2)|^2
    A = np.array([[d1 @ d1, -d1 @ d2], [d1 @ d2, -d2 @ d2]])
    b = np.array([(c2 - c1) @ d1, (c2 - c1) @ d2])
    s, t = np.linalg.solve(A, b)
    return 0.5 * ((c1 + s * d1) + (c2 + t * d2))


def experiment(baseline, sigma=0.5, n=2000):
    C1 = np.array([-baseline / 2, 0.0, 0.0])
    C2 = np.array([+baseline / 2, 0.0, 0.0])
    P1, P2 = camera(C1), camera(C2)
    e_dlt, e_mid = [], []
    for _ in range(n):
        X = np.array([rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(4, 6)])
        x1 = project(P1, X) + rng.normal(0, sigma, 2)
        x2 = project(P2, X) + rng.normal(0, sigma, 2)
        e_dlt.append(np.linalg.norm(triangulate_dlt(P1, P2, x1, x2) - X))
        e_mid.append(np.linalg.norm(triangulate_midpoint(P1, P2, x1, x2) - X))
    return np.median(e_dlt), np.median(e_mid)


def sanity_check():
    """Noise-free triangulation must be exact (to numerical precision)."""
    P1, P2 = camera(np.array([-0.5, 0, 0])), camera(np.array([0.5, 0, 0]))
    X = np.array([0.3, -0.2, 5.0])
    X_hat = triangulate_dlt(P1, P2, project(P1, X), project(P2, X))
    err = np.linalg.norm(X_hat - X)
    assert err < 1e-8, err
    return err


def figure_geometry():
    C1, C2 = np.array([-1.0, 0.0]), np.array([1.0, 0.0])
    X = np.array([0.4, 5.0])
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    for C, col, lab in ((C1, "#2563eb", "$C_1$"), (C2, "#dc2626", "$C_2$")):
        d = X - C
        # exact ray
        ax.plot([C[0], X[0]], [C[1], X[1]], color=col, lw=1.6)
        # perturbed ray (image noise)
        ang = np.deg2rad(1.4 if col == "#2563eb" else -1.2)
        R = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])
        d2 = R @ d
        ax.plot([C[0], C[0] + 1.25 * d2[0]], [C[1], C[1] + 1.25 * d2[1]],
                color=col, lw=1.2, ls="--")
        ax.scatter(*C, color=col, zorder=3)
        ax.annotate(lab, C + np.array([0, -0.4]), ha="center", color=col)
    ax.scatter(*X, color="black", zorder=3)
    ax.annotate("true point $X$", X + np.array([0.15, 0.1]))
    ax.set_xlim(-2, 3.2)
    ax.set_ylim(-0.8, 7.2)
    ax.set_aspect("equal")
    ax.set_title("Noise shifts the intersection (mostly along depth)", fontsize=11)
    ax.set_xlabel("x"); ax.set_ylabel("z (depth)")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "triangulation-geometry.svg"))
    plt.close(fig)


def figure_error(baselines, e_dlt, e_mid):
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.loglog(baselines, e_dlt, "o-", label="DLT (linear)", color="#2563eb")
    ax.loglog(baselines, e_mid, "s--", label="midpoint", color="#dc2626")
    ax.set_xlabel("baseline (scene units; depth is 4-6)")
    ax.set_ylabel("median 3D error")
    ax.set_title("Triangulation error vs baseline (0.5 px noise)")
    ax.grid(alpha=0.3, which="both")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "triangulation-error.svg"))
    plt.close(fig)


if __name__ == "__main__":
    print(f"noise-free reconstruction error: {sanity_check():.2e}")
    baselines = [0.1, 0.2, 0.5, 1.0, 2.0]
    e_dlt, e_mid = [], []
    print(f"{'baseline':>9} {'DLT':>10} {'midpoint':>10}")
    for b in baselines:
        d, m = experiment(b)
        e_dlt.append(d); e_mid.append(m)
        print(f"{b:9.2f} {d:10.4f} {m:10.4f}")
    figure_geometry()
    figure_error(baselines, e_dlt, e_mid)
