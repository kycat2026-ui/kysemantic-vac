"""Exploratory (not pre-registered; added after seeing v1 ablations, see the PREREGISTRATION.md amendment):
does the Baseline with only the 001 step cost added already match VAC full?"""
import json
import bench
from bench import ENVS, EVAL_SEEDS, TUNE_SEEDS, GRID_T, GRID_LR, one_run, ci, mean
from vac_agent import Agent

orig = bench.make_agent
def make_agent(kind, seed, T, lr):
    if kind == "base+001":
        return Agent(["001"], seed=seed, vac=True, lr=lr, T_base=T, breaker=None)
    return orig(kind, seed, T, lr)
bench.make_agent = make_agent

res = json.load(open("bench_results.json"))
lines = ["", "## Exploratory analysis (not pre-registered)", "",
         "Added **after** seeing the v1 ablations: removing 001 erases most of VAC's advantage, so this tests a Baseline with only the 001 step cost (same tuning procedure).", "",
         "| Environment | Baseline+001 (tuned) | VAC full | VAC − (Baseline+001), 95% CI |", "|---|---|---|---|"]
for env in ENVS:
    best = max(((mean([one_run(env, "base+001", s, T, lr)["primary"] for s in TUNE_SEEDS]), T, lr)
                for T in GRID_T for lr in GRID_LR))
    _, T, lr = best
    b1 = [one_run(env, "base+001", s, T, lr)["primary"] for s in EVAL_SEEDS]
    vT, vlr = res["envs"][env]["tuned"]["vac"]["T"], res["envs"][env]["tuned"]["vac"]["lr"]
    v = [one_run(env, "vac", s, vT, vlr)["primary"] for s in EVAL_SEEDS]
    m, lo, hi = ci([a - b for a, b in zip(v, b1)])
    print(env, f"base+001={mean(b1):.2f} (T={T},lr={lr}) vac={mean(v):.2f} diff={m:+.2f} [{lo:+.2f},{hi:+.2f}]")
    lines.append(f"| {env} | {mean(b1):.2f} (T={T}, lr={lr}) | {mean(v):.2f} | {m:+.2f} ({lo:+.2f}, {hi:+.2f}) |")
open("bench_results.md", "a", encoding="utf-8").write("\n".join(lines) + "\n")
