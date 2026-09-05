# Quantum Resilience Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Goal: `QUANTUM-RESILIENCE-001`  
State: `SOURCE_POLICY_AWARENESS_AND_PARTIAL_CENSUS_MERGED / CRYPTO_BACKENDS_BROADER_CENSUS_RESIDENT_CONSUMPTION_REQUIRED`  
Credential authority: `TV/TVC`  
GitHub token runtime authority: `NONE`

## Purpose

Make StegVerse cryptographically resilient to future cryptographically relevant quantum computers without changing the existing authority model. Post-quantum cryptography strengthens confidentiality, authenticity and key establishment; it does not grant execution, transition, routing, custody, publication, receiving or policy authority.

## Canonical public standards baseline

The initial standards baseline is NIST FIPS 203 (ML-KEM), FIPS 204 (ML-DSA), and FIPS 205 (SLH-DSA). StegVerse MUST remain crypto-agile rather than freezing one post-quantum algorithm forever.

## Current evidence and merged migration slices

Concrete source-evidenced exposures now represented include:

- `StegVerse-Labs/StegID` v1 continuity receipts: Ed25519, with hybrid migration policy built but no validated PQ backend;
- `StegVerse-Labs/StegID` current-phone DEVICE_POSSESSION: non-exportable browser P-256 key;
- `StegVerse-Labs/TVC/policy.rego`: Ed25519-only warrant signature assumptions, with hybrid migration policy built but no validated PQ backend/Rego binding;
- `StegVerse-Labs/continuity-vault-kit` SKAP browser ingress: ephemeral P-256 ECDH + HKDF-SHA256 + AES-256-GCM;
- `StegVerse-Labs/TVC` SKAP resident/browser recipient paths: P-256 recipient/resident keys and sealed-object handling;
- `StegVerse-Labs/StegTalk` ST-034 public TLS client: verified TLS with minimum TLSv1.2, but negotiated certificate/key-exchange algorithms remain unproven and therefore `QUANTUM_SAFETY_UNKNOWN`;
- `StegVerse-Labs/TVC` Service Gateway TLS-material adoption: source-side certificate/key validation exists, while authentic runtime certificate algorithm and negotiated key exchange remain unknown;
- `StegVerse-Labs/stegfin-governance` active wallet handoff: explicit USER_ONLY signing/broadcast through an external injected EIP-1193 wallet provider; StegVerse source does not establish the actual signer algorithm;
- `StegVerse-Labs/StegID` device-wallet capability: eligibility/capability decision only; it does not itself sign or broadcast.

Broader TLS/WebPKI, other device/node identity, active wallet-provider algorithms/chain constraints, software/update provenance, and long-lived stored confidentiality remain incompletely inventoried.

The SKAP P-256 key-establishment surfaces are explicitly harvest-now/decrypt-later relevant because recorded ciphertext may outlive the classical asymmetric assumption. This does not imply AES-256-GCM or HKDF-SHA256 are themselves deprecated; the migration target is the asymmetric key-establishment leg.

Current census source state:

```text
known CLASSICAL_ONLY surfaces in canonical crypto census: 3
known HYBRID_MIGRATION_REQUIRED surfaces in canonical crypto census: 2
PQC_VALIDATED surfaces: 0
TLS/confidentiality scoped census: PARTIAL_EXPLICIT
wallet/signature scoped census: PARTIAL_EXPLICIT
critical unresolved scope: remains present
```

Merged source progress:

```text
StegID PR #10
merge: 8ed1bd6f2ec35447bc1f3fd1ac922a717ce1b060
result: fail-closed hybrid Ed25519 + ML-DSA-65 receipt policy; real ML-DSA backend still required

TVC PR #321
merge: c743cebae4452fcbad7abcc7b40448953a9c5422
result: versioned legacy/hybrid signature-profile policy; missing PQ evidence and caller assertions fail closed; real ML-DSA verifier and Rego binding still required

.github PR #1016
merge: ed936a020f540b8ba0b66e0156e608a9711235fe
result: standing quantum-resilience awareness source for SV001/SV002/SV011; authentic resident consumption still required
validation head: 4e9f60c9382122cf27f9960a62b0a6ed406bad9c
Heartbeat run 33998703226: SUCCESS
Cross-Framework run 33998703249: SUCCESS
Organization control-plane run 33998703218: SUCCESS

.github PR #1017
merge: ef1a26a3e5aa42a518c08f93fd62ff621c9efd2e
result: concrete TLS/confidentiality census for StegTalk ST-034 and TVC Service Gateway TLS material; both remain QUANTUM_SAFETY_UNKNOWN
Heartbeat run 33999764057: SUCCESS
Organization control-plane run 33999764084: SUCCESS

.github PR #1018
merge: 328e1846ba50b62ee5251bcac316f9c2efd0e847
result: wallet/transaction-signature census preserving USER_ONLY sign/broadcast authority and explicitly refusing to infer the active signer algorithm from unrelated secp256k1 references
Heartbeat run 33999840503: SUCCESS
Organization control-plane run 33999840550: SUCCESS
```

The runtime-awareness source binds the canonical contract and census into three entity-specific standing states through the existing WorkerCoordinator/dispatcher substrate. Protected SV001/SV002/SV011 execution now requires both Astra-class standing awareness and quantum-resilience standing awareness. Missing quantum awareness fails closed as `QUANTUM_STANDING_AWARENESS_REQUIRED`.

These are source/control/census results only. They do not prove deployed PQ protection or authentic resident quantum awareness.

## Durable migration/census/runtime tasks

```text
StegVerse-Labs/continuity-vault-kit#187
purpose: hybrid P-256 + ML-KEM migration for SKAP browser key establishment

StegVerse-Labs/TVC#322
purpose: hybrid/PQ migration for TVC SKAP resident/browser P-256 surfaces

StegVerse-Labs/.github#1011
purpose: authentic resident consumption of standing quantum-resilience awareness for SV001/SV002/SV011
handoff: docs/QUANTUM_RUNTIME_AWARENESS_MIRROR_HANDOFF.md

StegVerse-Labs/.github#1013
purpose: wallet and transaction-signature census while preserving USER_ONLY sign/broadcast authority
handoff: docs/QUANTUM_WALLET_SIGNATURE_CENSUS_MIRROR_HANDOFF.md

StegVerse-Labs/.github#1014
purpose: TLS/WebPKI and long-lived confidentiality census
handoff: docs/QUANTUM_TLS_CONFIDENTIALITY_CENSUS_MIRROR_HANDOFF.md

StegVerse-Labs/Site#1027
purpose: determine which Site P-256 browser surfaces are active vs historical/example-only
```

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
11. Wallet migration MUST preserve explicit USER_ONLY signing and broadcast authority.

## Canonical states

- `UNINVENTORIED`
- `CLASSICAL_ONLY`
- `HYBRID_MIGRATION_REQUIRED`
- `HYBRID_ACTIVE`
- `PQC_VALIDATED`
- `DEPRECATED_CRYPTO_PRESENT`
- `QUANTUM_SAFETY_UNKNOWN`

A surface MUST NOT transition to `HYBRID_ACTIVE` or `PQC_VALIDATED` from documentation, suite naming, policy assertions, source merge or CI alone. Real cryptographic implementation and validation evidence are required.

## Three-entity responsibilities

### StegVerse-001
Preserve cryptographic lineage, key/algorithm transition history, receipt replay and historical-verification continuity. Detect replay divergence caused by migration and preserve pre-migration evidence without rewriting it.

### StegVerse-002
Own the canonical represented crypto census and algorithm-status knowledge: primitive, purpose, key lifetime, data lifetime, quantum exposure, migration state, evidence freshness and unresolved unknowns. It may propose policy changes but does not authorize them.

### SV-011
Construct and test bounded hybrid/PQC migration candidates, including compatibility, downgrade resistance, denied-consequence proofs, algorithm rollback and replacement paths. It may not self-grant authority or weaken existing controls to make migration pass.

## Remaining machine tasks

1. materialize the merged quantum-awareness source into the sovereign resident source tree and obtain the seven authentic artifacts defined by `docs/QUANTUM_RUNTIME_AWARENESS_MIRROR_HANDOFF.md`;
2. continue the crypto census until no CRITICAL surface is `UNINVENTORIED` or unbounded;
3. integrate a real validated ML-DSA backend into StegID receipt mint/verify paths;
4. integrate a real validated ML-DSA verifier into TVC and bind the active warrant gate to versioned suites;
5. design the P-256 current-phone device-possession migration around actual platform capability, with explicit compensating controls if native PQ device credentials are unavailable;
6. design and validate hybrid P-256 + ML-KEM key establishment for the SKAP browser/resident paths represented by continuity-vault-kit#187 and TVC#322;
7. extend the TLS/WebPKI census beyond the current StegTalk/TVC slices and introduce ML-KEM/hybrid dispositions where long-lived confidentiality creates harvest-now/decrypt-later risk;
8. extend the wallet census to actual admitted wallet-provider algorithms, chain constraints and repository-controlled verification/projection cryptography without changing USER_ONLY signing/broadcast authority;
9. inventory software/update provenance and long-lived stored confidentiality;
10. produce executable downgrade, stale-key, revoked-key, unknown-suite, hybrid verification, rollback and historical-verification tests;
11. propagate release-ready semantics to Site, Publisher, admissibility-wiki and stegguardian-wiki only after their handoffs permit it.

## Runtime-awareness evidence gate

Source merge `ed936a020f540b8ba0b66e0156e608a9711235fe` does not establish resident awareness. Runtime awareness requires the existing sovereign WorkerCoordinator to consume selector `quantum_resilience_awareness` and retain:

- `runtime-state/entity-quantum-awareness/stegverse-001.json`
- `runtime-state/entity-quantum-awareness/stegverse-002.json`
- `runtime-state/entity-quantum-awareness/sv-011.json`
- `receipts/sovereign-host/quantum-resilience/stegverse-001.latest.json`
- `receipts/sovereign-host/quantum-resilience/stegverse-002.latest.json`
- `receipts/sovereign-host/quantum-resilience/sv-011.latest.json`
- `receipts/sovereign-host/quantum-resilience-awareness.latest.json`

The aggregate must be `COMPLETED`, have `entity_count=3`, exact contract/census hashes, `runtime_awareness_materialized=true` and `standing_directive_active=true` before the entities may be classified quantum-resilience-aware.

## Completion gates

`QUANTUM-RESILIENCE-001` is complete only when:

- the crypto census covers all consequence-bearing cryptographic surfaces or explicitly records bounded unresolved scope;
- no critical surface remains `UNINVENTORIED` or unbounded;
- classical-only asymmetric dependencies have an admitted migration disposition;
- designated high-value paths have hybrid/PQC implementation and executable validation evidence;
- downgrade, rollback, stale-key and deprecated-algorithm paths fail closed;
- historical receipt verification survives algorithm migration;
- harvest-now/decrypt-later exposure has been classified and mitigated where required;
- all three AI entities authentically consume the standing quantum-resilience state in their assigned roles;
- wallet authority remains USER_ONLY for signing/broadcast;
- residual risks are stated without claiming absolute quantum security.

## Known downstream destinations

- `StegVerse-Labs/StegID`
- `StegVerse-Labs/TVC`
- `StegVerse-Labs/continuity-vault-kit`
- `StegVerse-Labs/StegOS`
- `StegVerse-Labs/Site`
- `GCAT-BCAT-Engine/Publisher`
- `admissibility-wiki`
- `stegguardian-wiki`

## Archive posture

This handoff is the canonical continuation point for the quantum-resilience program. Source/CI evidence must never be represented as deployed PQ protection or authentic resident execution evidence.
