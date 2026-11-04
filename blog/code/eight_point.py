"""Eight-point algorithm for the fundamental matrix: raw vs. Hartley-normalised.
Reproduces every number and figure in the Shopsmon article
"The eight-point algorithm and why normalisation matters".
Requires: numpy, matplotlib.   Run: python eight_point.py [--no-fig]
"""
import sys
import numpy as np

K = np.array([[800.0, 0, 320.0], [0, 800.0, 240.0], [0, 0, 1.0]])


def skew(t):
    return np.array([[0, -t[2], t[1]], [t[2], 0, -t[0]], [-t[1], t[0], 0]])


def rot_y(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


# Ground-truth two-view geometry: camera 1 = [I|0], camera 2 = [R|t]
R_true = rot_y(np.deg2rad(-8.0))
t_true = np.array([-1.0, 0.05, 0.05])
F_true = np.linalg.inv(K).T @ skew(t_true) @ R_true @ np.linalg.inv(K)
F_true /= np.linalg.norm(F_true)


def project(X, R, t):
    Xc = X @ R.T + t
    x = Xc @ K.T
    return x[:, :2] / x[:, 2:3]


def make_points(rng, n):
    return np.column_stack([rng.uniform(-1, 1, n), rng.uniform(-0.75, 0.75, n), rng.uniform(4, 8, n)])


def normalise(pts):
    """Hartley normalisation: centroid -> origin, mean distance -> sqrt(2)."""
    c = pts.mean(axis=0)
    d = np.sqrt(((pts - c) ** 2).sum(axis=1)).mean()
    s = np.sqrt(2) / d
    T = np.array([[s, 0, -s * c[0]], [0, s, -s * c[1]], [0, 0, 1.0]])
    ph = np.column_stack([pts, np.ones(len(pts))]) @ T.T
    return ph, T


def eight_point(p1, p2, normalised):
    """p1, p2: (N,2) pixel coordinates, N>=8. Convention: x2^T F x1 = 0."""
    if normalised:
        h1, T1 = normalise(p1)
        h2, T2 = normalise(p2)
    else:
        h1 = np.column_stack([p1, np.ones(len(p1))])
        h2 = np.column_stack([p2, np.ones(len(p2))])
        T1 = T2 = np.eye(3)
    # each row: kron(x2, x1) -> A f = 0 with f = vec(F) in row-major order
    A = np.stack([np.kron(b, a) for a, b in zip(h1, h2)])
    _, S, Vt = np.linalg.svd(A)
    F = Vt[-1].reshape(3, 3)
    # enforce rank 2
    U, D, Vt2 = np.linalg.svd(F)
    D[2] = 0.0
    F = U @ np.diag(D) @ Vt2
    F = T2.T @ F @ T1  # denormalise (identity if raw)
    return F / np.linalg.norm(F), S


def sym_epipolar_error(F, p1, p2):
    """Mean symmetric point-to-epipolar-line distance in pixels."""
    h1 = np.column_stack([p1, np.ones(len(p1))])
    h2 = np.column_stack([p2, np.ones(len(p2))])
    l2 = h1 @ F.T      # epipolar lines in image 2
    l1 = h2 @ F        # epipolar lines in image 1
    num = np.abs((h2 * l2).sum(1))
    d2 = num / np.hypot(l2[:, 0], l2[:, 1])
    d1 = num / np.hypot(l1[:, 0], l1[:, 1])
    return float(np.mean(0.5 * (d1 + d2)))


def run(sigmas, n_corr=20, trials=300, n_test=1000, seed=11):
    rng = np.random.default_rng(seed)
    # fixed noise-free test set (never used for estimation)
    Xt = make_points(rng, n_test)
    t1, t2 = project(Xt, np.eye(3), np.zeros(3)), project(Xt, R_true, t_true)
    rows = []
    for sg in sigmas:
        e_raw, e_nrm = [], []
        for _ in range(trials):
            X = make_points(rng, n_corr)
            q1, q2 = project(X, np.eye(3), np.zeros(3)), project(X, R_true, t_true)
            q1 = q1 + rng.normal(0, sg, q1.shape)
            q2 = q2 + rng.normal(0, sg, q2.shape)
            Fr, _ = eight_point(q1, q2, False)
            Fn, _ = eight_point(q1, q2, True)
            e_raw.append(sym_epipolar_error(Fr, t1, t2))
            e_nrm.append(sym_epipolar_error(Fn, t1, t2))
        rows.append((sg, float(np.median(e_raw)), float(np.median(e_nrm))))
    return rows


def conditioning(n_corr=20, trials=300, seed=5):
    """Median ratio S[0]/S[7] of the design matrix singular values (noise-free), raw vs normalised."""
    rng = np.random.default_rng(seed)
    r_raw, r_nrm = [], []
    for _ in range(trials):
        X = make_points(rng, n_corr)
        q1, q2 = project(X, np.eye(3), np.zeros(3)), project(X, R_true, t_true)
        _, Sr = eight_point(q1, q2, False)
        _, Sn = eight_point(q1, q2, True)
        r_raw.append(Sr[0] / Sr[7])
        r_nrm.append(Sn[0] / Sn[7])
    return float(np.median(r_raw)), float(np.median(r_nrm))


def geometry_figure(path):
    """Schematic cross-section of the epipolar plane (cameras C, C', point X)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    C, Cp, X = np.array([0.0, 0.0]), np.array([8.0, 0.0]), np.array([4.5, 5.0])
    d1 = np.array([0.5, np.sqrt(3) / 2])
    d2 = np.array([-0.5, np.sqrt(3) / 2])
    f = 1.6
    dir1, dir2 = np.array([np.sqrt(3) / 2, -0.5]), np.array([np.sqrt(3) / 2, 0.5])
    o1, o2 = C + f * d1, Cp + f * d2

    def hit(c, target, d):  # ray c->target meets the plane {p: (p-c).d = f}
        v = target - c
        return c + v * (f / (v @ d))

    x1, x2 = hit(C, X, d1), hit(Cp, X, d2)
    e1 = np.array([f / d1[0], 0.0])           # baseline meets image-plane line 1
    e2 = np.array([8 - f / (-d2[0]), 0.0])    # baseline meets image-plane line 2
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    ax.fill([*C, *Cp, *X][0::2], [*C, *Cp, *X][1::2], color="#cfe0ff", alpha=0.6, label="epipolar plane (cross-section)")
    ax.plot([C[0], Cp[0]], [C[1], Cp[1]], "k-", lw=1.6)
    ax.plot([C[0], X[0]], [C[1], X[1]], "-", color="#555")
    ax.plot([Cp[0], X[0]], [Cp[1], X[1]], "-", color="#555")
    for o, d in ((o1, dir1), (o2, dir2)):
        a = o + d * (-1.5 if d is dir1 else -3.0)
        b = o + d * (3.0 if d is dir1 else 1.5)
        ax.plot([a[0], b[0]], [a[1], b[1]], "-", color="#2f6bff", lw=2.2)
    pts = [(C, "C", (-0.5, -0.45)), (Cp, "C'", (0.15, -0.45)), (X, "X", (0.15, 0.15)),
           (x1, "x", (-0.5, 0.2)), (x2, "x'", (0.2, 0.2)), (e1, "e", (-0.1, -0.5)), (e2, "e'", (-0.1, -0.5))]
    for p, lab, off in pts:
        ax.plot(*p, "o", color="#d9534f" if lab in ("x", "x'", "e", "e'") else "k", ms=6)
        ax.annotate(lab, p + np.array(off), fontsize=13)
    ax.text(4.0, -0.95, "baseline", ha="center", fontsize=11)
    ax.text(0.2, 2.4, "image plane 1\n(section)", color="#2f6bff", fontsize=9, ha="right")
    ax.text(7.9, 2.4, "image plane 2\n(section)", color="#2f6bff", fontsize=9, ha="left")
    ax.set_xlim(-1.8, 9.8)
    ax.set_ylim(-1.3, 5.6)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path)


if __name__ == "__main__":
    # sanity: noise-free, both variants must reproduce F_true (up to sign)
    rng = np.random.default_rng(0)
    X = make_points(rng, 20)
    q1, q2 = project(X, np.eye(3), np.zeros(3)), project(X, R_true, t_true)
    for name, flag in (("raw", False), ("normalised", True)):
        F, _ = eight_point(q1, q2, flag)
        diff = min(np.linalg.norm(F - F_true), np.linalg.norm(F + F_true))
        print(f"sanity {name}: ||F - F_true|| = {diff:.2e}")
    print("rank of F_true:", np.linalg.matrix_rank(F_true))
    cr, cn = conditioning()
    print(f"median sigma1/sigma8 of A (noise-free): raw={cr:.3e}  normalised={cn:.3e}")
    sigmas = [0.0, 0.1, 0.5, 1.0, 2.0]
    rows = run(sigmas)
    print("sigma_px | raw median err (px) | normalised median err (px)")
    for sg, a, b in rows:
        print(f"{sg:8.2f} | {a:19.4f} | {b:26.4f}")
    if "--no-fig" not in sys.argv:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        pos = [r for r in rows if r[0] > 0]
        fig, ax = plt.subplots(figsize=(6.4, 4.2))
        ax.loglog([r[0] for r in pos], [r[1] for r in pos], "o-", label="raw 8-point", color="#d9534f")
        ax.loglog([r[0] for r in pos], [r[2] for r in pos], "s-", label="normalised 8-point", color="#2f6bff")
        ax.set_xlabel("image noise sigma (px)")
        ax.set_ylabel("median mean epipolar distance on test points (px)")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig("../../assets/img/blog/eight-point-error.svg")
        geometry_figure("../../assets/img/blog/eight-point-geometry.svg")
        print("figures written")
