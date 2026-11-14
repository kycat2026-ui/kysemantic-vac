# VAC Protocol

A working prototype of the **VAC System (Volitional-Affective Collapse Protocol) V1.0** by kysemantic.eth.

The nine modules in the white paper are being turned into runnable code. The agent loads its "volitional genome" from the VAC Protocol NFTs on-chain.

> "Pain", "will" and "survival drive" are names for system variables. They do not mean the machine has feelings or consciousness.

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
- [ ] Grid-world environment
- [ ] Implement modules 001–009
- [ ] Controlled experiment: standard agent vs. VAC agent
