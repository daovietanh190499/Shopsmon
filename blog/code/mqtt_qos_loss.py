"""MQTT QoS 0/1/2 handshakes on a lossy link: closed forms, Monte-Carlo simulation, burst loss.

Model (a single hop, stop-and-wait, as in MQTT-SN v1.2 section 6.13):
  * every packet is lost with probability p (Experiments 1, 2) or according to a two-state
    burst channel (Experiment 3);
  * the sender starts a retry timer T_retry when it sends a packet that expects a reply and
    retransmits (same message id, DUP=1) when it expires, at most N_RETRY times;
  * QoS 0: one PUBLISH, no reply.
    QoS 1: PUBLISH -> PUBACK. The receiver hands the message to the application on EVERY
           PUBLISH it receives (duplicates included) and answers each with a PUBACK.
    QoS 2: PUBLISH -> PUBREC, then PUBREL -> PUBCOMP. The receiver hands the message to the
           application once, on the first PUBLISH it receives (method A), and answers every
           PUBLISH with PUBREC and every PUBREL with PUBCOMP.
This is NOT the behaviour of MQTT over TCP, where the specification only requires re-sending
on reconnect (see the post); it models UDP-style links such as MQTT-SN.

Usage:  python mqtt_qos_loss.py            (about 15 seconds; prints every table used in the post
                                            and writes three SVG figures)
Environment: MQTT_OUT = output directory for the figures (default ../../assets/img/blog).
"""
import os
import time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

matplotlib.rcParams["svg.hashsalt"] = "mqtt-qos-loss"
matplotlib.rcParams["svg.fonttype"] = "none"
OUT = os.environ.get("MQTT_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "img", "blog"))

N_RETRY = 3                 # retransmissions after the first transmission (MQTT-SN recommends 3-5)
A = N_RETRY + 1             # attempts
T_RETRY = 10.0              # seconds (MQTT-SN recommends 10-15 s)
D = 0.05                    # one-way delay in seconds (assumption)
N_MSG = 400_000
PS = [0.01, 0.05, 0.10, 0.20, 0.30, 0.50]


# ---------------------------------------------------------------- closed forms (independent losses)
def cf(p, a=A):
    q = (1 - p) ** 2                      # PUBLISH and its reply both arrive
    fail = (1 - q) ** a                   # no reply after all attempts
    et = (1 - fail) / q                   # expected PUBLISH transmissions (QoS 1, or one QoS 2 phase)
    return dict(q=q,
                q0_lost=p,
                notdel=p ** a,            # no PUBLISH ever arrives (QoS 1 and 2)
                q1_unconf=fail,
                q1_et=et,
                q1_deliveries=(1 - p) * et,
                q1_packets=(2 - p) * et,
                q1_unconf_but_del=fail - p ** a,
                q2_incomplete=1 - (1 - fail) ** 2,
                q2_packets=(2 - p) * et * (1 + (1 - fail)))


# ---------------------------------------------------------------- simulation, independent losses
def sim(p, n, rng, a=A):
    pub1 = rng.random((n, a)) >= p
    rep1 = rng.random((n, a)) >= p
    ok1 = pub1 & rep1
    conf1 = ok1.any(1)
    first = np.where(conf1, ok1.argmax(1), a - 1)
    made1 = first + 1                                  # attempts actually sent in phase 1
    mask = np.arange(a)[None, :] < made1[:, None]
    deliveries = (pub1 & mask).sum(1)                  # QoS 1: one application delivery per received PUBLISH
    r = dict(
        q0_lost=1 - (rng.random(n) >= p).mean(),
        notdel=(deliveries == 0).mean(),
        q1_unconf=1 - conf1.mean(),
        q1_et=made1.mean(),
        q1_deliveries=deliveries.mean(),
        q1_dup=(deliveries >= 2).mean(),
        q1_unconf_but_del=((~conf1) & (deliveries > 0)).mean(),
        q1_packets=(made1 + deliveries).mean(),
        q1_conf_time=(first[conf1] * T_RETRY + 2 * D).mean(),
        q1_conf_time_max=(first[conf1] * T_RETRY + 2 * D).max(),
    )
    # QoS 2: phase 2 (PUBREL / PUBCOMP) only if phase 1 was confirmed
    pub2 = rng.random((n, a)) >= p
    rep2 = rng.random((n, a)) >= p
    ok2 = pub2 & rep2
    conf2 = ok2.any(1)
    made2 = np.where(conf2, ok2.argmax(1), a - 1) + 1
    mask2 = np.arange(a)[None, :] < made2[:, None]
    complete = conf1 & conf2
    packets = made1 + (pub1 & mask).sum(1) + np.where(conf1, made2 + (pub2 & mask2).sum(1), 0)
    r["q2_incomplete"] = 1 - complete.mean()
    r["q2_packets"] = packets.mean()
    r["q2_dup"] = 0.0                                   # by construction: one hand-over on the first PUBLISH
    return r


# ---------------------------------------------------------------- burst channel
# Per attempt the channel is Good (loss pg) or Bad (loss pb); both packets of one exchange see the same
# state; between consecutive attempts the state is kept with probability rho, otherwise redrawn from the
# stationary law (so the lag-1 state correlation is rho).
PI_B, PB, PG = 0.25, 0.8, 0.0          # mean loss = 0.25 * 0.8 = 0.20


def exact_burst(rho, a=A, pi_b=PI_B, pb=PB, pg=PG):
    pi = np.array([1 - pi_b, pi_b])
    l = np.array([pg, pb])
    m = rho * np.eye(2) + (1 - rho) * np.outer(np.ones(2), pi)

    def run(f):
        w = pi.copy()
        for _ in range(a - 1):
            w = (w * f) @ m
        return float((w * f).sum())
    return dict(notdel=run(l), unconf=run(1 - (1 - l) ** 2))


def sim_burst(rho, n, rng, a=A, pi_b=PI_B, pb=PB, pg=PG):
    s = np.empty((n, a), dtype=bool)
    s[:, 0] = rng.random(n) < pi_b
    for k in range(1, a):
        keep = rng.random(n) < rho
        s[:, k] = np.where(keep, s[:, k - 1], rng.random(n) < pi_b)
    loss = np.where(s, pb, pg)
    pub = rng.random((n, a)) >= loss
    rep = rng.random((n, a)) >= loss
    ok = pub & rep
    conf = ok.any(1)
    first = np.where(conf, ok.argmax(1), a - 1)
    mask = np.arange(a)[None, :] < (first + 1)[:, None]
    deliveries = (pub & mask).sum(1)
    return dict(notdel=(deliveries == 0).mean(), unconf=1 - conf.mean(),
                unconf_but_del=((~conf) & (deliveries > 0)).mean(),
                deliveries=deliveries.mean())


def need_attempts(p, target):
    q = (1 - p) ** 2
    return int(np.ceil(np.log(target) / np.log(1 - q)))


def main():
    t0 = time.time()
    rng = np.random.default_rng(20261121)
    print(f"Setup: N_RETRY={N_RETRY} (attempts {A}), T_RETRY={T_RETRY} s, one-way delay={D} s, {N_MSG} messages per row\n")

    print("== Experiment 1: independent losses, N_RETRY=3 (simulation | closed form) ==")
    rows = {}
    for p in PS:
        s = sim(p, N_MSG, rng)
        c = cf(p)
        rows[p] = (s, c)
        print(f"p={p:.2f}  QoS0 lost {s['q0_lost']:.4f}|{c['q0_lost']:.4f}   "
              f"QoS1/2 never delivered {s['notdel']:.5f}|{c['notdel']:.5f}   "
              f"QoS1 sender unconfirmed {s['q1_unconf']:.5f}|{c['q1_unconf']:.5f}   "
              f"QoS2 sender incomplete {s['q2_incomplete']:.5f}|{c['q2_incomplete']:.5f}")
    print()
    for p in PS:
        s, c = rows[p]
        print(f"p={p:.2f}  QoS1: PUBLISH tx {s['q1_et']:.4f}|{c['q1_et']:.4f}  app deliveries/msg {s['q1_deliveries']:.4f}|{c['q1_deliveries']:.4f}  "
              f"dup(>=2 deliveries) {s['q1_dup']:.4f}  unconfirmed-but-delivered {s['q1_unconf_but_del']:.5f}|{c['q1_unconf_but_del']:.5f}  "
              f"packets QoS1 {s['q1_packets']:.4f}|{c['q1_packets']:.4f}  QoS2 {s['q2_packets']:.4f}|{c['q2_packets']:.4f}  (QoS0 1)")
    print()
    for p in PS:
        s, _ = rows[p]
        print(f"p={p:.2f}  QoS1 mean time to confirm (confirmed msgs) {s['q1_conf_time']:.3f} s, worst {s['q1_conf_time_max']:.2f} s")
    print()

    print("== Attempts needed so that the sender is unconfirmed with probability <= target (closed form, independent losses) ==")
    for p in (0.05, 0.10, 0.20, 0.30, 0.50):
        print(f"p={p:.2f}  q={(1-p)**2:.4f}  target 1e-3: {need_attempts(p, 1e-3)} attempts ({need_attempts(p,1e-3)-1} retransmissions)   "
              f"target 1e-6: {need_attempts(p, 1e-6)} attempts ({need_attempts(p,1e-6)-1} retransmissions)")
    # check one value by simulation
    for p, a in ((0.30, need_attempts(0.30, 1e-3)), (0.50, need_attempts(0.50, 1e-3))):
        s = sim(p, 2_000_000, np.random.default_rng(5), a=a)
        print(f"  check p={p:.2f}, attempts={a}: simulated unconfirmed {s['q1_unconf']:.6f} (formula {cf(p, a)['q1_unconf']:.6f})")
    print()

    print(f"== Experiment 3: burst channel, mean loss {PI_B*PB:.2f} (P(bad)={PI_B}, loss in bad {PB}, loss in good {PG}), N_RETRY=3 ==")
    p0 = PI_B * PB
    iid = rows[0.20][1]
    print(f"independent losses p=0.20 (closed form): never delivered {iid['notdel']:.5f}  unconfirmed {iid['q1_unconf']:.5f}  "
          f"unconfirmed-but-delivered {iid['q1_unconf_but_del']:.5f}  deliveries/msg {iid['q1_deliveries']:.4f}")
    burst_rows = []
    for rho in (0.0, 0.5, 0.8, 0.95, 0.99):
        ex = exact_burst(rho)
        sm = sim_burst(rho, N_MSG, rng)
        burst_rows.append((rho, ex, sm))
        print(f"rho={rho:.2f}  never delivered exact {ex['notdel']:.5f} sim {sm['notdel']:.5f}   "
              f"unconfirmed exact {ex['unconf']:.5f} sim {sm['unconf']:.5f}   "
              f"unconfirmed-but-delivered sim {sm['unconf_but_del']:.5f}   deliveries/msg sim {sm['deliveries']:.4f}")
    print("more retransmissions under rho=0.95: ", end="")
    parts = []
    for a in (4, 6, 10, 20):
        ex = exact_burst(0.95, a=a)
        parts.append(f"attempts {a}: never delivered {ex['notdel']:.5f}, unconfirmed {ex['unconf']:.5f}")
    print(" | ".join(parts))
    print("independent losses p=0.20: ", " | ".join(f"attempts {a}: never delivered {cf(0.2, a)['notdel']:.2e}, unconfirmed {cf(0.2, a)['q1_unconf']:.2e}" for a in (4, 6, 10, 20)))
    print()

    # ------------------------------------------------------------ figures
    os.makedirs(OUT, exist_ok=True)
    # Figure 1: message sequence charts
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 5.2))
    names = ["QoS 0", "QoS 1 (PUBACK lost)", "QoS 2 (PUBREC lost)"]
    flows = [
        [("S", "R", "PUBLISH", False, 0, True)],
        [("S", "R", "PUBLISH", False, 0, True), ("R", "S", "PUBACK", True, 1, False), ("S", "R", "PUBLISH DUP=1", False, 2, True), ("R", "S", "PUBACK", False, 3, True)],
        [("S", "R", "PUBLISH", False, 0, True), ("R", "S", "PUBREC", True, 1, False), ("S", "R", "PUBLISH DUP=1", False, 2, True), ("R", "S", "PUBREC", False, 3, True),
         ("S", "R", "PUBREL", False, 4, True), ("R", "S", "PUBCOMP", False, 5, True)],
    ]
    notes = [["lost = gone"],
             ["app gets message twice"],
             ["app gets message once"]]
    for ax, nm, fl, nt in zip(axes, names, flows, notes):
        ax.set_xlim(0, 10); ax.set_ylim(-7.2, 1.2); ax.axis("off")
        ax.set_title(nm, fontsize=11)
        for x, lab in ((1.5, "Sender"), (8.5, "Receiver")):
            ax.text(x, 0.8, lab, ha="center", va="center", fontsize=10, weight="bold")
            ax.plot([x, x], [0.4, -7.0], color="#64748b", lw=1.2)
        for s, r, lab, lost, i, _ in fl:
            y = -0.6 - i * 1.1
            x0, x1 = (1.5, 8.5) if s == "S" else (8.5, 1.5)
            xe = x0 + (x1 - x0) * (0.55 if lost else 1.0)
            col = "#dc2626" if lost else "#0ea5e9"
            ax.annotate("", xy=(xe, y - 0.5), xytext=(x0, y), arrowprops=dict(arrowstyle="->", color=col, lw=1.6))
            ax.text((x0 + x1) / 2, y + 0.1, lab, ha="center", va="bottom", fontsize=8.5, color=col)
            if lost:
                ax.text(xe, y - 0.5, "X", color=col, fontsize=11, ha="center", va="center", weight="bold")
        ax.text(5, -7.1, nt[0], ha="center", va="top", fontsize=8.5, color="#334155")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "mqtt-qos-flows.svg"))
    plt.close(fig)

    # Figure 2: failure probabilities vs loss rate
    ps = np.array([0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5])
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    ax.plot(ps, ps, "o-", color="#64748b", label="QoS 0: message lost")
    ax.plot(ps, [cf(p)["notdel"] for p in ps], "s-", color="#22c55e", label="QoS 1/2: never delivered")
    ax.plot(ps, [cf(p)["q1_unconf"] for p in ps], "^-", color="#f59e0b", label="QoS 1: sender unconfirmed")
    ax.plot(ps, [cf(p)["q2_incomplete"] for p in ps], "v-", color="#a855f7", label="QoS 2: sender incomplete")
    for p in PS:
        s, _ = rows[p]
        ax.plot([p], [s["notdel"]], "k.", ms=5)
        ax.plot([p], [s["q1_unconf"]], "k.", ms=5)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("per-packet loss probability p"); ax.set_ylabel("probability (per message)")
    ax.set_title(f"N_RETRY = {N_RETRY} (4 attempts); lines = closed form, dots = simulation", fontsize=9.5)
    ax.grid(alpha=0.3, which="both"); ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "mqtt-qos-failure.svg")); plt.close(fig)

    # Figure 3: burst correlation
    rhos = np.linspace(0, 0.99, 100)
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    ax.plot(rhos, [exact_burst(r)["notdel"] for r in rhos], color="#22c55e", label="never delivered (burst channel)")
    ax.plot(rhos, [exact_burst(r)["unconf"] for r in rhos], color="#f59e0b", label="sender unconfirmed (burst channel)")
    ax.axhline(iid["notdel"], color="#22c55e", ls="--", lw=1.1, label="never delivered, independent losses")
    ax.axhline(iid["q1_unconf"], color="#f59e0b", ls="--", lw=1.1, label="sender unconfirmed, independent losses")
    for rho, ex, sm in burst_rows:
        ax.plot([rho], [sm["notdel"]], "k.", ms=6)
        ax.plot([rho], [sm["unconf"]], "k.", ms=6)
    ax.set_yscale("log")
    ax.set_xlabel("state persistence between attempts (rho)"); ax.set_ylabel("probability (per message)")
    ax.set_title("Same mean loss 0.20, QoS 1, 4 attempts (dots = simulation)", fontsize=9.5)
    ax.grid(alpha=0.3, which="both"); ax.legend(fontsize=7.5, loc="lower right")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "mqtt-qos-burst.svg")); plt.close(fig)
    print(f"done in {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
