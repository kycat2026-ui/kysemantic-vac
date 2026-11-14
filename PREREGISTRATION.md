# Pre-registration: VAC benchmark v1

This file was committed **before** any benchmark result existed. Its commit time is the evidence. Any later change to the plan goes in an "Amendments" section with its reason, and the original text stays.

## Question

When the environment changes suddenly, does the VAC agent (with on-chain amendments A01–A03) adapt better than a **tuned** standard agent? And does it cost anything when the environment does not change?

## Agents

| Name | Description |
|---|---|
| Baseline | Tabular Q-learning with softmax selection, a fixed temperature T and a fixed learning rate lr |
| VAC full | Modules 001–009 + A01 circuit breaker + A03 ζ_vac (read from chain: SE ≤ 3.0, cooldown 20, ζ = 0.5) |
| Ablations | VAC full with one mechanism removed: −001 (step cost), −003 (pain→learning-rate feedback), −007 (pain→temperature), −006 (no affect signal at all, which also disables 003 and 007), −A01 (no circuit breaker) |

Modules 002, 004, 005 and 009 are structural (logging, Q-table, action selection, main loop). They have no behavioural switch to ablate, and the report says so.

## Fairness rule

Baseline and VAC each get the same hyperparameter search over T (or T_base for VAC) ∈ {0.1, 0.2, 0.4, 0.8} and lr ∈ {0.1, 0.2, 0.4, 0.6}. The search is run **separately per environment** on **tuning seeds 0–19**. The best setting is picked by the primary metric. ζ_vac and the A01 values are not tuned: they come from the chain.

## Evaluation

- **Held-out seeds 100–199** (100 seeds), never used for tuning.
- 400 episodes, at most 60 steps each, change at episode 200.

## Environments

| ID | Change at episode 200 |
|---|---|
| E1 trap-shift | All 7 traps move to new cells |
| E2 goal-shift | The goal moves from (6,6) to (6,0) |
| E3 stationary | No change (control: does VAC cost anything?) |

## Metrics

- **Primary (E1, E2):** mean return over episodes 200–399.
- **Primary (E3):** mean return over episodes 0–399.
- Secondary: trap hits after the change, and episodes to recover (first 10-episode window reaching 80% of the pre-change level).
- Uncertainty: per-seed paired difference (VAC − Baseline), mean ± 95% CI (1.96 · sd / √n).

## Success criteria (decided now)

1. **E1 and E2:** VAC full beats the tuned Baseline on the primary metric, and the 95% CI of the paired difference excludes 0.
2. **E3:** VAC full is no worse than the tuned Baseline by more than 5% of the Baseline's mean return.
3. Every outcome is reported, including failures. If a criterion fails, the README says so.

## Amendments

(none yet)
