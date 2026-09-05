# Quantum Resilience Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Goal: `QUANTUM-RESILIENCE-001`  
State: `SOURCE_POLICY_SLICES_MERGED / CRYPTO_BACKENDS_CENSUS_RUNTIME_REQUIRED`  
Credential authority: `TV/TVC`  
GitHub token runtime authority: `NONE`

## Purpose

Make StegVerse cryptographically resilient to future cryptographically relevant quantum computers without changing the existing authority model. Post-quantum cryptography strengthens confidentiality, authenticity and key establishment; it does not grant execution, transition, routing, custody, publication, receiving or policy authority.

## Canonical public standards baseline

The initial standards baseline is NIST FIPS 203 (ML-KEM), FIPS 204 (ML-DSA), and FIPS 205 (SLH-DSA). StegVerse MUST remain crypto-agile rather than freezing one post-quantum algorithm forever.

## Current evidence and merged migration slices

Concrete classical-only exposures now represented in the census include:

- `StegVerse-Labs/StegID` v1 continuity receipts: Ed25519;
- `StegVerse-Labs/StegID` current-phone DEVICE_POSSESSION: non-exportable browser P-256 key;
- `StegVerse-Labs/TVC/policy.rego`: Ed25519-only warrant signature assumptions;
- TLS/WebPKI, other device/node identity, wallet signatures, software/update provenance, and long-lived stored confidentiality remain explicitly uninventoried.

Merged source progress:

```text
StegID PR #10
merge: 8ed1bd6f2ec35447bc1f3fd1ac922a717ce1b060
result: fail-closed hybrid Ed25519 + ML-DSA-65 receipt policy; real ML-DSA backend still required

TVC PR #321
merge: c743cebae4452fcbad7abcc7b40448953a9c5422
result: versioned legacy/hybrid signature-profile policy; missing PQ evidence and caller assertions fail closed; real ML-DSA verifier and Rego binding still required
```

These are migration-policy source results only. Neither merge proves deployed PQ protection.

## Quantum security invariants

1. `QUANTUM_SAFE_UNKNOWN != QUANTUM_SAFE`.
2. Capability never confers authority, including cryptanalytic or quantum capability.
3. TV/TVC remains the credential authority during and after migration.
4. InTr/Interlock remains the transition boundary.
5. Cryptographic algorithms MUST be explicit, versioned and replaceable.
6. Long-lived confidentiality MUST account for harvest-now/decrypt-later exposure.
7. Historical receipts MUST remain verifiable across algorithm deprecation without silently rewriting history.
8. Migration SHOULD be hybrid when practical for consequence-bearing paths: classical + standardized PQ protection until the migration gate is explicitly retired.
9. New PQ algorithms are not automatically admitted merely because they are post-quantum; implementation quality, side channels, parameter sets, provenance and validation remain required.
10. No second user-operated machine is required by this program.

## Canonical states

- `UNINVENTORIED`
- `CLASSICAL_ONLY`
- `HYBRID_MIGRATION_REQUIRED`
- `HYBRID_ACTIVE`
- `PQC_VALIDATED`
- `DEPRECATED_CRYPTO_PRESENT`
- `QUANTUM_SAFETY_UNKNOWN`

A surface MUST NOT transition to `HYBRID_ACTIVE` or `PQC_VALIDATED` from documentation, suite naming, policy assertions, or CI alone. Real cryptographic implementation and validation evidence are required.

## Three-entity responsibilities

### StegVerse-001
Preserve cryptographic lineage, key/algorithm transition history, receipt replay and historical-verification continuity. Detect replay divergence caused by migration and preserve pre-migration evidence without rewriting it.

### StegVerse-002
Own the canonical represented crypto census and algorithm-status knowledge: primitive, purpose, key lifetime, data lifetime, quantum exposure, migration state, evidence freshness and unresolved unknowns. It may propose policy changes but does not authorize them.

### SV-011
Construct and test bounded hybrid/PQC migration candidates, including compatibility, downgrade resistance, denied-consequence proofs, algorithm rollback and replacement paths. It may not self-grant authority or weaken existing controls to make migration pass.

## Remaining machine tasks

1. continue the crypto census until no CRITICAL surface is `UNINVENTORIED`;
2. integrate a real validated ML-DSA backend into StegID receipt mint/verify paths;
3. integrate a real validated ML-DSA verifier into TVC and bind the active warrant gate to versioned suites;
4. design the P-256 current-phone device-possession migration around actual platform capability, with explicit compensating controls if native PQ device credentials are unavailable;
5. inventory TLS/WebPKI and introduce ML-KEM/hybrid key establishment where long-lived confidentiality creates harvest-now/decrypt-later risk;
6. inventory wallet signing and software/update provenance without changing USER_ONLY signing/broadcast authority;
7. add runtime standing quantum-resilience awareness for StegVerse-001, StegVerse-002 and SV-011 through the existing WorkerCoordinator/dispatcher substrate;
8. produce executable downgrade, stale-key, revoked-key, unknown-suite, hybrid verification, rollback and historical-verification tests;
9. propagate release-ready semantics to Site, Publisher, admissibility-wiki and stegguardian-wiki only after their handoffs permit it.

## Completion gates

`QUANTUM-RESILIENCE-001` is complete only when:

- the crypto census covers all consequence-bearing cryptographic surfaces or explicitly records bounded unresolved scope;
- no critical surface remains `UNINVENTORIED`;
- classical-only asymmetric dependencies have an admitted migration disposition;
- designated high-value paths have hybrid/PQC implementation and executable validation evidence;
- downgrade, rollback, stale-key and deprecated-algorithm paths fail closed;
- historical receipt verification survives algorithm migration;
- harvest-now/decrypt-later exposure has been classified and mitigated where required;
- all three AI entities consume the standing quantum-resilience state in their assigned roles;
- residual risks are stated without claiming absolute quantum security.

## Known downstream destinations

- `StegVerse-Labs/StegID`
- `StegVerse-Labs/TVC`
- `StegVerse-Labs/StegOS`
- `StegVerse-Labs/Site`
- `GCAT-BCAT-Engine/Publisher`
- `admissibility-wiki`
- `stegguardian-wiki`

## Archive posture

This handoff is the canonical continuation point for the quantum-resilience program. Source/CI evidence must never be represented as deployed PQ protection or authentic resident execution evidence.
