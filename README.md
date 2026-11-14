# kysemantic-vac · VAC Protocol

> **VAC = Volitional-Affective Collapse** (by kysemantic.eth). This is unrelated to other projects that share the abbreviation "VAC", such as Verifiable Agent Claims.

**🟢 Live status: https://kycat2026-ui.github.io/kysemantic-vac/**

A working prototype of the **VAC System (Volitional-Affective Collapse Protocol) V1.0** by kysemantic.eth.

The nine modules in the white paper are being turned into runnable code. The agent loads its "volitional genome" from the VAC Protocol NFTs on-chain.

> "Pain", "will" and "survival drive" are names for system variables. They do not mean the machine has feelings or consciousness.

## 🔌 Attach your AI to the VAC constitution (free for noncommercial use)

Copy the single file [`vac_guard.py`](vac_guard.py) into your project. It needs nothing installed (Python standard library only):

```python
from vac_guard import VACGuard

guard = VACGuard()                  # rules come only from the official VAC Protocol NFTs (Ethereum mainnet)
if not guard.allowed():             # A02 creator veto: may I run? Fail-closed.
    raise SystemExit(guard.reason)

params = guard.params()             # {"se_threshold": 3.0, "cooldown": 20, "zeta": 0.5}, read from the chain

while running:
    surprise = my_ai.step()         # your AI's error, surprise or uncertainty
    if guard.breaker(surprise):     # A01 circuit breaker: too chaotic → pause or slow down
        continue
```

- **Single source:** at startup it checks the contract `0x4e22…f4fb` for its name and owner (kysemantic.eth). A look-alike contract is refused.
- **Creator veto:** any AI using this guard stops when the creator transfers out token #13.
- **Fail-closed:** if the chain can't be read, it doesn't run.
- Full example: [`example_attach.py`](example_attach.py). Run `python3 vac_guard.py` to see the current on-chain status.

## Rigorous benchmark v1 (pre-registered): honest findings

Pre-registration: [PREREGISTRATION.md](PREREGISTRATION.md) · Full results: [bench_results.md](bench_results.md)

- ✅ All three pre-registered criteria pass: VAC beats a **tuned** Baseline on held-out seeds, both after the environment changes (E1, E2) and in a stable environment (E3).
- ⚠️ **But the ablations show the advantage comes almost entirely from 001 (a small cost per step)**, a well-known reward-shaping trick. Removing the "pain" signal (006, which also disables 003 and 007) does not lower performance; it is even slightly higher.
- ⚠️ In the exploratory comparison, a Baseline with only the step cost added performs about the same as VAC full: a tie in E1, VAC slightly worse in E2, VAC slightly better in E3.
- Conclusion: **in this small grid world, the "pain → learning/exploration" mechanisms bring no measurable benefit yet.** The earlier "30% faster recovery" result compared against an untuned Baseline and is superseded by this benchmark.
- What VAC demonstrates is **on-chain governance** (NFTs decide parameters and the on/off switch), not a stronger learning algorithm.

## Quick start: the NFTs are the entry point

```bash
python3 vac_agent.py            # 1. read the NFTs on-chain → 2. enable modules → 3. run the experiment
python3 vac_agent.py --offline  # use an existing vac_genome.json
```

The agent first reads the VAC Protocol NFTs on Ethereum, and each module (001–009) is enabled only if its NFT is found. It then compares a standard agent with the VAC agent in a grid world, where the traps move halfway through. Results go to `results.md` and `results.png`.

Every push runs this automatically on GitHub Actions and commits the latest results back to the repo.

![results](results.png)

See [results.md](results.md) for the full results.

## Step 1: Read the NFT genome

```bash
python3 read_vac_nft.py                  # auto-detect the chain, read tokens 1–9
python3 read_vac_nft.py --chain base     # specify the chain
python3 read_vac_nft.py --ids 0-10       # specify a token range
```

- Read-only. It needs no private key and costs no gas.
- It uses only the Python standard library, so there is nothing to install.
- The output is `vac_genome.json`.

Contract: `0x4e22b334e53c1dc7e266b5996d32c05a6ac8f4fb`

## Constitutional amendments (on-chain rules)

| Token | Amendment | What the program does |
|---|---|---|
| #12 | A01 Emotional Circuit Breaker | Reads `SE Threshold` and `Cooldown Steps`; when pain exceeds the limit, the signal is capped and the agent cools down |
| #13 | A02 Creator Veto | **Checked first.** The program runs only while token #13 and Axiom #003 (token #4) are held by the same wallet; otherwise it halts. If ownership can't be confirmed on-chain, it also halts |
| #14 | A03 Zeta Calibration | Reads `Zeta` and uses it as ζ_vac |

To halt the system, transfer token #13 to another wallet. To resume, transfer it back.

## Related work

VAC is not the first attempt at these ideas. Below is related work, and how VAC differs.

**Surprise and prediction error driving learning and exploration**, which is the same family of ideas as VAC's "pain" signal:
- Achiam & Sastry (2017), [Surprise-Based Intrinsic Motivation for Deep Reinforcement Learning](https://arxiv.org/abs/1703.01732)
- Xu, Modirshanechi et al. (2021), [Novelty is not surprise](https://doi.org/10.1371/journal.pcbi.1009070), which finds that surprise speeds up human learning
- Le et al. (2024), [Beyond Surprise: Improving Exploration Through Surprise Novelty](https://arxiv.org/abs/2308.04836)

**Kill switches for AI agents**, now an industry standard:
- ServiceNow, [AI agent containment using kill switch protocol](https://www.servicenow.com/docs/r/SRy58xeijUUqttfwLgfrHQ/AXcrLMFYwlqODDrvnGbT6A)

**On-chain constitutions for AI agents:**
- [AgentCity: Constitutional Governance for Autonomous Agent Economies via Separation of Power](https://arxiv.org/abs/2604.07007) (2026). Smart contracts are the law, and every agent is bound to a responsible human principal.
- [The Governance Deficit in Autonomous Agents](https://hackernoon.com/the-governance-deficit-in-autonomous-agents) (Nostra), a constitutional DeFi agent

**How VAC differs:**
- The constitutional articles are themselves an NFT art series, and the parameters are written into the metadata.
- No custom smart contract is needed: transferring one standard ERC-721 NFT is the switch.
- If the chain can't be read, the system halts (fail-safe).
- A public, live status page lets anyone verify the current state.

## Module map (white paper → code)

| # | Module | Planned implementation |
|---|---|---|
| 001 | Irreversibility | Each step spends an energy budget; policy entropy is logged |
| 002 | Reciprocity | Will W (goal drive) / Resistance R (traps) |
| 003 | Recursive Closure | The affect signal updates value estimates |
| 004 | Attentional Manifold | Candidate actions with their value and cost |
| 005 | Collapse Operator | Probabilistic action selection |
| 006 | Affective Sensor | Prediction error → affect scalar SE |
| 007 | Re-entry Modulator | Boltzmann temperature adjusted by SE |
| 008 | Universal Constant ζ_vac | Global affect sensitivity |
| 009 | Unified Manifesto | Main loop plus report |

## Roadmap

- [x] Read NFT metadata on-chain
- [x] Grid-world environment
- [x] Implement modules 001–009 (enabled from the NFTs)
- [x] Controlled experiment: standard agent vs. VAC agent
- [x] Write numeric parameters into NFT metadata (amendments A01–A03)
- [x] Creator veto (A02)
- [x] Tune the baseline agent so the comparison is stricter (benchmark v1)
- [x] Ablation: switch off one module at a time (benchmark v1)
- [ ] Test the pain mechanisms in harder environments (noise, frequent changes, larger maps)
- [ ] Signature-based veto: the holder signs a message to halt without transferring the NFT
- [ ] Per-episode circuit breaker (cumulative pain) as an alternative to A01, compared experimentally
- [ ] Apply "brake on uncertainty" to language models and test whether it reduces hallucination

## License

This code is licensed under the [PolyForm Noncommercial License 1.0.0](LICENSE.md).

- ✅ **Free for noncommercial use**: personal projects, study, research, education, and nonprofits.
- 💼 **Commercial use requires a license**: companies or commercial products that want to use this code must get a commercial license from the author. To ask, open an [Issue](https://github.com/kycat2026-ui/kysemantic-vac/issues) or contact kysemantic.eth.

This license covers this repository's code only. The VAC Protocol white paper, NFT artwork and metadata stay the property of kysemantic.eth.

