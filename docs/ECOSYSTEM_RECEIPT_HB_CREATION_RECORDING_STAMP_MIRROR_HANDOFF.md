# Ecosystem Receipt HB Creation / Recording Stamp Mirror Handoff

Updated: 2026-09-20

Goal Task ID: `ECOSYSTEM-RECEIPT-HB-CREATION-RECORDING-STAMP-001`

COSV ID: `50000000100000`

Status: `ACTIVE / CANONICAL CREATION / CURRENT HB-MASTER RECORDS BINDING INSPECTED / CRYPTOGRAPHIC COMMITMENT GAP IDENTIFIED`

## Goal

Inspect the existing HeartBeat and Master Records contracts to determine whether HB checkpoints cryptographically commit a canonical Master Records state/root or only correlate by reference. If the relationship is only correlation, define the minimal non-authorizing extension that:

1. binds receipt creation to an HB reference;
2. binds Master Records recording/custody to an HB reference;
3. lets a later HB checkpoint commit the exact retained Master Records state/receipt set;
4. permits an independently verifiable external checkpoint anchor without making HeartBeat, the anchor provider, or Master Records an execution/transition/credential authority.

## Canonical authority boundaries

- HeartBeat: synchronization/timing/freshness/liveness/correlation/observability only.
- Master Records: custody, required-evidence validation, replay/query, and reconstruction authority only.
- Interlock/InTr: governed transition authority.
- WorkerCoordinator: claim/fence authority.
- TV/TVC: credential/scoped-authority issuance where applicable.
- External checkpoint anchor: evidence/notarization only; no StegVerse transition, execution, admission, custody, credential, routing, or governance authority.

## Inspection result

### Current HeartBeat contract

`control/heartbeat-protocol-anchor.json` defines a deterministic 100 Hz reference sequence derived from an oscillator-only protocol anchor. It explicitly declares `authority_scope=REFERENCE_DERIVATION_ONLY`, `observation_is_causal=false`, and `authority_effect=NONE_REFERENCE_ONLY`.

`heartbeat_runtime/engine_v13.py` inherits the v12 carrier and preserves non-authorizing observation/trigger behavior. The inspected current heartbeat contract contains no canonical field requiring a Master Records receipt-set root, canonical Master Records state digest, or custody-journal commitment in each HB checkpoint.

Therefore, current HeartBeat provides deterministic reference/correlation semantics, not a cryptographic commitment to Master Records state.

### Current Master Records contract

`workers/canonical_state_transition_custody.py` constructs canonical transition receipts, submits them through the existing Master Records HTTP or durable-local authority, requires `RECORDED`, `reconstruction_status=PASS`, `required_evidence_validation_status=PASS`, and exact `receipt_sha256 == reconstructed_receipt_sha256`.

Master Records therefore provides exact per-receipt custody/reconstruction identity. The current canonical receipt schema includes `recorded_at` but does not require `hb_creation_reference`, `hb_recording_reference`, or an HB checkpoint that commits the resulting canonical receipt set.

### Bound conclusion

The current system is **correlation/reference only across HB and Master Records**. It does not yet provide the stronger bidirectional cryptographic construction required to prove that a later HB checkpoint commits the exact Master Records state existing beneath it.

No claim is made that existing receipt timestamps are externally trusted time, that HB is externally anchored, or that deletion/insertion resistance across the HB↔Master Records seam is already established.

## Minimal non-authorizing extension

The extension must preserve existing receipt identity and authority boundaries while adding explicit evidence bindings.

### Receipt-side fields

Every canonical state-transition receipt capable of participating in this evidence lane should retain:

- `hb_creation_reference`: deterministic HB reference observed when the receipt body is first frozen;
- `hb_creation_protocol`: protocol/profile identifier used to derive/verify that reference.

Master Records custody must additionally retain, as custody metadata rather than mutating the already-frozen receipt body:

- `hb_recording_reference`: deterministic HB reference observed when Master Records durably records the receipt;
- `recorded_receipt_sha256`: exact canonical receipt digest;
- `master_record_ref`: existing custody locator.

The creation reference belongs to the producer-side evidence. The recording reference belongs to Master Records custody evidence. Neither reference authorizes anything.

### Master Records commitment checkpoint

A later HB checkpoint may carry a non-authorizing commitment object:

`stegverse.hb-master-records-checkpoint-commitment/v1`

Minimum fields:

- `hb_reference`
- `prior_hb_checkpoint_commitment_sha256` when a prior committed checkpoint exists
- `master_records_commitment_profile`
- `master_records_receipt_set_root_sha256`
- `master_records_receipt_count`
- `master_records_commitment_scope`
- `master_records_query_floor` / `master_records_query_ceiling` or equivalent deterministic inclusion boundary
- `authority_effect=NONE_EVIDENCE_COMMITMENT_ONLY`
- explicit false authority flags for HB and Master Records

The receipt-set root must be reproducible from canonical Master Records receipt identities ordered by a deterministic rule independent of wall-clock timestamps. The simplest admissible initial rule is ordered canonical `receipt_sha256` leaves selected by a closed sequence/query boundary, with the exact canonicalization and tree/root profile versioned.

This checkpoint does not copy or replace Master Records custody. It commits the observed custody state.

### External checkpoint anchor interface

Provider-neutral interface:

`stegverse.hb-external-checkpoint-anchor/v1`

Minimum fields:

- `checkpoint_commitment_sha256`
- `hb_reference`
- `anchor_profile`
- `anchor_provider_class`
- `submission_artifact_sha256`
- `provider_receipt_or_proof_ref`
- `provider_receipt_or_proof_sha256`
- `verification_profile`
- `verification_status`
- `independent_verifier_refs` when available
- `anchor_observed_time` only as provider evidence, never as StegVerse authority
- `authority_effect=NONE_EXTERNAL_EVIDENCE_ONLY`

The contract MUST NOT hard-code OpenTimestamps, Bitcoin, GitHub, or another provider. OpenTimestamps/Bitcoin can be one adapter/profile.

## Required invariants

1. HB reference does not authorize creation, recording, transition, execution, custody, admission, routing, or credentials.
2. Master Records custody does not authorize transitions or execution.
3. External anchoring does not authorize any StegVerse action.
4. An HB checkpoint cannot claim a Master Records commitment unless the root is deterministically reproducible from retained canonical receipt identities.
5. Deleting, inserting, replacing, or reordering any in-scope canonical receipt must change the committed root or fail reconstruction.
6. A receipt's creation reference cannot be rewritten by Master Records.
7. A Master Records recording reference cannot rewrite the canonical receipt digest.
8. External anchor verification must bind the exact HB checkpoint commitment digest, not a descriptive timestamp or mutable locator.
9. Existing receipts lacking these fields remain valid historical receipts; they are not retroactively promoted to this stronger proof class.

## Current proof ceiling

Source inspection establishes the gap and the shape of the minimal extension only.

It does **not** establish:

- authentic runtime emission of creation/recording HB stamps;
- an authentic HB checkpoint committing a Master Records root;
- any externally anchored HB checkpoint;
- deletion/insertion/reordering tamper tests against authentic retained runtime evidence;
- independent external-time proof.

## Next execution step

Implement the source-level evidence contract without changing HB or Master Records authority:

1. define versioned schemas for receipt HB evidence, HB→Master Records checkpoint commitment, and external checkpoint anchor;
2. add deterministic root construction/reconstruction tests;
3. add fail-closed tests proving deletion, insertion, replacement, and reorder change/fail the committed root;
4. add producer/Master Records integration only after the contract tests are green;
5. keep external provider adapters separate from the provider-neutral contract.

Do not run the MIR interoperability experiment merely because this source contract exists. That experiment should remain separate until authentic runtime evidence demonstrates the new commitment path or the experiment explicitly targets the current correlation-only boundary.
