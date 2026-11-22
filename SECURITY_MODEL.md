# VAC Prototype Security Model and Limitations

## Scope

This repository implements the **Volitional-Affective Collapse (VAC) prototype**: an ERC-721-backed configuration/creator-veto reader, a Python guard, and a small tabular Q-learning experiment.

It is **not** a general-purpose data-sovereignty system, an LLM sandbox, or a complete agent permission manager.

## What the current guard does

- Pins the configured contract address and requires Ethereum Mainnet (chainId 1).
- Checks that bytecode exists and that the contract reports the expected name and owner.
- Checks that A02 (token #13) and Axiom #003 (token #4) are currently held by the same wallet.
- Stops when the chain cannot be queried or required governance tokens cannot be confirmed.
- Reads A01/A03 parameters from NFT metadata and exposes an uncertainty/surprise circuit-breaker helper.
- The standalone guard checks the creator veto on each `allowed()` call by default; callers should check it at each security-sensitive action boundary, not only once at process startup.

## What it does not guarantee

- **No enforcement outside the integration.** An agent can bypass VAC simply by not importing or calling `VACGuard`; the guard does not intercept operating-system, network, file, tool, or model access.
- **No user-data permission system.** There are no per-user data scopes, consent records, purpose restrictions, access logs, or reliable revocation of data already disclosed to a model.
- **No LLM behavior guarantee.** The circuit breaker is a helper. It cannot force a model or external tool to obey it.
- **No full contract identity proof.** Name, owner, chain ID, and bytecode presence are identity checks, not a pinned runtime-bytecode hash or independent source-code verification.
- **No cryptographic IPFS verification in the Python reader.** It retrieves JSON through HTTPS gateways; it does not independently recompute and verify the CID against returned bytes. Treat gateway-fetched metadata as an external input until that verification is implemented.
- **No independent security audit.** Unit tests and successful workflow runs are regression evidence, not a formal audit or proof of correctness.
- **No scientific proof of affect or consciousness.** The benchmark evaluates a small tabular Q-learning environment only. Terms such as pain, will, and survival are variable names, not evidence of machine experience.

## Fail-closed behavior

The online reader must reject the wrong chain, wrong contract identity, missing bytecode, generic RPC failures, and incomplete metadata reads. It must not overwrite a previously valid genome with a partial result. The agent must not fall back to an old cached genome after a failed live read.

The explicit `--offline` option is for reproducibility or controlled offline experiments only. A cached genome is not proof of current on-chain ownership. The creator-veto check still queries Ethereum, but cached metadata itself can be stale or altered.

## Before production use

1. Pin and verify the deployed contract runtime bytecode hash against an independently verified source build.
2. Verify IPFS content against each CID before parsing metadata.
3. Add integration tests for RPC failure, malformed ABI responses, missing tokens, gateway substitution, ownership transfer, and immediate veto propagation.
4. Have an independent reviewer audit the contract, Python guard, GitHub Actions permissions, and deployment process.
5. If the intended product is user data sovereignty, build a separate permission-enforcement layer (scoped credentials, policy checks at every data/tool boundary, audit trail, and revocation) rather than treating NFT ownership as data access control.

## Current status

The current CI regression tests cover the fail-closed cases listed in the test suite. They do not replace the production-readiness items above.
