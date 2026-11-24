"""How many labelled decisions are needed before an automatic approver can be trusted?

Set-up ("shadow mode"): an automatic approver marks n changes as "would approve"; a human reviewer then
labels each one as fine or as containing a blocking defect. The number of bad approvals X among n is
modelled as Binomial(n, p), with p the unknown rate of bad approvals. The question is what the data can
certify about p, e.g. "p <= 2 % with 95 % confidence".

Experiments (all exact or seeded)
  1. One-sided 95 % upper bounds for p after k bad approvals: Clopper-Pearson (exact), Wilson, Jeffreys and
     Wald; the "rule of three" for k = 0; sample sizes needed for k = 0, 1, 2, 5 bad approvals.
  2. Exact coverage of those bounds (sum over the binomial distribution; one Monte-Carlo cross-check).
  3. Peeking: the certificate "Clopper-Pearson upper bound <= 2 %" is evaluated after every labelled
     decision (looking at accumulating data), against one look at the end, 20 uncorrected looks, and 20 looks with
     alpha/20 each. Probability of wrongly certifying when the true rate is 2 % to 5 %, and power for
     true rates of 0.25 % to 1 %.

Usage:  python shadow_auto_approve.py      (about 1 min; prints every table used in the post and writes
                                            three SVG figures)
Environment: SAA_OUT = output directory for the figures (default ../../assets/img/blog).
"""
import os
import time

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import beta, binom, norm

matplotlib.rcParams["svg.hashsalt"] = "shadow-auto-approve"
matplotlib.rcParams["svg.fonttype"] = "none"
OUT = os.environ.get("SAA_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "img", "blog"))
SEED = 20261124
ALPHA = 0.05
Z = norm.ppf(1 - ALPHA)  # one-sided 95 %: 1.6449
T0 = time.time()


# ---------------------------------------------------------------- bounds
def ub_cp(k, n, a=ALPHA):
    k = np.asarray(k, float)
    return np.where(k >= n, 1.0, beta.ppf(1 - a, k + 1, np.maximum(n - k, 1e-12)))


def ub_wilson(k, n, a=ALPHA):
    z = norm.ppf(1 - a)
    ph = np.asarray(k, float) / n
    return (ph + z * z / (2 * n) + z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))) / (1 + z * z / n)


def ub_jeffreys(k, n, a=ALPHA):
    k = np.asarray(k, float)
    return beta.ppf(1 - a, k + 0.5, n - k + 0.5)


def ub_wald(k, n, a=ALPHA):
    z = norm.ppf(1 - a)
    ph = np.asarray(k, float) / n
    return ph + z * np.sqrt(ph * (1 - ph) / n)


METHODS = [("Clopper-Pearson", ub_cp), ("Wilson", ub_wilson), ("Jeffreys", ub_jeffreys), ("Wald", ub_wald)]


def min_n(p0, k, a=ALPHA):
    """Smallest n with P(X <= k | n, p0) <= a, i.e. the CP upper bound after k bad approvals is <= p0."""
    lo, hi = max(k, 1), max(k, 1)
    while binom.cdf(k, hi, p0) > a:
        lo, hi = hi, hi * 2
    while lo < hi:
        mid = (lo + hi) // 2
        if binom.cdf(k, mid, p0) <= a:
            hi = mid
        else:
            lo = mid + 1
    return lo


# ---------------------------------------------------------------- 1. bounds and sample sizes
print("== 1a. One-sided 95 % upper bound on p after k = 0 bad approvals in n labelled decisions ==")
print(f"z = {Z:.4f}; rule of three: -ln(0.05) = {-np.log(ALPHA):.4f} (about 3)")
print(f"{'n':>6} {'CP':>8} {'3/n':>8} {'Wilson':>8} {'Jeffreys':>9} {'Wald':>6}")
for n in (10, 30, 100, 300, 1000):
    print(f"{n:>6} {ub_cp(0, n)*100:7.3f}% {min(3/n,1)*100:7.3f}% {ub_wilson(0, n)*100:7.3f}% {ub_jeffreys(0, n)*100:8.3f}% {ub_wald(0, n)*100:5.1f}%")

print("\n== 1b. One-sided 95 % upper bound after k bad approvals, n = 100 ==")
print(f"{'k':>3} {'p_hat':>6} {'CP':>8} {'Wilson':>8} {'Jeffreys':>9} {'Wald':>8}")
for k in (0, 1, 2, 3, 5):
    print(f"{k:>3} {k/100*100:5.1f}% {ub_cp(k,100)*100:7.2f}% {ub_wilson(k,100)*100:7.2f}% {ub_jeffreys(k,100)*100:8.2f}% {ub_wald(k,100)*100:7.2f}%")

print("\n== 1c. Smallest n whose Clopper-Pearson 95 % upper bound is <= p0, when k bad approvals are seen ==")
P0S = (0.05, 0.02, 0.01, 0.005, 0.001)
KS = (0, 1, 2, 5)
print(f"{'p0':>6} " + " ".join(f"k={k:<5}" for k in KS) + "  3/p0   ln(1/a)/ln(1/(1-p0))")
NREQ = {}
for p0 in P0S:
    row = [min_n(p0, k) for k in KS]
    NREQ[p0] = row
    print(f"{p0*100:5.1f}% " + " ".join(f"{v:<7}" for v in row) + f"  {3/p0:6.0f}  {np.log(ALPHA)/np.log(1-p0):8.2f}")

print("\n== 1d. P(0 bad approvals in n | true p) ==")
print(f"{'n':>5} " + " ".join(f"p={p*100:g}%".rjust(8) for p in (0.005, 0.01, 0.02, 0.03, 0.05)))
for n in (50, 100, 150, 300):
    print(f"{n:>5} " + " ".join(f"{(1-p)**n*100:7.2f}%" for p in (0.005, 0.01, 0.02, 0.03, 0.05)))

# ---------------------------------------------------------------- 2. exact coverage
print("\n== 2. Exact coverage of the one-sided 95 % upper bound (P[bound >= p]), in % ==")


def exact_coverage(fn, n, p):
    k = np.arange(0, n + 1)
    u = fn(k, n)
    return float(binom.pmf(k, n, p)[u >= p - 1e-15].sum())


PS = (0.005, 0.01, 0.02, 0.05)
NS = (50, 100, 300, 1000)
print(f"{'p':>6} {'n':>5} " + " ".join(f"{m:>16}" for m, _ in METHODS))
COV = {}
for p in PS:
    for n in NS:
        vals = [exact_coverage(fn, n, p) for _, fn in METHODS]
        COV[(p, n)] = vals
        print(f"{p*100:5.1f}% {n:>5} " + " ".join(f"{v*100:15.2f}%" for v in vals))

nc = np.arange(20, 1001, 2)
COV_P1 = {name: np.array([exact_coverage(fn, int(n), 0.01) for n in nc]) for name, fn in METHODS}
print(f"\nCoverage at p = 1 % over n = 20, 22, ..., 1000 ({len(nc)} values): share of n below 95 %, minimum")
for name, _ in METHODS:
    a = COV_P1[name]
    print(f"  {name:>16}: {np.mean(a < 0.95)*100:5.1f}% of n below 95 %, minimum {a.min()*100:.2f}% at n = {int(nc[a.argmin()])}")
w = COV_P1["Wald"]
loc = [(int(nc[t]), round(float(w[t]) * 100, 2)) for t in range(1, len(nc) - 1) if w[t] < w[t - 1] and w[t] < w[t + 1]]
print("  Wald local minima (n, coverage %):", loc)

rng = np.random.default_rng(SEED)
p_chk, n_chk = 0.01, 1000
x = rng.binomial(n_chk, p_chk, size=400_000)
mc = [float((fn(x, n_chk) >= p_chk).mean()) for _, fn in METHODS]
print(f"\nMonte-Carlo cross-check (400,000 draws, p = 1 %, n = {n_chk}): " + ", ".join(f"{m} {v*100:.2f}%" for (m, _), v in zip(METHODS, mc)))
x0 = rng.binomial(100, 0.01, size=400_000)
print(f"P(k = 0) at p = 1 %, n = 100: exact {(1-0.01)**100*100:.2f}%, Monte-Carlo {(x0 == 0).mean()*100:.2f}%")

# ---------------------------------------------------------------- 3. peeking
N = 2000
RUNS = 20000
CHUNK = 2000
P0 = 0.02
LOOKS = np.arange(100, N + 1, 100)  # 20 pre-planned looks
ns = np.arange(1, N + 1)


def k_table(a):
    """Largest k with P(X <= k | n, P0) <= a (-1 when no k qualifies) for n = 1..N."""
    out = np.full(N, -1, dtype=np.int16)
    for i, n in enumerate(ns):
        kk = int(binom.ppf(a, n, P0))
        while kk >= 0 and binom.cdf(kk, n, P0) > a:
            kk -= 1
        while binom.cdf(kk + 1, n, P0) <= a:
            kk += 1
        out[i] = kk if binom.cdf(kk, n, P0) <= a else -1
    return out


K_A = k_table(ALPHA)
K_B = k_table(ALPHA / len(LOOKS))
first_n = int(ns[np.argmax(K_A >= 0)])
print(f"\n== 3. Peeking (p0 = {P0*100:g} %, N = {N} labelled decisions, {RUNS} runs per rate, seed {SEED}) ==")
print(f"First n at which a certificate is possible: {first_n} (k = 0). K(N) = {K_A[N-1]} (largest k certified at n = {N}); K(1000) = {K_A[999]}; K(100) = {K_A[99]}")
print(f"With alpha/20 per look: first possible n = {int(ns[np.argmax(K_B >= 0)])}; K(N) = {K_B[N-1]}")

PRATES = (0.0025, 0.005, 0.01, 0.02, 0.03, 0.04, 0.05)
stats = {p: dict(fixed=0, peek=0, looks=0, bonf=0, first_peek=[], first_bonf=[]) for p in PRATES}
rng = np.random.default_rng(SEED + 1)
for _ in range(RUNS // CHUNK):
    U = rng.random((CHUNK, N), dtype=np.float32)  # common random numbers across rates
    for p in PRATES:
        cum = np.cumsum(U < p, axis=1, dtype=np.int16)
        ok = cum <= K_A[None, :]
        stats[p]["fixed"] += int(ok[:, N - 1].sum())
        anyok = ok.any(axis=1)
        stats[p]["peek"] += int(anyok.sum())
        stats[p]["first_peek"].extend((np.argmax(ok, axis=1)[anyok] + 1).tolist())
        stats[p]["looks"] += int(ok[:, LOOKS - 1].any(axis=1).sum())
        okb = cum[:, LOOKS - 1] <= K_B[None, LOOKS - 1]
        anyb = okb.any(axis=1)
        stats[p]["bonf"] += int(anyb.sum())
        stats[p]["first_bonf"].extend(LOOKS[np.argmax(okb, axis=1)[anyb]].tolist())

print("\nProbability of certifying 'p <= 2 %' within N decisions (in %); rows above 2 % are wrong certificates")
print(f"{'true p':>7} {'one look at N':>14} {'exact':>7} {'peek every':>11} {'20 looks':>9} {'20 looks':>9}")
print(f"{'':>7} {'':>14} {'':>7} {'decision':>11} {'(alpha)':>9} {'(a/20)':>9}")
for p in PRATES:
    s = stats[p]
    ex = binom.cdf(K_A[N - 1], N, p)
    print(f"{p*100:6.2f}% {s['fixed']/RUNS*100:13.2f}% {ex*100:6.2f}% {s['peek']/RUNS*100:10.2f}% {s['looks']/RUNS*100:8.2f}% {s['bonf']/RUNS*100:8.2f}%")

print("\nMedian number of labelled decisions at certification (among runs that certify)")
for p in PRATES[:3]:
    s = stats[p]
    mp = np.median(s["first_peek"]) if s["first_peek"] else float("nan")
    mb = np.median(s["first_bonf"]) if s["first_bonf"] else float("nan")
    print(f"p = {p*100:5.2f}%: peek every decision {mp:7.0f} (n = {len(s['first_peek'])}),  20 looks alpha/20 {mb:7.0f} (n = {len(s['first_bonf'])}),  fixed horizon N = {N}")

# ---------------------------------------------------------------- figures
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.3, "axes.spines.top": False, "axes.spines.right": False})


def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".svg"))
    if os.environ.get("SAA_PNG"):  # optional raster copy for visual checks
        fig.savefig(os.path.join(os.environ["SAA_PNG"], name + ".png"), dpi=110)
    plt.close(fig)


COL = {"Clopper-Pearson": "#2563eb", "Wilson": "#16a34a", "Jeffreys": "#f59e0b", "Wald": "#dc2626"}

# Fig 1: bound after k = 0 and exact coverage at p = 1 %
fig, ax = plt.subplots(1, 2, figsize=(10, 3.9))
nn = np.arange(5, 1001)
for name, fn in METHODS:
    ax[0].plot(nn, fn(0, nn) * 100, color=COL[name], label=name, lw=1.8)
ax[0].plot(nn, np.minimum(3 / nn, 1) * 100, "k--", lw=1, label="3/n")
ax[0].set_xscale("log")
ax[0].set_yscale("log")
ax[0].set_xlabel("labelled decisions n (0 bad approvals)")
ax[0].set_ylabel("95% upper bound on p (%)")
ax[0].set_title("Upper bound after zero failures")
ax[0].set_ylim(0.2, 100)
ax[0].legend(fontsize=8, loc="lower left")
for name, fn in METHODS:
    ax[1].plot(nc, COV_P1[name] * 100, color=COL[name], label=name, lw=1.2)
ax[1].axhline(95, color="k", ls="--", lw=1)
ax[1].set_xlabel("labelled decisions n")
ax[1].set_ylabel("exact coverage (%)")
ax[1].set_title("True p = 1 %: how often the bound is >= p")
ax[1].set_ylim(30, 101)
ax[1].legend(fontsize=8, loc="lower right")
fig.tight_layout()
save(fig, "saa-bounds")

# Fig 2: sample size vs p0
fig, ax = plt.subplots(figsize=(6.4, 4.2))
pg = np.geomspace(0.001, 0.1, 40)
for k, c in zip((0, 1, 2, 5), ("#2563eb", "#16a34a", "#f59e0b", "#dc2626")):
    ax.plot(pg * 100, [min_n(p, k) for p in pg], color=c, lw=1.8, label=f"k = {k} bad approvals")
ax.plot(pg * 100, 3 / pg, "k--", lw=1, label="3/p0")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("target p0 (%)")
ax.set_ylabel("labelled decisions needed")
ax.set_title("Decisions needed to certify p <= p0 (95%)")
ax.legend(fontsize=8)
fig.tight_layout()
save(fig, "saa-sample-size")

# Fig 3: peeking
fig, ax = plt.subplots(figsize=(6.8, 4.2))
pr = [p for p in PRATES if p >= 0.02]
for key, lab, c, ls in (("fixed", "one look at N", "#2563eb", "-"), ("bonf", "20 looks, alpha/20 each", "#16a34a", "-"),
                        ("looks", "20 looks, alpha each", "#f59e0b", "-"), ("peek", "look after every decision", "#dc2626", "-")):
    ax.plot([p * 100 for p in pr], [stats[p][key] / RUNS * 100 for p in pr], marker="o", color=c, ls=ls, label=lab)
ax.axhline(5, color="k", ls="--", lw=1)
ax.set_xlabel("true bad-approval rate p (%), all above-or-at the 2 % target")
ax.set_ylabel("P(certify 'p <= 2 %') (%)")
ax.set_title(f"Wrong certificates within N = {N} decisions")
ax.legend(fontsize=8)
fig.tight_layout()
save(fig, "saa-peeking")

print(f"\nDone in {time.time()-T0:.0f} s; figures in {os.path.abspath(OUT)}")
