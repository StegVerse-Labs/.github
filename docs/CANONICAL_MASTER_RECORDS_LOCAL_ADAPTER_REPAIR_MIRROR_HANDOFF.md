# Canonical Master Records Local Adapter Repair Mirror Handoff

Updated: 2026-09-17
Repository: `StegVerse-Labs/.github`

## Task pointer

- Goal Task ID: `CANONICAL-MASTER-RECORDS-LOCAL-ADAPTER-REPAIR-001`
- Parent Goal Task ID: `CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001`
- Discovered while tracing: `STEG-BROWSER-RUNTIME-CONNECTION-INGRESS-001`
- Issue: `StegVerse-Labs/.github#2079`
- COSV: `50000000100000`
- Status: `RETIRED / SOURCE REPAIR VALIDATED COMPLETE MERGED / AUTHENTIC RUNTIME CUSTODY NOT CLAIMED`

## Scope

Repair only the optional local adapter in `workers/canonical_state_transition_custody.py`. This task is separate from the immutable StegBrowser browser invocation because that invocation uses the Site browser API custody client, not this Python local adapter.

## Reproduced defect

The local adapter currently serializes a `stegverse.canonical-state-transition-receipt/v1` and passes that file directly to:

```text
master-records/orchestration:scripts/ingest_reusable_task_lifecycle.py
```

That ingester requires `stegverse.reusable-task-master-records-custody-request/v1` plus a genuine reusable-task lifecycle bundle containing the required manifest, trigger, result, expiry and residual evidence. Direct validation of a clearly labelled TEST_ONLY_NOT_INVOCATION state receipt therefore fails closed with:

```text
request schema mismatch
```

No custody write, invocation, runtime transition, or authority receipt was produced by that reproduction.

## Repair constraints

Do not relabel a state-transition receipt as a lifecycle request. Do not fabricate missing lifecycle evidence. Do not weaken `ingest_reusable_task_lifecycle.py` validation. Do not create a second custody authority or substitute local store.

The repair must preserve the canonical state-transition receipt contract and route the local adapter through a Master Records state-transition custody interface whose input contract is actually `stegverse.canonical-state-transition-receipt/v1`, or else remove the invalid local fallback while preserving a fail-closed canonical API path. Exact reconstruction and replay identity remain mandatory.

## Completion predicates

```text
LOCAL_ADAPTER_ACCEPTS_ONLY_VALID_CANONICAL_STATE_TRANSITION_CONTRACT = true
NO_SCHEMA_RELABELING = true
NO_FABRICATED_LIFECYCLE_EVIDENCE = true
DESTINATION_VALIDATION_NOT_WEAKENED = true
EXACT_RECONSTRUCTION_PRESERVED = true
NO_SECOND_CUSTODY_AUTHORITY = true
```

This task must not claim it repaired or executed the immutable StegBrowser browser invocation.

## Manual work

None.


## 2026-09-18 repair implementation

The invalid local fallback has been removed from `workers/canonical_state_transition_custody.py`. The repaired local path requires the existing `master-records/orchestration` canonical state-transition service plus explicit durable configuration: an absolute non-`/tmp` `MASTER_RECORDS_DB`, `MASTER_RECORDS_RECEIPT_KEY`, and `MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS=true`. It invokes `services.canonical_state_transition_custody.record_receipt(base, receipt)` with the exact canonical receipt. It does not relabel the receipt, call the reusable-task lifecycle ingester, fabricate lifecycle evidence, or create a second custody store.

Focused regression coverage is in `tests/test_canonical_master_records_local_adapter_repair.py`. Prior source head `11f07ae598faf790904e9ba3cea23f7d1e5a454f` passed 3/3 focused tests plus py_compile in run `35393803641`, job `105757920409`. Because current main advanced to Task Registry generation 45, that evidence is retained as prior validation only; the rebased exact head must revalidate before merge. No authentic runtime custody event is claimed.


## 2026-09-18 merged closeout

PR `#2136` merged the repair to `main` as `a21bbeb53e33210d4ac832f343582c02149d8c53`.

The merged worker blob `e944b3b1b94710ef21ed5eb283bd18dc86b7b14e` and focused-test blob `e23464524a755c62a6a1fb2b2f359007b2a01cda` exactly match the artifacts previously validated by workflow run `35393803641`, job `105757920409`, where all 3 focused tests and worker byte-compilation passed. Therefore the source repair is validated and merged without relying on a new validation workflow.

Superseded PR `#2125` is closed and must not be merged.

This closes only the local-adapter source defect. No authentic resident transition or Master Records runtime custody event is claimed. Runtime custody remains owned by the existing parent canonical custody path.


## 2026-09-18 merge reconciliation

Replacement PR `#2136` merged as `a21bbeb53e33210d4ac832f343582c02149d8c53` after generation-47 exact-head automatic runs `35398748609` and `35398748520` completed SUCCESS. The merged worker/test blobs exactly match the focused-validated blobs from run `35393803641`, job `105757920409` (3/3 focused tests plus py_compile PASS).

The child is source-repair complete and retired. This does not claim any authentic runtime transition was written to Master Records.
