# ERL Active-Research Universal InTr Runtime Binding Mirror Handoff

Updated: 2026-09-11

## Goal Task ID

`SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001`

Parent goal: `SS-EVIDENCE-COMPARISON-001`

COSV: `40000100100000`

Status: `ACTIVE / CLAIMED_INTEGRATION`

## Purpose

Bind the already-merged ERL active-research Universal InTr intent to the existing sovereign Universal InTr resident execution owner without creating a second runtime owner, dispatcher, scheduler, heartbeat, credential path, provider operation, or synthetic transport receipt.

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

PR `StegVerse-Labs/.github#1424` merged at `b89a1ec010fc8d94ef770d900cb8244c11afe363` after exact-head validation on `e9039116395577702fbe0e4b32b034638eb9d9d7` with organization-control, Heartbeat validation, and deterministic repository suite all successful.

Merged source includes:

- `workers/erl_active_research_intr_profile.py`
- `scripts/install_erl_active_research_universal_intr_route.py`
- `scripts/install_erl_device_kv_prior_lineage.py`
- deterministic tests for profile/path/identity/lineage/refusal semantics.

PR `StegVerse-Labs/.github#1444` then merged at `0bcfba4a7a99b1fc2b641580e805543a320a9f80` after exact-head organization-control, Heartbeat validation, and deterministic-suite success. It added `scripts/prepare_erl_active_research_intr_runtime_source.py`, which applies/checks the existing ERL route and DEVICE_KV lineage transforms without claiming runtime execution.

## Resident request wiring continuation

Current branch: `ss-erl-resident-request-wiring-001`.

Added:

- `control/resident-execution-request.d/erl-active-research-intr-runtime-binding-001.json`
  - exact Task/COSV identity;
  - exact `EXTERNAL_SYSTEM -> STEGOS_ECOSYSTEM -> DEVICE_SYSTEM -> KV` path;
  - existing terminal owner `SHWP-DEVICE-KV-INTR-OBSERVATION-001` / `StegVerse-Labs/continuity-vault-kit#79`;
  - provider replay forbidden;
  - TV/TVC credential authority, GitHub runtime authority NONE, no second machine.
- `control/resident-execution-request.d/consume-erl-active-research-intr-runtime-binding.py`
  - validates only the bounded request;
  - verifies resident source preparation with `--check`;
  - fails to `INPUT_NOT_MATERIALIZED` when local ERL source/dispatch inputs are absent;
  - when those local inputs exist, runs the merged ERL deterministic binding builder and persists only the exact binding/envelope sidecars;
  - explicitly stops at `BINDING_MATERIALIZED_AWAITING_AUTHENTIC_INTR_SUBMISSION` and does not submit transport, contact the provider, or synthesize receipts.
- `scripts/install_erl_resident_request_wiring.py`
  - idempotently adds the ERL selector to the existing resident dispatcher;
  - permits only the local nonsecret `STEGVERSE_ERL_ROOT` and `STEGVERSE_ERL_ACTIVE_RESEARCH_DISPATCH_PATH` bindings;
  - extends the existing native materialization allow-list with the already-merged ERL preparation/install scripts;
  - creates no second dispatcher/listener/runtime.
- `scripts/prepare_erl_active_research_intr_runtime_source.py` now includes the request-wiring installer in its apply/check sequence.
- deterministic tests cover request authority/path invariants, wiring idempotency, source-preparation composition, no-request behavior, and fail-closed preparation state.

## Existing proof that must not be repeated

- ERL PR #154 active-research dispatch merged.
- ERL PR #155 acquisition consumer merged.
- ERL PR #156 exact three-hop admission contract merged.
- ERL PR #157 reusable non-authorizing runtime binding merged at `bfb76a068717ff0aaf96c32af97ebcc43324149f`.
- CISA/Iran public-source capture provider write and exact-byte provider readback are already authentic and remain separate from InTr transport proof.

## Remaining work

1. Validate and merge the resident request-wiring branch only if applicable exact-head checks pass.
2. On the authentic sovereign resident source, apply `scripts/prepare_erl_active_research_intr_runtime_source.py`, then run it again with `--check`; source preparation remains non-authorizing.
3. Let the existing resident dispatcher consume `erl_active_research_intr_runtime_binding` when local ERL source/dispatch inputs are present; preserve the binding/envelope sidecars.
4. Add the bounded authentic shared-InTr submission from that materialized binding without provider replay or a second runtime owner.
5. Execute one authentic admitted ERL acquisition through the existing shared resident ingress.
6. Preserve authentic hop-1, hop-2, and DEVICE_SYSTEM -> KV hop-3 receipts with exact operation/packet/payload/prior-receipt continuity.
7. Verify the complete chain with the merged ERL consumer and bind the terminal transport proof to the existing provider readback evidence.
8. Reconcile the parent ERL handoff with exact receipt hashes and final proof class.

## Current state

`PROFILE_AND_SOURCE_PREPARATION_MERGED_AND_VALIDATED / RESIDENT_REQUEST_AND_BINDING_MATERIALIZATION_WIRING_ON_BRANCH / AUTHENTIC_RESIDENT_SOURCE_MATERIALIZATION_NOT_YET_OBSERVED / AUTHENTIC_INTR_SUBMISSION_AND_THREE_HOP_TRAVERSAL_NOT_YET_OBSERVED`
