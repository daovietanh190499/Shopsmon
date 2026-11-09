"""Bundle adjustment from scratch: Levenberg-Marquardt with the Schur complement, on synthetic multi-view scenes.

Run:  python bundle_adjustment.py      (about 7 minutes, mostly the dense baseline at 6336 unknowns; Python 3.12, NumPy, SciPy, Matplotlib)
Everything is seeded; the numbers printed here are the ones quoted in the blog post.
Writes ba-structure.svg and ba-convergence.svg next to this script (or into $BA_OUT).

Model: C pinhole cameras (fixed, known K), P 3D points, N observations (camera i sees point j at pixel u_ij).
Unknowns: per camera a rotation vector r_i and a translation t_i (x_cam = R(r_i) X + t_i), per point X_j.
Residual of observation (i, j): project(r_i, t_i, X_j) - u_ij, two numbers.
"""
import os
import time

import numpy as np
import scipy.sparse as sp
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["svg.hashsalt"] = "shopsmon-ba"      # deterministic ids in the SVG
plt.rcParams["svg.fonttype"] = "none"

OUT = os.environ.get("BA_OUT", os.path.dirname(os.path.abspath(__file__)))
F, CX, CY = 800.0, 320.0, 240.0                  # focal length (px) and principal point, same for all cameras
PP = np.array([CX, CY])
D6, D3 = np.arange(6), np.arange(3)


# ----------------------------------------------------------------------------------- scene
def look_at(C, target=np.zeros(3), up=np.array([0.0, 1.0, 0.0])):
    """World-to-camera rotation (rows = camera axes) for a camera at C looking at target."""
    z = target - C
    z = z / np.linalg.norm(z)
    x = np.cross(z, up)
    x = x / np.linalg.norm(x)
    y = np.cross(z, x)
    return np.vstack([x, y, z])


def make_scene(seed, n_cams, n_pts, sigma, mean_views=None, arc_deg=80.0, radius=8.0):
    """Points in a 4 x 3 x 2 box around the origin; cameras on an arc at distance `radius`, looking at the origin.
    Each point is seen by ~mean_views cameras (at least 2; default 60 % of the cameras); pixel noise sigma."""
    rng = np.random.default_rng(seed)
    X = np.column_stack([rng.uniform(-2, 2, n_pts), rng.uniform(-1.5, 1.5, n_pts), rng.uniform(-1, 1, n_pts)])
    ang = np.radians(np.linspace(-arc_deg / 2, arc_deg / 2, n_cams))
    cen = np.column_stack([radius * np.sin(ang), 0.8 * np.sin(2 * ang + 1.0), -radius * np.cos(ang)])
    Rm = np.array([look_at(c) for c in cen])
    t = -np.einsum("nij,nj->ni", Rm, cen)
    cam = np.hstack([Rot.from_matrix(Rm).as_rotvec(), t])
    p_obs = 0.6 if mean_views is None else min(0.6, mean_views / n_cams)
    vis = rng.random((n_cams, n_pts)) < p_obs
    for j in np.nonzero(vis.sum(0) < 2)[0]:
        vis[rng.choice(n_cams, 2, replace=False), j] = True
    ci, pi = np.nonzero(vis)
    uv_clean = project(cam[ci], X[pi])
    uv = uv_clean + rng.normal(scale=sigma, size=uv_clean.shape)
    return dict(cam=cam, X=X, cen=cen, ci=ci, pi=pi, uv=uv, sigma=sigma, C=n_cams, P=n_pts)


def project(cam, X):
    """cam: (N, 6) rotation vector + translation; X: (N, 3). Returns (N, 2) pixels."""
    Xc = Rot.from_rotvec(cam[:, :3]).apply(X) + cam[:, 3:]
    z = Xc[:, 2:3]
    z = np.where(np.abs(z) < 1e-9, 1e-9, z)
    return F * Xc[:, :2] / z + PP


def triangulate_all(cam, ci, pi, uv, P):
    """Linear (DLT) triangulation of every point from all of its observations, given (possibly wrong) cameras."""
    Rm = Rot.from_rotvec(cam[:, :3]).as_matrix()
    Pm = np.concatenate([Rm, cam[:, 3:, None]], axis=2)             # (C, 3, 4)
    xn = (uv - PP) / F
    order = np.argsort(pi, kind="stable")
    bounds = np.searchsorted(pi[order], np.arange(P + 1))
    X = np.empty((P, 3))
    for j in range(P):
        o = order[bounds[j]:bounds[j + 1]]
        Pj = Pm[ci[o]]
        A = np.concatenate([xn[o, 0][:, None] * Pj[:, 2] - Pj[:, 0], xn[o, 1][:, None] * Pj[:, 2] - Pj[:, 1]])
        h = np.linalg.svd(A)[2][-1]
        X[j] = h[:3] / h[3]
    return X


def init_guess(sc, rot_deg, cen_noise, seed):
    """Perturbed cameras (rotation noise rot_deg per axis, centre noise cen_noise per axis) + points triangulated from them."""
    rng = np.random.default_rng(seed)
    C = sc["C"]
    Rt = Rot.from_rotvec(sc["cam"][:, :3])
    Rn = Rot.from_rotvec(np.radians(rng.normal(0, rot_deg, (C, 3)))) * Rt
    cen = sc["cen"] + rng.normal(0, cen_noise, (C, 3))
    t = -np.einsum("nij,nj->ni", Rn.as_matrix(), cen)
    cam = np.hstack([Rn.as_rotvec(), t])
    return cam, triangulate_all(cam, sc["ci"], sc["pi"], sc["uv"], sc["P"])


# ----------------------------------------------------------------------------------- residuals, Jacobian blocks
def residual(cam, pts, ci, pi, uv):
    return project(cam[ci], pts[pi]) - uv


def jac_blocks(camo, Xo, h=1e-6):
    """Per-observation Jacobian blocks by central differences, all observations at once: (N,2,6) and (N,2,3)."""
    N = len(camo)
    Jc, Jp = np.empty((N, 2, 6)), np.empty((N, 2, 3))
    for k in range(6):
        a, b = camo.copy(), camo.copy()
        a[:, k] += h
        b[:, k] -= h
        Jc[:, :, k] = (project(a, Xo) - project(b, Xo)) / (2 * h)
    for k in range(3):
        a, b = Xo.copy(), Xo.copy()
        a[:, k] += h
        b[:, k] -= h
        Jp[:, :, k] = (project(camo, a) - project(camo, b)) / (2 * h)
    return Jc, Jp


def scatter(idx, vals, size):
    """Sum vals[n] into slot idx[n] (vals has shape (N, ...)); uses bincount, much faster than np.add.at."""
    flat = vals.reshape(len(idx), -1)
    out = np.empty((size, flat.shape[1]))
    for k in range(flat.shape[1]):
        out[:, k] = np.bincount(idx, weights=flat[:, k], minlength=size)
    return out.reshape((size,) + vals.shape[1:])


def jac_sparse_full(Jc, Jp, ci, pi, C):
    """The full (2N x (6C+3P)) sparse Jacobian from the blocks (used by the dense baseline and by SciPy)."""
    N = len(ci)
    rows = 2 * np.arange(N)[:, None, None] + np.arange(2)[None, :, None]
    rc = np.broadcast_to(rows, (N, 2, 6)).ravel()
    cc = np.broadcast_to(6 * ci[:, None, None] + D6[None, None, :], (N, 2, 6)).ravel()
    rp = np.broadcast_to(rows, (N, 2, 3)).ravel()
    cp = np.broadcast_to(6 * C + 3 * pi[:, None, None] + D3[None, None, :], (N, 2, 3)).ravel()
    return sp.csr_matrix((np.concatenate([Jc.ravel(), Jp.ravel()]), (np.concatenate([rc, rp]), np.concatenate([cc, cp]))),
                         shape=(2 * N, 6 * C + int(pi.max() + 1) * 3))


class Normal:
    """Normal-equation blocks at the current parameters:  [[B, E], [E^T, Cm]] [dc; dp] = -[gc; gp]."""

    def __init__(self, cam, pts, sc):
        ci, pi, C, P = sc["ci"], sc["pi"], sc["C"], sc["P"]
        self.sc = sc
        self.r = residual(cam, pts, ci, pi, sc["uv"])
        self.cost = 0.5 * float(np.sum(self.r ** 2))
        self.Jc, self.Jp = jac_blocks(cam[ci], pts[pi])
        self.B = scatter(ci, np.einsum("nri,nrj->nij", self.Jc, self.Jc), C)
        self.Cm = scatter(pi, np.einsum("nri,nrj->nij", self.Jp, self.Jp), P)
        self.E = np.einsum("nri,nrj->nij", self.Jc, self.Jp)                      # (N, 6, 3): one block per observation
        self.gc = scatter(ci, np.einsum("nri,nr->ni", self.Jc, self.r), C)
        self.gp = scatter(pi, np.einsum("nri,nr->ni", self.Jp, self.r), P)
        rows = np.broadcast_to(6 * ci[:, None, None] + D6[None, :, None], self.E.shape).ravel()
        cols = np.broadcast_to(3 * pi[:, None, None] + D3[None, None, :], self.E.shape).ravel()
        self.Esp = sp.csr_matrix((self.E.ravel(), (rows, cols)), shape=(6 * C, 3 * P))


def solve_schur(nb, lam):
    """Schur complement step: eliminate the 3x3 point blocks, solve a (6C x 6C) system for the cameras, back-substitute."""
    C, P = nb.sc["C"], nb.sc["P"]
    Bd, Cd = nb.B.copy(), nb.Cm.copy()
    Bd[:, D6, D6] *= 1 + lam                       # Marquardt damping: scale the diagonal
    Cd[:, D3, D3] *= 1 + lam
    Cinv = sp.bsr_matrix((np.linalg.inv(Cd), np.arange(P), np.arange(P + 1)), shape=(3 * P, 3 * P))
    Bsp = sp.bsr_matrix((Bd, np.arange(C), np.arange(C + 1)), shape=(6 * C, 6 * C))
    S = (Bsp - nb.Esp @ Cinv @ nb.Esp.T).toarray()
    rhs = -nb.gc.ravel() + nb.Esp @ (Cinv @ nb.gp.ravel())
    dc = np.linalg.solve(S, rhs)
    dp = Cinv @ (-nb.gp.ravel() - nb.Esp.T @ dc)
    return dc.reshape(C, 6), dp.reshape(P, 3)


def solve_dense(nb, lam):
    """Baseline: form the full (6C+3P) normal matrix and solve it with a dense factorisation."""
    C, P = nb.sc["C"], nb.sc["P"]
    J = jac_sparse_full(nb.Jc, nb.Jp, nb.sc["ci"], nb.sc["pi"], C)
    H = (J.T @ J).toarray()
    g = J.T @ nb.r.ravel()
    d = np.arange(H.shape[0])
    H[d, d] *= 1 + lam
    delta = np.linalg.solve(H, -g)
    return delta[:6 * C].reshape(C, 6), delta[6 * C:].reshape(P, 3)


def lm(cam, pts, sc, max_iter=60, lam=1e-3, solver=solve_schur):
    """Levenberg-Marquardt. Returns cam, pts, history of RMS reprojection error, number of accepted steps."""
    N = len(sc["ci"])
    hist = []
    nb = Normal(cam, pts, sc)
    hist.append(np.sqrt(2 * nb.cost / (2 * N)))
    for it in range(max_iter):
        while True:
            try:
                dc, dp = solver(nb, lam)
                cam2, pts2 = cam + dc, pts + dp
                r2 = residual(cam2, pts2, sc["ci"], sc["pi"], sc["uv"])
                cost2 = 0.5 * float(np.sum(r2 ** 2))
            except np.linalg.LinAlgError:      # singular block (e.g. a point behind its cameras): damp harder
                cost2 = np.inf
            if np.isfinite(cost2) and cost2 < nb.cost:
                break
            lam *= 4
            if lam > 1e12:
                return cam, pts, hist, it
        rel = (nb.cost - cost2) / nb.cost
        cam, pts = cam2, pts2
        lam = max(lam / 3, 1e-9)
        nb = Normal(cam, pts, sc)
        hist.append(np.sqrt(2 * nb.cost / (2 * N)))
        if rel < 1e-9:
            break
    return cam, pts, hist, it + 1


# ----------------------------------------------------------------------------------- evaluation
def umeyama(src, dst):
    """Similarity (s, R, t) minimising |dst - (s R src + t)|."""
    ms, md = src.mean(0), dst.mean(0)
    cov = (dst - md).T @ (src - ms) / len(src)
    U, D, Vt = np.linalg.svd(cov)
    Sg = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        Sg[2, 2] = -1
    R = U @ Sg @ Vt
    s = np.trace(np.diag(D) @ Sg) / (((src - ms) ** 2).sum() / len(src))
    return s, R, md - s * R @ ms


def errors(cam, pts, sc, keep=None):
    """Gauge-free errors: align the estimate to the ground truth with a similarity, then measure.
    Returns RMS point error (scene units), RMS camera-centre error (scene units), RMS camera rotation error (deg).
    keep: optional boolean mask of the points to use (a point that ended far from the truth would otherwise
    dominate the alignment)."""
    Re = Rot.from_rotvec(cam[:, :3]).as_matrix()
    cen = -np.einsum("nji,nj->ni", Re, cam[:, 3:])
    keep = np.ones(len(pts), bool) if keep is None else keep
    s, Ra, ta = umeyama(np.vstack([cen, pts[keep]]), np.vstack([sc["cen"], sc["X"][keep]]))
    pe = np.linalg.norm(sc["X"][keep] - (s * pts[keep] @ Ra.T + ta), axis=1)
    ce = np.linalg.norm(sc["cen"] - (s * cen @ Ra.T + ta), axis=1)
    Rt = Rot.from_rotvec(sc["cam"][:, :3]).as_matrix()
    M = np.einsum("nji,njk->nik", Rt, np.einsum("nij,kj->nik", Re, Ra))       # R_true^T (R_est Ra^T)
    ang = np.degrees(np.arccos(np.clip((np.trace(M, axis1=1, axis2=2) - 1) / 2, -1, 1)))
    return float(np.sqrt(np.mean(pe ** 2))), float(np.sqrt(np.mean(ce ** 2))), float(np.sqrt(np.mean(ang ** 2)))


def expected_rms(sc):
    """RMS residual expected at the optimum: sigma * sqrt(dof / (2N)), dof = 2N - (6C + 3P - 7) (7 gauge freedoms)."""
    N = len(sc["ci"])
    dof = 2 * N - (6 * sc["C"] + 3 * sc["P"] - 7)
    return sc["sigma"] * np.sqrt(dof / (2 * N))


def rms_of(cam, pts, sc):
    return float(np.sqrt(np.mean(residual(cam, pts, sc["ci"], sc["pi"], sc["uv"]) ** 2)))


def scipy_solve(cam, pts, sc, loss="linear", f_scale=1.0):
    """SciPy trust-region reflective with the same analytic sparse Jacobian (tr_solver='lsmr')."""
    C, P = sc["C"], sc["P"]

    def fun(x):
        return residual(x[:6 * C].reshape(C, 6), x[6 * C:].reshape(P, 3), sc["ci"], sc["pi"], sc["uv"]).ravel()

    def jac(x):
        cm, ps = x[:6 * C].reshape(C, 6), x[6 * C:].reshape(P, 3)
        Jc, Jp = jac_blocks(cm[sc["ci"]], ps[sc["pi"]])
        return jac_sparse_full(Jc, Jp, sc["ci"], sc["pi"], C)

    sol = least_squares(fun, np.concatenate([cam.ravel(), pts.ravel()]), jac=jac, method="trf", tr_solver="lsmr",
                        x_scale="jac", loss=loss, f_scale=f_scale, ftol=1e-12, xtol=1e-12, gtol=1e-12, max_nfev=200)
    return sol.x[:6 * C].reshape(C, 6), sol.x[6 * C:].reshape(P, 3)


def pct(a, q):
    return float(np.percentile(a, q))


# ----------------------------------------------------------------------------------- experiments
def main():
    t00 = time.time()
    SIGMA, ROT, CEN = 0.5, 1.0, 0.1
    print(f"pinhole f = {F} px, principal point ({CX}, {CY}); box 4 x 3 x 2 at the origin; cameras at distance 8 on an 80 degree arc")

    # ---- 1. one scene: convergence, cross-checks
    print("\n== 1. One scene (seed 0): C = 10 cameras, P = 200 points, sigma = 0.5 px, initial error 1 deg / 0.1 units per axis")
    sc = make_scene(0, 10, 200, SIGMA)
    N = len(sc["ci"])
    cam0, pts0 = init_guess(sc, ROT, CEN, seed=1000)
    print(f"observations N = {N} (2N = {2 * N} residuals), unknowns 6C + 3P = {6 * sc['C'] + 3 * sc['P']}, gauge freedoms 7, "
          f"degrees of freedom = {2 * N - (6 * sc['C'] + 3 * sc['P'] - 7)}")
    cam1, pts1, hist, nit = lm(cam0, pts0, sc)
    exp = expected_rms(sc)
    print("RMS reprojection per iteration (px): " + ", ".join(f"{h:.4f}" for h in hist))
    print(f"initial RMS {hist[0]:.3f} px -> final {hist[-1]:.4f} px after {nit} iterations; "
          f"expected at optimum sigma*sqrt(dof/2N) = {exp:.4f} px; RMS of the noise realised on the observations = "
          f"{np.sqrt(np.mean((sc['uv'] - project(sc['cam'][sc['ci']], sc['X'][sc['pi']])) ** 2)):.4f} px; "
          f"RMS at the true parameters = {rms_of(sc['cam'], sc['X'], sc):.4f} px")
    e0, e1 = errors(cam0, pts0, sc), errors(cam1, pts1, sc)
    print(f"errors vs truth (point RMS, camera-centre RMS in units; rotation RMS in deg): initial {e0[0]:.4f}, {e0[1]:.4f}, {e0[2]:.3f}"
          f"  ->  after BA {e1[0]:.4f}, {e1[1]:.4f}, {e1[2]:.3f}")
    nb = Normal(cam0, pts0, sc)
    for lam in (1e-3, 1.0):
        a, b = solve_schur(nb, lam), solve_dense(nb, lam)
        dmax = max(np.abs(a[0] - b[0]).max(), np.abs(a[1] - b[1]).max())
        scale = max(np.abs(b[0]).max(), np.abs(b[1]).max())
        print(f"Schur vs dense step at lambda = {lam}: max |difference| = {dmax:.2e} (largest entry of the step {scale:.3e})")
    c2, p2 = scipy_solve(cam0, pts0, sc)
    print(f"SciPy least_squares (trf + lsmr, same Jacobian): final RMS {rms_of(c2, p2, sc):.4f} px (ours {hist[-1]:.4f}); "
          f"point RMS error {errors(c2, p2, sc)[0]:.4f} (ours {e1[0]:.4f})")
    # more scenes for hist plot
    hist_plot = hist

    # ---- 2. accuracy over 20 seeds
    print("\n== 2. 20 scenes (seeds 0-19), same setup: median (p10-p90)")
    ratios, f_rms, i_rms, pe0, pe1, ce0, ce1, re0, re1, its = ([] for _ in range(10))
    for s in range(20):
        sc = make_scene(s, 10, 200, SIGMA)
        c0, p0 = init_guess(sc, ROT, CEN, seed=1000 + s)
        c1, p1, h, n_it = lm(c0, p0, sc)
        ratios.append(h[-1] / expected_rms(sc))
        i_rms.append(h[0]); f_rms.append(h[-1]); its.append(n_it)
        a, b = errors(c0, p0, sc), errors(c1, p1, sc)
        pe0.append(a[0]); ce0.append(a[1]); re0.append(a[2]); pe1.append(b[0]); ce1.append(b[1]); re1.append(b[2])
    f = lambda v, d=4: f"{np.median(v):.{d}f} ({pct(v, 10):.{d}f}-{pct(v, 90):.{d}f})"
    print(f"RMS reprojection initial (px): {f(i_rms, 2)}")
    print(f"RMS reprojection final (px): {f(f_rms)}; final / expected: {f(ratios)}")
    print(f"point RMS error (units): initial {f(pe0)} -> after {f(pe1)}")
    print(f"camera-centre RMS error (units): initial {f(ce0)} -> after {f(ce1)}")
    print(f"camera rotation RMS error (deg): initial {f(re0, 3)} -> after {f(re1, 3)}")
    print(f"accepted LM iterations: {f(its, 1)}; max {max(its)}")

    # ---- 3. basin of convergence
    print("\n== 3. Initial error (rotation std per axis in deg; camera-centre std per axis in units = 0.1 x the rotation value) vs success; 30 scenes each")
    print("success = final RMS within 10 % of the expected optimum value")
    print("| rot. noise (deg/axis) | centre noise (units/axis) | initial RMS (px), median | success | median final RMS of failures (px) |")
    for rd in (0.5, 1, 2, 3, 5, 10):
        ok, init, bad = 0, [], []
        for s in range(30):
            sc = make_scene(s, 10, 200, SIGMA)
            c0, p0 = init_guess(sc, rd, 0.1 * rd, seed=2000 + s)
            c1, p1, h, _ = lm(c0, p0, sc, max_iter=100)
            init.append(h[0])
            if h[-1] <= 1.1 * expected_rms(sc):
                ok += 1
            else:
                bad.append(h[-1])
        print(f"| {rd} | {0.1 * rd:.2f} | {np.median(init):.1f} | {ok}/30 | {np.median(bad):.2f} |" if bad
              else f"| {rd} | {0.1 * rd:.2f} | {np.median(init):.1f} | {ok}/30 | - |")

    # ---- 4. cost of one step: Schur versus dense normal equations
    print("\n== 4. Time of the linear-system phase of one LM step (median of 3), P = 20 C points, ~8 views per point")
    print("| C | P | N obs | unknowns n | dense normal eq. (s) | Schur (s) | ratio | max |step difference| |")
    rows = []
    for C in (8, 16, 32, 64, 96):
        P = 20 * C
        sc = make_scene(5, C, P, SIGMA, mean_views=8)
        c0, p0 = init_guess(sc, ROT, CEN, seed=3000)
        nb = Normal(c0, p0, sc)
        td, ts = [], []
        for _ in range(3):
            t0 = time.perf_counter(); a = solve_dense(nb, 1e-3); td.append(time.perf_counter() - t0)
            t0 = time.perf_counter(); b = solve_schur(nb, 1e-3); ts.append(time.perf_counter() - t0)
        dmax = max(np.abs(a[0] - b[0]).max(), np.abs(a[1] - b[1]).max())
        rows.append((C, P, len(sc["ci"]), 6 * C + 3 * P, np.median(td), np.median(ts)))
        print(f"| {C} | {P} | {len(sc['ci'])} | {6 * C + 3 * P} | {np.median(td):.3f} | {np.median(ts):.3f} | {np.median(td) / np.median(ts):.1f} | {dmax:.1e} |")
    sc = make_scene(5, 96, 1920, SIGMA, mean_views=8)
    for rd, cn in ((0.5, 0.05), (1.0, 0.1)):
        c0, p0 = init_guess(sc, rd, cn, seed=3000)
        t0 = time.perf_counter()
        c1, p1, h, n_it = lm(c0, p0, sc)
        dt = time.perf_counter() - t0
        rn2 = np.sum(residual(c1, p1, sc["ci"], sc["pi"], sc["uv"]) ** 2, axis=1)
        pt_rms = np.sqrt(np.bincount(sc["pi"], weights=rn2, minlength=sc["P"]) / (2 * np.bincount(sc["pi"], minlength=sc["P"])))
        good = pt_rms <= 5.0                                    # points whose own RMS residual is above 5 px are reported separately
        og = good[sc["pi"]]
        rms_good = float(np.sqrt(rn2[og].sum() / (2 * og.sum())))
        print(f"full LM run with Schur, C = 96, P = 1920, N = {len(sc['ci'])}, initial error {rd} deg / {cn} units: "
              f"{dt:.1f} s, {n_it} iterations, RMS {h[0]:.2f} -> {h[-1]:.4f} px (expected {expected_rms(sc):.4f}); "
              f"{int((~good).sum())} points with own RMS residual above 5 px; without them RMS {rms_good:.4f} px, "
              f"point RMS error {errors(c1, p1, sc, keep=good)[0]:.4f} units, camera-centre RMS error {errors(c1, p1, sc, keep=good)[1]:.4f} units")

    # ---- 5. outliers: plain least squares versus Huber loss
    print("\n== 5. 5 % of the observations replaced by gross errors (30-80 px in a random direction); 10 scenes")
    print("| method | point RMS error (units) median (p10-p90) | camera rotation RMS error (deg) |")
    pl, hu, plr, hur, h2, h2r = [], [], [], [], [], []
    for s in range(10):
        sc = make_scene(s, 10, 200, SIGMA)
        rng = np.random.default_rng(4000 + s)
        N = len(sc["ci"])
        bad = rng.choice(N, int(round(0.05 * N)), replace=False)
        ang = rng.uniform(0, 2 * np.pi, len(bad))
        mag = rng.uniform(30, 80, len(bad))
        sc["uv"] = sc["uv"].copy()
        sc["uv"][bad] += np.column_stack([mag * np.cos(ang), mag * np.sin(ang)])
        c0, p0 = init_guess(sc, ROT, CEN, seed=2500 + s)
        c1, p1, _, _ = lm(c0, p0, sc)
        c2, p2 = scipy_solve(c0, p0, sc, loss="huber", f_scale=1.0)
        c3, p3 = scipy_solve(c1, p1, sc, loss="huber", f_scale=1.0)          # two-stage: Huber started from the LS solution
        a, b, d = errors(c1, p1, sc), errors(c2, p2, sc), errors(c3, p3, sc)
        pl.append(a[0]); plr.append(a[2]); hu.append(b[0]); hur.append(b[2]); h2.append(d[0]); h2r.append(d[2])
    print(f"| least squares (own LM) | {f(pl)} | {f(plr, 3)} |")
    print(f"| Huber loss, f_scale 1 px, started from the initial guess (SciPy) | {f(hu)} | {f(hur, 3)} |")
    print(f"| Huber loss, f_scale 1 px, started from the least-squares solution (SciPy) | {f(h2)} | {f(h2r, 3)} |")

    # ---- figures
    sc_s = make_scene(3, 5, 12, SIGMA, mean_views=3)
    cs, ps = init_guess(sc_s, ROT, CEN, seed=7)
    nbs = Normal(cs, ps, sc_s)
    Js = jac_sparse_full(nbs.Jc, nbs.Jp, sc_s["ci"], sc_s["pi"], sc_s["C"])
    Hs = (Js.T @ Js)
    Ss = (sp.bsr_matrix((nbs.B, np.arange(5), np.arange(6)), shape=(30, 30))
          - nbs.Esp @ sp.bsr_matrix((np.linalg.inv(nbs.Cm), np.arange(12), np.arange(13)), shape=(36, 36)) @ nbs.Esp.T)
    fig, ax = plt.subplots(1, 3, figsize=(10, 4.0), gridspec_kw=dict(width_ratios=[1, 1.2, 0.9]))
    for a_, M, ttl in ((ax[0], Js, f"Jacobian J ({Js.shape[0]} x {Js.shape[1]})"), (ax[1], Hs, f"J^T J ({Hs.shape[0]} x {Hs.shape[1]})"),
                       (ax[2], Ss, f"Schur S ({Ss.shape[0]} x {Ss.shape[1]})")):
        a_.spy(M.tocsr(), markersize=1.6 if M is not Ss else 4, color="#2563eb")
        a_.set_title(ttl, fontsize=10)
        a_.set_xticks([]); a_.set_yticks([])
    for x_ in (30 - 0.5,):
        ax[1].axvline(x_, color="#ef4444", lw=0.8); ax[1].axhline(x_, color="#ef4444", lw=0.8)
        ax[0].axvline(x_, color="#ef4444", lw=0.8)
    fig.suptitle("5 cameras, 12 points: left of the red line = camera parameters (6 each), right = point parameters (3 each)", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "ba-structure.svg"))
    plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    ax[0].semilogy(range(len(hist_plot)), hist_plot, "o-", color="#2563eb", label="RMS reprojection error")
    ax[0].axhline(exp, color="#ef4444", ls="--", label=f"expected at optimum ({exp:.3f} px)")
    ax[0].set_xlabel("LM iteration"); ax[0].set_ylabel("RMS reprojection error (px)")
    ax[0].set_title("Convergence on one scene (10 cameras, 200 points)", fontsize=10)
    ax[0].legend(fontsize=8)
    n_ = [r_[3] for r_ in rows]
    ax[1].loglog(n_, [r_[4] for r_ in rows], "s-", color="#ef4444", label="dense normal equations")
    ax[1].loglog(n_, [r_[5] for r_ in rows], "o-", color="#2563eb", label="Schur complement")
    ax[1].set_xlabel("number of unknowns n = 6C + 3P"); ax[1].set_ylabel("time of the linear solve (s)")
    ax[1].set_title("One LM step: dense vs Schur", fontsize=10)
    ax[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "ba-convergence.svg"))
    plt.close(fig)
    print(f"\nwrote ba-structure.svg, ba-convergence.svg; total {time.time() - t00:.0f} s")


if __name__ == "__main__":
    main()
