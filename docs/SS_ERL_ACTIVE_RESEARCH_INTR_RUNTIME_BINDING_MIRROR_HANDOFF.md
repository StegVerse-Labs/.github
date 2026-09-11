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

The profile preserves one operation identity, one packet identity, one acquisition-envelope hash, and prior-receipt lineage across the path. The terminal hop is projected onto the existing DEVICE_KV owner only after the preceding two transitions have been observed by the shared ingress path.

## Implementation on current branch

Branch: `ss-erl-active-research-intr-profile-001`

Implemented:

- `workers/erl_active_research_intr_profile.py`
  - validates the merged ERL binding/envelope/intent/request contract;
  - rejects skipped/reordered canonical boundaries and authority transfer;
  - emits hop 1 only after exact ERL binding bytes are admitted by the shared `STEGOS_ECOSYSTEM` ingress;
  - emits hop 2 only as the same admitted packet is projected into the resident device-materialization path;
  - preserves operation ID, packet ID, envelope hash, and receipt lineage;
  - creates no terminal KV receipt and explicitly retains `terminal_runtime_receipt_present=false`;
  - projects the final request to `StegVerse-Labs/continuity-vault-kit#79` with `DEVICE_SYSTEM -> KV` as the remaining adjacent boundary;
  - forbids provider-operation replay and keeps TV/TVC/GitHub authority separation unchanged.
- `scripts/install_erl_active_research_universal_intr_route.py`
  - idempotently installs the ERL profile into the existing `workers/universal_intr_profiled_ingress.py` source;
  - creates no listener, scheduler, heartbeat, WorkerCoordinator, credential path, or second execution owner.
- `tests/test_erl_active_research_intr_profile.py`
  - covers identity/lineage preservation, terminal-owner projection, skipped-boundary rejection, authority-transfer rejection, write-once collision refusal, and installer idempotency/shared-listener reuse.

The implementation does not claim that hop 3 occurred. Authentic DEVICE_SYSTEM -> KV receipt production remains owned by the existing DEVICE_KV resident runtime and must occur only after actual runtime receipt/validation of the terminal bytes.

## Existing proof that must not be repeated

- ERL PR #154 active-research dispatch merged.
- ERL PR #155 acquisition consumer merged.
- ERL PR #156 exact three-hop admission contract merged.
- ERL PR #157 reusable non-authorizing runtime binding merged at `bfb76a068717ff0aaf96c32af97ebcc43324149f`.
- CISA/Iran public-source capture provider write and exact-byte provider readback are already authentic and separate from InTr transport proof.

## Remaining work

1. Run exact-head validation for the profile implementation and installer.
2. Merge only if the applicable validation lanes pass.
3. Ensure the terminal DEVICE_KV consumer preserves the upstream hop-2 receipt as the prior receipt for the authentic terminal hop; do not substitute the ingress-record hash if that would break canonical ERL lineage.
4. Execute one authentic admitted ERL acquisition through the resident shared ingress when a sovereign resident device surface is available.
5. Preserve the authentic terminal receipt and verify the complete three-receipt chain with the merged ERL consumer.
6. Bind terminal proof to the pre-existing MyKV provider-write/readback evidence without re-running the provider operation.
7. Reconcile the parent ERL handoff with exact runtime receipt hashes and final proof class.

## Current state

`CANONICAL_RUNTIME_OWNER_IDENTIFIED / ERL_SHARED_INGRESS_PROFILE_IMPLEMENTED_ON_BRANCH / TERMINAL_PRIOR_LINEAGE_RECONCILIATION_AND_EXACT_HEAD_VALIDATION_PENDING / AUTHENTIC_THREE_HOP_TRAVERSAL_NOT_YET_OBSERVED`
