# SDK WorkSpace External-Collaboration Authentic Runtime 004 Mirror Handoff

Updated: 2026-09-11
Repository: `StegVerse-Labs/.github`
Goal Task ID: `SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004`
Parent Goal Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
COSV: `71000000100110`
Status: `ACTIVE / RESOLVER SOURCE REPAIR IN REVIEW / EXISTING AUTHORIZED RESIDENT RECONNECTION STILL REQUIRED`

## Purpose

This is the active canonical successor after parent `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003` retired at 20/20. It owns the remaining authentic resident reseal/listener, custody, callback, owner-present consent, provider probe, SDK re-evaluation, MIR, Master Records, one-device, propagation, and public-distribution predicates.

## Authority boundary

Task Registry is coordination only. WorkerCoordinator owns claim/fence authority; Interlock/InTr owns governed transition authority; TV/TVC owns credential/provider/release authority; Master Records owns observed reality/reconstruction; `StegVerse-org/LLM-adapter#72` remains the Service Gateway owner. GitHub has no runtime authority. No hosted fallback or second user-operated device is authorized.

## Reconciled merged source state

The existing source chain remains merged and validated through `.github` #1393, SDK #196, `.github` #1402, LLM-adapter #332, SDK #199, `.github` #1415, TVC #403, SDK #201, and `.github` #1427. G18 terminalization is not a downstream admission gate. TV/TVC release authorization remains separate and must be authentically GRANTED before any StegCore release operation.

## Fresh observation

This session rechecked all available authentic evidence channels:

- authorized remote-resident connector: zero devices;
- exact GitHub receipt search: no authentic reseal receipt and no authentic listener receipt, only documentation/consumer references;
- retained Google Drive exact receipt search: zero matches for both receipt filenames.

Therefore no resident execution, target custody/readback, listener health, CMC-029 live TLS adoption, sovereign callback reachability, Google consent, provider probe, MIR, Master Records reconstruction, one-device completion, downstream propagation, or public distribution is claimed.

## Resolver defect and repair

Fresh source inspection found two deterministic discovery defects that can block the exact next sequence even after resident reconnection:

1. `scripts/resolve_task_runtime_candidates.py` searched only the aggregate `data/canonical-task-registry.json`, while this active successor is represented by its dedicated canonical record under `data/canonical-task-records/SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004.json`.
2. The successor required `resident_request_dispatch` with `mutation_required=true`, but the canonical resident dispatcher profile deliberately declares `mutation_allowed=false`; comparable resident-dispatch coordination such as `HIL-RESIDENT-SESSION-MANIFOLD-ACTIVATION-001` uses `mutation_required=false` because discovery does not grant mutation authority.

Branch `repair/sdk-workspace-runtime-resolver-004` repairs both conditions without changing runtime authority:

- resolver falls back to an exact dedicated canonical task record only when the aggregate registry has no row, and fails closed on duplicate aggregate identities or record-ID mismatch;
- successor runtime discovery now uses `mutation_required=false` while WorkerCoordinator/InTr remain required for governed mutation/execution;
- README reviewed: no public capability change, so no README text change is required.

This source repair does **not** prove a current runtime match. `current_observation_required=true` remains intact, so a DECLARED_ONLY/offline resident still fails closed.

## Current proof boundary

```text
portable exact dispatch: MERGED / VALIDATED
Service Gateway three-route source: MERGED / VALIDATED
resolver standalone-record fallback: SOURCE REPAIR IN REVIEW
successor dispatcher discovery mutation semantic: SOURCE REPAIR IN REVIEW
resident reseal receipt: NOT OBSERVED
resident listener receipt: NOT OBSERVED
authorized remote runtime online: NOT OBSERVED
target client-secret custody/readback: NOT PROVEN
resident listener health 127.0.0.1:8786: NOT PROVEN
sovereign stegverse.org callback/public HTTPS reachability: NOT PROVEN
owner-present Google consent/session: NOT PROVEN
authoritative provider-file probe: NOT PROVEN
SDK complete-predicate re-evaluation: NOT PROVEN
MIR transition reporting: NOT PROVEN
Master Records reconstruction: NOT PROVEN
one-current-device end-to-end: NOT PROVEN
downstream propagation complete: FALSE
public distributions complete: FALSE
```

Expected resident receipts remain:

```text
receipts/sovereign-host/sdk-workspace-external-collab-client-secret-reseal.latest.json
receipts/sovereign-host/sdk-workspace-external-collab-consent-listener.latest.json
```

## Exact next sequence

1. Validate and merge the resolver repair only if exact-head repository CI is green.
2. Re-resolve this active task through the canonical runtime-profile resolver and recheck the existing authorized resident connection.
3. When the existing resident is present, exact-dispatch only `sdk_workspace_external_collab_client_secret_reseal` and `sdk_workspace_external_collab_consent_listener` from already-local canonical source.
4. Accept only authentic reseal `TARGET_ALREADY_PRESENT`, `COMPLETED`, or exact `BLOCKED`; validate custody/readback without overwrite.
5. Accept only authentic listener `SERVICE_ALREADY_HEALTHY`, `COMPLETED` with `loopback_health_verified=true`, or exact `BLOCKED`.
6. After listener health, prove the existing Service Gateway public routes and CMC-029/native-TLS adoption without callback-query leakage.
7. Only after target custody plus sovereign callback reachability, perform owner-present Google consent on the current iPhone.
8. Run one exact authoritative provider-file metadata probe, then SDK re-evaluation, MIR, Master Records reconstruction, one-device proof, downstream propagation, and public-distribution proof.
9. Do not manually publish StegCore; wait for authentic TV/TVC GRANTED release authority and required resident SKAP/double-Interlock evidence.

## Human action

None now. Do not initiate Google consent and do not manually publish StegCore `v0.3.0`.
