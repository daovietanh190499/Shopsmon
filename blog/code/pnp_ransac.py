"""Camera pose from 2D-3D matches (PnP) with outliers: linear DLT, Gauss-Newton refinement and RANSAC.

Run:  python -u pnp_ransac.py      (about 15 minutes on one core; Python 3.12, NumPy, SciPy, Matplotlib)
      PNP_PARTS=A|B|C runs one group of experiments (see main) so that three processes can share the work.
Everything is seeded; the numbers printed here are the ones quoted in the blog post.
Writes pnp-ransac-example.svg and pnp-ransac-curves.svg next to this script (or into $PNP_OUT).

Scene: n = 200 world points, observed by a camera with f = 800 px, principal point (320, 240), image 640 x 480.
Each observation gets N(0, sigma^2) pixel noise; a fraction eps of the matches is replaced by a uniformly random pixel
(a wrong match). The task is to recover the camera pose (R, t) with x ~ K (R X + t).
"""
import math
import os
import sys
import time

import numpy as np
from scipy.optimize import least_squares

OUT = os.environ.get("PNP_OUT", os.path.dirname(os.path.abspath(__file__)))
F, CX, CY, WID, HEI = 800.0, 320.0, 240.0, 640.0, 480.0
N_PTS = 200
TRIALS = int(os.environ.get("PNP_TRIALS", "60"))    # scenes per table row (60 for the numbers in the post)
P_CONF = 0.99          # RANSAC confidence
MAX_ITER = 6000
S_MIN = 6              # minimal sample for the linear (DLT) solver


# ------------------------------------------------------------------ geometry helpers
def skew(v):
    return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0.0]])


def rodrigues(w):
    """Rotation matrix from a rotation vector."""
    th = np.linalg.norm(w)
    if th < 1e-12:
        return np.eye(3) + skew(w)
    S = skew(w / th)
    return np.eye(3) + math.sin(th) * S + (1 - math.cos(th)) * S @ S


def rot_err_deg(Ra, Rb):
    return math.degrees(math.acos(np.clip((np.trace(Ra.T @ Rb) - 1) / 2, -1, 1)))


def centre(R, t):
    return -R.T @ t


def project(R, t, X):
    """Pixels and camera-frame depth of world points X (n x 3)."""
    Xc = X @ R.T + t
    z = Xc[:, 2]
    u = F * Xc[:, 0] / z + CX
    v = F * Xc[:, 1] / z + CY
    return np.column_stack([u, v]), z


def residuals(R, t, X, uv):
    p, z = project(R, t, X)
    r = np.linalg.norm(p - uv, axis=1)
    r[z <= 0] = np.inf
    return r


# ------------------------------------------------------------------ synthetic scene
def make_scene(seed, n=N_PTS, sigma=1.0, planar=False):
    """Return dict with world points X, clean pixels, true pose and a fixed random order for nested outliers."""
    rng = np.random.default_rng(seed)
    w = rng.normal(size=3)
    w = w / np.linalg.norm(w) * math.radians(rng.uniform(5, 30))
    R = rodrigues(w)
    C = rng.normal(size=3) * 0.3
    t = -R @ C
    u = rng.uniform(40, WID - 40, n)
    v = rng.uniform(40, HEI - 40, n)
    z = np.full(n, 6.0) if planar else rng.uniform(4.0, 8.0, n)      # planar = all points on the plane z_c = 6
    Xc = np.column_stack([z * (u - CX) / F, z * (v - CY) / F, z])
    X = (Xc - t) @ R                                                 # world = R^T (Xc - t)
    uv_clean, _ = project(R, t, X)
    noise = rng.normal(size=(n, 2)) * sigma
    wrong = np.column_stack([rng.uniform(0, WID, n), rng.uniform(0, HEI, n)])
    order = rng.permutation(n)
    return dict(X=X, uv_clean=uv_clean, noise=noise, wrong=wrong, order=order, R=R, t=t, seed=seed)


def observe(sc, eps):
    """Noisy pixels with the first round(eps*n) entries of the fixed order replaced by random pixels."""
    n = len(sc["X"])
    k = int(round(eps * n))
    uv = sc["uv_clean"] + sc["noise"]
    inl = np.ones(n, bool)
    bad = sc["order"][:k]
    uv = uv.copy()
    uv[bad] = sc["wrong"][bad]
    inl[bad] = False
    return uv, inl


# ------------------------------------------------------------------ solvers
def dlt_pose(X, uv):
    """Linear pose from n >= 6 matches: solve for the 3x4 matrix P = [R | t] in normalised coordinates, then project to SO(3)."""
    xn = (uv[:, 0] - CX) / F
    yn = (uv[:, 1] - CY) / F
    n = len(X)
    Xh = np.column_stack([X, np.ones(n)])
    A = np.zeros((2 * n, 12))
    A[0::2, 0:4] = Xh
    A[0::2, 8:12] = -xn[:, None] * Xh
    A[1::2, 4:8] = Xh
    A[1::2, 8:12] = -yn[:, None] * Xh
    p = np.linalg.svd(A, full_matrices=False)[2][-1]
    P = p.reshape(3, 4)
    if np.linalg.det(P[:, :3]) < 0:
        P = -P
    U, S, Vt = np.linalg.svd(P[:, :3])
    R = U @ Vt
    s = S.mean()
    t = P[:, 3] / s
    return R, t


def gauss_newton(R, t, X, uv, iters=15):
    """Minimise the sum of squared pixel reprojection errors over (R, t) (small damping, rotation as left perturbation)."""
    lam = 1e-6
    prev = None
    for _ in range(iters):
        Xc = X @ R.T + t
        x, y, z = Xc[:, 0], Xc[:, 1], Xc[:, 2]
        pred = np.column_stack([F * x / z + CX, F * y / z + CY])
        r = (pred - uv).ravel()
        cost = float(r @ r)
        n = len(X)
        Jt = np.zeros((n, 2, 3))
        Jt[:, 0, 0] = F / z
        Jt[:, 0, 2] = -F * x / z**2
        Jt[:, 1, 1] = F / z
        Jt[:, 1, 2] = -F * y / z**2
        # d(Xc)/d(omega) = -[Xc]x
        Sx = np.zeros((n, 3, 3))
        Sx[:, 0, 1], Sx[:, 0, 2] = -z, y
        Sx[:, 1, 0], Sx[:, 1, 2] = z, -x
        Sx[:, 2, 0], Sx[:, 2, 1] = -y, x
        Jw = np.einsum("nij,njk->nik", Jt, -Sx)
        J = np.concatenate([Jw, Jt], axis=2).reshape(2 * n, 6)
        H = J.T @ J
        g = J.T @ r
        step = -np.linalg.solve(H + lam * np.diag(np.diag(H)), g)
        R_new = rodrigues(step[:3]) @ R
        t_new = t + step[3:]
        if prev is not None and abs(prev - cost) < 1e-9 * max(cost, 1.0):
            R, t = R_new, t_new
            break
        prev = cost
        R, t = R_new, t_new
    return R, t


def refine(X, uv, R, t, tau, rounds=3):
    """Re-estimate with all points that agree within tau, then polish with Gauss-Newton; repeat."""
    inl = residuals(R, t, X, uv) < tau
    for _ in range(rounds):
        if inl.sum() < S_MIN:
            break
        R2, t2 = dlt_pose(X[inl], uv[inl])
        R2, t2 = gauss_newton(R2, t2, X[inl], uv[inl])
        inl2 = residuals(R2, t2, X, uv) < tau
        R, t = R2, t2
        if np.array_equal(inl2, inl):
            break
        inl = inl2
    return R, t, inl


def n_iter_needed(w, s, p=P_CONF):
    """Iterations so that, with probability p, at least one size-s sample is free of outliers (inlier ratio w)."""
    ws = w**s
    if ws <= 0:
        return MAX_ITER
    if ws >= 1:
        return 1
    return int(math.ceil(math.log(1 - p) / math.log(1 - ws)))


def ransac(X, uv, tau, rng, truth=None, p=P_CONF, adaptive=True, max_iter=MAX_ITER, s=S_MIN):
    """RANSAC with DLT minimal samples; best hypothesis = most inliers (ties: lower truncated cost), then refit.
    truth: optional boolean mask of the real inliers, used only for diagnostics (count of outlier-free samples)."""
    n = len(X)
    best_cnt, best_cost, best_pose = -1, np.inf, None
    need = max_iter
    it = 0
    clean_samples = 0
    while it < min(need, max_iter):
        it += 1
        idx = rng.choice(n, s, replace=False)
        if truth is not None and truth[idx].all():
            clean_samples += 1
        try:
            R, t = dlt_pose(X[idx], uv[idx])
        except np.linalg.LinAlgError:
            continue
        r = residuals(R, t, X, uv)
        cnt = int((r < tau).sum())
        cost = float((np.minimum(r, tau) ** 2).sum())
        if cnt > best_cnt or (cnt == best_cnt and cost < best_cost):
            best_cnt, best_cost, best_pose = cnt, cost, (R, t)
            if adaptive:
                need = n_iter_needed(cnt / n, s, p)
    R, t = best_pose
    R, t, inl = refine(X, uv, R, t, tau)
    return dict(R=R, t=t, inl=inl, iters=it, clean=clean_samples, best_cnt=best_cnt)


def pose_errors(R, t, sc):
    return rot_err_deg(R, sc["R"]), float(np.linalg.norm(centre(R, t) - centre(sc["R"], sc["t"])))


def is_success(re, pe):
    return re < 1.0 and pe < 0.1


# ------------------------------------------------------------------ experiments
def sanity():
    print("== 0. Sanity checks")
    sc = make_scene(0, sigma=0.0)
    uv, _ = observe(sc, 0.0)
    R, t = dlt_pose(sc["X"], uv)
    print(f"noise-free DLT on {N_PTS} points: rot err {rot_err_deg(R, sc['R']):.2e} deg, centre err {np.linalg.norm(centre(R, t) - centre(sc['R'], sc['t'])):.2e}")
    # minimal sample (6 points) without noise
    R6, t6 = dlt_pose(sc["X"][:6], uv[:6])
    print(f"noise-free DLT on 6 points: rot err {rot_err_deg(R6, sc['R']):.2e} deg")
    # Gauss-Newton against SciPy least_squares on a noisy scene
    sc = make_scene(1, sigma=1.0)
    uv, _ = observe(sc, 0.0)
    R0, t0 = dlt_pose(sc["X"], uv)
    Rg, tg = gauss_newton(R0, t0, sc["X"], uv)

    def fun(q):
        Rq = rodrigues(q[:3]) @ R0
        return (project(Rq, t0 + q[3:], sc["X"])[0] - uv).ravel()

    sol = least_squares(fun, np.zeros(6), method="lm", xtol=1e-14, ftol=1e-14)
    Rs = rodrigues(sol.x[:3]) @ R0
    ts = t0 + sol.x[3:]
    print(f"Gauss-Newton vs SciPy LM (sigma=1, 200 points): rotation differs {rot_err_deg(Rg, Rs):.2e} deg, "
          f"centre differs {np.linalg.norm(centre(Rg, tg) - centre(Rs, ts)):.2e}; "
          f"RMS reprojection {math.sqrt(np.mean(residuals(Rg, tg, sc['X'], uv)**2)):.4f} px (SciPy {math.sqrt(np.mean(residuals(Rs, ts, sc['X'], uv)**2)):.4f})")
    print(f"expected RMS for the true pose: sigma*sqrt(2*(1-(6)/(2*200)))~{math.sqrt(2 * (1 - 6 / 400)):.4f} px (radial)")


def exp_outliers(trials=TRIALS, eps_list=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6), sigma=1.0):
    print(f"\n== 1. Outlier fraction (n={N_PTS}, sigma={sigma} px, tau=3 px, p={P_CONF}, {trials} scenes per row)")
    rows = {}
    hdr = ("eps", "DLT all: median rot err", "p90", "success", "DLT+GN all: median", "success", "RANSAC: median rot err", "p90", "success",
           "oracle median", "iters mean", "iters theory", "clean-sample frac", "theory (1-eps)^6", "iters max")
    print(" | ".join(hdr))
    for eps in eps_list:
        e = {k: [] for k in ("dlt", "dltgn", "ran", "orc", "it", "clean", "pos_dlt", "pos_ran")}
        ok = {"dlt": 0, "dltgn": 0, "ran": 0, "orc": 0}
        for tr in range(trials):
            sc = make_scene(1000 + tr, sigma=sigma)
            uv, inl = observe(sc, eps)
            R, t = dlt_pose(sc["X"], uv)
            re, pe = pose_errors(R, t, sc)
            e["dlt"].append(re)
            ok["dlt"] += is_success(re, pe)
            Rg, tg = gauss_newton(R, t, sc["X"], uv, iters=30)
            re2, pe2 = pose_errors(Rg, tg, sc)
            e["dltgn"].append(re2)
            ok["dltgn"] += is_success(re2, pe2)
            rng = np.random.default_rng(50000 + tr)
            res = ransac(sc["X"], uv, 3.0, rng, truth=inl)
            re3, pe3 = pose_errors(res["R"], res["t"], sc)
            e["ran"].append(re3)
            ok["ran"] += is_success(re3, pe3)
            e["it"].append(res["iters"])
            e["clean"].append(res["clean"] / res["iters"])
            Ro, to = dlt_pose(sc["X"][inl], uv[inl])
            Ro, to = gauss_newton(Ro, to, sc["X"][inl], uv[inl])
            re4, pe4 = pose_errors(Ro, to, sc)
            e["orc"].append(re4)
            ok["orc"] += is_success(re4, pe4)
        w = 1 - eps
        th = n_iter_needed(w, S_MIN)
        q = lambda a, p_: float(np.percentile(a, p_))
        rows[eps] = dict(dlt_med=q(e["dlt"], 50), dlt_p90=q(e["dlt"], 90), dlt_ok=ok["dlt"] / trials,
                         gn_med=q(e["dltgn"], 50), gn_ok=ok["dltgn"] / trials,
                         ran_med=q(e["ran"], 50), ran_p90=q(e["ran"], 90), ran_ok=ok["ran"] / trials,
                         ran_q25=q(e["ran"], 25), ran_q75=q(e["ran"], 75), dlt_q25=q(e["dlt"], 25), dlt_q75=q(e["dlt"], 75),
                         gn_q25=q(e["dltgn"], 25), gn_q75=q(e["dltgn"], 75),
                         orc_med=q(e["orc"], 50), it_mean=float(np.mean(e["it"])), it_med=q(e["it"], 50), it_max=int(np.max(e["it"])), it_theory=th,
                         clean=float(np.mean(e["clean"])), clean_th=w**S_MIN)
        r = rows[eps]
        print(f"{eps:.1f} | {r['dlt_med']:.3f} | {r['dlt_p90']:.3f} | {r['dlt_ok']*100:.1f}% | {r['gn_med']:.3f} | {r['gn_ok']*100:.1f}% | "
              f"{r['ran_med']:.4f} | {r['ran_p90']:.4f} | {r['ran_ok']*100:.1f}% | {r['orc_med']:.4f} | {r['it_mean']:.1f} | {r['it_theory']} | "
              f"{r['clean']:.4f} | {r['clean_th']:.4f} | {r['it_max']}", flush=True)
    return rows


def exp_noise(trials=TRIALS, eps=0.3, sigmas=(0.5, 1.0, 2.0, 4.0)):
    print(f"\n== 2. Pixel noise (eps={eps}, tau=3 sigma, {trials} scenes per row)")
    print("sigma | RANSAC median rot err | p90 | success | oracle median | RANSAC/oracle | median centre err RANSAC | oracle | iters mean")
    out = {}
    for sg in sigmas:
        er, eo, pr, po, its, ok = [], [], [], [], [], 0
        for tr in range(trials):
            sc = make_scene(1000 + tr, sigma=sg)
            uv, inl = observe(sc, eps)
            rng = np.random.default_rng(60000 + tr)
            res = ransac(sc["X"], uv, 3.0 * sg, rng, truth=inl)
            re, pe = pose_errors(res["R"], res["t"], sc)
            er.append(re)
            pr.append(pe)
            ok += is_success(re, pe)
            its.append(res["iters"])
            Ro, to = dlt_pose(sc["X"][inl], uv[inl])
            Ro, to = gauss_newton(Ro, to, sc["X"][inl], uv[inl])
            ro, po_ = pose_errors(Ro, to, sc)
            eo.append(ro)
            po.append(po_)
        out[sg] = dict(med=float(np.median(er)), p90=float(np.percentile(er, 90)), ok=ok / trials, orc=float(np.median(eo)),
                       pos=float(np.median(pr)), pos_o=float(np.median(po)), it=float(np.mean(its)))
        o = out[sg]
        print(f"{sg} | {o['med']:.4f} | {o['p90']:.4f} | {o['ok']*100:.1f}% | {o['orc']:.4f} | {o['med']/o['orc']:.3f} | {o['pos']:.4f} | {o['pos_o']:.4f} | {o['it']:.1f}", flush=True)
    return out


def exp_threshold(trials=int(os.environ.get("PNP_TRIALS_T", "30")), eps=0.3, sigma=1.0,
                  taus=tuple(float(s) for s in os.environ.get("PNP_TAUS", "0.5,1,2,3,5,10,30").split(","))):
    print(f"\n== 3. Inlier threshold tau (eps={eps}, sigma={sigma} px, {trials} scenes per row)")
    print("tau | success | median rot err | p90 | mean iters | mean #inliers kept (of 140 true)")
    out = {}
    for tau in taus:
        er, its, cnt, ok = [], [], [], 0
        for tr in range(trials):
            sc = make_scene(1000 + tr, sigma=sigma)
            uv, inl = observe(sc, eps)
            rng = np.random.default_rng(70000 + tr)
            res = ransac(sc["X"], uv, tau, rng, truth=inl)
            re, pe = pose_errors(res["R"], res["t"], sc)
            er.append(re)
            ok += is_success(re, pe)
            its.append(res["iters"])
            cnt.append(int(res["inl"].sum()))
        out[tau] = dict(ok=ok / trials, med=float(np.median(er)), p90=float(np.percentile(er, 90)), it=float(np.mean(its)), kept=float(np.mean(cnt)))
        o = out[tau]
        print(f"{tau} | {o['ok']*100:.1f}% | {o['med']:.4f} | {o['p90']:.4f} | {o['it']:.1f} | {o['kept']:.1f}", flush=True)
    return out


def exp_planar(trials=TRIALS, eps=0.3, sigma=1.0):
    print(f"\n== 4. Coplanar 3D points (eps={eps}, sigma={sigma} px, tau=3 px, {trials} scenes)")
    out = {}
    for planar in (False, True):
        er, its, ok = [], [], 0
        for tr in range(trials):
            sc = make_scene(1000 + tr, sigma=sigma, planar=planar)
            uv, inl = observe(sc, eps)
            rng = np.random.default_rng(80000 + tr)
            res = ransac(sc["X"], uv, 3.0, rng, truth=inl, max_iter=2000)
            re, pe = pose_errors(res["R"], res["t"], sc)
            er.append(re)
            ok += is_success(re, pe)
            its.append(res["iters"])
        out[planar] = dict(ok=ok / trials, med=float(np.median(er)), p90=float(np.percentile(er, 90)), it=float(np.mean(its)))
        print(f"planar={planar}: success {out[planar]['ok']*100:.1f}%, median rot err {out[planar]['med']:.3f} deg, p90 {out[planar]['p90']:.3f}, mean iterations {out[planar]['it']:.1f}", flush=True)
    return out


def exp_few_outliers(trials=TRIALS, eps_list=(0.0, 0.005, 0.01, 0.02, 0.05), sigma=1.0):
    """How few wrong matches does it take to break the linear fit? (200 points: eps = 0.005 is a single wrong match.)"""
    print(f"\n== 6. Very few outliers (n={N_PTS}, sigma={sigma} px, {trials} scenes per row; eps*n wrong matches)")
    print("eps | wrong matches | DLT all: median rot err | p90 | success | DLT+GN all: median | p90 | success")
    for eps in eps_list:
        e1, e2, ok1, ok2 = [], [], 0, 0
        for tr in range(trials):
            sc = make_scene(1000 + tr, sigma=sigma)
            uv, _ = observe(sc, eps)
            R, t = dlt_pose(sc["X"], uv)
            re, pe = pose_errors(R, t, sc)
            e1.append(re)
            ok1 += is_success(re, pe)
            Rg, tg = gauss_newton(R, t, sc["X"], uv, iters=30)
            re2, pe2 = pose_errors(Rg, tg, sc)
            e2.append(re2)
            ok2 += is_success(re2, pe2)
        q = lambda a, p_: float(np.percentile(a, p_))
        print(f"{eps} | {int(round(eps * N_PTS))} | {q(e1, 50):.3f} | {q(e1, 90):.3f} | {ok1 / trials * 100:.1f}% | "
              f"{q(e2, 50):.3f} | {q(e2, 90):.3f} | {ok2 / trials * 100:.1f}%", flush=True)


def exp_clean_samples(trials=TRIALS, eps=0.3, sigma=1.0, per_scene=100):
    """A sample with no wrong match is not the same as a good model: how many of the true inliers does the 6-point DLT
    hypothesis of an outlier-free sample collect within tau = 3 px? (Explains why adaptive RANSAC runs longer than N.)"""
    print(f"\n== 7. Quality of outlier-free 6-point hypotheses (eps={eps}, sigma={sigma} px, tau=3 px, {trials} scenes x {per_scene} clean samples)")
    rng = np.random.default_rng(90000)
    frac, rot = [], []
    for tr in range(trials):
        sc = make_scene(1000 + tr, sigma=sigma)
        uv, inl = observe(sc, eps)
        good = np.where(inl)[0]
        for _ in range(per_scene):
            idx = rng.choice(good, S_MIN, replace=False)
            R, t = dlt_pose(sc["X"][idx], uv[idx])
            cnt = int((residuals(R, t, sc["X"], uv)[inl] < 3.0).sum())
            frac.append(cnt / len(good))
            rot.append(rot_err_deg(R, sc["R"]))
    frac, rot = np.array(frac), np.array(rot)
    print(f"true inliers collected by a clean sample: median {np.median(frac) * 100:.1f}%, p10 {np.percentile(frac, 10) * 100:.1f}%, "
          f"p90 {np.percentile(frac, 90) * 100:.1f}%; share of clean samples that collect >= 90% of the inliers: {np.mean(frac >= 0.9) * 100:.1f}%; "
          f"rotation error of the clean 6-point hypothesis: median {np.median(rot):.2f} deg, p90 {np.percentile(rot, 90):.2f} deg", flush=True)


def table_sample_size():
    print("\n== 5. Iterations needed N = ceil(log(1-p)/log(1-(1-eps)^s)), p = 0.99 (formula, not measured)")
    print("eps | s=3 | s=4 | s=6 | s=8")
    for eps in (0.1, 0.3, 0.5, 0.7):
        print(f"{eps} | " + " | ".join(str(n_iter_needed(1 - eps, s)) for s in (3, 4, 6, 8)))


# ------------------------------------------------------------------ figures
def figures(rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["svg.hashsalt"] = "shopsmon"
    plt.rcParams["svg.fonttype"] = "none"
    plt.rcParams["font.size"] = 9

    # Figure 1: one scene, 40 % outliers
    sc = make_scene(7, sigma=1.0)
    uv, inl = observe(sc, 0.4)
    res = ransac(sc["X"], uv, 3.0, np.random.default_rng(3), truth=inl)
    Rd, td = dlt_pose(sc["X"], uv)
    pr, _ = project(res["R"], res["t"], sc["X"])
    rr = residuals(res["R"], res["t"], sc["X"], uv)
    rd = residuals(Rd, td, sc["X"], uv)
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.9), gridspec_kw=dict(width_ratios=[1.15, 1]))
    a = ax[0]
    a.add_patch(plt.Rectangle((0, 0), WID, HEI, fill=False, ec="#94a3b8"))
    for i in np.where(~res["inl"])[0]:
        a.annotate("", xy=pr[i], xytext=uv[i], arrowprops=dict(arrowstyle="->", color="#f87171", lw=0.6, alpha=0.7))
    a.scatter(uv[res["inl"], 0], uv[res["inl"], 1], s=9, c="#16a34a", label=f"accepted by RANSAC ({res['inl'].sum()})")
    a.scatter(uv[~res["inl"], 0], uv[~res["inl"], 1], s=14, c="#dc2626", marker="x", label=f"rejected ({(~res['inl']).sum()})")
    a.set_xlim(-10, WID + 10)
    a.set_ylim(HEI + 10, -10)
    a.set_aspect("equal")
    a.set_title("Image plane: matches and RANSAC pose")
    a.legend(loc="lower right", fontsize=7.5, framealpha=0.9)
    b = ax[1]
    bins = np.logspace(-1, 3, 45)
    b.hist(np.clip(rd, 0.1, 999), bins=bins, color="#f59e0b", alpha=0.75, label="plain DLT on all 200 matches")
    b.hist(np.clip(rr, 0.1, 999), bins=bins, color="#2563eb", alpha=0.75, label="RANSAC pose")
    b.axvline(3.0, color="k", ls="--", lw=1)
    b.text(3.3, b.get_ylim()[1] * 0.92, "tau = 3 px", fontsize=8)
    b.set_xscale("log")
    b.set_xlabel("reprojection error (px)")
    b.set_ylabel("matches")
    b.set_title("Residuals under each pose")
    b.legend(fontsize=7.5, loc="upper left", framealpha=0.9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "pnp-ransac-example.svg"))
    plt.close(fig)

    # Figure 2: accuracy and iterations versus outlier fraction
    eps = sorted(rows)
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.7))
    a = ax[0]
    for key, col, lab in (("dlt", "#f59e0b", "plain DLT, all matches"), ("gn", "#dc2626", "DLT + Gauss-Newton, all matches"), ("ran", "#2563eb", "RANSAC + refit")):
        med = [rows[e][f"{key}_med"] for e in eps]
        lo = [rows[e][f"{key}_q25"] for e in eps]
        hi = [rows[e][f"{key}_q75"] for e in eps]
        a.plot(eps, med, "o-", color=col, label=lab, ms=4)
        a.fill_between(eps, lo, hi, color=col, alpha=0.15)
    a.plot(eps, [rows[e]["orc_med"] for e in eps], "k--", lw=1, label="oracle (true inliers only)")
    a.set_yscale("log")
    a.set_xlabel("outlier fraction eps")
    a.set_ylabel("rotation error (deg), median and IQR")
    a.set_title(f"Pose accuracy ({TRIALS} scenes per point)")
    a.legend(fontsize=7.5, loc="center left")
    b = ax[1]
    b.plot(eps, [rows[e]["it_theory"] for e in eps], "k--", label="formula N (s = 6, p = 0.99)")
    b.plot(eps, [rows[e]["it_mean"] for e in eps], "o-", color="#2563eb", ms=4, label="RANSAC, mean iterations used")
    b.plot(eps, [rows[e]["it_max"] for e in eps], "^:", color="#64748b", ms=4, label=f"RANSAC, maximum over {TRIALS} scenes")
    b.set_yscale("log")
    b.set_xlabel("outlier fraction eps")
    b.set_ylabel("iterations")
    b.set_title("Iterations: formula and measured")
    b.legend(fontsize=7.5, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "pnp-ransac-curves.svg"))
    plt.close(fig)
    print("\nfigure 1 scene (seed 7, eps 0.4): iterations", res["iters"], "accepted", int(res["inl"].sum()), "of", len(inl),
          "(true inliers", int(inl.sum()), "); true inliers accepted", int((res['inl'] & inl).sum()), "; outliers accepted", int((res['inl'] & ~inl).sum()),
          "; median residual plain DLT %.1f px, RANSAC %.2f px" % (np.median(rd), np.median(rr[inl])),
          "; rotation err plain DLT %.2f deg, RANSAC %.3f deg" % (rot_err_deg(Rd, sc["R"]), rot_err_deg(res["R"], sc["R"])))


def main():
    """PNP_PARTS (default ABC) lets the three groups run as separate processes on separate cores:
    A = sanity + outlier-fraction table + sample-size table + figures, B = pixel-noise table, C = coplanar test,
    D = very few outliers (0.5 % to 5 %), E = inlier-threshold table (30 scenes per row),
    F = quality of outlier-free minimal samples."""
    parts = os.environ.get("PNP_PARTS", "ABCDEF")
    t0 = time.time()
    if "A" in parts:
        sanity()
        rows = exp_outliers()
        table_sample_size()
        figures(rows)
    if "B" in parts:
        exp_noise()
    if "E" in parts:
        exp_threshold()          # 30 scenes per row (PNP_TRIALS_T); PNP_TAUS selects the thresholds
    if "C" in parts:
        exp_planar()
    if "D" in parts:
        exp_few_outliers()
    if "F" in parts:
        exp_clean_samples()
    print(f"\nTotal time {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
