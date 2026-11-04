"""Gradient descent vs. conjugate gradient and the condition number; effect of standardising features.
Reproduces every number and figure in the Shopsmon article
"Gradient descent and the condition number: why least squares gets slow".
Requires: numpy, matplotlib.   Run: python gd_conditioning.py [--no-fig]
"""
import os
import sys
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "img", "blog")
TOL = 1e-6


def a_norm(A, e):
    return float(np.sqrt(e @ (A @ e)))


def gd_iters(A, b, x_star, step, tol=TOL, cap=300_000):
    """Fixed-step gradient descent on f(x)=1/2 x'Ax - b'x from x0=0.
    Returns (k, ratio): the first k with ||x_k-x*||_A <= tol*||x_0-x*||_A (k=None if the cap is hit) and the final ratio."""
    x = np.zeros_like(b)
    e0 = a_norm(A, x - x_star)
    for k in range(1, cap + 1):
        x = x - step * (A @ x - b)
        ratio = a_norm(A, x - x_star) / e0
        if ratio <= tol:
            return k, ratio
    return None, ratio


def cg_iters(A, b, x_star, tol=TOL, cap=100_000):
    """Conjugate gradient from x0=0; same stopping rule in the A-norm."""
    x = np.zeros_like(b)
    r = b - A @ x
    p = r.copy()
    rs = r @ r
    e0 = a_norm(A, x - x_star)
    for k in range(1, cap + 1):
        Ap = A @ p
        alpha = rs / (p @ Ap)
        x = x + alpha * p
        r = r - alpha * Ap
        if a_norm(A, x - x_star) <= tol * e0:
            return k
        rs_new = r @ r
        p = r + (rs_new / rs) * p
        rs = rs_new
    return None


def make_spd(kappa, d, rng):
    Q, _ = np.linalg.qr(rng.standard_normal((d, d)))
    lam = np.logspace(0, np.log10(kappa), d)  # eigenvalues from 1 to kappa
    return (Q * lam) @ Q.T, lam


def experiment_quadratics():
    rng = np.random.default_rng(3)
    d = 100
    rows = []
    for kappa in (10, 100, 1000, 10000):
        A, lam = make_spd(kappa, d, rng)
        b = rng.standard_normal(d)
        x_star = np.linalg.solve(A, b)
        step = 2.0 / (lam[0] + lam[-1])                      # optimal fixed step
        rho = (kappa - 1) / (kappa + 1)
        k_gd_pred = int(np.ceil(np.log(TOL) / np.log(rho)))  # from ||e_k||_A <= rho^k ||e_0||_A
        k_gd, _ = gd_iters(A, b, x_star, step)
        sq = np.sqrt(kappa)
        q = (sq - 1) / (sq + 1)
        k_cg_bound = int(np.ceil(np.log(TOL / 2) / np.log(q)))  # from ||e_k||_A <= 2 q^k ||e_0||_A
        k_cg = cg_iters(A, b, x_star)
        rows.append((kappa, rho, k_gd_pred, k_gd, q, k_cg_bound, k_cg))
    return rows


def sanity_exact_rate():
    """2-D diagonal quadratic: with the optimal step the error norm shrinks by exactly rho per step."""
    kappa = 50.0
    A = np.diag([1.0, kappa])
    x = np.array([1.0, 1.0])
    step = 2.0 / (1.0 + kappa)
    rho = (kappa - 1) / (kappa + 1)
    e0 = np.linalg.norm(x)
    for _ in range(25):
        x = x - step * (A @ x)
    return np.linalg.norm(x) / e0, rho ** 25


def make_regression(rng, n=2000):
    area = rng.normal(100, 30, n)                 # m^2
    rooms = rng.integers(1, 7, n).astype(float)   # 1..6
    age = rng.uniform(0, 50, n)                   # years
    dist = rng.normal(5, 2, n)                    # km
    X = np.column_stack([np.ones(n), area, rooms, age, dist])
    w_true = np.array([20.0, 1.5, 4.0, -0.3, -2.0])
    y = X @ w_true + rng.normal(0, 5, n)
    return X, y


def experiment_standardise():
    rng = np.random.default_rng(5)
    X, y = make_regression(rng)
    n = len(y)
    mu, sd = X[:, 1:].mean(axis=0), X[:, 1:].std(axis=0)
    Xc = X.copy()
    Xc[:, 1:] = X[:, 1:] - mu                       # centred only
    Xs = X.copy()
    Xs[:, 1:] = (X[:, 1:] - mu) / sd                # centred and scaled to unit variance
    res = {}
    for name, M in (("raw", X), ("centred", Xc), ("standardised", Xs)):
        A = M.T @ M / n
        b = M.T @ y / n
        lam = np.linalg.eigvalsh(A)
        kappa = lam[-1] / lam[0]
        x_star = np.linalg.solve(A, b)
        step = 2.0 / (lam[0] + lam[-1])
        rho = (kappa - 1) / (kappa + 1)
        pred = int(np.ceil(np.log(TOL) / np.log(rho)))
        k_gd, ratio = gd_iters(A, b, x_star, step)
        k_cg = cg_iters(A, b, x_star)
        res[name] = dict(kappa=kappa, pred=pred, gd=k_gd, gd_ratio=ratio, cg=k_cg, lam_min=lam[0], lam_max=lam[-1])
    return res


def figures(rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10, "svg.fonttype": "none", "axes.spines.top": False, "axes.spines.right": False})
    os.makedirs(OUT, exist_ok=True)

    # Figure 1: GD paths on two quadratics, optimal fixed step
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 4.0))
    for ax, kappa in zip(axes, (2.0, 20.0)):
        A = np.diag([1.0, kappa])
        step = 2.0 / (1.0 + kappa)
        x = np.array([6.0, 1.0]) if kappa > 5 else np.array([3.0, 1.5])
        path = [x.copy()]
        for _ in range(14):
            x = x - step * (A @ x)
            path.append(x.copy())
        path = np.array(path)
        gx = np.linspace(-7, 7, 300)
        gy = np.linspace(-2.2, 2.2, 300)
        GX, GY = np.meshgrid(gx, gy)
        Z = 0.5 * (GX ** 2 + kappa * GY ** 2)
        ax.contour(GX, GY, Z, levels=[0.25, 1, 2.5, 6, 12, 22, 36], colors="#9aa7bd", linewidths=0.8)
        ax.plot(path[:, 0], path[:, 1], "-o", color="#2f6df6", ms=3.5, lw=1.4)
        ax.plot([0], [0], marker="*", color="#d93a3a", ms=11, ls="none")
        ax.set_title(f"condition number $\\kappa$ = {kappa:g},  rate $\\rho$ = {(kappa-1)/(kappa+1):.3f}")
        ax.set_xlabel("$x_1$")
        ax.set_ylabel("$x_2$")
        ax.set_xlim(-7, 7)
        ax.set_ylim(-2.2, 2.2)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "gd-paths.svg"), format="svg")
    plt.close(fig)

    # Figure 2: iterations to reach 1e-6 vs kappa
    kap = np.array([r[0] for r in rows], float)
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.loglog(kap, [r[3] for r in rows], "o-", color="#2f6df6", label="gradient descent (measured)")
    ax.loglog(kap, [r[2] for r in rows], "--", color="#2f6df6", alpha=0.6, label="GD bound: ln(1e-6)/ln(\u03c1)")
    ax.loglog(kap, [r[6] for r in rows], "s-", color="#d93a3a", label="conjugate gradient (measured)")
    ax.loglog(kap, [r[5] for r in rows], "--", color="#d93a3a", alpha=0.6, label="CG bound")
    ax.set_xlabel("condition number \u03ba of A")
    ax.set_ylabel("iterations to reach 1e-6 (A-norm error)")
    ax.legend(frameon=False, fontsize=9)
    ax.grid(True, which="both", alpha=0.25)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "gd-iterations.svg"), format="svg")
    plt.close(fig)


def main():
    a, b = sanity_exact_rate()
    print(f"sanity (2-D, kappa=50, 25 steps): error ratio {a:.6e} vs rho^25 {b:.6e}")
    rows = experiment_quadratics()
    print("kappa | rho | GD bound | GD measured | q=(sqrt k-1)/(sqrt k+1) | CG bound | CG measured")
    for r in rows:
        print(f"{r[0]:>6} | {r[1]:.6f} | {r[2]:>6} | {r[3]} | {r[4]:.4f} | {r[5]:>4} | {r[6]}")
    res = experiment_standardise()
    for k, v in res.items():
        print(k, f"lam_min={v['lam_min']:.4g} lam_max={v['lam_max']:.4g} kappa={v['kappa']:.4g} GD bound={v['pred']} GD measured={v['gd']} (error ratio at stop {v['gd_ratio']:.3e}) CG measured={v['cg']}")
    if "--no-fig" not in sys.argv:
        figures(rows)
        print("figures written to", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
