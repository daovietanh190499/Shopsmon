"""Kalman filtering of noisy position fixes for a mobile robot (1-D, constant-velocity model).

State x = [position, velocity]. The robot receives a noisy position fix every dt seconds
(z = position + N(0, r^2)). The truth is simulated from the same model with white-noise
acceleration (process-noise intensity q), so the matched filter is exactly optimal.

Experiments
  1. Matched filter vs theory: steady-state prior covariance and gain from the discrete algebraic
     Riccati equation (DARE) against Monte-Carlo estimates; NEES (expected 2) and NIS (expected 1).
  2. Baselines on a held-out set: raw fixes, an EWMA with the best alpha chosen on a separate tuning
     set, a fixed-gain filter using the steady-state Kalman gain, and the full time-varying filter.
  3. Wrong noise assumptions: the filter assumes R and q scaled by 0.1 ... 10 (RMSE ratio, mean NEES).
  4. Outlier fixes (heavy-tailed measurement noise) with and without chi-square gating, and a
     "kidnapped" jump of the true position (3 m) where gating can lock the filter out.

Usage:  python kalman_amr_fusion.py      (about 70 s; prints every table used in the post and writes
                                          three SVG figures)
Environment: KAL_OUT = output directory for the figures (default ../../assets/img/blog).
"""
import os
import time

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.linalg import solve_discrete_are

matplotlib.rcParams["svg.hashsalt"] = "kalman-amr-fusion"
matplotlib.rcParams["svg.fonttype"] = "none"
OUT = os.environ.get("KAL_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "img", "blog"))
SEED = 20261123

DT = 0.1          # s between fixes
Q_PSD = 0.5       # white-noise acceleration intensity, (m/s^2)^2 * s
R_STD = 0.30      # position-fix noise std, m
STEPS = 600
M0 = (0.0, 1.0)   # prior mean of [position, velocity]
P0 = (1.0, 0.25)  # prior variances (pos, vel); the truth is drawn from this prior
WIN = 100         # steady-state window starts here (k >= WIN)
CHI2_99 = 6.634896601021214     # chi-square(1) 99 % quantile
CHI2_999 = 10.827566170662733   # chi-square(1) 99.9 % quantile


def model(dt, q):
    F = np.array([[1.0, dt], [0.0, 1.0]])
    Q = q * np.array([[dt ** 3 / 3, dt ** 2 / 2], [dt ** 2 / 2, dt]])
    return F, Q


def gen_truth(rng, runs, steps, dt=DT, q=Q_PSD):
    F, Q = model(dt, q)
    L = np.linalg.cholesky(Q)
    x = np.empty((runs, steps, 2))
    x[:, 0, 0] = M0[0] + rng.normal(0, np.sqrt(P0[0]), runs)
    x[:, 0, 1] = M0[1] + rng.normal(0, np.sqrt(P0[1]), runs)
    for k in range(1, steps):
        x[:, k] = x[:, k - 1] @ F.T + rng.standard_normal((runs, 2)) @ L.T
    return x


def gen_meas(rng, x, r=R_STD, eps=0.0, out_scale=10.0):
    z = x[:, :, 0] + r * rng.standard_normal(x.shape[:2])
    is_out = np.zeros(z.shape, bool)
    if eps > 0:
        is_out = rng.random(z.shape) < eps
        z = z + is_out * (out_scale * r * rng.standard_normal(z.shape))
    return z, is_out


def kalman(z, q, r, dt=DT, gate=None, reset_n=None, x_true=None):
    """Vectorised over runs. Returns dict with estimates, accepted mask, NIS and (if x_true) NEES."""
    runs, steps = z.shape
    F, Q = model(dt, q)
    R = r * r
    x1 = np.full(runs, M0[0]); x2 = np.full(runs, M0[1])
    p11 = np.full(runs, P0[0]); p12 = np.zeros(runs); p22 = np.full(runs, P0[1])
    xs = np.empty((runs, steps, 2)); nis = np.empty((runs, steps)); acc_h = np.empty((runs, steps), bool)
    pri11 = np.empty((runs, steps)); pri12 = np.empty((runs, steps)); pri22 = np.empty((runs, steps))
    nees = np.empty((runs, steps)) if x_true is not None else None
    kgain = np.empty((runs, steps, 2))
    consec = np.zeros(runs, int)
    for k in range(steps):
        if k > 0:
            x1, x2 = x1 + dt * x2, x2
            p11, p12, p22 = (p11 + 2 * dt * p12 + dt * dt * p22 + Q[0, 0],
                             p12 + dt * p22 + Q[0, 1],
                             p22 + Q[1, 1])
        pri11[:, k], pri12[:, k], pri22[:, k] = p11, p12, p22
        S = p11 + R
        y = z[:, k] - x1
        nis[:, k] = y * y / S
        acc = np.ones(runs, bool) if gate is None else (nis[:, k] <= gate)
        K1 = p11 / S; K2 = p12 / S
        kgain[:, k, 0], kgain[:, k, 1] = K1, K2
        nx1, nx2 = x1 + K1 * y, x2 + K2 * y
        n11, n12, n22 = p11 - K1 * p11, p12 - K1 * p12, p22 - K2 * p12
        x1, x2 = np.where(acc, nx1, x1), np.where(acc, nx2, x2)
        p11, p12, p22 = np.where(acc, n11, p11), np.where(acc, n12, p12), np.where(acc, n22, p22)
        if reset_n is not None:
            consec = np.where(acc, 0, consec + 1)
            rs = consec >= reset_n
            x1 = np.where(rs, z[:, k], x1)
            p11 = np.where(rs, R, p11); p12 = np.where(rs, 0.0, p12)
            consec = np.where(rs, 0, consec)
        acc_h[:, k] = acc
        xs[:, k, 0], xs[:, k, 1] = x1, x2
        if nees is not None:
            e1 = x_true[:, k, 0] - x1; e2 = x_true[:, k, 1] - x2
            nees[:, k] = (p22 * e1 * e1 - 2 * p12 * e1 * e2 + p11 * e2 * e2) / (p11 * p22 - p12 ** 2)
    return dict(x=xs, nis=nis, acc=acc_h, nees=nees, pri=(pri11, pri12, pri22), K=kgain)


def rmse(est, truth, comp):
    e = est[:, WIN:, comp] - truth[:, WIN:, comp]
    return float(np.sqrt(np.mean(e * e)))


def ewma(z, alpha):
    s = np.empty_like(z)
    s[:, 0] = z[:, 0]
    for k in range(1, z.shape[1]):
        s[:, k] = s[:, k - 1] + alpha * (z[:, k] - s[:, k - 1])
    return s


def fixed_gain(z, K, dt=DT):
    runs, steps = z.shape
    out = np.empty((runs, steps, 2))
    x1 = np.full(runs, M0[0]); x2 = np.full(runs, M0[1])
    for k in range(steps):
        if k > 0:
            x1 = x1 + dt * x2
        y = z[:, k] - x1
        x1, x2 = x1 + K[0] * y, x2 + K[1] * y
        out[:, k, 0], out[:, k, 1] = x1, x2
    return out


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(SEED)
    F, Q = model(DT, Q_PSD)
    H = np.array([[1.0, 0.0]])
    R = R_STD ** 2

    # ------------------------------------------------------------------ 1. matched filter vs theory
    RUNS = 2000
    x = gen_truth(rng, RUNS, STEPS)
    z, _ = gen_meas(rng, x)
    f = kalman(z, Q_PSD, R_STD, x_true=x)
    Pp = solve_discrete_are(F.T, H.T, Q, np.array([[R]]))        # steady-state PRIOR covariance
    Sss = Pp[0, 0] + R
    Kss = (Pp @ H.T / Sss).ravel()
    Ppost = Pp - np.outer(Kss, H @ Pp).reshape(2, 2)
    print("== 1. matched filter vs DARE theory (runs=%d, steps=%d, dt=%.2f s, q=%.2f, r=%.2f m)" % (RUNS, STEPS, DT, Q_PSD, R_STD))
    print("DARE prior covariance   P11=%.6f  P12=%.6f  P22=%.6f" % (Pp[0, 0], Pp[0, 1], Pp[1, 1]))
    print("DARE steady-state gain  K1=%.6f  K2=%.6f   (alpha=K1, beta=K2*dt=%.6f)" % (Kss[0], Kss[1], Kss[1] * DT))
    print("DARE posterior std      pos=%.5f m  vel=%.5f m/s" % (np.sqrt(Ppost[0, 0]), np.sqrt(Ppost[1, 1])))
    last = slice(STEPS - 100, STEPS)
    print("filter gain at k=%d      K1=%.6f  K2=%.6f" % (STEPS - 1, f["K"][0, -1, 0], f["K"][0, -1, 1]))
    # prior error = truth - prior estimate; reconstruct prior estimate = F @ previous posterior
    xp = np.empty_like(f["x"])
    xp[:, 1:, 0] = f["x"][:, :-1, 0] + DT * f["x"][:, :-1, 1]
    xp[:, 1:, 1] = f["x"][:, :-1, 1]
    ep = (x - xp)[:, STEPS - 100:, :]
    emp = np.array([[np.mean(ep[:, :, 0] ** 2), np.mean(ep[:, :, 0] * ep[:, :, 1])],
                    [np.mean(ep[:, :, 0] * ep[:, :, 1]), np.mean(ep[:, :, 1] ** 2)]])
    print("Monte-Carlo prior cov (last 100 steps, all runs)  P11=%.6f  P12=%.6f  P22=%.6f" % (emp[0, 0], emp[0, 1], emp[1, 1]))
    print("relative difference     P11 %+.2f %%  P12 %+.2f %%  P22 %+.2f %%" % tuple(100 * (emp[i, j] / Pp[i, j] - 1) for i, j in [(0, 0), (0, 1), (1, 1)]))
    ne = f["nees"].mean(axis=1); ni = f["nis"].mean(axis=1)
    print("mean NEES per run: %.4f +- %.4f (std error)   expected 2" % (ne.mean(), ne.std(ddof=1) / np.sqrt(RUNS)))
    print("mean NIS  per run: %.4f +- %.4f (std error)   expected 1" % (ni.mean(), ni.std(ddof=1) / np.sqrt(RUNS)))
    print("fraction of NIS > chi2(1) 99%% quantile: %.4f (expected 0.01)" % np.mean(f["nis"] > CHI2_99))
    print("position RMSE in steady state: measured %.5f m, theory sqrt(P11 post) %.5f m" % (rmse(f["x"], x, 0), np.sqrt(Ppost[0, 0])))
    # independent, larger check of the consistency statistics (the first sample is one draw; this one has 20x the runs x steps/3)
    rc = np.random.default_rng(SEED + 3)
    RC, SC = 20000, 200
    xc = gen_truth(rc, RC, SC)
    zc, _ = gen_meas(rc, xc)
    fc = kalman(zc, Q_PSD, R_STD, x_true=xc)
    nec = fc["nees"].mean(axis=1); nic = fc["nis"].mean(axis=1)
    print("independent check (runs=%d, steps=%d): mean NEES %.4f +- %.4f   mean NIS %.4f +- %.4f" % (
        RC, SC, nec.mean(), nec.std(ddof=1) / np.sqrt(RC), nic.mean(), nic.std(ddof=1) / np.sqrt(RC)))

    # ------------------------------------------------------------------ 2. baselines (tuning set vs test set)
    print("\n== 2. baselines, held-out set (%d runs), RMSE over k >= %d" % (RUNS, WIN))
    rt = np.random.default_rng(SEED + 1)
    xt = gen_truth(rt, 500, STEPS)
    zt, _ = gen_meas(rt, xt)
    alphas = np.round(np.arange(0.05, 1.0001, 0.05), 2)
    tune = []
    for a in alphas:
        s = ewma(zt, a)
        tune.append(rmse(np.stack([s, s], -1), xt, 0))
    best_a = float(alphas[int(np.argmin(tune))])
    print("EWMA alpha chosen on the tuning set (500 runs): %.2f (tuning RMSE %.4f m)" % (best_a, min(tune)))
    s = ewma(z, best_a)
    v_s = np.zeros_like(s); v_s[:, 1:] = (s[:, 1:] - s[:, :-1]) / DT
    v_raw = np.zeros_like(z); v_raw[:, 1:] = (z[:, 1:] - z[:, :-1]) / DT
    xf = fixed_gain(z, Kss)
    rows = [
        ("raw fixes (velocity by differencing)", rmse(np.stack([z, v_raw], -1), x, 0), rmse(np.stack([z, v_raw], -1), x, 1)),
        ("EWMA alpha=%.2f (velocity by differencing)" % best_a, rmse(np.stack([s, v_s], -1), x, 0), rmse(np.stack([s, v_s], -1), x, 1)),
        ("fixed gain (steady-state Kalman gain)", rmse(xf, x, 0), rmse(xf, x, 1)),
        ("full Kalman filter (time-varying gain)", rmse(f["x"], x, 0), rmse(f["x"], x, 1)),
    ]
    for name, rp, rv in rows:
        print("%-46s position RMSE %.4f m   velocity RMSE %.4f m/s" % (name, rp, rv))
    print("max |fixed-gain - full KF| over k >= %d: position %.2e m, velocity %.2e m/s" % (
        WIN, np.abs(xf[:, WIN:, 0] - f["x"][:, WIN:, 0]).max(), np.abs(xf[:, WIN:, 1] - f["x"][:, WIN:, 1]).max()))
    # transient: error at the first steps
    print("position RMSE at k=0..4 (full KF): " + ", ".join("%.3f" % np.sqrt(np.mean((f["x"][:, k, 0] - x[:, k, 0]) ** 2)) for k in range(5)))
    print("position RMSE at k=0..4 (fixed gain): " + ", ".join("%.3f" % np.sqrt(np.mean((xf[:, k, 0] - x[:, k, 0]) ** 2)) for k in range(5)))

    # ------------------------------------------------------------------ 3. mismatched noise
    print("\n== 3. wrong noise assumptions (same data as above); filter assumes r*sqrt(sR) and q*sQ")
    scales = [0.1, 0.3, 1.0, 3.0, 10.0]
    base = rmse(f["x"], x, 0)
    ratio = np.zeros((5, 5)); nees_g = np.zeros((5, 5)); vratio = np.zeros((5, 5))
    basev = rmse(f["x"], x, 1)
    for i, sq in enumerate(scales):
        for j, sr in enumerate(scales):
            g = kalman(z, Q_PSD * sq, R_STD * np.sqrt(sr), x_true=x)
            ratio[i, j] = rmse(g["x"], x, 0) / base
            vratio[i, j] = rmse(g["x"], x, 1) / basev
            nees_g[i, j] = g["nees"][:, WIN:].mean()
    hdr = "assumed R scale:   " + "".join("%9.1f" % s_ for s_ in scales)
    print("position RMSE / matched RMSE (%.4f m)" % base); print(hdr)
    for i, sq in enumerate(scales):
        print("assumed q x%-6.1f   " % sq + "".join("%9.3f" % ratio[i, j] for j in range(5)))
    print("velocity RMSE / matched RMSE (%.4f m/s)" % basev); print(hdr)
    for i, sq in enumerate(scales):
        print("assumed q x%-6.1f   " % sq + "".join("%9.3f" % vratio[i, j] for j in range(5)))
    print("mean NEES (k >= %d, filter's own covariance; consistent = 2)" % WIN); print(hdr)
    for i, sq in enumerate(scales):
        print("assumed q x%-6.1f   " % sq + "".join("%9.2f" % nees_g[i, j] for j in range(5)))

    # ------------------------------------------------------------------ 4. outliers, gating, kidnapped jump
    print("\n== 4a. outlier fixes: with probability eps a fix gets extra N(0,(10 r)^2) noise (runs=%d)" % 1000)
    ro = np.random.default_rng(SEED + 2)
    xo = gen_truth(ro, 1000, STEPS)
    eps_list = [0.0, 0.005, 0.01, 0.02, 0.05, 0.10]
    methods = (("plain", {}), ("gate 99 %", dict(gate=CHI2_99)), ("gate 99.9 %", dict(gate=CHI2_999)),
               ("gate 99 % + reset(5)", dict(gate=CHI2_99, reset_n=5)))
    res = {m[0]: [] for m in methods}
    med = {m[0]: [] for m in methods}
    nbad = {m[0]: [] for m in methods}
    detail = {}
    for eps in eps_list:
        zo, is_out = gen_meas(ro, xo, eps=eps)
        for name, kw in methods:
            g = kalman(zo, Q_PSD, R_STD, **kw)
            res[name].append(rmse(g["x"], xo, 0))
            run_rmse = np.sqrt(np.mean((g["x"][:, WIN:, 0] - xo[:, WIN:, 0]) ** 2, axis=1))
            med[name].append(float(np.median(run_rmse)))
            nbad[name].append(int(np.sum(run_rmse > 1.0)))
            if "gate" in kw:
                rej = ~g["acc"]
                detail[(eps, name)] = (rej[~is_out].mean(), (rej[is_out].mean() if is_out.any() else float("nan")))
    print("position RMSE over all runs (m), steady-state window")
    print("eps                  " + "".join("%9.3f" % e for e in eps_list))
    for name in res:
        print("%-21s" % name + "".join("%9.4f" % v for v in res[name]))
    print("median over runs of the per-run position RMSE (m)")
    for name in med:
        print("%-21s" % name + "".join("%9.4f" % v for v in med[name]))
    print("number of runs (of 1000) whose per-run RMSE exceeds 1 m")
    for name in nbad:
        print("%-21s" % name + "".join("%9d" % v for v in nbad[name]))
    print("share of inlier fixes rejected / share of outlier fixes rejected")
    for name in ("gate 99 %", "gate 99.9 %"):
        print("%-13s" % name + "  ".join("eps=%.3f: %5.2f %% / %s" % (e, 100 * detail[(e, name)][0], ("%5.1f %%" % (100 * detail[(e, name)][1])) if e > 0 else "  n/a") for e in eps_list))

    # lock-out diagnosis on CLEAN fixes: which runs get stuck with the 99 % gate and why
    zc0, _ = gen_meas(np.random.default_rng(SEED + 4), xo, eps=0.0)
    g0 = kalman(zc0, Q_PSD, R_STD, gate=CHI2_99)
    run_rmse0 = np.sqrt(np.mean((g0["x"][:, WIN:, 0] - xo[:, WIN:, 0]) ** 2, axis=1))
    stuck = np.where(run_rmse0 > 1.0)[0]
    thr = np.sqrt(CHI2_99 * Pp[1, 1])
    print("\n== 4a'. lock-out of the 99 %% gate on clean fixes (new noise draw): %d of 1000 runs have RMSE > 1 m" % len(stuck))
    print("back-of-envelope velocity-error threshold sqrt(chi2_99 * P22_prior) = %.3f m/s" % thr)
    for i in stuck:
        rej = ~g0["acc"][i]
        best = cur = bs = st = 0
        for k, rr in enumerate(rej):
            if rr:
                if cur == 0:
                    st = k
                cur += 1
                if cur > best:
                    best, bs = cur, st
            else:
                cur = 0
        print("  run %4d: longest rejection streak %3d steps from k=%d, velocity error at its start %+.2f m/s" % (i, best, bs, g0["x"][i, bs, 1] - xo[i, bs, 1]))
    allbest = []
    for i in range(1000):
        cur = best = 0
        for rr in ~g0["acc"][i]:
            cur = cur + 1 if rr else 0
            best = max(best, cur)
        allbest.append(best)
    print("longest rejection streak over all 1000 runs: median %d, 99th percentile %d, max %d" % (int(np.median(allbest)), int(np.percentile(allbest, 99)), max(allbest)))

    print("\n== 4b. kidnapped jump: at k=300 the true position jumps +3 m (10 r), clean fixes (runs=1000)")
    xj = gen_truth(ro, 1000, STEPS)
    xj[:, 300:, 0] += 3.0
    zj, _ = gen_meas(ro, xj)
    K_JUMP = 300
    for name, kw in (("plain", {}), ("gate 99 %", dict(gate=CHI2_99)), ("gate 99 % + reset after 5 rejects", dict(gate=CHI2_99, reset_n=5))):
        g = kalman(zj, Q_PSD, R_STD, **kw)
        err = np.abs(g["x"][:, K_JUMP:, 0] - xj[:, K_JUMP:, 0])
        ok = err < 3 * R_STD
        first = np.where(ok.any(axis=1), ok.argmax(axis=1), -1)
        rec100 = float(np.mean((first >= 0) & (first < 100)))
        rec = first[first >= 0]
        print("%-36s recovered within 100 steps (10 s): %5.1f %%   within %d steps: %5.1f %%   median first step with error < 3 r: %s" % (
            name, 100 * rec100, STEPS - K_JUMP, 100 * float(np.mean(first >= 0)),
            ("%d" % int(np.median(rec))) if len(rec) else "n/a"))
    g = kalman(zj, Q_PSD, R_STD, gate=CHI2_99)
    print("share of fixes rejected after the jump (gate 99 %%, no reset): %.1f %%" % (100 * (~g["acc"][:, K_JUMP:]).mean()))

    # ------------------------------------------------------------------ figures
    tk = np.arange(STEPS) * DT
    i0 = 3
    fig, ax = plt.subplots(2, 1, figsize=(6.4, 5.2), sharex=True)
    sl = slice(0, 200)
    ax[0].plot(tk[sl], z[i0, sl], ".", ms=3, color="#9ca3af", label="fixes z")
    ax[0].plot(tk[sl], x[i0, sl, 0], "-", color="#111827", lw=1.2, label="true position")
    ax[0].plot(tk[sl], f["x"][i0, sl, 0], "-", color="#2563eb", lw=1.4, label="Kalman estimate")
    ax[0].set_ylabel("position (m)"); ax[0].legend(fontsize=8, loc="upper left")
    ax[1].plot(tk[sl], v_raw[i0, sl], "-", color="#d1d5db", lw=0.8, label="difference of fixes")
    ax[1].plot(tk[sl], x[i0, sl, 1], "-", color="#111827", lw=1.2, label="true velocity")
    ax[1].plot(tk[sl], f["x"][i0, sl, 1], "-", color="#2563eb", lw=1.4, label="Kalman estimate")
    ax[1].set_ylim(-3, 5); ax[1].set_xlabel("time (s)"); ax[1].set_ylabel("velocity (m/s)"); ax[1].legend(fontsize=8, loc="upper right")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "kalman-amr-trace.svg")); plt.close(fig)

    fig, ax = plt.subplots(figsize=(5.2, 4.4))
    im = ax.imshow(np.log10(ratio), origin="lower", cmap="YlOrRd", vmin=0, vmax=np.log10(ratio).max())
    ax.set_xticks(range(5)); ax.set_xticklabels([str(s_) for s_ in scales]); ax.set_yticks(range(5)); ax.set_yticklabels([str(s_) for s_ in scales])
    ax.set_xlabel("assumed R / true R"); ax.set_ylabel("assumed q / true q")
    for i in range(5):
        for j in range(5):
            ax.text(j, i, "%.2f" % ratio[i, j], ha="center", va="center", fontsize=8, color="black")
    ax.set_title("position RMSE / matched RMSE", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "kalman-amr-mismatch.svg")); plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(7.4, 3.7))
    xs_ = list(range(len(eps_list)))
    for name, col in (("plain", "#dc2626"), ("gate 99 %", "#2563eb"), ("gate 99.9 %", "#059669"), ("gate 99 % + reset(5)", "#7c3aed")):
        ax[0].plot(xs_, med[name], "o-", color=col, label=name)
        ax[1].plot(xs_, nbad[name], "o-", color=col, label=name)
    for a in ax:
        a.set_xticks(xs_); a.set_xticklabels(["%g" % (100 * e) for e in eps_list]); a.set_xlabel("share of outlier fixes (%)")
    ax[0].set_ylabel("median per-run position RMSE (m)"); ax[1].set_ylabel("runs (of 1000) with RMSE > 1 m")
    ax[0].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "kalman-amr-outliers.svg")); plt.close(fig)
    print("\nelapsed %.1f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
