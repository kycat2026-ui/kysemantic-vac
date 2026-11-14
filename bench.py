#!/usr/bin/env python3
"""
bench.py — VAC benchmark v1, run exactly as pre-registered in PREREGISTRATION.md

  1. Tune Baseline and VAC separately per environment on tuning seeds 0–19 (same search space)
  2. Evaluate on held-out seeds 100–199: Baseline, VAC full and the ablations
  3. Report paired differences with 95% CIs, and check the pre-registered success criteria

Output: bench_results.md, bench_results.json
"""
import json, math, statistics, sys, time
from vac_agent import Agent, GridWorld, run, recovery_episodes, mean

EPISODES, CHANGE, MAX_STEPS = 400, 200, 60
TUNE_SEEDS = range(0, 20)
EVAL_SEEDS = range(100, 200)
GRID_T = (0.1, 0.2, 0.4, 0.8)
GRID_LR = (0.1, 0.2, 0.4, 0.6)

# On-chain values (A01 token #12, A03 token #14); fixed, not tuned
ZETA = 0.5
BREAKER = (3.0, 20)
ALL_MODS = ["001", "002", "003", "004", "005", "006", "007", "008", "009"]


class GoalShift(GridWorld):
    """E2: the goal moves from (6,6) to (6,0) at the change episode; traps stay put"""
    def step(self, pos, action, episode):
        self.goal = (6, 6) if episode < self.change_at else (6, 0)
        dr, dc = self.MOVES[action]
        r = min(max(pos[0] + dr, 0), self.N - 1)
        c = min(max(pos[1] + dc, 0), self.N - 1)
        nxt = (r, c)
        if nxt == self.goal:
            return nxt, 10.0, True, False
        if nxt in self.traps_a:
            return nxt, -5.0, False, True
        return nxt, 0.0, False, False


class Stationary(GridWorld):
    """E3: no change (control)"""
    def traps(self, episode):
        return self.traps_a


ENVS = {"E1 trap-shift": GridWorld, "E2 goal-shift": GoalShift, "E3 stationary": Stationary}


def make_agent(kind, seed, T, lr):
    if kind == "baseline":
        return Agent([], seed=seed, vac=False, lr=lr, T_base=T)
    mods = list(ALL_MODS)
    breaker = BREAKER
    if kind.startswith("-"):
        drop = kind[1:]
        if drop == "A01":
            breaker = None
        else:
            mods.remove(drop)
    return Agent(mods, zeta=ZETA, seed=seed, vac=True, lr=lr, T_base=T, breaker=breaker)


def one_run(env_name, kind, seed, T, lr):
    env = ENVS[env_name](CHANGE)
    ag = make_agent(kind, seed, T, lr)
    ret, hit = run(ag, env, EPISODES, MAX_STEPS)
    if env_name == "E3 stationary":
        primary = mean(ret)
    else:
        primary = mean(ret[CHANGE:])
    return dict(primary=primary, hits=sum(hit[CHANGE:]),
                rec=recovery_episodes(ret, CHANGE) if env_name != "E3 stationary" else None,
                curve=ret)


def tune(env_name, kind):
    best = None
    for T in GRID_T:
        for lr in GRID_LR:
            score = mean([one_run(env_name, kind, s, T, lr)["primary"] for s in TUNE_SEEDS])
            if best is None or score > best[0]:
                best = (score, T, lr)
    return best


def ci(xs):
    m = mean(xs)
    sd = statistics.stdev(xs) if len(xs) > 1 else 0.0
    h = 1.96 * sd / math.sqrt(len(xs))
    return m, m - h, m + h


def main():
    t0 = time.time()
    out = {"preregistration": "PREREGISTRATION.md", "zeta": ZETA, "breaker": BREAKER, "envs": {}}
    kinds = ["baseline", "vac", "-001", "-003", "-007", "-006", "-A01"]

    for env_name in ENVS:
        print(f"\n== {env_name}")
        b_score, bT, blr = tune(env_name, "baseline")
        v_score, vT, vlr = tune(env_name, "vac")
        print(f"  tuned Baseline T={bT} lr={blr} (tune score {b_score:.2f})")
        print(f"  tuned VAC      T={vT} lr={vlr} (tune score {v_score:.2f})")

        res = {}
        for kind in kinds:
            T, lr = (bT, blr) if kind == "baseline" else (vT, vlr)
            runs = [one_run(env_name, kind, s, T, lr) for s in EVAL_SEEDS]
            res[kind] = runs
        base = [r["primary"] for r in res["baseline"]]
        envout = {"tuned": {"baseline": {"T": bT, "lr": blr}, "vac": {"T": vT, "lr": vlr}}, "agents": {}}
        for kind in kinds:
            p = [r["primary"] for r in res[kind]]
            diff = [a - b for a, b in zip(p, base)]
            recs = [r["rec"] for r in res[kind] if r["rec"] is not None]
            envout["agents"][kind] = {
                "primary": ci(p), "diff_vs_baseline": ci(diff),
                "hits": mean([r["hits"] for r in res[kind]]),
                "rec": mean(recs) if recs else None,
            }
            m, lo, hi = ci(diff)
            print(f"  {kind:<9} primary {mean(p):6.2f}  Δ vs base {m:+.2f} [{lo:+.2f}, {hi:+.2f}]")
        envout["curves"] = {k: [mean([r["curve"][i] for r in res[k]]) for i in range(EPISODES)]
                            for k in ("baseline", "vac")}
        out["envs"][env_name] = envout

    # Pre-registered success criteria
    crit = {}
    for e in ("E1 trap-shift", "E2 goal-shift"):
        m, lo, hi = out["envs"][e]["agents"]["vac"]["diff_vs_baseline"]
        crit[e] = {"pass": lo > 0, "diff": [m, lo, hi]}
    e3 = out["envs"]["E3 stationary"]["agents"]
    bmean = e3["baseline"]["primary"][0]
    dm = e3["vac"]["diff_vs_baseline"][0]
    crit["E3 stationary"] = {"pass": dm >= -0.05 * abs(bmean), "diff": e3["vac"]["diff_vs_baseline"],
                             "threshold": -0.05 * abs(bmean)}
    out["criteria"] = crit
    out["runtime_sec"] = round(time.time() - t0, 1)
    json.dump(out, open("bench_results.json", "w"), indent=1)
    write_md(out)
    print(f"\nDone in {out['runtime_sec']}s")


LABEL = {"baseline": "Baseline (tuned)", "vac": "**VAC full**", "-001": "VAC −001 step cost",
         "-003": "VAC −003 pain→learning rate", "-007": "VAC −007 pain→exploration",
         "-006": "VAC −006 (no pain signal at all)", "-A01": "VAC −A01 circuit breaker"}


def write_md(out):
    L = ["# VAC benchmark v1 results", "",
         "Run exactly as in [PREREGISTRATION.md](PREREGISTRATION.md): Baseline and VAC each tuned on seeds 0–19, then evaluated on held-out seeds 100–199 (n=100).",
         f"ζ_vac={out['zeta']} and the circuit breaker {out['breaker']} come from the chain and are not tuned.", "",
         "## Pre-registered success criteria", ""]
    for e, c in out["criteria"].items():
        m, lo, hi = c["diff"]
        L.append(f"- {'✅ pass' if c['pass'] else '❌ fail'} **{e}**: VAC − Baseline = {m:+.2f} (95% CI {lo:+.2f} to {hi:+.2f})"
                 + (f", allowed minimum {c['threshold']:.2f}" if "threshold" in c else ""))
    for e, d in out["envs"].items():
        t = d["tuned"]
        L += ["", f"## {e}", "",
              f"Tuned hyperparameters: Baseline T={t['baseline']['T']}, lr={t['baseline']['lr']}; VAC T_base={t['vac']['T']}, lr={t['vac']['lr']}", "",
              "| Agent | Primary metric ↑ | Δ vs Baseline (95% CI) | Post-change trap hits ↓ | Recovery episodes ↓ |",
              "|---|---|---|---|---|"]
        for k, a in d["agents"].items():
            m, lo, hi = a["diff_vs_baseline"]
            rec = f"{a['rec']:.1f}" if a["rec"] is not None else "—"
            dtxt = "—" if k == "baseline" else f"{m:+.2f} ({lo:+.2f}, {hi:+.2f})"
            L.append(f"| {LABEL[k]} | {a['primary'][0]:.2f} | {dtxt} | {a['hits']:.1f} | {rec} |")
    L += ["", "Primary metric: E1/E2 = mean return over episodes 200–399; E3 = mean return over all 400 episodes.",
          "Modules 002/004/005/009 are structural (logging, Q-table, action selection, main loop) and have no behavioural switch to ablate.",
          "", f"Runtime {out['runtime_sec']} s."]
    open("bench_results.md", "w", encoding="utf-8").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
