"""Essential matrix -> (R, t): the four candidate poses, the cheirality test, and how accuracy depends on noise and baseline.

Run:  python essential_matrix.py      (about 1 minute; Python 3.12, NumPy, Matplotlib)
Everything is seeded; the numbers printed here are the ones quoted in the blog post.
Writes essential-candidates.svg and essential-errors.svg next to this script (or into $ESS_OUT).
"""
import os
import numpy as np

OUT = os.environ.get("ESS_OUT", os.path.dirname(os.path.abspath(__file__)))
K = np.array([[800.0, 0, 320.0], [0, 800.0, 240.0], [0, 0, 1.0]])
KINV = np.linalg.inv(K)
W = np.array([[0.0, -1, 0], [1, 0, 0], [0, 0, 1]])


# ------------------------------------------------------------------ geometry helpers
def skew(v):
    return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0.0]])


def rodrigues(axis, angle):
    a = axis / np.linalg.norm(axis)
    S = skew(a)
    return np.eye(3) + np.sin(angle) * S + (1 - np.cos(angle)) * S @ S


def angle_deg(R):
    """Rotation angle of a rotation matrix, in degrees."""
    return np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))


def vec_angle_deg(a, b):
    c = a @ b / (np.linalg.norm(a) * np.linalg.norm(b))
    return np.degrees(np.arccos(np.clip(c, -1, 1)))


# ------------------------------------------------------------------ synthetic two-view scene
def make_scene(seed, n=50, baseline=1.0, sigma=0.0, rot_deg=15.0):
    """n points 4-8 units in front of camera 1; camera 2 = (R, t) with |C2| = baseline; pixel noise sigma."""
    rng = np.random.default_rng(seed)
    X = np.column_stack([rng.uniform(-2, 2, n), rng.uniform(-1.5, 1.5, n), rng.uniform(4, 8, n)])
    R = rodrigues(rng.normal(size=3), np.radians(rot_deg) * rng.uniform(0.5, 1.0))
    phi = rng.uniform(-np.pi / 2, np.pi / 2)            # camera centre mostly to the side of camera 1
    d = np.array([np.sin(phi), 0.15 * rng.normal(), np.cos(phi) * 0.3])
    C2 = baseline * d / np.linalg.norm(d)               # baseline 0 = pure rotation (degenerate case)
    t = -R @ C2                                         # x2 = R x1 + t
    x1 = (K @ X.T).T
    x1 = x1[:, :2] / x1[:, 2:]
    X2 = X @ R.T + t
    x2 = (K @ X2.T).T
    x2 = x2[:, :2] / x2[:, 2:]
    x1 = x1 + rng.normal(scale=sigma, size=x1.shape)
    x2 = x2 + rng.normal(scale=sigma, size=x2.shape)
    return dict(X=X, R=R, t=t, x1=x1, x2=x2)


def to_normalised(px):
    """Pixel coordinates -> normalised camera coordinates (x/z, y/z, 1)."""
    h = np.column_stack([px, np.ones(len(px))])
    return h @ KINV.T


# ------------------------------------------------------------------ estimation
def hartley(h):
    c = h[:, :2].mean(0)
    d = np.sqrt(((h[:, :2] - c) ** 2).sum(1)).mean()
    s = np.sqrt(2) / d
    T = np.array([[s, 0, -s * c[0]], [0, s, -s * c[1]], [0, 0, 1.0]])
    return h @ T.T, T


def estimate_E(n1, n2):
    """Normalised eight-point algorithm on normalised camera coordinates, then projection onto the essential manifold."""
    h1, T1 = hartley(n1)
    h2, T2 = hartley(n2)
    A = np.stack([np.kron(b, a) for a, b in zip(h1, h2)])   # x2^T E x1 = 0, row = kron(x2, x1)
    _, _, Vt = np.linalg.svd(A)
    E = Vt[-1].reshape(3, 3)
    E = T2.T @ E @ T1
    U, S, Vt = np.linalg.svd(E)
    s = (S[0] + S[1]) / 2                                   # essential matrices have singular values (s, s, 0)
    return U @ np.diag([s, s, 0.0]) @ Vt


def decompose(E):
    """The four candidate (R, t) of an essential matrix; |t| = 1."""
    U, _, Vt = np.linalg.svd(E)
    if np.linalg.det(U) < 0:
        U[:, 2] *= -1
    if np.linalg.det(Vt) < 0:
        Vt[2] *= -1
    R1 = U @ W @ Vt
    R2 = U @ W.T @ Vt
    t = U[:, 2]
    return [(R1, t), (R1, -t), (R2, t), (R2, -t)]


def triangulate(R, t, n1, n2):
    """Linear (DLT) triangulation of every match for P1 = [I|0], P2 = [R|t]; returns (N,3) points in camera 1."""
    P1 = np.hstack([np.eye(3), np.zeros((3, 1))])
    P2 = np.hstack([R, t[:, None]])
    A = np.stack([n1[:, 0:1] * P1[2] - P1[0], n1[:, 1:2] * P1[2] - P1[1],
                  n2[:, 0:1] * P2[2] - P2[0], n2[:, 1:2] * P2[2] - P2[1]], axis=1)   # (N,4,4)
    _, _, Vt = np.linalg.svd(A)
    Xh = Vt[:, -1, :]
    return Xh[:, :3] / Xh[:, 3:4]


def count_in_front(R, t, n1, n2):
    """Cheirality: how many triangulated points have positive depth in BOTH cameras."""
    X = triangulate(R, t, n1, n2)
    z1 = X[:, 2]
    z2 = (X @ R.T + t)[:, 2]
    return int(np.sum((z1 > 0) & (z2 > 0))), X


def recover_pose(n1, n2):
    E = estimate_E(n1, n2)
    cands = decompose(E)
    counts = [count_in_front(R, t, n1, n2)[0] for R, t in cands]
    best = int(np.argmax(counts))
    return cands[best], cands, counts, E


def pose_errors(R_est, t_est, R_true, t_true):
    return angle_deg(R_est.T @ R_true), vec_angle_deg(t_est, t_true)


# ------------------------------------------------------------------ experiments
def demo(seed=0, sigma=0.5):
    sc = make_scene(seed, sigma=sigma)
    n1, n2 = to_normalised(sc["x1"]), to_normalised(sc["x2"])
    (Rb, tb), cands, counts, E = recover_pose(n1, n2)
    print(f"== Demo (seed {seed}, N=50, noise {sigma} px) ==")
    S = np.linalg.svd(E, compute_uv=False)
    print("singular values of the estimated E:", np.round(S / S[0], 4))
    print("true rotation angle %.2f deg; |t| of the second camera = %.2f (scale is unobservable)" % (angle_deg(sc["R"]), np.linalg.norm(sc["t"])))
    # twisted pair: R2 R1^T is a 180-degree rotation about the baseline
    R1, R2 = cands[0][0], cands[2][0]
    rel = R2 @ R1.T
    print("angle of R2 R1^T = %.3f deg" % angle_deg(rel))
    w, V = np.linalg.eig(rel)
    axis = np.real(V[:, np.argmin(abs(w - 1))])
    print("angle between that axis and the baseline direction t: %.3f deg" % min(vec_angle_deg(axis, cands[0][1]), 180 - vec_angle_deg(axis, cands[0][1])))
    print("candidate | points in front of both cameras (of 50) | rotation error (deg) | t-direction error (deg)")
    names = ["(R1, +t)", "(R1, -t)", "(R2, +t)", "(R2, -t)"]
    for nm, (R, t), c in zip(names, cands, counts):
        re_, te_ = pose_errors(R, t, sc["R"], sc["t"])
        print(f"{nm} | {c:2d} | {re_:7.3f} | {te_:7.3f}")
    return sc, cands, counts, n1, n2


def sweep(settings, trials=200, **fixed):
    rows = []
    for si, val in enumerate(settings):
        re_, te_, ok = [], [], 0
        for k in range(trials):
            kw = dict(fixed)
            kw.update(val)
            sc = make_scene(1000 * (si + 1) + k, **kw)
            n1, n2 = to_normalised(sc["x1"]), to_normalised(sc["x2"])
            (R, t), _, _, _ = recover_pose(n1, n2)
            if np.linalg.norm(sc["t"]) < 1e-12:        # pure rotation: the translation direction does not exist
                r, te = angle_deg(R.T @ sc["R"]), np.nan
                ok += int(r < 5)
            else:
                r, te = pose_errors(R, t, sc["R"], sc["t"])
                ok += int(r < 5 and te < 30)           # "correct candidate": right branch of the 4-fold ambiguity
            re_.append(r); te_.append(te)
        rows.append((val, np.array(re_), np.array(te_), ok / trials))
    return rows


def fmt_row(label, re_, te_, ok):
    q = lambda a, p: np.percentile(a, p)
    rot = f"{label} | rot err median {np.median(re_):6.3f} (p10 {q(re_,10):6.3f}, p90 {q(re_,90):7.3f}) deg"
    if np.isnan(te_).all():
        return rot + f" | t-dir err undefined (t = 0) | rotation within 5 deg {100*ok:5.1f} %"
    return (rot + f" | t-dir err median {np.median(te_):6.2f} (p10 {q(te_,10):6.2f}, p90 {q(te_,90):6.2f}) deg"
            f" | correct branch {100*ok:5.1f} %")


def main():
    sc, cands, counts, n1, n2 = demo()
    # no-noise sanity check: exact recovery
    s0 = make_scene(7, sigma=0.0)
    (R, t), _, c, _ = recover_pose(to_normalised(s0["x1"]), to_normalised(s0["x2"]))
    r, te = pose_errors(R, t, s0["R"], s0["t"])
    print(f"\nSanity check, zero noise: rotation error {r:.2e} deg, t-direction error {te:.2e} deg, points in front {max(c)}/50")

    print("\n== Noise sweep: 200 scenes per row, N=50, baseline 1 (depth 4-8) ==")
    noise = [0.0, 0.25, 0.5, 1.0, 2.0, 4.0]
    rows_n = sweep([dict(sigma=s) for s in noise], trials=200)
    for (v, re_, te_, ok) in rows_n:
        print(fmt_row(f"sigma={v['sigma']:4.2f} px", re_, te_, ok))

    print("\n== Baseline sweep: 200 scenes per row, N=50, noise 1 px (depth 4-8) ==")
    bases = [0.0, 0.02, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0]
    rows_b = sweep([dict(baseline=b) for b in bases], trials=200, sigma=1.0)
    for (v, re_, te_, ok) in rows_b:
        print(fmt_row(f"baseline={v['baseline']:4.2f}", re_, te_, ok))

    print("\n== Number of matches, noise 1 px, baseline 1: 200 scenes per row ==")
    ns = [8, 12, 20, 50, 200]
    rows_m = sweep([dict(n=m) for m in ns], trials=200, sigma=1.0)
    for (v, re_, te_, ok) in rows_m:
        print(fmt_row(f"N={v['n']:3d}", re_, te_, ok))

    # ---------------------------------------------------------------- figures
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10, "svg.hashsalt": "essential", "svg.fonttype": "none"})

    fig, axs = plt.subplots(1, 4, figsize=(12.5, 3.6), sharex=True, sharey=True)
    names = ["(R1, +t)", "(R1, -t)", "(R2, +t)", "(R2, -t)"]
    for ax, nm, (R, t), c in zip(axs, names, cands, counts):
        cnt, X = count_in_front(R, t, n1, n2)
        z2 = (X @ R.T + t)[:, 2]
        front = (X[:, 2] > 0) & (z2 > 0)
        # true scale: rescale |t| to the true baseline so the pictures are comparable
        s = np.linalg.norm(sc["t"])
        Xs, ts = X * s, t * s
        ax.scatter(Xs[front, 0], Xs[front, 2], s=9, c="#16a34a", label="in front of both")
        ax.scatter(Xs[~front, 0], Xs[~front, 2], s=9, c="#dc2626", label="behind a camera")
        C2 = -R.T @ ts
        d2 = R.T @ np.array([0, 0, 1.0])
        for C, d, col in [(np.zeros(3), np.array([0, 0, 1.0]), "#1d4ed8"), (C2, d2, "#9333ea")]:
            ax.plot(C[0], C[2], "s", color=col, ms=7)
            ax.annotate("", xy=(C[0] + 1.3 * d[0], C[2] + 1.3 * d[2]), xytext=(C[0], C[2]),
                        arrowprops=dict(arrowstyle="-|>", color=col, lw=1.6))
        ax.set_title(f"{nm}: {cnt}/50 in front", fontsize=10)
        ax.set_xlabel("X"); ax.grid(alpha=0.25); ax.set_xlim(-14, 14); ax.set_ylim(-14, 14)
    axs[0].set_ylabel("Z (top view)")
    axs[0].legend(loc="lower left", fontsize=7, frameon=False)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "essential-candidates.svg"))
    if os.environ.get("ESS_PNG"):                       # optional raster preview
        fig.savefig(os.environ["ESS_PNG"] + "-candidates.png", dpi=80)
    plt.close(fig)

    fig, axs = plt.subplots(1, 2, figsize=(10.5, 3.6))
    xs = np.array(noise[1:])                            # sigma = 0 cannot be shown on a log axis
    for key, lab, col in [(2, "translation direction", "#9333ea"), (1, "rotation", "#1d4ed8")]:
        med = [np.median(r[key]) for r in rows_n[1:]]
        lo = [np.percentile(r[key], 10) for r in rows_n[1:]]
        hi = [np.percentile(r[key], 90) for r in rows_n[1:]]
        axs[0].plot(range(len(xs)), med, "o-", color=col, label=lab + " (median)")
        axs[0].fill_between(range(len(xs)), lo, hi, color=col, alpha=0.15)
    axs[0].set_xticks(range(len(xs))); axs[0].set_xticklabels([str(x) for x in noise[1:]])
    axs[0].set_xlabel("pixel noise sigma"); axs[0].set_ylabel("error (degrees)"); axs[0].set_yscale("log")
    axs[0].set_title("Error vs noise (200 scenes, 10-90 % band)"); axs[0].legend(fontsize=8, frameon=False); axs[0].grid(alpha=0.25, which="both")
    bx = np.array(bases)
    for key, lab, col in [(2, "translation direction", "#9333ea"), (1, "rotation", "#1d4ed8")]:
        med = [np.median(r[key]) for r in rows_b]
        lo = [np.percentile(r[key], 10) for r in rows_b]
        hi = [np.percentile(r[key], 90) for r in rows_b]
        axs[1].plot(range(len(bx)), med, "o-", color=col, label=lab + " (median)")
        axs[1].fill_between(range(len(bx)), lo, hi, color=col, alpha=0.15)
    axs[1].set_xticks(range(len(bx))); axs[1].set_xticklabels([str(x) for x in bases])
    axs[1].set_xlabel("baseline (scene depth 4-8)"); axs[1].set_yscale("log")
    axs[1].set_title("Error vs baseline (noise 1 px)"); axs[1].grid(alpha=0.25, which="both")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "essential-errors.svg"))
    if os.environ.get("ESS_PNG"):
        fig.savefig(os.environ["ESS_PNG"] + "-errors.png", dpi=80)
    plt.close(fig)
    print("\nfigures written to", OUT)


if __name__ == "__main__":
    main()
