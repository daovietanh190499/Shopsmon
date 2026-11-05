"""Post-training int8 quantization of a small MLP for an edge (TinyML) task, simulated in NumPy.
Reproduces every number and figure in the Shopsmon article
"Int8 quantization for edge AI: from the formula to measured error".
Task (synthetic): classify vibration windows as normal / imbalance / bearing-fault from FFT features.
Requires: numpy, matplotlib.   Run: python int8_quantization.py [--no-fig] [--seeds N]
"""
import os
import sys
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "img", "blog")
FS, N = 1024, 128                  # sampling rate (Hz), window length (samples)
DIMS = (64, 32, 16, 3)             # MLP: 64 -> 32 -> 16 -> 3


# ------------------------------------------------------------------ data
def make_windows(rng, n_per_class):
    t = np.arange(N) / FS
    X, y = [], []
    for c in range(3):
        for _ in range(n_per_class):
            f0 = rng.uniform(28, 32)
            ph = rng.uniform(0, 2 * np.pi)
            s = np.sin(2 * np.pi * f0 * t + ph)
            if c == 1:             # imbalance: stronger 2nd harmonic
                s = s + rng.uniform(0.2, 0.6) * np.sin(4 * np.pi * f0 * t + rng.uniform(0, 2 * np.pi))
            if c == 2:             # bearing fault: periodic decaying impulses (~3.5 x rotation rate)
                fr = rng.uniform(3.2, 3.8) * f0
                tau = rng.uniform(0, 1 / fr)
                for tk in np.arange(tau, t[-1], 1 / fr):
                    m = t >= tk
                    s[m] += rng.uniform(0.5, 1.5) * np.exp(-(t[m] - tk) * 400) * np.sin(2 * np.pi * 300 * (t[m] - tk))
            s = s + rng.normal(0, 0.3, N)
            mag = np.abs(np.fft.rfft(s * np.hanning(N)))[:64]
            X.append(np.log1p(mag)); y.append(c)
    X = np.array(X); y = np.array(y)
    p = rng.permutation(len(y))
    return X[p], y[p]


# ------------------------------------------------------------------ floating-point MLP (NumPy float64) trained with Adam
def init_params(rng):
    P = []
    for a, b in zip(DIMS[:-1], DIMS[1:]):
        P.append([rng.normal(0, np.sqrt(2.0 / a), (b, a)), np.zeros(b)])   # W has shape (out, in)
    return P


def forward(P, X, keep=False):
    h, acts = X, [X]
    for i, (W, b) in enumerate(P):
        h = h @ W.T + b
        if i < len(P) - 1:
            h = np.maximum(h, 0)
        acts.append(h)
    return (h, acts) if keep else h


def train(P, X, y, rng, epochs=40, lr=3e-3, bs=128):
    m = [[np.zeros_like(W), np.zeros_like(b)] for W, b in P]
    v = [[np.zeros_like(W), np.zeros_like(b)] for W, b in P]
    step = 0
    for _ in range(epochs):
        idx = rng.permutation(len(y))
        for s in range(0, len(y), bs):
            j = idx[s:s + bs]
            logits, acts = forward(P, X[j], keep=True)
            p = np.exp(logits - logits.max(1, keepdims=True)); p /= p.sum(1, keepdims=True)
            g = p; g[np.arange(len(j)), y[j]] -= 1; g /= len(j)
            step += 1
            for i in reversed(range(len(P))):
                gW, gb = g.T @ acts[i], g.sum(0)
                if i > 0:
                    g = (g @ P[i][0]) * (acts[i] > 0)
                for k, gr in enumerate((gW, gb)):
                    m[i][k] = 0.9 * m[i][k] + 0.1 * gr
                    v[i][k] = 0.999 * v[i][k] + 0.001 * gr * gr
                    mh, vh = m[i][k] / (1 - 0.9 ** step), v[i][k] / (1 - 0.999 ** step)
                    P[i][k] -= lr * mh / (np.sqrt(vh) + 1e-8)
    return P


# ------------------------------------------------------------------ quantization
def quant_weights(W, bits, per_channel):
    """Symmetric signed quantization, zero-point 0. Returns integer matrix and scale(s) of shape (out,)."""
    qmax = 2 ** (bits - 1) - 1
    amax = np.abs(W).max(1) if per_channel else np.full(W.shape[0], np.abs(W).max())
    s = np.maximum(amax, 1e-12) / qmax
    q = np.clip(np.round(W / s[:, None]), -qmax, qmax).astype(np.int32)
    return q, s


def act_params(lo, hi, bits=8):
    """Asymmetric unsigned quantization of an activation range [lo, hi] that always contains 0."""
    lo, hi = min(lo, 0.0), max(hi, 0.0)
    s = max(hi - lo, 1e-12) / (2 ** bits - 1)
    z = int(np.clip(round(-lo / s), 0, 2 ** bits - 1))
    return s, z


def calibrate(P, Xcal, bits=8):
    _, acts = forward(P, Xcal, keep=True)
    return [act_params(a.min(), a.max(), bits) for a in acts[:-1]]      # input of every layer


def quant_forward(P, X, wbits=8, per_channel=True, abits=8, cal=None):
    """Integer-only matrix products (int32 accumulators); requantization simulated with a float multiplier."""
    cal = cal or calibrate(P, X, abits)
    qmax_a = 2 ** abits - 1
    s_x, z_x = cal[0]
    xq = np.clip(np.round(X / s_x) + z_x, 0, qmax_a).astype(np.int32)
    for i, (W, b) in enumerate(P):
        wq, s_w = quant_weights(W, wbits, per_channel)
        bq = np.round(b / (s_w * s_x)).astype(np.int64)                    # int32 bias, scale s_w*s_x
        acc = (xq - z_x).astype(np.int64) @ wq.T.astype(np.int64) + bq     # integer accumulation
        y = acc * (s_w * s_x)                                              # real value of the output
        if i == len(P) - 1:
            return y
        y = np.maximum(y, 0)
        s_x, z_x = cal[i + 1]
        xq = np.clip(np.round(y / s_x) + z_x, 0, qmax_a).astype(np.int32)


def sqnr_db(W, Wq_deq):
    return 10 * np.log10((W ** 2).sum() / ((W - Wq_deq) ** 2).sum())


def deq(W, bits, per_channel):
    q, s = quant_weights(W, bits, per_channel)
    return q * s[:, None]


# ------------------------------------------------------------------ experiments
def one_seed(seed, bits_list):
    rng = np.random.default_rng(seed)
    Xtr, ytr = make_windows(rng, 1000)
    Xte, yte = make_windows(rng, 1000)
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
    Xtr, Xte = (Xtr - mu) / sd, (Xte - mu) / sd
    P = train(init_params(rng), Xtr, ytr, rng)
    cal = calibrate(P, Xtr[:256])
    lf = forward(P, Xte)
    res = dict(fp=(lf.argmax(1) == yte).mean())
    for pc, name in ((False, "pt"), (True, "pc")):
        for b in bits_list:
            lq = quant_forward(P, Xte, wbits=b, per_channel=pc, cal=cal)
            res[(name, b)] = (lq.argmax(1) == yte).mean()
            if b == 8:
                res[(name, "agree")] = (lq.argmax(1) == lf.argmax(1)).mean()
                res[(name, "err")] = np.abs(lq - lf).mean() / np.abs(lf).mean()
    return res, P


def main():
    nseeds = 12
    if "--seeds" in sys.argv:
        nseeds = int(sys.argv[sys.argv.index("--seeds") + 1])
    bits_list = [8, 6, 5, 4, 3, 2]

    # --- sanity check: the affine round trip error never exceeds s/2 inside the range
    rng = np.random.default_rng(0)
    x = rng.uniform(-1.3, 2.1, 100000)
    s, z = act_params(x.min(), x.max(), 8)
    xq = np.clip(np.round(x / s) + z, 0, 255)
    err = np.abs(x - s * (xq - z)).max()
    print(f"sanity: 8-bit round trip on U(-1.3,2.1): scale={s:.6f} zero_point={z} max error={err:.6f} <= s/2={s / 2:.6f}: {err <= s / 2 + 1e-12}")

    runs, P0 = [], None
    for sd in range(nseeds):
        r, P = one_seed(sd, bits_list)
        runs.append(r)
        if sd == 0:
            P0 = P
    ms = lambda key: (100 * np.mean([r[key] for r in runs]), 100 * np.std([r[key] for r in runs]))

    print(f"\n== Experiment 1: accuracy on {nseeds} independent seeds (new data + new training each), 3000 test windows each ==")
    print("float (fp64) : %.2f +- %.2f %%" % ms("fp"))
    for name, lab in (("pt", "int8 per-tensor "), ("pc", "int8 per-channel")):
        print(lab, ": %.2f +- %.2f %%" % ms((name, 8)),
              "| agreement with float: %.2f %%" % ms((name, "agree"))[0],
              "| mean |dlogit|/mean|logit|: %.4f" % np.mean([r[(name, "err")] for r in runs]))
    d_pt = np.array([r["fp"] - r[("pt", 8)] for r in runs]) * 100
    d_pc = np.array([r["fp"] - r[("pc", 8)] for r in runs]) * 100
    print("accuracy drop vs float (points): per-tensor mean %.3f (max %.2f), per-channel mean %.3f (max %.2f)" % (d_pt.mean(), d_pt.max(), d_pc.mean(), d_pc.max()))

    print("\n== Experiment 2: weight bit-width (activations stay 8-bit), mean +- std accuracy % ==")
    print("bits | per-tensor      | per-channel")
    for b in bits_list:
        a, bb = ms(("pt", b)), ms(("pc", b))
        print(f"{b:4d} | {a[0]:6.2f} +- {a[1]:5.2f} | {bb[0]:6.2f} +- {bb[1]:5.2f}")

    print("\n== Experiment 3: weight SQNR (dB) of the seed-0 network, all layers pooled ==")
    Wall = np.concatenate([W.ravel() for W, _ in P0])
    print("bits | 6.02*bits | per-tensor | per-channel")
    for b in (8, 6, 4, 3, 2):
        pt = np.concatenate([deq(W, b, False).ravel() for W, _ in P0])
        pc = np.concatenate([deq(W, b, True).ravel() for W, _ in P0])
        print(f"{b:4d} | {6.02 * b:9.1f} | {sqnr_db(Wall, pt):10.1f} | {sqnr_db(Wall, pc):11.1f}")

    nparam = sum(W.size + b.size for W, b in P0)
    nw = sum(W.size for W, _ in P0)
    nb = sum(b.size for _, b in P0)
    nch = sum(W.shape[0] for W, _ in P0)
    f32 = 4 * nparam
    i8 = nw + 4 * nb + 4 * nch
    print(f"\n== Size: {nparam} parameters; float32 storage = {f32} B; int8 weights + int32 biases + float32 per-channel scales = {i8} B ({f32 / i8:.2f}x smaller) ==")
    print("per-layer weight range |W|max:", ", ".join(f"{np.abs(W).max():.2f}" for W, _ in P0),
          "| per-row max/min of row max|W| (layer 1): %.1f" % (np.abs(P0[0][0]).max(1).max() / np.abs(P0[0][0]).max(1).min()))

    if "--no-fig" not in sys.argv:
        make_figures(runs, bits_list, P0)


def make_figures(runs, bits_list, P0):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(OUT, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

    # Figure 1: the 3-bit grid and the rounding error
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
    W = P0[0][0].ravel()
    ax[0].hist(W, bins=60, color="#9db4ff", edgecolor="none")
    q, s = quant_weights(P0[0][0], 3, False)
    for k in range(-3, 4):
        ax[0].axvline(k * s[0], color="#d33", lw=0.9)
    ax[0].set_title("Layer-1 weights and the 7 levels of a 3-bit grid")
    ax[0].set_xlabel("weight value"); ax[0].set_ylabel("count")
    xs = np.linspace(-1, 1, 2001)
    sc = 1 / 3
    ax[1].plot(xs, xs - np.round(xs / sc) * sc, color="#222", lw=1)
    ax[1].axhline(sc / 2, color="#d33", ls="--", lw=0.8); ax[1].axhline(-sc / 2, color="#d33", ls="--", lw=0.8)
    ax[1].set_title("Rounding error x - Q(x): bounded by s/2")
    ax[1].set_ylim(-0.23, 0.23)
    ax[1].set_xlabel("x"); ax[1].set_ylabel("error"); ax[1].text(-0.98, sc / 2 + 0.02, "+s/2", color="#d33")
    ax[1].text(-0.98, -sc / 2 - 0.045, "-s/2", color="#d33")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "int8-grid.svg")); plt.close(fig)

    # Figure 2: accuracy vs weight bits
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for name, lab, col in (("pt", "per-tensor", "#d33"), ("pc", "per-channel", "#2563eb")):
        m = [100 * np.mean([r[(name, b)] for r in runs]) for b in bits_list]
        sdv = [100 * np.std([r[(name, b)] for r in runs]) for b in bits_list]
        ax.errorbar(bits_list, m, yerr=sdv, marker="o", capsize=3, label=lab, color=col)
    ax.axhline(100 * np.mean([r["fp"] for r in runs]), color="#666", ls="--", lw=1, label="float reference")
    ax.set_xlabel("weight bits (activations 8-bit)"); ax.set_ylabel("test accuracy (%)")
    ax.set_xticks(bits_list); ax.invert_xaxis(); ax.legend(frameon=False)
    ax.set_title("Accuracy vs weight bit-width (mean ± std, %d seeds)" % len(runs))
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "int8-bits.svg")); plt.close(fig)

    # Cover (raster, for social sharing): 1200x630
    fig = plt.figure(figsize=(12, 6.3), dpi=100)
    fig.patch.set_facecolor("#0f172a")
    ax = fig.add_axes([0.07, 0.08, 0.86, 0.5]); ax.set_facecolor("#0f172a")
    w = np.sort(P0[0][0].ravel())
    xs = np.linspace(w.min(), w.max(), 3000)
    q, s = quant_weights(P0[0][0], 3, False)
    ax.plot(xs, xs, color="#475569", lw=1.2)
    ax.step(xs, np.clip(np.round(xs / s[0]), -3, 3) * s[0], color="#38bdf8", lw=2.2, where="mid")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    fig.text(0.07, 0.86, "Int8 quantization for edge AI", color="white", fontsize=40, fontweight="bold")
    fig.text(0.07, 0.72, "From the formula to measured error  |  NumPy, %d seeds" % len(runs), color="#94a3b8", fontsize=22)
    fig.text(0.93, 0.03, "shopsmon.com", color="#64748b", fontsize=16, ha="right")
    fig.savefig(os.path.join(OUT, "int8-quantization-cover.png"), facecolor=fig.get_facecolor()); plt.close(fig)
    print("figures written to", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
