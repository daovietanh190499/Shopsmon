"""PCA through the SVD: derivation checks, numerical stability and a sensor-array experiment.

Run:  python pca_svd.py            (about 2 s; Python 3.12, NumPy, Matplotlib)
Everything is seeded; the numbers printed here are the ones quoted in the blog post.
Writes pca-sensors.svg and pca-stability.svg next to this script (or into $PCA_OUT).
"""
import os
import numpy as np

OUT = os.environ.get("PCA_OUT", os.path.dirname(os.path.abspath(__file__)))
D, K, N_TRAIN, N_TEST = 16, 3, 1000, 1000
NOISE = 0.3                       # per-channel sensor noise (std)
LATENT_STD = np.array([3.0, 2.0, 1.0])


# ---------------------------------------------------------------- PCA, two ways
def pca_svd(X, k):
    """PCA of the rows of X via thin SVD of the centred matrix. Returns mean, components (k,d), singular values."""
    mu = X.mean(0)
    _, s, Vt = np.linalg.svd(X - mu, full_matrices=False)
    return mu, Vt[:k], s


def pca_cov(X, k):
    """PCA via eigendecomposition of the sample covariance (forms X^T X, squaring the condition number)."""
    mu = X.mean(0)
    Xc = X - mu
    w, V = np.linalg.eigh(Xc.T @ Xc / (len(X) - 1))
    order = np.argsort(w)[::-1]
    return mu, V[:, order[:k]].T, w[order]


def reconstruct(X, mu, comps):
    return (X - mu) @ comps.T @ comps + mu


# ---------------------------------------------------------------- synthetic sensor array
def make_sensors(seed, n):
    """16 correlated channels driven by 3 latent sources (+ offset + noise); loadings fixed by `seed`."""
    rng = np.random.default_rng(seed)
    A = rng.normal(size=(D, K))                      # loadings
    off = rng.normal(scale=2.0, size=D)              # per-channel offset
    def draw(m, r):
        Z = r.normal(size=(m, K)) * LATENT_STD
        return Z @ A.T + off + r.normal(scale=NOISE, size=(m, D))
    return draw(n, rng), draw, rng


def main():
    # ============================================================ 1. correctness
    print("=== 1. SVD route vs covariance route (seed 0, n = %d, d = %d) ===" % (N_TRAIN, D))
    Xtr, draw, rng = make_sensors(0, N_TRAIN)
    mu1, C1, s = pca_svd(Xtr, K)
    mu2, C2, lam = pca_cov(Xtr, K)
    var_svd = s ** 2 / (N_TRAIN - 1)
    print("max |sigma_i^2/(n-1) - lambda_i|, all %d values : %.2e" % (D, np.abs(var_svd - lam).max()))
    signs = np.sign(np.sum(C1 * C2, 1))
    print("top-%d component vectors, max |v_svd - v_cov| after sign fix : %.2e" % (K, np.abs(C1 - signs[:, None] * C2).max()))
    print("eigenvalues of the covariance (top 6):", np.array2string(lam[:6], precision=3))
    print("variance share of the first %d components: %.2f %%" % (K, 100 * lam[:K].sum() / lam.sum()))

    # Eckart-Young: ||X - X_k||_F^2 = sum_{i>k} sigma_i^2
    print("\n=== 2. Eckart-Young identity on the training matrix ===")
    print(" k   ||Xc - Xc_k||_F^2    sum_{i>k} sigma_i^2")
    Xc = Xtr - Xtr.mean(0)
    for k in (1, 2, 3, 5, 8):
        mu, comps, _ = pca_svd(Xtr, k)
        err = np.linalg.norm(Xtr - reconstruct(Xtr, mu, comps)) ** 2
        print("%2d   %16.6f   %16.6f" % (k, err, np.sum(s[k:] ** 2)))

    # ============================================================ 3. compression on held-out data
    print("\n=== 3. 20 seeds: fit on %d samples, evaluate on %d held-out samples (k = %d) ===" % (N_TRAIN, N_TEST, K))
    rmse, fpr, det = [], [], {0.5: [], 1.0: [], 2.0: [], 3.0: []}
    det_min = {d: [] for d in det}
    for seed in range(20):
        Xtr, draw, rng = make_sensors(seed, N_TRAIN)
        Xte = draw(N_TEST, rng)
        mu, comps, _ = pca_svd(Xtr, K)
        rmse.append(np.sqrt(np.mean((Xte - reconstruct(Xte, mu, comps)) ** 2)))
        spe_tr = np.sum((Xtr - reconstruct(Xtr, mu, comps)) ** 2, 1)
        thr = np.quantile(spe_tr, 0.99)               # SPE (Q statistic) threshold from training residuals
        spe_te = np.sum((Xte - reconstruct(Xte, mu, comps)) ** 2, 1)
        fpr.append(np.mean(spe_te > thr))
        for delta in det:                              # offset fault of size delta on one channel
            rates = []
            for ch in range(D):
                Xf = Xte.copy()
                Xf[:, ch] += delta
                rates.append(np.mean(np.sum((Xf - reconstruct(Xf, mu, comps)) ** 2, 1) > thr))
            det[delta].append(np.mean(rates))
            det_min[delta].append(np.min(rates))
    theory = NOISE * np.sqrt((D - K) / D)
    print("held-out reconstruction RMSE per value : %.4f +- %.4f   (noise-only expectation %.4f)" % (np.mean(rmse), np.std(rmse), theory))
    print("storage: %d floats per sample -> %d scores (%.2fx smaller, plus %d x %d basis once)" % (D, K, D / K, K, D))
    print("false-alarm rate on held-out normal data : %.2f %% +- %.2f %%   (target 1 %%)" % (100 * np.mean(fpr), 100 * np.std(fpr)))
    print("detection rate of a one-channel offset fault (mean over 16 channels / worst channel), threshold = 99th pct of training SPE:")
    for delta in det:
        print("  offset %.1f  (%.1f x noise std):  %5.1f %% +- %.1f   worst channel %5.1f %%" % (
            delta, delta / NOISE, 100 * np.mean(det[delta]), 100 * np.std(det[delta]), 100 * np.mean(det_min[delta])))

    # ============================================================ 4. numerical stability
    print("\n=== 4. recovering singular values of a matrix with known spectrum (200 x 10) ===")
    r = np.random.default_rng(1)
    U, _ = np.linalg.qr(r.normal(size=(200, 10)))
    V, _ = np.linalg.qr(r.normal(size=(10, 10)))
    true = np.logspace(0, -10, 10)
    M = U @ np.diag(true) @ V.T
    s_svd = np.linalg.svd(M, compute_uv=False)
    ev = np.linalg.eigvalsh(M.T @ M)[::-1]
    s_cov = np.sqrt(np.maximum(ev, 0.0))
    print("cond(M) = %.1e,  cond(M^T M) = %.1e" % (true[0] / true[-1], (true[0] / true[-1]) ** 2))
    print(" i      true sigma     SVD route   rel.err    cov route   rel.err")
    for i in range(10):
        print("%2d   %12.3e  %12.3e  %8.1e  %12.3e  %8.1e" % (
            i + 1, true[i], s_svd[i], abs(s_svd[i] - true[i]) / true[i], s_cov[i], abs(s_cov[i] - true[i]) / true[i]))
    print("negative eigenvalues of M^T M: %d  (smallest %.2e)" % (np.sum(ev < 0), ev.min()))
    print("machine epsilon: %.2e, sqrt(eps) = %.2e" % (np.finfo(float).eps, np.sqrt(np.finfo(float).eps)))

    # ============================================================ figures
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10, "svg.hashsalt": "pca-svd", "svg.fonttype": "none"})

    Xtr, draw, rng = make_sensors(0, N_TRAIN)
    Xte = draw(N_TEST, rng)
    mu, comps_all, s = pca_svd(Xtr, D)
    lam = s ** 2 / (N_TRAIN - 1)
    ks = np.arange(0, D)            # k = D reconstructs exactly (error ~1e-30), omitted from the plot
    err_te = [np.mean((Xte - reconstruct(Xte, mu, comps_all[:k])) ** 2) if k else np.mean((Xte - mu) ** 2) for k in ks]
    err_tr = [np.mean((Xtr - reconstruct(Xtr, mu, comps_all[:k])) ** 2) if k else np.mean((Xtr - mu) ** 2) for k in ks]
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.5))
    ax[0].bar(np.arange(1, D + 1), lam, color="#2563eb")
    ax[0].set_yscale("log"); ax[0].set_xlabel("component"); ax[0].set_ylabel("variance (eigenvalue)")
    ax[0].axhline(NOISE ** 2, color="#dc2626", ls="--", lw=1)
    ax[0].text(D, NOISE ** 2 * 1.4, "noise variance 0.09", color="#dc2626", ha="right", fontsize=9)
    ax[0].set_title("Scree plot, 16 sensor channels")
    ax[1].plot(ks, err_tr, "o-", color="#2563eb", ms=4, label="training")
    ax[1].plot(ks, err_te, "s--", color="#f59e0b", ms=4, label="held-out")
    ax[1].set_yscale("log"); ax[1].set_xlabel("number of components k"); ax[1].set_ylabel("mean squared error per value")
    ax[1].legend(frameon=False); ax[1].set_title("Reconstruction error vs k")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "pca-sensors.svg")); plt.close(fig)

    fig, ax = plt.subplots(figsize=(5.6, 3.8))
    idx = np.arange(1, 11)
    ax.semilogy(idx, true, "k-", lw=1.5, label="true")
    ax.semilogy(idx, s_svd, "o", color="#2563eb", ms=6, label="SVD of M")
    ax.semilogy(idx, np.where(s_cov > 0, s_cov, np.nan), "s", color="#dc2626", ms=5, label="sqrt(eig(M$^T$M))")
    ax.axhline(np.sqrt(np.finfo(float).eps) * true[0], color="gray", ls=":", lw=1)
    ax.text(10, np.sqrt(np.finfo(float).eps) * true[0] * 2, r"$\sqrt{\epsilon}\,\sigma_1$", ha="right", fontsize=9, color="gray")
    ax.set_xlabel("index i"); ax.set_ylabel(r"$\sigma_i$"); ax.legend(frameon=False)
    ax.set_title("Singular values recovered in float64")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "pca-stability.svg")); plt.close(fig)


if __name__ == "__main__":
    main()
