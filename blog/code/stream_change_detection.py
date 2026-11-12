"""Change detection on a sensor stream: Shewhart, EWMA and CUSUM, calibrated to the same false-alarm rate.

Everything is simulated with fixed seeds (NumPy only for the experiments, Matplotlib for the two figures).
Usage:  python stream_change_detection.py [figure_dir]
Run time: roughly 2-4 minutes on a laptop.

Model: x_t = mu_t + e_t with e_t ~ N(0, 1) (the stream is already centred and scaled to unit noise).
mu_t = 0 before the change and delta afterwards. Run length = number of samples until the first alarm.
"""
import os
import sys
import time
from math import erf, exp, sqrt

import numpy as np

LAM = 1.0 / 8.0                 # EWMA weight: a power of two, so z += (x - z) >> 3 on an integer MCU
SD_EWMA = sqrt(LAM / (2.0 - LAM))  # asymptotic standard deviation of z for unit-variance white noise
K_CUSUM = 0.5                   # CUSUM reference value (tuned for a shift of 1 sigma)
ARL0_TARGET = 1.0 / (2.0 * (1.0 - 0.5 * (1.0 + erf(3.0 / sqrt(2.0)))))   # 3-sigma Shewhart: 370.4
KINDS = ("shewhart", "ewma", "cusum")
FIG_DIR = sys.argv[1] if len(sys.argv) > 1 else "."


def med3(a):
    """Running median of three along the last axis (output is 2 samples shorter)."""
    x, y, z = a[..., :-2], a[..., 1:-1], a[..., 2:]
    return np.maximum(np.minimum(x, y), np.minimum(np.maximum(x, y), z))


def noise(rng, n, length, phi=0.0):
    """White (phi=0) or AR(1) Gaussian noise with unit marginal variance, float32, shape (n, length)."""
    if phi == 0.0:
        return rng.standard_normal((n, length), dtype=np.float32)
    burn = 60
    e = rng.standard_normal((n, length + burn))
    out = np.empty_like(e)
    out[:, 0] = e[:, 0]
    s = sqrt(1.0 - phi * phi)
    for t in range(1, length + burn):
        out[:, t] = phi * out[:, t - 1] + s * e[:, t]
    return out[:, burn:].astype(np.float32)


def stream(rng, n, T, delta=0.0, phi=0.0, prefilter=False):
    """n independent streams of length T after an optional 3-point median prefilter.
    Two warm-up samples (no shift) precede t = 1 so that the filter has a full window."""
    x = noise(rng, n, T + 2, phi)
    x[:, 2:] += np.float32(delta)
    return med3(x) if prefilter else x[:, 2:]


def stat_path(kind, X):
    """Detection statistic at every step, scaled so that the alarm condition is stat > threshold.
    shewhart: |x|;  ewma: |z| / sd(z);  cusum: max(S+, S-). No reset (the first crossing is what matters)."""
    n, T = X.shape
    P = np.empty((n, T), np.float32)
    if kind == "shewhart":
        np.abs(X, out=P)
    elif kind == "ewma":
        z = np.zeros(n)
        for t in range(T):
            z += LAM * (X[:, t] - z)
            P[:, t] = np.abs(z) / SD_EWMA
    else:
        sp = np.zeros(n)
        sm = np.zeros(n)
        for t in range(T):
            x = X[:, t]
            sp = np.maximum(0.0, sp + x - K_CUSUM)
            sm = np.maximum(0.0, sm - x - K_CUSUM)
            P[:, t] = np.maximum(sp, sm)
    return P


def first_cross(P, thr):
    """Run length (1-based) of the first sample with P > thr; T if none (censored). Returns (len, n_censored)."""
    c = P > thr
    hit = c.any(axis=1)
    rl = np.where(hit, c.argmax(axis=1) + 1, P.shape[1])
    return rl, int((~hit).sum())


def run_lengths(kind, thr, delta, n, T, prefilter=False, phi=0.0, seed=0, chunk=2500):
    rng = np.random.default_rng(seed)
    out, cens = [], 0
    for i in range(0, n, chunk):
        P = stat_path(kind, stream(rng, min(chunk, n - i), T, delta, phi, prefilter))
        rl, c = first_cross(P, thr)
        out.append(rl)
        cens += c
    rl = np.concatenate(out)
    return rl.mean(), rl.std(ddof=1) / sqrt(len(rl)), np.median(rl), cens


def calibrate(kind, prefilter, n=8000, T=4500, seed=11):
    """Threshold giving in-control ARL0 = ARL0_TARGET (bisection, common random numbers)."""
    rng = np.random.default_rng(seed)
    P = np.concatenate([stat_path(kind, stream(rng, 2000, T, 0.0, 0.0, prefilter)) for _ in range(n // 2000)])
    lo, hi = 0.5, 12.0
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        rl, _ = first_cross(P, mid)
        if rl.mean() < ARL0_TARGET:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def step_factory(kind, n):
    """Stateful one-step detector for streaming runs (with reset after an alarm)."""
    st = {"z": np.zeros(n), "sp": np.zeros(n), "sm": np.zeros(n)}

    def step(x, thr):
        if kind == "shewhart":
            s = np.abs(x)
        elif kind == "ewma":
            st["z"] += LAM * (x - st["z"])
            s = np.abs(st["z"]) / SD_EWMA
        else:
            st["sp"] = np.maximum(0.0, st["sp"] + x - K_CUSUM)
            st["sm"] = np.maximum(0.0, st["sm"] - x - K_CUSUM)
            s = np.maximum(st["sp"], st["sm"])
        a = s > thr
        if a.any():
            st["z"][a] = 0.0
            st["sp"][a] = 0.0
            st["sm"][a] = 0.0
        return a

    return step


def alarm_rate(kind, thr, prefilter, p_spike, n=2000, T=5000, seed=5):
    """Alarms per 1000 samples on an in-control stream in which a fraction p_spike of samples is replaced
    by an isolated +-8 sigma glitch. The detector restarts after each alarm."""
    rng = np.random.default_rng(seed)
    x = rng.standard_normal((n, T + 2))
    sp = rng.random((n, T + 2)) < p_spike
    x[sp] = 8.0 * np.where(rng.random(sp.sum()) < 0.5, -1.0, 1.0)
    if prefilter:
        x = med3(x)
    else:
        x = x[:, 2:]
    step = step_factory(kind, n)
    alarms = 0
    for t in range(T):
        alarms += int(step(x[:, t], thr).sum())
    return 1000.0 * alarms / (n * T)


def fixed_point_ewma(delta, scale, thr, n, T, seed):
    """EWMA with lambda = 1/8 in integer arithmetic: z += (x - z) >> 3, x quantised to 1/scale sigma."""
    rng = np.random.default_rng(seed)
    X = stream(rng, n, T, delta)
    z = np.zeros(n, np.int32)
    first = np.full(n, T, np.int64)
    alive = np.ones(n, bool)
    lim = thr * SD_EWMA * scale
    for t in range(T):
        xq = np.rint(X[:, t] * scale).astype(np.int32)
        z += (xq - z) >> 3                       # arithmetic shift = floor division by 8
        hit = alive & (np.abs(z) > lim)
        first[hit] = t + 1
        alive &= ~hit
        if not alive.any():
            break
    return first.mean(), first.std(ddof=1) / sqrt(n), int(alive.sum())


def siegmund_arl_plus(k, h):
    """One-sided CUSUM in-control ARL, Siegmund's corrected diffusion approximation (b = h + 1.166)."""
    b = h + 1.166
    return (exp(2 * k * b) - 2 * k * b - 1.0) / (2 * k * k)


def main():
    t0 = time.time()
    print("== setup ==")
    print(f"LAM={LAM} (sd of z = {SD_EWMA:.5f}), CUSUM k={K_CUSUM}, target ARL0 = {ARL0_TARGET:.1f}")

    # ---- calibration --------------------------------------------------------------------------------------
    thr, thr_f = {}, {}
    for kind in KINDS:
        thr[kind] = calibrate(kind, False)
        thr_f[kind] = calibrate(kind, True)
        print(f"calibrated {kind:8s} plain thr = {thr[kind]:.4f}   median-of-3 thr = {thr_f[kind]:.4f}   ({time.time()-t0:.0f}s)")
    print(f"Shewhart analytic threshold 3.0000; calibrated {thr['shewhart']:.4f}")
    print(f"Siegmund approx. two-sided CUSUM ARL0 at calibrated h={thr['cusum']:.4f}: "
          f"{siegmund_arl_plus(K_CUSUM, thr['cusum']) / 2:.1f}")

    # ---- experiment 1: ARL0 (independent validation) and ARL1 ------------------------------------------------
    print("\n== Experiment 1: in-control ARL0 and out-of-control ARL1 (20000 runs each, mean +- s.e., median) ==")
    deltas = [0.5, 1.0, 1.5, 2.0, 3.0]
    tmax = {0.5: 3000, 1.0: 1500, 1.5: 800, 2.0: 400, 3.0: 200}
    res = {}
    for prefilter, th, label in ((False, thr, "plain"), (True, thr_f, "median-of-3")):
        print(f"-- {label} --")
        for kind in KINDS:
            m, se, med, c = run_lengths(kind, th[kind], 0.0, 20000, 4500, prefilter, seed=101)
            row = {0.0: (m, se, med, c)}
            line = f"{kind:8s} ARL0 = {m:7.1f} +- {se:4.1f} (median {med:5.0f}, censored {c})"
            for d in deltas:
                m, se, med, c = run_lengths(kind, th[kind], d, 20000, tmax[d], prefilter, seed=200 + int(d * 10))
                row[d] = (m, se, med, c)
            res[(prefilter, kind)] = row
            print(line)
            print("         ARL1: " + "   ".join(f"d={d}: {row[d][0]:.2f}+-{row[d][1]:.2f} (med {row[d][2]:.0f}, cens {row[d][3]})" for d in deltas))
        print(f"   ({time.time()-t0:.0f}s)")

    # ---- experiment 2: isolated spikes ---------------------------------------------------------------------
    print("\n== Experiment 2: alarms per 1000 samples, restart after alarm (2000 streams x 5000 samples) ==")
    for prefilter, th, label in ((False, thr, "plain"), (True, thr_f, "median-of-3")):
        for kind in KINDS:
            a0 = alarm_rate(kind, th[kind], prefilter, 0.0)
            a1 = alarm_rate(kind, th[kind], prefilter, 0.002)
            print(f"{label:11s} {kind:8s} clean {a0:5.2f}   with 0.2% spikes of 8 sigma {a1:5.2f}")
    print(f"   ({time.time()-t0:.0f}s)")

    # ---- experiment 3: autocorrelated noise ----------------------------------------------------------------
    print("\n== Experiment 3: ARL0 when the noise is AR(1) with unit variance (thresholds calibrated for white noise, plain) ==")
    for phi in (0.0, 0.3, 0.5, 0.7):
        parts = []
        for kind in KINDS:
            m, se, med, c = run_lengths(kind, thr[kind], 0.0, 20000, 6000, False, phi=phi, seed=303)
            parts.append(f"{kind} {m:7.1f}+-{se:4.1f} (cens {c})")
        print(f"phi={phi}: " + "   ".join(parts))
    print(f"   ({time.time()-t0:.0f}s)")

    # ---- experiment 4: fixed-point EWMA --------------------------------------------------------------------
    print("\n== Experiment 4: EWMA lambda=1/8 in integer arithmetic (20000 runs), float threshold ==")
    rng = np.random.default_rng(404)
    xs = stream(rng, 1, 2000, 1.0)
    zf = np.zeros(1)
    for scale in (256, 64, 16, 8):
        zq = np.zeros(1, np.int32)
        zf = np.zeros(1)
        worst = 0.0
        for t in range(2000):
            zf += LAM * (xs[:, t] - zf)
            zq += (np.rint(xs[:, t] * scale).astype(np.int32) - zq) >> 3
            worst = max(worst, abs(zq[0] / scale - zf[0]))
        print(f"scale 1/{scale} sigma: max |z_int - z_float| over one 2000-sample stream = {worst:.4f} sigma")
    m, se, med, c = run_lengths("ewma", thr["ewma"], 0.0, 20000, 4500, False, seed=101)
    print(f"float   : ARL0 {m:7.1f}+-{se:4.1f}")
    m1, se1, _, _ = run_lengths("ewma", thr["ewma"], 1.0, 20000, 1500, False, seed=210)
    print(f"float   : ARL1(d=1) {m1:6.2f}+-{se1:4.2f}")
    for scale in (256, 64, 16, 8):
        a0, s0, c0 = fixed_point_ewma(0.0, scale, thr["ewma"], 20000, 4500, 101)
        a1, s1, c1 = fixed_point_ewma(1.0, scale, thr["ewma"], 20000, 1500, 210)
        a5, s5, c5 = fixed_point_ewma(2.0, scale, thr["ewma"], 20000, 400, 220)
        print(f"int 1/{scale:3d}: ARL0 {a0:7.1f}+-{s0:4.1f} (cens {c0})   ARL1(d=1) {a1:6.2f}+-{s1:4.2f} (cens {c1})   ARL1(d=2) {a5:5.2f}+-{s5:4.2f}")
    print(f"   ({time.time()-t0:.0f}s)")

    make_figures(thr, res)
    print(f"\ntotal {time.time()-t0:.0f}s")


def make_figures(thr, res):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["svg.hashsalt"] = "shopsmon"
    plt.rcParams["svg.fonttype"] = "none"
    colors = {"shewhart": "#6b7280", "ewma": "#2563eb", "cusum": "#dc2626"}
    names = {"shewhart": "Shewhart |x| > 3", "ewma": "EWMA (lambda = 1/8)", "cusum": "CUSUM (k = 0.5)"}

    # Figure 1: one stream, shift of 1 sigma at t = 151
    rng = np.random.default_rng(7)
    T, tau = 300, 150
    x = rng.standard_normal(T)
    x[tau:] += 1.0
    z = np.zeros(T)
    sp = np.zeros(T)
    sm = np.zeros(T)
    zz = s1 = s2 = 0.0
    for t in range(T):
        zz += LAM * (x[t] - zz)
        s1 = max(0.0, s1 + x[t] - K_CUSUM)
        s2 = max(0.0, s2 - x[t] - K_CUSUM)
        z[t], sp[t], sm[t] = zz, s1, s2
    cus = np.maximum(sp, sm)
    ew = np.abs(z) / SD_EWMA
    tt = np.arange(1, T + 1)
    fig, ax = plt.subplots(3, 1, figsize=(9.2, 7.0), sharex=True)
    ax[0].plot(tt, x, lw=0.8, color=colors["shewhart"])
    ax[0].axhline(3, color="k", ls="--", lw=0.8)
    ax[0].axhline(-3, color="k", ls="--", lw=0.8)
    ax[0].set_ylabel("x_t")
    ax[0].set_title("Shewhart: alarm if |x_t| > %.2f" % thr["shewhart"], fontsize=10, loc="left")
    ax[1].plot(tt, ew, lw=1.0, color=colors["ewma"])
    ax[1].axhline(thr["ewma"], color="k", ls="--", lw=0.8)
    ax[1].set_ylabel("|z_t| / sd(z)")
    ax[1].set_title("EWMA: alarm if above %.3f" % thr["ewma"], fontsize=10, loc="left")
    ax[2].plot(tt, cus, lw=1.0, color=colors["cusum"])
    ax[2].axhline(thr["cusum"], color="k", ls="--", lw=0.8)
    ax[2].set_ylabel("max(S+, S-)")
    ax[2].set_title("CUSUM: alarm if above %.3f" % thr["cusum"], fontsize=10, loc="left")
    ax[2].set_xlabel("t (shift of +1 sigma starts at t = 151)")
    first = {}
    for i, (arr, lim) in enumerate(((np.abs(x), thr["shewhart"]), (ew, thr["ewma"]), (cus, thr["cusum"]))):
        idx = np.where(arr[tau:] > lim)[0]
        if idx.size:
            first[i] = tau + int(idx[0]) + 1
            ax[i].axvline(first[i], color="#16a34a", lw=1.2)
    for a in ax:
        a.axvline(tau + 1, color="#f59e0b", lw=1.2)
        a.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "change-detect-example.svg"))
    plt.close(fig)
    print("figure 1 first alarms after the change (t):", first)

    # Figure 2: ARL1 versus delta
    deltas = [0.5, 1.0, 1.5, 2.0, 3.0]
    fig, ax = plt.subplots(1, 1, figsize=(6.4, 4.4))
    for kind in KINDS:
        row = res[(False, kind)]
        ax.errorbar(deltas, [row[d][0] for d in deltas], yerr=[row[d][1] for d in deltas],
                    marker="o", lw=1.4, color=colors[kind], label=names[kind])
    ax.set_yscale("log")
    ax.set_xlabel("size of the shift (units of the noise standard deviation)")
    ax.set_ylabel("mean samples to alarm (ARL1)")
    ax.set_title("All three tuned to ARL0 = %.0f" % ARL0_TARGET, fontsize=10, loc="left")
    ax.grid(alpha=0.25, which="both")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "change-detect-arl.svg"))
    plt.close(fig)


if __name__ == "__main__":
    main()
