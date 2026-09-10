# Data Reclamation Disclosure Ingestion Mirror Handoff

Goal Task ID: `SS-DATA-RECLAMATION-DISCLOSURE-INGESTION-001`
Parent Goal Task ID: `SS-EVIDENCE-COMPARISON-001`
COSV: `40000100100000`
Status: `ACTIVE / CLAIMED_INTEGRATION`

## Scope

Convert provider privacy policies, subprocessor lists, regulator/court records, user exports, and authentic transfer observations into normalized disclosure-graph evidence without treating disclosure as proof that a specific subject's data traversed an edge.

The current implementation trajectory adds bidirectional reconciliation between SKAP-maintained accounts and evidence-backed mappings. SKAP is the known-account baseline; evidence mapping is independently classified and may expand downstream or reveal organizations with no known SKAP account origin.

## Bidirectional SKAP ⇄ evidence model

For each SKAP-maintained account, reconciliation classifies the provider as `KNOWN_AND_MAPPED` or `KNOWN_BUT_UNMAPPED` and retains downstream organization references and evidence references. Independently verified propagation observations that cannot be traced to a known SKAP provider or mapped downstream organization are classified as `EVIDENCE_WITHOUT_KNOWN_ACCOUNT_ORIGIN`.

Downstream organizations remain discovery context. A provider-declared relationship, inferred edge, or graph path does not prove subject-specific traversal. `INFERRED_UNVERIFIED` must never be promoted to `OBSERVED_TRANSFER` without authentic transfer evidence.

## Completion predicates

- Supported evidence source classes ingest deterministically.
- Original evidence references and source provenance are retained.
- `INFERRED_UNVERIFIED` remains distinct from provider-declared or observed-transfer evidence.
- No provider disclosure alone becomes subject-specific traversal proof.
- Reconciliation fixtures cover conflicting and superseded evidence.
- SKAP-known accounts are deterministically classified as mapped or unmapped.
- Evidence-backed organizations with no known account origin are surfaced separately.
- Cross-subject SKAP/evidence reconciliation fails closed.

## Current implementation

- Canonical task claimed for integration on 2026-09-10.
- ERL branch `feat/skap-evidence-reconciliation-20260910` adds `schemas/skap-evidence-reconciliation.schema.json`, `scripts/reconcile_skap_evidence.py`, deterministic fixtures, and validation integrated into `scripts/validate_digital_data_reclamation.py`.
- Runtime/provider deletion is not part of this task and is not claimed.

## Manual work

None.
