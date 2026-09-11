# ERL Active-Research Universal InTr Runtime Binding Mirror Handoff

Updated: 2026-09-11

## Goal Task ID

`SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001`

Parent goal: `SS-EVIDENCE-COMPARISON-001`

COSV: `40000100100000`

Status: `ACTIVE / CLAIMED_INTEGRATION`

## Purpose

Bind the already-merged ERL active-research Universal InTr intent to the existing sovereign Universal InTr resident execution owner without creating a second runtime owner, dispatcher, scheduler, heartbeat, credential path, provider operation, or synthetic transport receipt.

## Canonical owner and path

Existing terminal owner remains `SHWP-DEVICE-KV-INTR-OBSERVATION-001` through the shared `workers/universal_intr_profiled_ingress.py`, `scripts/consume_device_kv_intr_materialization_request.py`, and downstream owner `StegVerse-Labs/continuity-vault-kit#79`. TV/TVC remains credential authority; GitHub runtime authority is `NONE`.

Canonical path:

```text
EXTERNAL_SYSTEM
-> STEGOS_ECOSYSTEM
-> DEVICE_SYSTEM
-> KV
```

One operation identity, one packet identity, one exact acquisition-envelope payload hash, and prior-receipt lineage must be preserved across all three authentic adjacent transitions.

## Merged implementation evidence

- PR #1424 merged at `b89a1ec010fc8d94ef770d900cb8244c11afe363` after organization-control, Heartbeat validation, and deterministic-suite PASS. It added the ERL shared-ingress profile, route installer, DEVICE_KV prior-lineage preservation, and tests.
- PR #1444 merged at `0bcfba4a7a99b1fc2b641580e805543a320a9f80` after the same three exact-head validation classes PASS. It added bounded resident source preparation.
- PR #1468 merged at `233992aead73e054f9ded66d62af29b0980107a8` from exact head `ceab2ab090ca8d8edd813400180b12d25df1c873` after organization-control, Heartbeat validation, and deterministic-suite PASS. It added the canonical resident request, binding-materialization consumer, resident request wiring installer, resident-source copy wiring, and deterministic tests. Binding/envelope sidecars remain write-once while status evidence is an atomic latest projection so `INPUT_NOT_MATERIALIZED` can legitimately advance later.

No merged source above proves resident execution or any InTr hop.

## Local shared-InTr submission continuation

Current branch: `ss-erl-local-intr-submission-001`.

Implemented on branch:

- `scripts/submit_erl_active_research_intr_binding.py`
  - accepts only a runtime-local ERL binding sidecar;
  - requires a loopback-only `http://127.0.0.1|localhost|::1/.../intr/materialization` endpoint;
  - requires an already-issued `TVC_RELAY_EGRESS` authorization identifier and never creates one;
  - POSTs the exact canonical binding bytes with the shared Universal InTr transport headers;
  - rejects hosted execution and any non-loopback endpoint;
  - validates only the authentic ERL profile response from the shared listener;
  - accepts exactly two verified upstream `FORWARDED` receipts and requires their lineage to bind the projected terminal `DEVICE_SYSTEM -> KV` request;
  - records `terminal_runtime_receipt_present=false` and never fabricates hop 3 or replays the provider operation.
- `control/resident-execution-request.d/consume-erl-active-research-intr-submission.py`
  - delegates to the bounded submitter through the existing resident dispatcher;
  - remains a non-authorizing dispatcher consumer and waits when source/input is unavailable.
- `scripts/install_erl_resident_request_wiring.py`
  - registers the local submission consumer in the existing dispatcher;
  - adds the submitter to the existing native resident source copy/required allow-list;
  - creates no second listener, dispatcher, runtime, or credential path.
- `scripts/install_erl_active_research_universal_intr_route.py`
  - repairs a discovered digest-format defect: `validate_transport_headers()` returns bare 64-hex while the ERL profile requires a `sha256:` URI;
  - upgrades both fresh and already-installed legacy ERL route source to pass `sha256:<digest>` fail-closed.
- deterministic tests cover loopback-only submission, exact TVC relay headers, two-hop profile-response lineage, route digest normalization, and existing-dispatcher/native-materialization reuse.

## Existing proof that must not be repeated

- ERL PR #154 active-research dispatch merged.
- ERL PR #155 acquisition consumer merged.
- ERL PR #156 exact three-hop admission contract merged.
- ERL PR #157 reusable non-authorizing runtime binding merged at `bfb76a068717ff0aaf96c32af97ebcc43324149f`.
- CISA/Iran public-source capture provider write and exact-byte provider readback are already authentic and remain separate from InTr transport proof.

## Remaining work

1. Validate and merge the local-submission branch only if applicable exact-head checks pass.
2. On the authentic sovereign resident source, apply and verify `scripts/prepare_erl_active_research_intr_runtime_source.py`.
3. Materialize the existing local ERL source/dispatch inputs and deterministic binding/envelope through the existing resident dispatcher.
4. Materialize the bounded submission input only when an authentic loopback shared ingress and already-issued TVC relay authorization ID exist.
5. Observe one authentic shared-ingress ERL response, preserving authentic hop 1 and hop 2 receipts and the projected terminal request.
6. Let the existing DEVICE_KV owner execute the terminal bytes and preserve authentic hop 3 with exact prior-receipt continuity.
7. Verify the complete three-receipt chain with the merged ERL consumer and bind terminal transport proof to the pre-existing provider readback evidence without provider replay.
8. Reconcile the parent ERL handoff with exact receipt hashes and final proof class.

## Current state

`PROFILE_SOURCE_PREPARATION_AND_RESIDENT_BINDING_WIRING_MERGED_AND_VALIDATED / LOOPBACK_TVC_AUTHORIZED_SHARED_INTR_SUBMISSION_IMPLEMENTED_ON_BRANCH / AUTHENTIC_RESIDENT_SOURCE_MATERIALIZATION_NOT_YET_OBSERVED / AUTHENTIC_THREE_HOP_TRAVERSAL_NOT_YET_OBSERVED`
