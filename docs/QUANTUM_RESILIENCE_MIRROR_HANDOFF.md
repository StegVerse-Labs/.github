# Quantum Resilience Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Goal: `QUANTUM-RESILIENCE-001`  
State: `SOURCE_PROGRAM_INITIALIZED / CRYPTO_CENSUS_AND_MIGRATION_REQUIRED`  
Credential authority: `TV/TVC`  
GitHub token runtime authority: `NONE`

## Purpose

Make StegVerse cryptographically resilient to future cryptographically relevant quantum computers without changing the existing authority model. Post-quantum cryptography strengthens confidentiality, authenticity and key establishment; it does not grant execution, transition, routing, custody, publication, receiving or policy authority.

## Canonical public standards baseline

The initial standards baseline is NIST FIPS 203 (ML-KEM), FIPS 204 (ML-DSA), and FIPS 205 (SLH-DSA). NIST states that these standards are ready for implementation now. NIST continues standardization work on additional algorithms, so StegVerse MUST remain crypto-agile rather than freezing one post-quantum algorithm forever.

## Current evidence

Repository search has already established two concrete classical-only risks that require migration planning:

- `StegVerse-Labs/StegID` v1 continuity receipts are explicitly Ed25519-only, including frozen invariants and keyring/signature contracts.
- `StegVerse-Labs/TVC/policy.rego` presently requires `w.signature.alg == "ed25519"` for relevant signed material.

These facts are evidence of quantum-vulnerable asymmetric dependencies, not evidence that every StegVerse cryptographic surface has been inventoried.

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

A surface MUST NOT transition to `PQC_VALIDATED` from documentation or algorithm name alone. Implementation and validation evidence are required.

## Three-entity responsibilities

### StegVerse-001
Preserve cryptographic lineage, key/algorithm transition history, receipt replay and historical-verification continuity. Detect replay divergence caused by migration and preserve pre-migration evidence without rewriting it.

### StegVerse-002
Own the canonical represented crypto census and algorithm-status knowledge: primitive, purpose, key lifetime, data lifetime, quantum exposure, migration state, evidence freshness and unresolved unknowns. It may propose policy changes but does not authorize them.

### SV-011
Construct and test bounded hybrid/PQC migration candidates, including compatibility, downgrade resistance, denied-consequence proofs, algorithm rollback and replacement paths. It may not self-grant authority or weaken existing controls to make migration pass.

## Initial machine tasks

1. Create a canonical cryptographic census with evidence-backed entries and explicit unknowns.
2. Add a quantum-resilience contract and deterministic validator.
3. Establish mandatory crypto-agility requirements for new consequence-bearing protocols.
4. Create migration tasks for the first observed classical-only roots: StegID Ed25519 continuity receipts and TVC Ed25519 policy.
5. Extend the census across TLS/WebPKI, device/node identity, wallet signatures, software/update provenance, receipt signing, key exchange, storage encryption and long-lived encrypted data.
6. Build hybrid migration tests using standardized PQ primitives while preserving authority separation.
7. Add harvest-now/decrypt-later classification for data with confidentiality lifetime beyond the migration horizon.
8. Make StegVerse-001, StegVerse-002 and SV-011 runtime-aware of this program through the existing resident substrate; do not create a parallel scheduler or WorkerCoordinator.

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
