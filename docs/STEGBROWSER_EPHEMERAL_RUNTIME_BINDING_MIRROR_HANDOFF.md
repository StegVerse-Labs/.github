# StegBrowser Ephemeral Runtime Binding Mirror Handoff

Updated: 2026-09-11

## Task pointer

- Goal Task ID: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV vector: `40000100100000`
- Canonical record: `data/canonical-task-records/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`
- Native app-target handoff: `StegVerse-Labs/StegOS/docs/STEGBROWSER_IOS_RESIDENT_APP_TARGET_MIRROR_HANDOFF.md`
- TVC Apple handoff: `StegVerse-Labs/TVC/docs/APP_STORE_CONNECT_TV_TVC_SKAP_MIRROR_HANDOFF.md`

## Current objective

The Goal remains ACTIVE and is not superseded. The immediate objective is authentic resident consumption of the exact TVC source-promotion continuation, followed by pinned TVC materialization, same-primary-runtime restart, and live Apple owner-ingress evidence. Native StegSocials publication remains downstream of a working current-iPhone resident instance.

## Canonical source chain

```text
Canonical Work StegBrowser ingress
-> StegBrowser task-specific convergence bootstrap
-> global runtime-node convergence visitor
-> registered selector stegbrowser_tvc_source_promotion
-> existing resident dispatcher
-> exact TVC source-promotion consumer
-> existing private-source handoff
-> exact TVC aef6b6f5 materialization
-> #387 transient promotion hook
-> #386 same-primary-runtime rebind/restart
-> TVC primary 127.0.0.1:8765 + SKAP ingress 127.0.0.1:8775
-> Apple recipient/liveness/InTr OWNER_INGRESS_READY
-> current-iPhone SKAP credential custody
-> TVC Apple operations
-> same-device IPA signing / Build Upload / TestFlight
-> current-iPhone resident discovery
```

Relevant merged source evidence:

```text
.github #1358
  merge 9776ceba4877f8c213af534176f277c28ec58d39
  exact request/consumer + selector stegbrowser_tvc_source_promotion

TVC #386
  merge 2e1bda01699439731569dce45d5d7b4c5b342424
  verified immutable TVC materialization -> existing primary runtime

TVC #387
  merge aef6b6f5dc99d2a531718ca475d20858ae8e68a6
  successful private-source read -> transient promotion dispatch

.github #1437
  merge 495b329392669d979253a609a45dd62b3195dfe8
  Task Registry/COSV reconciliation

.github #1440
  merge 7f2b83b7abf4bc7163e0e3e5dde6946f547e9f79
  global convergence visitor selects stegbrowser_tvc_source_promotion
  runtime-node profile and global resume projection align to AUTHENTIC_TVC_SOURCE_PROMOTION_CONSUMPTION

.github #1441
  merge 55c33048e1671143d7cc30ccb74b677f9e8241f1
  canonical handoff reconciliation after #1440
```

## Bootstrap reachability repair

After #1440, the convergence visitor knew how to select `stegbrowser_tvc_source_promotion`, but `scripts/install_and_run_canonical_work_event_bootstrap.py` still invoked the global convergence visitor only when the explicit Canonical Work task ID was either the Runtime Profile Map or the dedicated global measurement child. A Canonical Work bootstrap for `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001` therefore did not itself call the visitor.

The current source repair adds:

```text
STEGBROWSER_TASK_ID = STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001
GLOBAL_CONVERGENCE_TASK_IDS = {
  RUNTIME_PROFILE_MAP_TASK_ID,
  GLOBAL_MEASUREMENT_TASK_ID,
  STEGBROWSER_TASK_ID
}
```

and adds regression coverage requiring the StegBrowser bootstrap to trigger the existing global convergence path. This creates no new scheduler, dispatcher, heartbeat, WorkerCoordinator implementation, credential path, hosted fallback, or machine. The existing collision preflight, Canonical Work route, convergence visitor, resident dispatcher, TV/TVC authority, Interlock/InTr transition authority, and Master Records runtime-reality boundaries remain unchanged.

This repair is source-only until exact-head validation passes and the change is merged. Even after merge, authentic resident execution must still be observed separately.

## Current authentic runtime evidence

Expected first dedicated receipt:

```text
receipts/sovereign-host/stegbrowser-tvc-source-promotion-request-consumption.latest.json
```

No authentic runtime instance of that receipt is currently present in canonical GitHub evidence, and the authorized remote resident connector currently reports no online device. Therefore these remain unclaimed:

```text
resident dispatcher consumed stegbrowser_tvc_source_promotion: NOT OBSERVED
exact TVC request staged by authentic resident:               NOT OBSERVED
pinned TVC materialization executed:                          NOT OBSERVED
#387 transient promotion executed:                            NOT OBSERVED
#386 same-primary-runtime restart executed:                    NOT OBSERVED
simultaneous 8765/8775 listeners observed:                    NOT OBSERVED
Apple recipient/liveness/InTr OWNER_INGRESS_READY:            NOT OBSERVED
real Apple credential SKAP custody:                           NOT OBSERVED
current-iPhone signing / TestFlight / discovery:              NOT OBSERVED
```

GitHub Actions remains validation/evidence transport only. Source, profile, or CI state does not mint execution authority or runtime truth.

## Apple and current-iPhone boundary

Apple Developer Program Account Holder membership was previously observed active through `2027-09-09`. The App Store Connect Terms/account UI gate remains external to StegVerse source. The Team API key remains `NOT_CREATED_OR_NOT_OBSERVED`, and no real `.p8` may be placed in GitHub, logs, artifacts, task payloads, or chat. Credential ingress remains current-iPhone local sealing -> InTr -> Device/KV/SKAP -> callback-only TVC provider operation once owner ingress is live.

StegOS source includes the current-iPhone WASM signing implementation; authentic current-iPhone signing evidence remains unobserved.

## Remaining sequence

1. Validate and merge the StegBrowser task-specific bootstrap convergence repair.
2. Obtain authentic resident consumption of `stegbrowser_tvc_source_promotion` through the task-specific Canonical Work bootstrap and existing convergence route.
3. Observe exact TVC `aef6b6f5dc99d2a531718ca475d20858ae8e68a6` materialization, #387 transient promotion, and #386 same-primary-runtime restart receipts.
4. Observe simultaneous TVC primary `8765` and SKAP ingress `8775`, then exact Apple recipient/liveness/InTr `OWNER_INGRESS_READY`.
5. Resolve the external Apple Terms/account gate, generate the Team API key, and seal it from the current iPhone directly into SKAP without credential export.
6. Observe authentic Device -> KV -> SKAP custody and execute TVC Apple identifier/capability/resource/provisioning operations.
7. Execute and verify same-device IPA signing, TVC Build Upload, TestFlight installation, and canonical same-device resident discovery.
8. Only after working-instance proof continue native StegSocials publication/readback and downstream custody.

## README disposition

Repository `README.md` was re-reviewed. Its Canonical Work architecture remains accurate: registered resident mechanisms are reused, Task Registry does not mint execution authority, and runtime completion requires authentic downstream evidence. No README text change is required for this bootstrap-routing repair.

## Current state

`ACTIVE_NOT_SUPERSEDED / CANONICAL_RESIDENT_SOURCE_MERGED_VALIDATED / RESIDENT_EXACT_TVC_SOURCE_REQUEST_MERGED_VALIDATED_1358 / TASK_REGISTRY_AND_COSV_RECONCILED_1437 / GLOBAL_CONVERGENCE_STEGBROWSER_SELECTOR_REPAIR_MERGED_VALIDATED_1440 / STEGBROWSER_TASK_BOOTSTRAP_CONVERGENCE_REPAIR_IMPLEMENTED_VALIDATION_PENDING / AUTHENTIC_RESIDENT_SOURCE_PROMOTION_CONSUMPTION_NOT_OBSERVED / AUTHENTIC_TVC_MATERIALIZATION_AND_RESTART_NOT_OBSERVED / LIVE_APPLE_OWNER_INGRESS_READY_NOT_OBSERVED / APPLE_TEAM_API_KEY_NOT_CREATED_OR_NOT_OBSERVED / SAME_DEVICE_SIGNING_SOURCE_IMPLEMENTED_RUNTIME_NOT_OBSERVED / AUTHENTIC_CURRENT_IPHONE_INSTALL_LISTENER_DISCOVERY_PENDING`
