# SV-DN-1 Current Source Identity Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Parent Goal: `SV-DN1-PRODUCTION-SOURCE-PREPARATION-001`
Consumer trajectory: `STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001`
State: `CURRENT_SOURCE_IDENTITY_REPAIR_IN_VALIDATION / AUTHENTIC_SOURCE_PREP_RECEIPT_PENDING`

## Defect

The v2 production-source worker correctly derives current component identity from a complete `sha256-content-manifest`, but it also treated historical migration Git blob SHA-1 values as immutable hashes of the present-day source files.

That made legitimate SDK evolution fail closed before the current content identity could be established. `StegVerse-org/StegVerse-SDK:stegverse/governance_ingress_runtime.py` has evolved beyond its historical migration blob while remaining the current runtime source needed by the generic governed-consequence path.

## Repair

`workers/sv_dn1_production_source_prep_current_identity_worker.py` is now the process-adapter entrypoint. It reuses the canonical production-source worker and changes only the legacy migration-anchor equality hook:

```text
historical Git blob SHA-1
    -> retained as provenance evidence
required current runtime marker path
    -> must exist
observed current marker Git blob SHA-1
    -> recorded for comparison
historical equality
    -> informative, not an admission requirement
complete current source tree
    -> sha256-content-manifest recomputed and becomes source identity
```

The canonical base worker still owns package schema validation, file-by-file SHA-256 verification, complete manifest derivation, source-package materialization, node requirement, hosted-runtime refusal, credential-environment refusal, no-network constraint, and repository-writeback prohibition.

## Fail-closed boundary

This repair does **not** accept arbitrary source merely because a directory exists. A component still requires all configured runtime marker paths, and its full current tree is hashed into the canonical `sha256:<source_bundle_sha256>` identity. Content-addressed packages must still verify every declared file hash and complete bundle digest.

Missing marker files remain `SourceIdentityDrift`. Missing local source/package remains `HANDOFF_READY`. No network fallback is introduced.

## Compatibility receipt

The v2 receipt retains `migration_anchors_verified=true` for schema compatibility, but successful receipts are enriched with:

```text
migration_anchor_policy=HISTORICAL_PROVENANCE_NOT_CURRENT_BYTE_PIN
historical_migration_anchor_equality_required=false
current_source_identity_verified=true
current_source_identity_scheme=sha256-content-manifest
```

Within this policy, `migration_anchors_verified` means the historical provenance contract and required marker set were verified and recorded; it no longer means current bytes must equal historical Git blobs.

## Runtime boundary

Source merge/CI does not establish the four authentic resident source identities. Completion still requires the resident `stegverse.sv-dn1.production-source-prep-receipt/v2` with all four current source roots and identities. The native-email governed archive consumer may use those roots only after that receipt is authentically present and accepted by the Healer source-prep bridge.

## README determination

`NO_README_CHANGE_REQUIRED`: this is a scoped source-identity compatibility correction. Repository-level runtime responsibilities are unchanged.
