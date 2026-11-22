# VAC Security Scope and Deployment Boundaries

Last reviewed: 2026-11-23

## Current implementation

The current repository is an **off-chain Python prototype that reads an existing ERC-721 contract and uses NFT ownership as an input to local execution rules**.

The Ethereum contract address configured by the reader and guard is:

`0x4e22b334e53c1dc7e266b5996d32c05a6ac8f4fb`

The repository is configured for Ethereum Mainnet (chain ID 1). The reader checks the chain ID, deployed bytecode, ERC-721 interface, contract name, and symbol before accepting the source. It refuses incomplete metadata reads and the agent refuses to fall back to an old cache after a failed live read.

The current creator-veto rule checks that A02 (token #13) and Axiom #003 (token #4) are owned by the same address. The standalone VACGuard also checks ownership before returning parameters.

## What the current implementation DOES provide

- Public, read-only lookup of the configured NFT contract and its token metadata.
- A chain-based ownership signal for the configured A02 / constitution tokens.
- Fail-closed behavior in the Python entry points for the tested missing-token, invalid-chain, and failed-read cases.
- Explicit regression tests and CI execution for those cases.

## What it DOES NOT provide

This prototype must not be described as a complete user-data-sovereignty or AI security enforcement system.

It currently does **not**:

- Intercept or sandbox every prompt, model call, tool call, memory read, file read, or external API request made by an AI agent.
- Force an arbitrary AI service or an unintegrated application to obey VAC rules. The Python guard is voluntary: an application can bypass it unless the execution environment is designed to enforce it.
- Provide fine-grained, per-user, per-data, per-purpose, or per-recipient consent and permissions.
- Prove that an NFT holder is the same person as the user whose personal data is being processed.
- Revoke data already copied, cached, exported, inferred, or sent to a third party. A token transfer can change the on-chain ownership signal; it cannot recall information already disclosed.
- Guarantee availability or immutability of off-chain metadata merely because a tokenURI points to IPFS. Gateway availability and pinning remain separate dependencies.
- Provide a complete tamper-evident audit log of every data access or prove that an AI actually complied.
- Replace independent smart-contract, application, infrastructure, privacy, or cryptographic audits.

## Is a new contract deployment required?

**No, not for the current Python reader/guard hardening.** Those changes are off-chain and do not alter the deployed contract's bytecode or storage.

A new deployment or contract upgrade should be considered only after a separate contract-level requirements review identifies a necessary on-chain feature, such as explicit permission scopes, policy versioning, revocation semantics, or events needed for auditability. Any such change requires a migration plan for existing token IDs, metadata, ownership, and consumers before deployment.

## Required gates before production use

1. Independently verify the deployed contract source and runtime bytecode against the intended source build.
2. Review the complete NFT inventory, token IDs, tokenURI values, metadata content, and current owner addresses directly from Ethereum Mainnet.
3. Run adversarial tests for RPC failure, malformed ABI responses, missing and unavailable metadata, token transfer during execution, and stale or substituted local files.
4. Threat-model how the guard is integrated into each AI application's actual data and tool access paths. A bypassable library is not an enforcement boundary.
5. Define a user-consent and permission model, including identity binding, least privilege, expiration, revocation, and audit evidence.
6. Obtain independent security and privacy review before processing real sensitive personal data.

## Status language

Use these terms accurately:

- **Implemented:** code is present in this repository.
- **CI-tested:** automated tests pass for the scenarios covered by the test suite.
- **Chain-observed:** a specific workflow successfully queried the configured contract at a recorded time.
- **Audited:** only after a qualified independent review has been completed and its scope and findings are published.

Passing CI does not mean the system is audited or production-safe.
