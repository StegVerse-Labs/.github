# Quantum Device/Node Identity Census Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Parent: `StegVerse-Labs/.github#1008` / `QUANTUM-RESILIENCE-001`  
Issue: `StegVerse-Labs/.github#1022`  
State: `INITIAL_SOURCE_CENSUS_BUILT / BROADER_ACTIVE-SURFACE CLASSIFICATION REQUIRED`

## Purpose

Bound the previously uninventoryed `OTHER-DEVICE-NODE-IDENTITY` quantum-resilience surface without conflating device/node identity with TLS, SKAP key establishment, wallet transaction signing, or generic attestation language.

This handoff is the continuation source of truth for `.github#1022`.

## Authority invariants

- TV/TVC remains credential authority.
- InTr/Interlock remains transition authority.
- Device/node cryptographic possession, identity, membership or attestation evidence does not itself grant execution, routing, custody, publication, receiving or policy authority.
- No PQ-readiness claim is permitted from documentation, source presence, CI, checksum/manifests or algorithm naming alone.
- No second user-operated machine is introduced by this work.

## Initial source-evidenced classification

### 1. Current primary-phone device possession — active classical asymmetric root

Repository: `StegVerse-Labs/StegID`

Observed source:
- `web/device_wallet_bootstrap.js`
- `docs/PHONE_DEVICE_WALLET_BOOTSTRAP_MIRROR_HANDOFF.md`
- `STEGID_MIRROR_HANDOFF.md`

Observed cryptography:
- non-exportable browser `P-256` device key;
- `ECDSA` with `SHA-256` challenge sign/verify for `DEVICE_POSSESSION`;
- platform WebAuthn user verification is a separate `HUMAN_CONTINUITY` step and must not be silently treated as proving a specific attestation/signature algorithm when source does not establish it.

Classification: `CLASSICAL_ONLY / HYBRID_MIGRATION_REQUIRED`.

This is already represented by `STEGID-CURRENT-PHONE-DEVICE-POSSESSION` in the canonical quantum census and remains a critical migration root.

### 2. StegFin phone projection — consumer/projection of the same device-possession semantic

Repository: `StegVerse-Labs/stegfin-governance`

Observed source:
- `ui/stegid-device-wallet-bootstrap.js`
- `ui/device-wallet-identity.js`
- `ui/evidence-export.js`

Observed behavior:
- repeats/verifies P-256 `DEVICE_POSSESSION` behavior for the phone-side StegID flow;
- consumes StegID device-admission evidence and preserves separation from wallet `SIGN`/`BROADCAST` authority.

Classification: `CLASSICAL_ONLY / SOURCE-PROJECTION-OF-STEGID-DEVICE-POSSESSION`.

This must not be double-counted as a second independent credential authority root unless separate key custody/registration is proven.

### 3. Site legacy/client P-256 material — scoped but active identity role unresolved

Repository: `StegVerse-Labs/Site`

Observed source:
- `docs/stegtvc-client-merkle-enhanced.txt` contains browser-generated ECDSA P-256 key material.

Current classification: `QUANTUM_SAFETY_UNKNOWN / ACTIVE-ROLE-UNPROVEN`.

The source occurrence alone does not prove this path is current, deployed, or used for device/node identity rather than example/historical client material. Site-owned follow-up must classify active vs historical/example-only before it can be promoted to a concrete device/node identity surface.

### 4. StegOS / StegLenses attestation terminology — cryptographic primitive not established by scoped evidence

Repositories:
- `StegVerse-Labs/StegOS`
- `StegVerse-Labs/StegLenses`

Observed sources include runtime-attestation schemas and node-model/architecture documents using `attestation` terminology.

Current classification: `QUANTUM_SAFETY_UNKNOWN / ATTESTATION-SEMANTICS-OBSERVED / CRYPTOGRAPHIC-PRIMITIVE-UNPROVEN`.

Do not treat semantic or schema-level attestation as cryptographic device attestation until an actual signer/verifier, key custody model, trust root, revocation path and runtime use are source-evidenced.

## Exclusions from this census slice

The following are deliberately excluded from `OTHER-DEVICE-NODE-IDENTITY` unless later evidence proves identity/attestation use:

- continuity-vault-kit browser P-256 ECDH: SKAP key establishment/confidentiality;
- TVC SKAP resident/browser P-256 keys: recipient/sealed-object confidentiality;
- TLS/WebPKI keys: transport authentication/key establishment;
- wallet-provider transaction signatures: USER_ONLY wallet authority;
- generic hash receipts/manifests: integrity evidence, not signer identity.

## Current bounded state

The former single `OTHER-DEVICE-NODE-IDENTITY = UNINVENTORIED` bucket can now be narrowed to:

1. `StegID current-phone DEVICE_POSSESSION`: explicit P-256 / classical-only / migration required;
2. `stegfin-governance` phone projection: same semantic root unless independent custody is proven;
3. `Site` P-256 client material: active identity role unresolved;
4. `StegOS` / `StegLenses` attestation semantics: cryptographic implementation/trust roots unresolved;
5. all other device/node registration, membership and attestation surfaces: not yet proven complete.

Therefore `.github#1022` remains open. The critical class is no longer wholly uninventoryed, but broader source coverage is still incomplete and no PQ implementation or runtime evidence is claimed.

## Next machine tasks

1. search active StegOS, TVC, StegID, Site and adjacent node/device repositories for concrete device/node registration, identity, membership and attestation signer/verifier implementations;
2. for every concrete surface record primitive, purpose, key custody/non-exportability, trust root, lifetime, revocation/replacement semantics and runtime status;
3. distinguish active source from historical/example/test-only material;
4. update `control/quantum-crypto-census.json` so `OTHER-DEVICE-NODE-IDENTITY` becomes a bounded partial-explicit umbrella rather than `UNINVENTORIED` only after this branch is reviewed/merged;
5. create repo-specific migration issues only where an actual classical asymmetric identity/attestation surface is proven;
6. do not classify any surface `HYBRID_ACTIVE` or `PQC_VALIDATED` without real cryptographic implementation and executable evidence.

## Completion gate for #1022

Close only when no consequence-bearing device/node identity, possession, registration, membership or attestation surface remains unbounded, and every observed classical asymmetric root has an explicit migration disposition.
