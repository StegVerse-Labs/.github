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


## Canonical local source-root discovery — 2026-08-30

A second machine-execution seam was removed after the resident materialization fix. The current-basis consumer no longer requires four manually populated component-root environment variables when the existing canonical production source materialization is already present.

Resolution order:

```text
explicit STEGVERSE_*_SOURCE_ROOT for a component, if present and valid
-> STEGVERSE_SOURCE_MATERIALIZATION_ROOT/components/<component>
-> /var/lib/stegverse/source/components/<component>
-> fail closed as BLOCKED_LOCAL_SOURCE_ROOTS_NOT_OBSERVED
```

This matches the existing production source-preparation architecture. The generic resident dispatcher now forwards the non-secret `STEGVERSE_SOURCE_MATERIALIZATION_ROOT` locator when present. No remote checkout, network fetch, GitHub/provider credential, or new runtime authority is introduced.

This correction removes manual environment wiring as a prerequisite when the canonical local component tree already exists. Authentic resident execution remains separately evidence-bound.


## Resident materialization and source-discovery closures — 2026-08-30

Two source/runtime plumbing defects are now closed and merged:

```text
resident refresh rematerialization:
  PR #500
  merge: 0c45dfc7e413c5da8fcc89f33637e1783a6eb558
  current-basis resident request validation: 33293861330 SUCCESS
  organization control plane: 33293861332 SUCCESS
  Heartbeat Worker Project: 33293861363 SUCCESS

canonical local source-root discovery:
  PR #511
  merge: 6d03c0d3d41f45ac91b740c091f16b7ddf9097bf
  current-basis resident request validation: 33294733821 SUCCESS
  Heartbeat Worker Project: 33294733819 SUCCESS
  organization control plane: 33294733918 SUCCESS
```

The consumer is now materialized by the resident source-refresh path and resolves already-local component roots without requiring four manual environment variables.

The public Site projection is also separately complete and anonymously observed at frozen v0.4:

```text
Site PR #700 merge: 8a13182c7630eab1efa613cde45229b4de27a975
public verification: run 33294523117 attempt 2 / job 99211964506 PASS
projection state: FROZEN / execution window OPEN
authentic execution: NOT_RUN
results: absent
```

These closures do not substitute for resident execution.

## Exact canonical source-blob binding — 2026-08-30

Before invoking the SDK harness, the resident consumer now verifies the exact experiment-critical Git blob identities already merged in the canonical component repositories:

```text
SDK:
  scripts/run_cross_framework_current_basis_v04.py
    93a423a76d1662329f0511dd531646c5b21ff55b
  inspection/examples/cross-framework-current-basis-request.draft.json
    59d818a15fc7be732c97dae7d2174d8cfe9a7bab
  stegverse/sovereign_validation_runtime.py
    6bc0944633b6299c19f065f44dd5999434445dd7
  stegverse/current_basis.py
    5971a050d94fc237cad65d23ba5ac873ee6900b4

StegCore:
  src/stegcore/current_basis.py
    c56179d1ba92a3f487dd62eddd41b812028c48c3
  src/stegcore/transaction_lifecycle.py
    81935669846fedd2867272810b090226b05780ab

Core-Lite:
  core_lite/transaction_route.py
    734923a86bfcd4d41d07e0fb8797de50f0fb9408

Master Records:
  services/manifest_receipt_custody.py
    26a4c1e082ee91128648b2b9bd13cc32ce915f82
```

A local source tree that is present but stale now emits `BLOCKED_CANONICAL_SOURCE_IDENTITY_MISMATCH` and records every expected/observed blob identity without attempting the experiment. This prevents a superficially complete but stale local materialization from being mistaken for the frozen v0.4 execution basis.

Current evidence boundary remains:

```text
resident request source: MERGED
resident consumer source: MERGED
resident dispatcher integration: MERGED
resident source-refresh materialization defect: CLOSED / MERGED / VALIDATED
canonical local source discovery defect: CLOSED / MERGED / VALIDATED
exact critical source identity guard: IMPLEMENTED / VALIDATION PENDING
resident request consumption: NOT OBSERVED
authentic StegVerse execution: NOT OBSERVED
S1 observation: NOT OBSERVED
post-observation transition receipt: NOT OBSERVED
Master Records custody/replay/reconstruction: NOT OBSERVED
RUN_COMPLETE.json: NOT OBSERVED
user action required: false
second machine required: false
```


## Reconciled machine-execution state — 2026-08-30

This section is authoritative over older intermediate status text above.

```text
source implementation issue #468: CLOSED / COMPLETE
stale implementation PR #471: CLOSED / SUPERSEDED_BY_CURRENT_MAIN
resident request source: MERGED / VALIDATED
resident consumer source: MERGED / VALIDATED
dispatcher integration: MERGED / VALIDATED
source-refresh consumer materialization: MERGED / VALIDATED
canonical local component-root discovery: MERGED / VALIDATED
exact experiment-critical source-blob guard: MERGED / VALIDATED
frozen manifest source identity guard: MERGED / VALIDATED
Site frozen-v0.4 projection: PUBLICLY OBSERVED
known scoped scaffolding/stubs: 0
resident request consumption: NOT OBSERVED
authentic StegVerse execution: NOT OBSERVED
S1 observation: NOT OBSERVED
post-observation S0->S1 receipt: NOT OBSERVED
Master Records custody/replay/reconstruction: NOT OBSERVED
RUN_COMPLETE.json: NOT OBSERVED
user action required: false
second machine required: false
```

Canonical source closure evidence:

- request/consumer merge: `b881eaba3b2e5eca64630a4d684352c22f782ca9`
- refresh materialization merge: `0c45dfc7e413c5da8fcc89f33637e1783a6eb558`
- component-root discovery merge: `6d03c0d3d41f45ac91b740c091f16b7ddf9097bf`
- experiment-critical source-blob binding merge: `c379903b25ebf369ba3aaf7b295d6a725e9d6ec8`
- current-basis resident validation: `33295402064 SUCCESS`
- Heartbeat Worker Project: `33295402124 SUCCESS`
- organization control plane: `33295402115 SUCCESS`
- Site public projection observation: run `33294523117` attempt 2 / job `99211964506 PASS`

No further repository-source construction is currently known to be required for the exact v0.4 run. The next state-changing transition must be authentic non-hosted resident execution and evidence production.
