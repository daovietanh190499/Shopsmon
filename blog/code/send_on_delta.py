"""Send-on-delta (deadband, report-by-exception) reporting of a sensor stream.

A sensor samples every tick. A send-on-delta reporter keeps the last value it transmitted (the
"reference") and transmits a new sample only when |sample - reference| > delta (strict
inequality, as in the OPC UA AbsoluteDeadband filter, OPC 10000-4 section 7.22.2). The receiver
holds the last received value (zero-order hold, ZOH).

Experiments
  1. Constant signal + white noise (sigma = 1): message rate versus delta/sigma. Simulation, an exact
     Markov-chain computation, and the naive formula that forgets that the reference is itself a
     noisy sample.
  2. Noise-free random walk (step std sigma_w = 1): message rate versus delta, and the ZOH error of
     send-on-delta against periodic sampling with the SAME number of messages.
  3. Noisy random walk (noise std 1, step std 0.05): reconstruction error against the true signal at
     equal message budgets for periodic, periodic-with-averaging, raw send-on-delta and
     send-on-delta on an EWMA-filtered signal.
  4. Heartbeat: silent gaps with and without a "send at least every H ticks" rule.

Usage:  python send_on_delta.py        (about 2 minutes; prints every table used in the post and
                                        writes three SVG figures)
Environment: SOD_OUT = output directory for the figures (default ../../assets/img/blog).
"""
import os
import time
from math import erf, sqrt

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

matplotlib.rcParams["svg.hashsalt"] = "send-on-delta"
matplotlib.rcParams["svg.fonttype"] = "none"
OUT = os.environ.get("SOD_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "img", "blog"))
SEED = 20261122


# ------------------------------------------------------------------ core reporter
def sod_indices(x, delta):
    """Indices at which a send-on-delta reporter transmits (the first sample is always sent)."""
    xs = x.tolist()
    ref = xs[0]
    idx = [0]
    for i in range(1, len(xs)):
        v = xs[i]
        if v - ref > delta or ref - v > delta:
            ref = v
            idx.append(i)
    return np.array(idx)


def sod_heartbeat_indices(x, delta, hb):
    """Send-on-delta plus a heartbeat: also transmit when hb ticks passed since the last message."""
    xs = x.tolist()
    ref = xs[0]
    last = 0
    idx = [0]
    for i in range(1, len(xs)):
        v = xs[i]
        if v - ref > delta or ref - v > delta or i - last >= hb:
            ref = v
            last = i
            idx.append(i)
    return np.array(idx)


def zoh(n, idx, vals):
    """Receiver reconstruction: hold the last received value."""
    lengths = np.diff(np.append(idx, n))
    return np.repeat(vals, lengths)


def ewma(x, alpha):
    y = np.empty_like(x)
    prev = x[0]
    y[0] = prev
    xs = x.tolist()
    for i in range(1, len(xs)):
        prev += alpha * (xs[i] - prev)
        y[i] = prev
    return y


def Phi(z):
    return 0.5 * (1 + erf(z / sqrt(2)))


# ------------------------------------------------------------------ Experiment 1: noise only
def naive_rate(d):
    """Probability that one fresh sample differs from a FIXED reference sample by more than d."""
    return 2 * (1 - Phi(d / sqrt(2)))


def exact_rate(d, lim=9.0, m=1801, iters=400):
    """Messages per tick for a constant signal in N(0,1) noise.

    The reference offset a (the noise of the last transmitted sample) is a Markov chain over report
    times: the next report is the first fresh sample with |n - a| > d, so its density is
    phi(a') 1[|a' - a| > d] / P_a. With pi the stationary law of a and P_a = P(|n - a| > d), a cycle
    lasts 1/P_a ticks on average, hence rate = 1 / E_pi[1 / P_a].
    """
    a = np.linspace(-lim, lim, m)
    h = a[1] - a[0]
    phi = np.exp(-a * a / 2) / np.sqrt(2 * np.pi)
    P = np.array([Phi(v - d) + 1 - Phi(v + d) for v in a])
    mask = np.abs(a[None, :] - a[:, None]) > d
    K = mask * phi[None, :] * h
    K /= K.sum(1, keepdims=True)
    pi = np.ones(m) / m
    for _ in range(iters):
        pi = pi @ K
        pi /= pi.sum()
    return 1.0 / float((pi / P).sum())


def experiment1(ds, n=200_000, seeds=10):
    rng = np.random.default_rng(SEED)
    rows = []
    for d in ds:
        rates = []
        for _ in range(seeds):
            x = rng.standard_normal(n)
            rates.append((len(sod_indices(x, d)) - 1) / (n - 1))
        rates = np.array(rates)
        rows.append((d, rates.mean(), rates.std(ddof=1) / np.sqrt(seeds), exact_rate(d), naive_rate(d)))
    return rows


# ------------------------------------------------------------------ Experiment 2: random walk
def experiment2(deltas, n=400_000, seeds=10):
    rng = np.random.default_rng(SEED + 1)
    rows = []
    for d in deltas:
        rate, rm_sod, rm_per, mx_sod, mx_per, per_used = [], [], [], [], [], []
        for _ in range(seeds):
            x = np.cumsum(rng.standard_normal(n))
            idx = sod_indices(x, d)
            e = zoh(n, idx, x[idx]) - x
            rate.append(len(idx) / n)
            rm_sod.append(np.sqrt(np.mean(e ** 2)))
            mx_sod.append(np.max(np.abs(e)))
            p = max(1, int(round(n / len(idx))))         # periodic with the same message count
            pidx = np.arange(0, n, p)
            ep = zoh(n, pidx, x[pidx]) - x
            rm_per.append(np.sqrt(np.mean(ep ** 2)))
            mx_per.append(np.max(np.abs(ep)))
            per_used.append(p)
        rows.append(dict(d=d, rate=np.mean(rate), rate_se=np.std(rate, ddof=1) / np.sqrt(seeds),
                         theory=1 / d ** 2, rmse_sod=np.mean(rm_sod), rmse_per=np.mean(rm_per),
                         max_sod=np.max(mx_sod), max_per=np.mean(mx_per), period=np.mean(per_used)))
    return rows


# ------------------------------------------------------------------ Experiment 3: noisy walk, equal budgets
SIG_STEP, NOISE, ALPHA = 0.05, 1.0, 0.1


def make_noisy(rng, n):
    s = np.cumsum(SIG_STEP * rng.standard_normal(n))
    return s, s + NOISE * rng.standard_normal(n)


def calibrate(y, target_rate):
    """Bisection on delta so that the reporter sends target_rate messages per tick on series y."""
    lo, hi = 0.0, float(np.ptp(y))
    for _ in range(18):
        mid = 0.5 * (lo + hi)
        r = len(sod_indices(y, mid)) / len(y)
        if r > target_rate:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))


def experiment3(budgets, n_cal=100_000, n=100_000, seeds=6):
    rng = np.random.default_rng(SEED + 2)
    s_cal, x_cal = make_noisy(rng, n_cal)
    y_cal = ewma(x_cal, ALPHA)
    tests = [make_noisy(rng, n) for _ in range(seeds)]
    tests = [(s, x, ewma(x, ALPHA)) for s, x in tests]
    out = []
    for b in budgets:
        per = int(round(1 / b))
        d_raw = calibrate(x_cal, b)
        d_ew = calibrate(y_cal, b)
        res = {k: [] for k in ("per_raw", "per_mean", "sod_raw", "sod_ewma")}
        rates = {k: [] for k in res}
        for s, x, y in tests:
            pidx = np.arange(0, n, per)
            res["per_raw"].append(rmse(zoh(n, pidx, x[pidx]), s)); rates["per_raw"].append(len(pidx) / n)
            # periodic with averaging: at tick k*per report the mean of the last `per` samples
            ridx = np.arange(per - 1, n, per)
            means = x[: (n // per) * per].reshape(-1, per).mean(1)
            rec = np.concatenate([np.full(ridx[0], x[0]), zoh(n - ridx[0], ridx - ridx[0], means)])   # before the first block mean: hold the first sample (causal)
            res["per_mean"].append(rmse(rec, s)); rates["per_mean"].append(len(ridx) / n)
            ix = sod_indices(x, d_raw)
            res["sod_raw"].append(rmse(zoh(n, ix, x[ix]), s)); rates["sod_raw"].append(len(ix) / n)
            iy = sod_indices(y, d_ew)
            res["sod_ewma"].append(rmse(zoh(n, iy, y[iy]), s)); rates["sod_ewma"].append(len(iy) / n)
        out.append(dict(b=b, per=per, d_raw=d_raw, d_ew=d_ew,
                        rmse={k: (np.mean(v), np.std(v, ddof=1) / np.sqrt(seeds)) for k, v in res.items()},
                        rate={k: np.mean(v) for k, v in rates.items()}))
    floors = dict(raw=float(np.mean([rmse(x, s) for s, x, y in tests])), ewma=float(np.mean([rmse(y, s) for s, x, y in tests])))
    return out, floors


# ------------------------------------------------------------------ Experiment 4: heartbeat
def experiment4(d=10.0, hbs=(None, 200, 100, 50), n=400_000, seeds=10):
    rng = np.random.default_rng(SEED + 3)
    xs = [np.cumsum(rng.standard_normal(n)) for _ in range(seeds)]
    rows = []
    for hb in hbs:
        rate, gmax, gq99, rm = [], [], [], []
        for x in xs:
            idx = sod_indices(x, d) if hb is None else sod_heartbeat_indices(x, d, hb)
            gaps = np.diff(idx)
            rate.append(len(idx) / n)
            gmax.append(gaps.max())
            gq99.append(np.quantile(gaps, 0.99))
            rm.append(rmse(zoh(n, idx, x[idx]), x))
        rows.append(dict(hb=hb, rate=np.mean(rate), gmax=int(np.max(gmax)), gq99=np.mean(gq99), rmse=np.mean(rm)))
    return rows


# ------------------------------------------------------------------ figures
def fig1(rows):
    d = np.array([r[0] for r in rows])
    dd = np.linspace(0.3, 4.2, 40)
    fig, ax = plt.subplots(figsize=(4.8, 3.3))
    ax.semilogy(dd, [exact_rate(v) for v in dd], color="#0ea5e9", lw=1.8, label="exact (Markov chain)")
    ax.semilogy(dd, [naive_rate(v) for v in dd], color="#94a3b8", lw=1.4, ls="--", label="naive: fixed reference")
    ax.errorbar(d, [r[1] for r in rows], yerr=[2 * r[2] for r in rows], fmt="o", color="#ef4444", ms=4, capsize=2, label="simulation (2 SE)")
    ax.set_xlabel(r"deadband $\delta/\sigma$")
    ax.set_ylabel("messages per sample")
    ax.set_title("Constant signal in white noise", fontsize=10)
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "send-on-delta-noise-rate.svg"))
    plt.close(fig)


def fig2():
    rng = np.random.default_rng(SEED + 10)
    n = 700
    x = np.cumsum(rng.standard_normal(n))
    d = 6.0
    idx = sod_indices(x, d)
    p = max(1, int(round(n / len(idx))))
    pidx = np.arange(0, n, p)
    fig, axs = plt.subplots(2, 1, figsize=(6.2, 4.6), sharex=True, sharey=True)
    for ax, ii, title in ((axs[0], idx, f"send-on-delta, delta = {d:g} ({len(idx)} messages)"),
                          (axs[1], pidx, f"periodic every {p} ticks ({len(pidx)} messages)")):
        rec = zoh(n, ii, x[ii])
        ax.plot(x, color="#94a3b8", lw=1.0, label="signal")
        ax.step(np.arange(n), rec, where="post", color="#0ea5e9", lw=1.4, label="receiver (hold)")
        ax.plot(ii, x[ii], "o", color="#ef4444", ms=3, label="messages")
        ax.set_title(title, fontsize=9)
        ax.grid(True, alpha=0.25)
    axs[0].legend(fontsize=7, loc="upper left", ncol=3)
    axs[1].set_xlabel("sample")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "send-on-delta-trace.svg"))
    plt.close(fig)
    e1 = np.abs(zoh(n, idx, x[idx]) - x).max()
    e2 = np.abs(zoh(n, pidx, x[pidx]) - x).max()
    return len(idx), p, len(pidx), e1, e2


def fig3(res):
    fig, ax = plt.subplots(figsize=(4.8, 3.3))
    names = {"per_raw": ("periodic, raw sample", "#94a3b8", "s"), "per_mean": ("periodic, mean of block", "#10b981", "^"),
             "sod_raw": ("send-on-delta, raw", "#ef4444", "o"), "sod_ewma": ("send-on-delta, EWMA", "#0ea5e9", "D")}
    b = [r["b"] for r in res]
    for k, (lab, col, mk) in names.items():
        ax.errorbar(b, [r["rmse"][k][0] for r in res], yerr=[2 * r["rmse"][k][1] for r in res], color=col, marker=mk, ms=4, lw=1.3, capsize=2, label=lab)
    ax.set_xscale("log")
    ax.set_xlabel("messages per sample (budget)")
    ax.set_ylabel("RMSE against true signal")
    ax.set_title("Noisy random walk, noise 1, step 0.05", fontsize=10)
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "send-on-delta-budget.svg"))
    plt.close(fig)


# ------------------------------------------------------------------ main
if __name__ == "__main__":
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    print("== Experiment 1: constant signal + N(0,1) noise; 10 seeds x 200000 samples")
    r1 = experiment1([0.5, 1.0, 1.5, 2.0, 3.0, 4.0])
    print("delta/sigma | simulated rate (SE) | exact chain | naive fixed-reference | exact/naive")
    for d, m, se, ex, nv in r1:
        print(f"{d:4.1f} | {m:.5f} ({se:.5f}) | {ex:.5f} | {nv:.5f} | {ex / nv:.3f}")
    fig1(r1)
    print("\n== Experiment 2: noise-free random walk (step std 1); 10 seeds x 400000 samples")
    r2 = experiment2([2.0, 5.0, 10.0, 20.0])
    print("delta | rate (SE) | 1/delta^2 | rate*delta^2 | period used | RMSE SoD | RMSE periodic | ratio | max|err| SoD | max|err| periodic")
    for r in r2:
        print(f"{r['d']:5.1f} | {r['rate']:.5f} ({r['rate_se']:.5f}) | {r['theory']:.5f} | {r['rate'] * r['d'] ** 2:.3f} | {r['period']:.1f} | "
              f"{r['rmse_sod']:.3f} | {r['rmse_per']:.3f} | {r['rmse_sod'] / r['rmse_per']:.3f} | {r['max_sod']:.3f} | {r['max_per']:.2f}")
    print("RMSE/delta for SoD:", " ".join(f"{r['rmse_sod'] / r['d']:.3f}" for r in r2), "(continuous-time value 1/sqrt(6) = %.3f)" % (1 / np.sqrt(6)))
    ns, p, npd, e1, e2 = fig2()
    print(f"trace figure: SoD delta=6 {ns} messages, max|err| {e1:.3f}; periodic every {p} ticks {npd} messages, max|err| {e2:.3f}")
    print("\n== Experiment 3: noisy random walk (noise 1, step 0.05), EWMA alpha=%.2f; delta calibrated on one series, tested on 6 other series of 100000" % ALPHA)
    r3, floors = experiment3([1 / 200, 1 / 100, 1 / 50, 1 / 20, 1 / 10])
    print("budget | period | delta raw | delta EWMA | RMSE periodic raw | periodic mean | SoD raw | SoD EWMA | achieved rates (per_raw, per_mean, sod_raw, sod_ewma)")
    for r in r3:
        print(f"1/{r['per']:<3d} | {r['per']:3d} | {r['d_raw']:.3f} | {r['d_ew']:.3f} | " +
              " | ".join(f"{r['rmse'][k][0]:.3f} (+-{r['rmse'][k][1]:.3f})" for k in ("per_raw", "per_mean", "sod_raw", "sod_ewma")) +
              " | " + ", ".join(f"{r['rate'][k]:.4f}" for k in ("per_raw", "per_mean", "sod_raw", "sod_ewma")))
    print(f"floor (every sample transmitted): RMSE of the raw sample {floors['raw']:.3f}, RMSE of the EWMA-filtered signal {floors['ewma']:.3f}")
    fig3(r3)
    print("\n== Experiment 4: noise-free random walk, delta=10, heartbeat H; 10 seeds x 400000 samples")
    r4 = experiment4()
    print("H | rate | longest silent gap (max over seeds) | 99th percentile gap | RMSE")
    for r in r4:
        print(f"{r['hb']} | {r['rate']:.5f} | {r['gmax']} | {r['gq99']:.1f} | {r['rmse']:.3f}")
    print(f"\nelapsed {time.time() - t0:.0f} s")
