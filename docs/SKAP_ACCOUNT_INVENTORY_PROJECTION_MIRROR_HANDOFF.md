# SKAP Account Inventory Projection Mirror Handoff

Goal Task ID: `SS-SKAP-ACCOUNT-INVENTORY-PROJECTION-001`
Parent Goal Task ID: `SS-DATA-RECLAMATION-DISCLOSURE-INGESTION-001`
COSV: `40000100100000`
Status: `ACTIVE / CLAIMED_IMPLEMENTATION`

## Scope

Produce an authentic machine-readable projection of accounts maintained within SKAP for comparison against evidence-based mapping. The projection is metadata-only and must not expose passwords, tokens, private keys, sealed credential payloads, or other secret material.

Required projection fields are the stable SKAP account reference, provider organization reference, account class, and account status. The ERL consumer contract is `stegverse.skap.account-inventory-projection/v1` and requires `contains_secret_material=false`.

## Current implementation

TVC now contains `tools/skap_account_inventory_projection.py`, focused tests, a dedicated validation workflow, documentation, and a TVC mirror handoff. The producer enumerates receipt-side metadata under `_Vault/SKAP/Receipts/**`; it never opens `_Vault/SKAP/Credentials/**` or sealed payload content. Stable account references are deterministic opaque hashes of local source references and those source references are not emitted.

The producer accepts both newer `credential_ref` receipt metadata and owner-ingress `object_id` metadata. Account status defaults to `UNKNOWN` unless a recognized non-secret `account_status` explicitly establishes `ACTIVE`, `INACTIVE`, or `CLOSED`.

Synthetic/test receipt metadata is excluded. The authenticated KnowledgeVault observation on 2026-09-10 found the RC17 synthetic Coinbase object/ingress/lifecycle set and no other direct SKAP receipt/lifecycle entries. The RC17 ingress receipt explicitly records `synthetic_material_only=true`; therefore the producer must fail with `no_real_skap_account_metadata_found` rather than produce a false real-account projection.

## Completion predicates

- Real SKAP-maintained account metadata can be enumerated from the authoritative SKAP surface.
- Secret material is structurally excluded from the projection.
- Stable account/provider references are emitted deterministically.
- Output validates against the ERL projection schema.
- The ERL SKAP ⇄ evidence reconciler consumes an authentic projection and produces coverage/exposure classifications.
- Synthetic/test SKAP records cannot satisfy real-account enumeration.

## Current evidence

- ERL PR #151 merged at `41722df474638bfca3297549fff215fc39375f7e` with the projection schema, bidirectional reconciler, deterministic fixtures, and fail-closed validation.
- `.github` PR #1319 merged at `5871cd2682885a73a2e5dbfc6a00fa13f12bafb3`, creating this canonical child task.
- TVC source currently includes the projection producer and focused tests through `5ba886cd5fd79cc87c038a3bafb8523a62fb576c`; dedicated validation is running on that lineage.
- Authenticated KnowledgeVault `_Vault/SKAP` has distinct `Credentials`, `Receipts`, `Revocations`, `Lifecycle`, and `Sealed` branches. Current receipt/lifecycle observation is synthetic RC17 Coinbase test evidence only; no real-account projection is claimed.

## Remaining work

1. Obtain green dedicated TVC validation for the hardened synthetic-exclusion implementation.
2. Populate/observe at least one authentic non-synthetic SKAP-maintained account receipt or lifecycle metadata record.
3. Generate the authentic non-secret projection from that surface.
4. Validate the exact output against the ERL schema and feed it to the merged ERL reconciler.
5. Retain projection and reconciliation evidence and retire this child only after those predicates are proven.

## Manual work

None currently.
