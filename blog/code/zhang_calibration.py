"""Zhang's closed-form camera calibration from a planar pattern, on synthetic data.
Reproduces every number and figure in the Shopsmon article
"Camera calibration from a chessboard: Zhang's method".
Requires: numpy, matplotlib.   Run: python zhang_calibration.py [--no-fig]

Pipeline (closed-form part of Z. Zhang, IEEE TPAMI 22(11):1330-1334, 2000):
  1. estimate a homography H_i per view (normalised DLT),
  2. stack the two constraints per view on B = K^-T K^-1:  V b = 0,
  3. b = smallest right singular vector of V, K from B in closed form.
No non-linear refinement and no lens distortion in this experiment.
"""
import os
import sys
import numpy as np

K_TRUE = np.array([[820.0, 0.0, 322.0], [0.0, 810.0, 238.0], [0.0, 0.0, 1.0]])
IMG_W, IMG_H = 640, 480
NX, NY, SQ = 9, 6, 0.025  # 9x6 corner grid, 25 mm squares (metres)


def pattern():
    X, Y = np.meshgrid(np.arange(NX) * SQ, np.arange(NY) * SQ)
    return np.column_stack([X.ravel(), Y.ravel()])


def rodrigues(w):
    th = np.linalg.norm(w)
    if th < 1e-12:
        return np.eye(3)
    k = w / th
    Kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(th) * Kx + (1 - np.cos(th)) * Kx @ Kx


def random_pose(rng):
    """Random plane pose [R|t]; pattern centre ~0.45-0.75 m in front, tilt up to ~50 deg. Retry until fully in view."""
    P = pattern()
    centre = np.array([(NX - 1) * SQ / 2, (NY - 1) * SQ / 2, 0.0])
    while True:
        axis = rng.normal(size=3)
        axis /= np.linalg.norm(axis)
        R = rodrigues(axis * np.deg2rad(rng.uniform(15, 50)))
        t = np.array([rng.uniform(-0.05, 0.05), rng.uniform(-0.04, 0.04), rng.uniform(0.45, 0.75)]) - R @ centre
        pts = project(P, R, t)
        if (pts[:, 0].min() > 5 and pts[:, 0].max() < IMG_W - 5 and pts[:, 1].min() > 5 and pts[:, 1].max() < IMG_H - 5
                and ((np.column_stack([P, np.zeros(len(P))]) @ R.T + t)[:, 2] > 0.1).all()):
            return R, t


def project(P2, R, t, K=K_TRUE):
    X = np.column_stack([P2, np.zeros(len(P2))]) @ R.T + t
    x = X @ K.T
    return x[:, :2] / x[:, 2:3]


def hartley(pts):
    c = pts.mean(axis=0)
    d = np.sqrt(((pts - c) ** 2).sum(axis=1)).mean()
    s = np.sqrt(2) / d
    T = np.array([[s, 0, -s * c[0]], [0, s, -s * c[1]], [0, 0, 1.0]])
    return np.column_stack([pts, np.ones(len(pts))]) @ T.T, T


def homography(src, dst):
    """Normalised DLT: dst ~ H src (both (N,2))."""
    a, Ta = hartley(src)
    b, Tb = hartley(dst)
    x, y, u, v = a[:, 0], a[:, 1], b[:, 0], b[:, 1]
    o, z = np.ones(len(a)), np.zeros(len(a))
    r1 = np.column_stack([x, y, o, z, z, z, -u * x, -u * y, -u])
    r2 = np.column_stack([z, z, z, x, y, o, -v * x, -v * y, -v])
    _, _, Vt = np.linalg.svd(np.vstack([r1, r2]))
    H = np.linalg.inv(Tb) @ Vt[-1].reshape(3, 3) @ Ta
    return H / np.linalg.norm(H)


def vij(H, i, j):
    h_i, h_j = H[:, i], H[:, j]
    return np.array([h_i[0] * h_j[0], h_i[0] * h_j[1] + h_i[1] * h_j[0], h_i[1] * h_j[1],
                     h_i[2] * h_j[0] + h_i[0] * h_j[2], h_i[2] * h_j[1] + h_i[1] * h_j[2], h_i[2] * h_j[2]])


def calibrate(Hs, zero_skew=False):
    """Closed-form intrinsics from homographies. Image coords are shifted/scaled first for conditioning."""
    s = 0.5 * (IMG_W + IMG_H) / 2
    N = np.array([[1 / s, 0, -IMG_W / 2 / s], [0, 1 / s, -IMG_H / 2 / s], [0, 0, 1.0]])
    rows = []
    for H in Hs:
        Hn = N @ H
        rows.append(vij(Hn, 0, 1))
        rows.append(vij(Hn, 0, 0) - vij(Hn, 1, 1))
    if zero_skew:
        rows.append([0, 1, 0, 0, 0, 0])
    _, S, Vt = np.linalg.svd(np.array(rows))
    b = Vt[-1]
    if b[0] < 0:
        b = -b
    B11, B12, B22, B13, B23, B33 = b
    den = B11 * B22 - B12 ** 2
    v0 = (B12 * B13 - B11 * B23) / den
    lam = B33 - (B13 ** 2 + v0 * (B12 * B13 - B11 * B23)) / B11
    # B must be positive definite for a real camera; with noisy data and few views the
    # estimate can leave that cone, in which case the closed form has no real solution.
    if den <= 0 or lam / B11 <= 0 or lam * B11 / den <= 0:
        raise ValueError("estimated B is not positive definite")
    alpha = np.sqrt(lam / B11)
    beta = np.sqrt(lam * B11 / den)
    gamma = -B12 * alpha ** 2 * beta / lam
    u0 = gamma * v0 / beta - B13 * alpha ** 2 / lam
    Kn = np.array([[alpha, gamma, u0], [0, beta, v0], [0, 0, 1.0]])
    return np.linalg.inv(N) @ Kn, S


def one_trial(rng, n_views, sigma, zero_skew=False):
    P = pattern()
    Hs = []
    for _ in range(n_views):
        R, t = random_pose(rng)
        x = project(P, R, t) + rng.normal(0, sigma, (len(P), 2))
        Hs.append(homography(P, x))
    K, S = calibrate(Hs, zero_skew)
    return K, S


def errors(K):
    fx_err = abs(K[0, 0] - K_TRUE[0, 0]) / K_TRUE[0, 0] * 100
    fy_err = abs(K[1, 1] - K_TRUE[1, 1]) / K_TRUE[1, 1] * 100
    pp_err = np.hypot(K[0, 2] - K_TRUE[0, 2], K[1, 2] - K_TRUE[1, 2])
    return 0.5 * (fx_err + fy_err), pp_err


def study(trials=300, views=(3, 5, 10, 20), sigmas=(0.1, 0.5, 1.0), seed=2026):
    rng = np.random.default_rng(seed)
    res = {}
    for sg in sigmas:
        for n in views:
            f, p, fail = [], [], 0
            for _ in range(trials):
                try:
                    K, _ = one_trial(rng, n, sg)
                except ValueError:
                    fail += 1
                    continue
                e = errors(K)
                f.append(e[0])
                p.append(e[1])
            # medians over the successful trials only; the failure rate is reported separately
            res[(sg, n)] = (np.median(f), np.median(p), 100.0 * fail / trials)
    return res


def make_figures(res, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(outdir, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "svg.fonttype": "none"})

    # Figure 1: geometry of the setup - plane in world, several camera views of the same grid
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2))
    rng = np.random.default_rng(7)
    P = pattern()
    ax = axs[0]
    ax.set_title("Pattern in the world plane Z = 0 (units: mm)")
    ax.plot(P[:, 0] * 1000, P[:, 1] * 1000, "o", ms=4, color="#2a6fdb")
    ax.set_aspect("equal")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.invert_yaxis()
    ax.grid(alpha=0.3)
    ax = axs[1]
    ax.set_title("The same grid seen in 4 random views (pixels)")
    cols = ["#2a6fdb", "#e0482b", "#1f9d55", "#b8860b"]
    for c in cols:
        R, t = random_pose(rng)
        x = project(P, R, t)
        ax.plot(x[:, 0], x[:, 1], "o", ms=3, color=c)
    ax.set_xlim(0, IMG_W)
    ax.set_ylim(IMG_H, 0)
    ax.set_aspect("equal")
    ax.set_xlabel("u (px)")
    ax.set_ylabel("v (px)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "zhang-views.svg"))
    plt.close(fig)

    # Figure 2: error vs number of views, one curve per noise level
    sigmas = sorted({k[0] for k in res})
    views = sorted({k[1] for k in res})
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2))
    for sg, c in zip(sigmas, cols):
        axs[0].plot(views, [res[(sg, n)][0] for n in views], "o-", color=c, label=f"sigma = {sg} px")
        axs[1].plot(views, [res[(sg, n)][1] for n in views], "o-", color=c, label=f"sigma = {sg} px")
    for a, ttl, yl in ((axs[0], "Focal length error", "median relative error (%)"),
                       (axs[1], "Principal point error", "median distance error (px)")):
        a.set_xscale("log")
        a.set_yscale("log")
        a.set_xticks(views)
        a.set_xticklabels([str(v) for v in views])
        a.set_xlabel("number of views")
        a.set_ylabel(yl)
        a.set_title(ttl)
        a.grid(alpha=0.3, which="both")
        a.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "zhang-error.svg"))
    plt.close(fig)


if __name__ == "__main__":
    # ---- sanity: no noise, 5 views -> exact K up to numerical precision
    rng = np.random.default_rng(1)
    K0, S0 = one_trial(rng, 5, 0.0)
    print("noise-free K estimate:\n", np.round(K0, 6))
    print("sanity max |K - K_true| (noise-free, 5 views): %.3e" % np.abs(K0 - K_TRUE).max())
    # ---- 2 views + zero-skew constraint, noise-free
    K2, _ = one_trial(np.random.default_rng(2), 2, 0.0, zero_skew=True)
    print("sanity max |K - K_true| (noise-free, 2 views, zero skew): %.3e" % np.abs(K2 - K_TRUE).max())
    # ---- one noisy example (sigma 0.5, 10 views)
    Kn, _ = one_trial(np.random.default_rng(3), 10, 0.5)
    print("example sigma=0.5 px, 10 views: fx=%.2f fy=%.2f u0=%.2f v0=%.2f skew=%.3f" %
          (Kn[0, 0], Kn[1, 1], Kn[0, 2], Kn[1, 2], Kn[0, 1]))
    # ---- Monte-Carlo study
    res = study()
    print("\nmedian over successful trials (300 per cell); cell = focal err % / principal-point err px / failure rate %")
    print("sigma  " + "".join(f"{n:>24d} views" for n in (3, 5, 10, 20)))
    for sg in (0.1, 0.5, 1.0):
        print(f"{sg:<6}" + "".join(
            f"{res[(sg, n)][0]:>14.3f}% /{res[(sg, n)][1]:6.2f} /{res[(sg, n)][2]:5.1f}" for n in (3, 5, 10, 20)))
    if "--no-fig" not in sys.argv:
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "img", "blog")
        make_figures(res, os.path.normpath(out))
        print("figures written to", os.path.normpath(out))
