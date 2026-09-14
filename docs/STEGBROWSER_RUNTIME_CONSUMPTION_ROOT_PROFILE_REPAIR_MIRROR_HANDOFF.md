# StegBrowser Runtime Consumption Root Profile Repair / KV Entrypoint Correction Mirror Handoff

Updated: 2026-09-14
Goal Task ID: `STEG-BROWSER-RUNTIME-CONSUMPTION-001`
COSV: `40000100100000`
Canonical parent handoff: `docs/STEGBROWSER_RUNTIME_CONSUMPTION_MIRROR_HANDOFF.md`
State: `ACTIVE / CHECKED_OUT / NEGATIVE_RUNTIME_EVIDENCE_RETAINED / ROOT_PROFILE_REPAIR_RELEASED / KV_ENTRYPOINT_INTR_LAUNCHER_RELEASED / CANONICAL_RUNTIME_PREDICATES_UNRESOLVED`

## Retained authentic negative runtime evidence

A user-operated current-device debug surface previously executed the published Canonical Work launcher and returned:

```json
{
  "state": "FAIL_CLOSED",
  "reason": "root InTr profile HTTP 404",
  "authority_effect": "NONE"
}
```

That observation remains valid negative runtime evidence for that specific debug path. It proves only that the debug launcher reached its root-InTr readiness probe and failed closed. It does not prove `INGRESS_ADMITTED`, Canonical Work resident consumption, WorkerCoordinator claim/fence, TVC promotion, self-building completion, or owner-ingress readiness.

## Root-profile repair retained as diagnostic source continuity

Site PR `#1310` repaired the nested-scope `/intr/profile` routing defect without creating a second worker/runtime. Exact repair head `d707d9b69ddd00205395a7809a5bd59ee79b4a90` passed its six required Site validations, merged as `3a067ff48845044a8be42b42061929c1b7489651`, and propagated through Pages run `34857816945` successfully.

This remains useful diagnostic/observation capability. It is **not** the required progression mechanism for the Goal.

## Architectural correction: device-specific launch is not the progression boundary

A particular iPhone, browser instance, or physical device must not be treated as the required trigger for this Goal. The canonical task already selects `ADMITTED-EPHEMERAL-STEGOS-NODE`, sets `external_device_required=false`, forbids a second user-operated device, and relies on Task Registry -> Canonical Work -> Interlock/InTr -> admitted runtime progression.

The earlier interpretation that the same registered iPhone "must execute the launcher again" is superseded. A physical device can supply transport/execution or debugging evidence, but device class is not governance authority and is not the canonical progression prerequisite.

## KV launcher belongs behind Interlock/InTr at the StegVerse entry point

Site PR `#1311` implements the corrected entry boundary. The StegVerse entry point no longer treats `My KV` as a plain hyperlink or a device-specific launcher. It now invokes the already-existing governed KV path:

```text
StegVerse entry point
-> KV launcher
-> kv.interlock.request.v1
-> generated device-kv InTr materialization
-> destination = KV / KnowledgeVault:Interlock
-> existing DEVICE_KV ingress/query-return path
-> exact governed installation projection/readback
-> My KV surface
```

The launcher reuses the existing `StegVerseKVInstallationStatusBridge`, generated `device-kv` connector, HB/InTr carrier, Node continuity/outbox, and DEVICE_KV materialization/result path. It declares `device_class_requirement=NONE`, does not contain an iPhone-specific progression condition, and creates no second service worker, InTr runtime, scheduler, WorkerCoordinator, or credential plane.

Exact Site source head `833d4bbc20f983e8c630f8b3619ef3882b73abc8` passed all six triggered validations:

- Site Handoff Orchestrator
- Site Node Continuity
- Site Homepage Chat
- Node IndexedDB Schema Migration
- Site Bootstrap Validate - No Non-TV/TVC Credential Authority
- Ecosystem Heartbeat Orchestration

PR `#1311` merged as `5f6c663b1294bb9f7cc8083c78c574b293e5ddf7` and exact-merge Pages deployment run `34861289935` completed successfully.

Those facts establish source release and public propagation only. They do not establish authentic KV runtime admission/readback or any canonical completion predicate.

## Authority invariants

- Task Registry = coordination/work identity; it does not mint execution authority.
- KnowledgeVault = durable user-controlled state.
- Interlock/InTr = state-transition admission and bounded transport; no authority transfer.
- WorkerCoordinator = claim/fence authority where applicable.
- TV/TVC = credential/provider authority.
- Master Records = observed-reality/provenance authority.
- HeartBeat = observability/timing/reference only.
- GitHub = source/validation/evidence transport only; runtime authority `NONE`.
- Physical device class = incidental execution/transport characteristic, not governance authority or progression prerequisite.

## Current canonical progression

The Goal must continue through the existing canonical chain rather than requiring the user to re-present intermediate identifiers or manually trigger a particular device surface:

```text
Task Registry exact check-in -> CONTINUE
-> existing Canonical Work event bootstrap
-> applicable Interlock/InTr admission
-> ADMITTED-EPHEMERAL-STEGOS-NODE materialization
-> authentic Canonical Work resident consumption
-> current WorkerCoordinator claim/fence
-> stegbrowser_tvc_source_promotion consumption
-> pinned TVC materialization/restart
-> immutable observer
-> simultaneous TVC/SKAP observation
-> OWNER_INGRESS_READY_OBSERVED
```

The KV entrypoint launcher is now correctly positioned behind Interlock/InTr and can produce authentic KV admission/readback evidence when invoked by an eligible entrypoint execution. It is not a replacement for Canonical Work authority or WorkerCoordinator authority.

## Still unresolved

No new authentic observation in this correction establishes:

- `CANONICAL_WORK_RESIDENT_CONSUMPTION_OBSERVED`;
- current WorkerCoordinator claim/fence;
- canonical InTr admission for this Goal;
- `STEGBROWSER_TVC_SOURCE_PROMOTION_CONSUMPTION_OBSERVED`;
- pinned TVC primary-runtime restart;
- immutable observer execution;
- simultaneous TVC 8765 / SKAP 8775;
- `OWNER_INGRESS_READY_OBSERVED`.

The first unresolved canonical completion predicate therefore remains `CANONICAL_WORK_RESIDENT_CONSUMPTION_OBSERVED`.

## Manual-work disposition

No device-specific manual trigger is a canonical prerequisite for the next step. Manual work is required only if a later transition reaches a genuine user-only authority boundary such as explicit user approval, wallet signature, biometric/credential release, or an external provider action that cannot be delegated under the existing authority model.
