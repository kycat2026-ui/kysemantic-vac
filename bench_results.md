# VAC benchmark v1 results

Run exactly as in [PREREGISTRATION.md](PREREGISTRATION.md): Baseline and VAC each tuned on seeds 0–19, then evaluated on held-out seeds 100–199 (n=100).
ζ_vac=0.5 and the circuit breaker (3.0, 20) come from the chain and are not tuned.

## Pre-registered success criteria

- ✅ pass **E1 trap-shift**: VAC − Baseline = +1.52 (95% CI +0.93 to +2.11)
- ✅ pass **E2 goal-shift**: VAC − Baseline = +0.69 (95% CI +0.40 to +0.98)
- ✅ pass **E3 stationary**: VAC − Baseline = +0.58 (95% CI +0.51 to +0.65), allowed minimum -0.44

## E1 trap-shift

Tuned hyperparameters: Baseline T=0.4, lr=0.6; VAC T_base=0.1, lr=0.6

| Agent | Primary metric ↑ | Δ vs Baseline (95% CI) | Post-change trap hits ↓ | Recovery episodes ↓ |
|---|---|---|---|---|
| Baseline (tuned) | 6.32 | — | 80.5 | 96.8 |
| **VAC full** | 7.84 | +1.52 (+0.93, +2.11) | 82.6 | 72.2 |
| VAC −001 step cost | 6.23 | -0.10 (-0.45, +0.25) | 72.5 | 99.6 |
| VAC −003 pain→learning rate | 8.12 | +1.80 (+1.24, +2.36) | 71.4 | 57.6 |
| VAC −007 pain→exploration | 8.15 | +1.82 (+1.27, +2.38) | 65.2 | 54.8 |
| VAC −006 (no pain signal at all) | 7.93 | +1.60 (+1.02, +2.18) | 74.4 | 61.5 |
| VAC −A01 circuit breaker | 7.72 | +1.40 (+0.83, +1.96) | 86.1 | 76.2 |

## E2 goal-shift

Tuned hyperparameters: Baseline T=0.8, lr=0.6; VAC T_base=0.2, lr=0.6

| Agent | Primary metric ↑ | Δ vs Baseline (95% CI) | Post-change trap hits ↓ | Recovery episodes ↓ |
|---|---|---|---|---|
| Baseline (tuned) | 7.72 | — | 1.7 | 45.6 |
| **VAC full** | 8.41 | +0.69 (+0.40, +0.98) | 0.8 | 31.4 |
| VAC −001 step cost | 5.15 | -2.57 (-3.17, -1.98) | 0.6 | 97.4 |
| VAC −003 pain→learning rate | 8.56 | +0.84 (+0.55, +1.13) | 0.7 | 28.5 |
| VAC −007 pain→exploration | 8.43 | +0.71 (+0.40, +1.02) | 0.9 | 30.8 |
| VAC −006 (no pain signal at all) | 8.54 | +0.82 (+0.54, +1.09) | 0.7 | 28.9 |
| VAC −A01 circuit breaker | 8.40 | +0.68 (+0.37, +1.00) | 0.5 | 31.6 |

## E3 stationary

Tuned hyperparameters: Baseline T=0.4, lr=0.6; VAC T_base=0.1, lr=0.6

| Agent | Primary metric ↑ | Δ vs Baseline (95% CI) | Post-change trap hits ↓ | Recovery episodes ↓ |
|---|---|---|---|---|
| Baseline (tuned) | 8.76 | — | 0.0 | — |
| **VAC full** | 9.34 | +0.58 (+0.51, +0.65) | 0.0 | — |
| VAC −001 step cost | 8.78 | +0.02 (+0.00, +0.04) | 0.0 | — |
| VAC −003 pain→learning rate | 9.33 | +0.57 (+0.50, +0.64) | 0.0 | — |
| VAC −007 pain→exploration | 9.24 | +0.48 (+0.42, +0.55) | 0.0 | — |
| VAC −006 (no pain signal at all) | 9.24 | +0.48 (+0.42, +0.55) | 0.0 | — |
| VAC −A01 circuit breaker | 9.36 | +0.60 (+0.53, +0.66) | 0.0 | — |

Primary metric: E1/E2 = mean return over episodes 200–399; E3 = mean return over all 400 episodes.
Modules 002/004/005/009 are structural (logging, Q-table, action selection, main loop) and have no behavioural switch to ablate.

Runtime 92.3 s.

## Exploratory analysis (not pre-registered)

Added **after** seeing the v1 ablations: removing 001 erases most of VAC's advantage, so this tests a Baseline with only the 001 step cost (same tuning procedure).

| Environment | Baseline+001 (tuned) | VAC full | VAC − (Baseline+001), 95% CI |
|---|---|---|---|
| E1 trap-shift | 7.72 (T=0.1, lr=0.4) | 7.84 | +0.12 (-0.44, +0.69) |
| E2 goal-shift | 8.71 (T=0.1, lr=0.6) | 8.41 | -0.31 (-0.49, -0.12) |
| E3 stationary | 9.24 (T=0.1, lr=0.6) | 9.34 | +0.10 (+0.07, +0.12) |
