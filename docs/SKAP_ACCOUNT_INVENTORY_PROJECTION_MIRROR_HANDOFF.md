# SKAP Account Inventory Projection Mirror Handoff

Goal Task ID: `SS-SKAP-ACCOUNT-INVENTORY-PROJECTION-001`
Parent Goal Task ID: `SS-DATA-RECLAMATION-DISCLOSURE-INGESTION-001`
COSV: `40000100100000`
Status: `INACTIVE / UNCLAIMED`

## Scope

Produce an authentic machine-readable projection of accounts maintained within SKAP for comparison against evidence-based mapping. The projection is metadata-only and must not expose passwords, tokens, private keys, sealed credential payloads, or other secret material.

Required projection fields are the stable SKAP account reference, provider organization reference, account class, and account status. The ERL consumer contract is `stegverse.skap.account-inventory-projection/v1` and requires `contains_secret_material=false`.

## Completion predicates

- Real SKAP-maintained account metadata can be enumerated from the authoritative SKAP surface.
- Secret material is structurally excluded from the projection.
- Stable account/provider references are emitted deterministically.
- Output validates against the ERL projection schema.
- The ERL SKAP ⇄ evidence reconciler consumes an authentic projection and produces coverage/exposure classifications.

## Current evidence

ERL PR #151 merged at `41722df474638bfca3297549fff215fc39375f7e` with the projection schema, bidirectional reconciler, deterministic fixtures, and fail-closed validation. No existing canonical SKAP account-index producer was found during repository search, so producer implementation is intentionally separated into this task.

## Manual work

None at task creation.
