# StegBrowser Runtime Consumption Mirror Handoff

Updated: 2026-09-14

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-CONSUMPTION-001`
- Parent: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV: `40000100100000`
- Canonical task record: `data/canonical-task-records/STEG-BROWSER-RUNTIME-CONSUMPTION-001.json`
- Status: `ACTIVE / CHECKED_OUT`
- Selected substrate: `ADMITTED-EPHEMERAL-STEGOS-NODE`
- External/second user-operated device required: `false`

## Canonical continuation

```text
Task Registry CONTINUE
-> standing Healer resident scheduler carrier
-> neutral RT-REUSABLE-TASK-SCHEDULER-001
-> RT-STEGBROWSER-RUNTIME-CONSUMPTION-001
-> SovereignLocalEventRuntimeAdapter
-> EVENT_EPHEMERAL StegOS runtime
-> runtime-local PROPOSED Canonical Work projection
-> Interlock/InTr admission
-> authentic successor resident consumption
-> exact-byte custody into the existing resident runtime
-> existing stegbrowser_tvc_source_promotion consumer
-> pinned TVC aef6b6f5dc99d2a531718ca475d20858ae8e68a6 materialization/restart
-> immutable observer 4c78f8653b8a5899350479d57c58e936b50e023a
-> simultaneous 127.0.0.1:8765 + 127.0.0.1:8775
-> OWNER_INGRESS_READY_OBSERVED
-> Master Records custody/reconstruction
```

No second scheduler, WorkerCoordinator, runtime plane, credential path, device identity, dispatcher, or provider authority may be introduced.

## Merged source continuity

- `.github#1781`: exact Task Registry `CONTINUE` preflight.
- `.github#1789`: WorkerCoordinator self-heal source-root continuity.
- `.github#1817`: substrate-order / modified-record validation repair.
- `.github#1831` / `6f1b08ee786c8f72395cfa5d393397bcdb7404c5`: executable reusable runner binding.
- `.github#1834` / `5ca9abf473ac1cfeb07efa23f397321cad07b3e5`: runtime-local `PROPOSED` ingress projection while canonical Goal remains `ACTIVE / CHECKED_OUT`.
- `StegVerse-Healer#73` / `22683b8583c30f5ba8c720eaad999e3a13a23d9e`: existing standing Healer / neutral reusable scheduler carrier binding, hourly eligible with bounded 15-minute retries.
- `Site#1305` / `4a10b42d4bb2743205c774d3c667cefc7353a710`: same-device root Universal InTr / Canonical Work capability.
- `Site#1310` / `3a067ff48845044a8be42b42061929c1b7489651`: repair for authentic current-iPhone `root InTr profile HTTP 404` negative runtime result.

These are source/configuration evidence only and do not substitute for authentic runtime receipts.

## Autonomous resident continuation defect and repair

The standing Healer carrier and neutral scheduler already select `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001`, so ChatGPT remote shell access is not part of the production path. Review of the reusable runner exposed the remaining deterministic continuation gap after an authentic ephemeral Canonical Work cycle:

1. the runner produced/validated Canonical Work consumption inside the event-ephemeral StegOS runtime;
2. the neutral scheduler already supplied the existing resident runtime as `parameters.runtime_root`, but the runner ignored it;
3. the required successor consumption evidence therefore remained inside the ephemeral runtime instead of being retained under the existing resident sovereign-host custody path;
4. the runner then looked for the TVC source-promotion receipt inside the ephemeral runtime instead of invoking the already-registered `stegbrowser_tvc_source_promotion` consumer against the resident runtime.

Branch `fix-stegbrowser-autonomous-resident-evidence-bridge` repairs only that missing connection. The runner now:

- consumes the neutral scheduler's existing `runtime_root` / `STEGVERSE_HEARTBEAT_ROOT` binding;
- requires resident and event-ephemeral roots to be distinct;
- copies the authentic Canonical Work successor consumption receipt and its bootstrap receipt byte-for-byte into the existing resident runtime only after the originals are observed and validated;
- records a non-authorizing evidence-custody sidecar with SHA-256 provenance;
- invokes the existing `control/resident-execution-request.d/consume-stegbrowser-tvc-source-promotion.py` consumer against that same resident runtime;
- validates `STAGED`, `ALREADY_STAGED`, or `RESTAGED_EXACT_SOURCE` for exact TVC SHA `aef6b6f5dc99d2a531718ca475d20858ae8e68a6`;
- then continues to the existing immutable observer boundary and fails closed if terminal runtime observation has not yet occurred.

The repair does not create another scheduler, dispatcher, WorkerCoordinator, runtime authority, credential path, or device requirement. Exact-byte retention does not rewrite or reinterpret the authentic receipt.

Validation is pending for this branch. Merge/source validation must not be promoted into runtime proof.

## First unresolved authentic predicate

`CANONICAL_WORK_RESIDENT_CONSUMPTION_OBSERVED`

Required retained receipt:

```text
receipts/sovereign-host/canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json
```

After the autonomous continuation repair is merged and consumed by the existing resident scheduler, the next eligible Healer cycle may produce this receipt without ChatGPT process access or user device action.

## Required later runtime evidence

```text
receipts/sovereign-host/canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json
receipts/sovereign-host/stegbrowser-runtime-consumption-evidence-custody.latest.json
receipts/sovereign-host/stegbrowser-tvc-source-promotion-request-consumption.latest.json
receipts/sovereign-host/worker-source-refresh.latest.json
receipts/sovereign-host/resident-refresh-dispatch.latest.json
receipts/sovereign-host/resident-request-dispatch.latest.json
/var/lib/stegverse/tvc/primary-runtime-source-promotion/dispatch-latest.json
/var/lib/stegverse/tvc/primary-runtime-source-promotion/latest.json
/var/lib/stegverse/skap/browser-recipient/apple/receipts/runtime-observation-latest.json
```

Historical parent receipts remain provenance only.

## Authority invariants

- Task Registry: coordination only.
- Healer carrier / neutral reusable scheduler: scheduling and invocation transport only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed transition authority.
- TV/TVC: credential/provider authority.
- KV/SKAP Vault: user-verification/custody authority.
- Master Records: observed-reality/reconstruction authority.
- HeartBeat: observability/timing/freshness and resident carrier timing only.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.
- StegOS nodes/devices: interchangeable execution/transport surfaces; no second user-operated device prerequisite.

## Completion predicate

Complete only when authentic evidence establishes successor Canonical Work consumption; current WorkerCoordinator claim/fence; InTr admission; current-dispatch-bound TVC source promotion; pinned TVC materialization/restart; immutable observer execution; simultaneous TVC 8765 + SKAP 8775; `OWNER_INGRESS_READY_OBSERVED`; Master Records custody/reconstruction; and no parallel scheduler/dispatcher/credential/device path.

## Current state

`ACTIVE / CHECKED_OUT / TASK_REGISTRY_CHECKIN_CONTINUE_OBSERVED / EPHEMERAL_STEGOS_SELECTED / REUSABLE_EPHEMERAL_RUNNER_BINDING_MERGED / RUNTIME_LOCAL_PREINGRESS_PROJECTION_REPAIR_MERGED / EXISTING_HEALER_NEUTRAL_SCHEDULER_CARRIER_BOUND / AUTONOMOUS_RESIDENT_EVIDENCE_CONTINUATION_REPAIR_IN_VALIDATION / CANONICAL_WORK_RESIDENT_CONSUMPTION_NOT_OBSERVED / WORKERCOORDINATOR_CLAIM_FENCE_NOT_OBSERVED / TVC_SOURCE_PROMOTION_CONSUMPTION_NOT_OBSERVED / OWNER_INGRESS_READY_NOT_OBSERVED / REMOTE_DEVICE_NOT_REQUIRED / NO_SECOND_USER_OPERATED_DEVICE`

## Manual work

None.
