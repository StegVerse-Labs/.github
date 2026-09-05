# Quantum Software / Update Provenance Census Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Parent: `QUANTUM-RESILIENCE-001` / `.github#1008`  
Issue: `#1019`  
Subgoal: `QUANTUM-SOFTWARE-PROVENANCE-CENSUS-001`  
State: `SOURCE_CENSUS_IMPLEMENTED / BROADER_AUTHENTICATED_PROVENANCE_INVENTORY_REQUIRED`

## Purpose

Inventory software, release, package, update and artifact-authenticity paths that could become invalid under future cryptographically relevant quantum capability. Integrity evidence and authenticated provenance remain distinct.

## Current source-evidenced surfaces

### Continuity Vault Kit v0.1.9

The canonical continuity-vault-kit handoff records a published ZIP, SHA-256 sidecar, manifest, release evidence receipts and verification tooling. Scoped source search found no cosign, Sigstore, GPG, minisign or other authenticated release-signature mechanism. This means the represented release currently has strong integrity/reproducibility evidence but authenticated signer identity is not established by the scoped repository source.

State: `HASH_MANIFEST_ONLY_AUTHENTICITY_UNPROVEN / QUANTUM_SAFETY_UNKNOWN`.

### StegCore portable release

`tools/prepare_portable_release.py` binds archives to source commit, component versions, SHA-256 archive hashes and `SHA256SUMS`. It explicitly preserves TV/TVC publication authority and denies GitHub release/execution authority. Scoped source search found no authenticated artifact-signature mechanism.

State: `HASH_MANIFEST_ONLY_AUTHENTICITY_UNPROVEN / QUANTUM_SAFETY_UNKNOWN`.

## Critical distinction

```text
SHA-256 checksum -> integrity comparison
manifest -> integrity/contents description
CI success -> workflow result
GitHub Release presence -> hosting/publication event
source merge -> source history event

NONE of the above alone proves authenticated signer identity or PQ provenance.
```

## Required migration disposition

Future consequence-bearing release/update paths must carry a versioned authenticated provenance envelope whose verification algorithm and signer/key-custody semantics are explicit and replaceable. Historical hash verification must remain available. Valid provenance must not itself grant execution or transition authority.

A hybrid classical + standardized PQ signature transition may be appropriate for StegVerse-controlled provenance, but no algorithm is admitted merely by naming it. Real implementation, key custody, signature verification, rollback handling, and runtime/release evidence are required before `HYBRID_ACTIVE` or `PQC_VALIDATED` may be claimed.

## Authority invariants

- credential/publication authority remains `TV/TVC` where already assigned;
- InTr/Interlock remains the admissible transition boundary;
- GitHub token/runtime authority remains `NONE`;
- release signing validity never grants execution authority;
- no second user-operated machine is introduced;
- historical release evidence is not rewritten during migration.

## Installed files

- `control/quantum-software-update-provenance-census.json`
- `scripts/validate_quantum_software_update_provenance_census.py`
- `tests/test_quantum_software_update_provenance_census.py`
- `docs/QUANTUM_SOFTWARE_UPDATE_PROVENANCE_CENSUS_MIRROR_HANDOFF.md`

## Remaining machine work

1. inventory organization tag/commit signing and release-signing policy;
2. inventory container/package registry attestations and provenance;
3. inventory Site/web/mobile/StegOS update authenticity;
4. inventory dependency/package provenance and verification;
5. define admitted versioned provenance envelope and crypto-agility semantics;
6. integrate real authenticated provenance signing/verifying without collapsing signature validity into authority;
7. prove downgrade, rollback, revoked-key, deprecated-algorithm and historical verification behavior.

## Completion gate

This subgoal is not complete until consequence-bearing software/update paths are either authentically signed/attested with explicit algorithm and custody semantics or are explicitly classified as bounded unresolved risk with migration ownership. No PQ deployment claim is authorized by this source census.
