# Cross-Framework Current-Basis v0.4 Resident Execution Mirror Handoff

Updated: 2026-08-29
Repository: `StegVerse-Labs/.github`
Issue: #478
Current source-fix branch: `fix/current-basis-resident-refresh-materialization-484`

## Goal

Dispatch one bounded authentic StegVerse execution of the exact frozen cross-framework current-basis v0.4 test through the existing sovereign resident runtime. This lane does not create a second scheduler, heartbeat, evaluator, credential path, or runtime authority.

## Exact upstream bindings

```text
SDK execution harness merge: StegVerse-org/StegVerse-SDK@2b1ae25662aaade5033e6bacac98d9ba5233fdee
StegCore native current-basis merge: StegVerse-Labs/StegCore@e80e927616750a88ad7fc88f4017fc496474f1e4
resident request/consumer merge: StegVerse-Labs/.github@b881eaba3b2e5eca64630a4d684352c22f782ca9
frozen manifest SHA-256: 07a08496c21b31f70f6f45ef731aa5f6b2522a6fc8f67f2d0a4c2b6fceda7a3f
frozen manifest Git blob SHA-1: 59d818a15fc7be732c97dae7d2174d8cfe9a7bab
test_id: cross-framework-current-basis-001
```

## Runtime boundary

```text
existing WorkerCoordinator / resident dispatcher
-> bounded current-basis resident request consumer
-> already-materialized local SDK + StegCore + Core-Lite + Master Records roots
-> SDK scripts/run_cross_framework_current_basis_v04.py
-> canonical StegCore current_basis derivation
-> canonical SDK sovereign validation runtime
-> Master Records custody
-> S1 observation
-> post-observation S0->S1 receipt
-> replay
-> reconstruction
-> local RUN_COMPLETE.json
```

GitHub Actions is source validation only and MUST NOT execute this test. No network source fetch, GitHub credential, provider credential, counterpart result, or external consequence is allowed.

## Local source requirements

The resident consumer uses only locally materialized roots already exposed to the sovereign runtime:

```text
STEGVERSE_SDK_SOURCE_ROOT
STEGVERSE_STEGCORE_SOURCE_ROOT
STEGVERSE_CORE_LITE_SOURCE_ROOT
STEGVERSE_MASTER_RECORDS_SOURCE_ROOT
```

Missing roots or missing exact harness/manifest/current-basis files produce a machine-observable blocked state. They do not create a user-action requirement and do not authorize remote checkout.

## Source-refresh materialization correction

Post-merge inspection of the actual resident source-refresh path found one concrete execution blocker: `scripts/dispatch_resident_execution_requests.py` and `control/resident-execution-request.d/` were copied into the resident runtime, but the newly added `scripts/consume_cross_framework_current_basis_v04_request.py` was not listed in `STATIC_FILES` in `scripts/refresh_sovereign_worker_runtime_source.py`.

Without that entry, a refreshed resident runtime would see the request and dispatcher but report the current-basis consumer as `CONSUMER_NOT_MATERIALIZED`; authentic execution could therefore never start.

The active correction adds the exact consumer to the static refresh set and adds a regression guard proving both the consumer and request directory are materialized. This is source/runtime plumbing only; it does not itself claim that the resident host has refreshed or consumed the request.

## Completion

Terminal success requires local result:

```text
~/.stegverse/state/cross-framework-current-basis-v04/result/RUN_COMPLETE.json
status=COMPLETE
manifest_sha256=07a08496...
independent_execution_complete=true
s1_observed=true
transition_receipt_bound=true
custody_recorded=true
replay_recorded=true
reconstruction_recorded=true
counterpart_result_consumed_before_completion=false
external_side_effect=false
```

Repository publication of the resultant packet is a later evidence-transport step and remains separate from resident execution authority.

## Current state

```text
resident request source: MERGED
resident consumer source: MERGED
resident dispatcher integration: MERGED
resident request/source validation: SUCCESS
source-refresh consumer materialization: FIX IMPLEMENTED / VALIDATION PENDING
resident source refresh after correction: NOT OBSERVED
resident request consumption: NOT OBSERVED
authentic StegVerse execution: NOT OBSERVED
Master Records custody/replay/reconstruction: NOT OBSERVED
user action required: false
second machine required: false
```
