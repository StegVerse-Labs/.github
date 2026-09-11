# ERL Active-Research Universal InTr Runtime Binding Mirror Handoff

Updated: 2026-09-11

## Goal Task ID

`SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001`

Parent goal: `SS-EVIDENCE-COMPARISON-001`

COSV: `40000100100000`

Status: `ACTIVE / CLAIMED_INTEGRATION`

## Purpose

Bind the already-merged ERL active-research Universal InTr intent to the existing sovereign Universal InTr resident execution owner without creating a second runtime owner, dispatcher, scheduler, heartbeat, credential path, or synthetic transport receipt.

## Reconciled canonical owner

The existing resident DEVICE_SYSTEM -> KV materialization owner remains:

- canonical runtime task: `SHWP-DEVICE-KV-INTR-OBSERVATION-001`
- profiled ingress: `workers/universal_intr_profiled_ingress.py`
- materialization consumer: `scripts/consume_device_kv_intr_materialization_request.py`
- downstream owner: `StegVerse-Labs/continuity-vault-kit#79`
- resident refresh/execute bridge: `scripts/refresh_and_execute_resident_task.py`
- credential authority: `TV/TVC`
- GitHub runtime authority: `NONE`

`StegVerse-Labs/Executive_Rhetoric_Ledger:active-research-kv-consumer` remains a repository-side ERL consumer identity, not an independent resident owner.

## Canonical path

```text
EXTERNAL_SYSTEM
-> STEGOS_ECOSYSTEM
-> DEVICE_SYSTEM
-> KV
```

One operation identity, one packet identity, one exact acquisition-envelope payload hash, and prior-receipt lineage must be preserved across all three authentic adjacent transitions.

## Merged implementation evidence

PR `StegVerse-Labs/.github#1424` merged at `b89a1ec010fc8d94ef770d900cb8244c11afe363` after exact-head validation on `e9039116395577702fbe0e4b32b034638eb9d9d7`.

Exact-head workflows observed successful before merge:

- `Validate organization control plane - No GitHub Token Authority` — success
- `Heartbeat Worker Project - Validation Only / No GitHub Token Authority` — success
- `Deterministic Repository Suite - Diagnostic Evidence Only` — success

Merged source now includes:

- `workers/erl_active_research_intr_profile.py`
  - validates the ERL binding/envelope/intent/materialization contract;
  - rejects skipped/reordered canonical boundaries and authority transfer;
  - preserves operation ID, packet ID, payload hash, and prior-receipt lineage;
  - projects only the terminal `DEVICE_SYSTEM -> KV` event to the existing CVK owner;
  - does not fabricate or claim the terminal runtime receipt.
- `scripts/install_erl_active_research_universal_intr_route.py`
  - idempotently installs the ERL route into the existing shared Universal InTr listener source;
  - creates no second listener, scheduler, heartbeat, WorkerCoordinator, credential path, or execution owner.
- `scripts/install_erl_device_kv_prior_lineage.py`
  - idempotently repairs the existing DEVICE_KV observation worker so authenticated upstream hop-2 lineage can become the terminal hop prior-receipt basis;
  - retains the existing ingress-record-hash behavior for non-ERL events;
  - fails closed on malformed ERL upstream lineage.
- deterministic tests covering profile validation, lineage preservation, terminal-owner projection, refusal semantics, shared-listener reuse, installer idempotency, and DEVICE_KV prior-lineage transformation.

## Resident source materialization

Current follow-on branch: `ss-erl-runtime-source-materialization-001`.

Added `scripts/prepare_erl_active_research_intr_runtime_source.py` as one bounded local preparation entrypoint. It invokes only the two already-merged idempotent source installers and then supports `--check` verification. It does not itself execute transport, mint claims/fences, contact a provider, create receipts, or grant authority.

Because no authorized sovereign resident device is currently connected to the available remote execution surface, the installers have not been run against an authentic resident checkout in this session. That condition must not be converted into synthetic runtime evidence or a second-device dependency.

## Existing proof that must not be repeated

- ERL PR #154 active-research dispatch merged.
- ERL PR #155 acquisition consumer merged.
- ERL PR #156 exact three-hop admission contract merged.
- ERL PR #157 reusable non-authorizing runtime binding merged at `bfb76a068717ff0aaf96c32af97ebcc43324149f`.
- CISA/Iran public-source capture provider write and exact-byte provider readback are already authentic and remain separate from InTr transport proof.

## Remaining work

1. Validate and merge the resident-source preparation entrypoint.
2. On the authentic sovereign resident source, apply `scripts/prepare_erl_active_research_intr_runtime_source.py`, then run it again with `--check`; this is source preparation only.
3. Execute one authentic admitted ERL acquisition through the existing shared resident ingress.
4. Preserve the authentic hop-1, hop-2, and terminal DEVICE_SYSTEM -> KV hop-3 receipts with exact operation/packet/payload/prior-receipt continuity.
5. Verify the complete three-receipt chain with the merged ERL consumer.
6. Bind the terminal KV transport proof to the pre-existing authentic MyKV provider-write/readback evidence without repeating the provider operation.
7. Reconcile the parent ERL handoff with exact runtime receipt hashes and final proof class.
8. Reconcile root README documentation when the resident source materialization is canonically installed; no README text may imply runtime traversal before authentic execution.

## Current state

`PROFILE_IMPLEMENTATION_MERGED_AND_EXACT_HEAD_VALIDATED / RESIDENT_SOURCE_PREPARATION_ENTRYPOINT_ON_BRANCH / AUTHENTIC_RESIDENT_SOURCE_MATERIALIZATION_NOT_YET_OBSERVED / AUTHENTIC_THREE_HOP_TRAVERSAL_NOT_YET_OBSERVED`
