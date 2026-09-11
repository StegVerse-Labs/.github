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

## Canonical source chain now merged

The current source chain is:

```text
Canonical Work StegBrowser ingress
-> global convergence visitor
-> registered selector stegbrowser_tvc_source_promotion
-> existing resident dispatcher
-> #1358 exact TVC source-promotion consumer
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

Relevant merged evidence:

```text
.github #1358
  head  a6b6c9928e21f3b8eb41017ee8a26336ecda197d
  merge 9776ceba4877f8c213af534176f277c28ec58d39
  adds exact request/consumer + selector stegbrowser_tvc_source_promotion

TVC #386
  merge 2e1bda01699439731569dce45d5d7b4c5b342424
  promotes verified immutable TVC materialization into the existing primary service

TVC #387
  merge aef6b6f5dc99d2a531718ca475d20858ae8e68a6
  dispatches successful exact private-source materialization into the separate transient promotion unit

.github #1434
  merge 5eba3974ff9c141aab74e616742e959ecdbd2ded
  reconciles source/runtime claims and removes stale validation-pending wording

.github #1437
  merge 495b329392669d979253a609a45dd62b3195dfe8
  reconciles Task Registry/COSV signing and runtime-evidence state

.github #1440
  head  9431a772a0b2034cb6d5da54074b037d3de337dc
  merge 7f2b83b7abf4bc7163e0e3e5dde6946f547e9f79
  routes StegBrowser through the existing convergence visitor to stegbrowser_tvc_source_promotion
  aligns runtime-node profile and global resume projection to AUTHENTIC_TVC_SOURCE_PROMOTION_CONSUMPTION
```

All three exact-head #1440 validation lanes passed: organization control-plane validation, heartbeat validation, and the complete deterministic repository suite. This is source/validation evidence only and does not prove sovereign runtime execution.

## Convergence selector repair

The concrete source defect closed by #1440 was that the #1358 consumer was registered in `scripts/dispatch_resident_execution_requests.py` and materialized by sovereign source refresh, but `scripts/run_global_runtime_evidence_convergence.py` did not include the StegBrowser task in its explicit `TASK_SELECTORS` map. The visitor invokes the existing dispatcher with explicit `--only-consumer` selectors, so the source-promotion consumer could be present without ever being selected by that convergence cycle.

#1440 fixes that by reusing the existing visitor/dispatcher only:

```text
STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001
-> stegbrowser_tvc_source_promotion
```

StegBrowser is no longer treated as a post-dispatch `CANONICAL_WORK_ONLY` lane inside that runner because Canonical Work is the prerequisite that invokes the convergence path. The runtime-node profile retains the canonical-work receipt as prerequisite evidence and identifies `stegbrowser_tvc_source_promotion` as the registered resident selector. No second scheduler, dispatcher, heartbeat, hosted fallback, credential authority, or user-operated machine was introduced.

## Current authentic runtime evidence

The expected dedicated consumption receipt remains:

```text
receipts/sovereign-host/stegbrowser-tvc-source-promotion-request-consumption.latest.json
```

Current canonical GitHub search still finds only the consumer source that defines this path, not an authentic runtime receipt. Therefore all of the following remain unclaimed:

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

Apple Developer Program Account Holder membership was previously observed active through `2027-09-09`. The App Store Connect Terms/account UI gate remains external to StegVerse source. The Team API key remains `NOT_CREATED_OR_NOT_OBSERVED`, and no real `.p8` may be placed in GitHub, logs, artifacts, task payloads, or chat. When owner ingress becomes ready, credential ingress remains current-iPhone local sealing -> InTr -> Device/KV/SKAP -> callback-only TVC provider operation.

StegOS source includes the current-iPhone WASM signing implementation; authentic current-iPhone signing evidence remains unobserved.

## Remaining sequence

1. Obtain authentic resident consumption of `stegbrowser_tvc_source_promotion` through the now-merged #1440 convergence route.
2. Observe exact TVC `aef6b6f5dc99d2a531718ca475d20858ae8e68a6` materialization, #387 transient promotion, and #386 same-primary-runtime restart receipts.
3. Observe simultaneous TVC primary `8765` and SKAP ingress `8775`, then exact Apple recipient/liveness/InTr `OWNER_INGRESS_READY`.
4. Resolve the external Apple Terms/account gate, generate the Team API key, and seal it from the current iPhone directly into SKAP without credential export.
5. Observe authentic Device -> KV -> SKAP custody and execute TVC Apple identifier/capability/resource/provisioning operations.
6. Execute and verify same-device IPA signing, TVC Build Upload, TestFlight installation, and canonical same-device resident discovery.
7. Only after working-instance proof continue native StegSocials publication/readback and downstream custody.

## README disposition

Repository `README.md` was re-reviewed during the #1440 repair. Its Canonical Work architecture remains accurate: registered resident mechanisms are reused, the Task Registry does not mint execution authority, and runtime completion requires authentic downstream evidence. No README text change was required.

## Current state

`ACTIVE_NOT_SUPERSEDED / CANONICAL_RESIDENT_SOURCE_MERGED_VALIDATED / RESIDENT_EXACT_TVC_SOURCE_REQUEST_MERGED_VALIDATED_1358 / TASK_REGISTRY_AND_COSV_RECONCILED_1437 / GLOBAL_CONVERGENCE_STEGBROWSER_SELECTOR_REPAIR_MERGED_VALIDATED_1440 / STALE_PR_1206_CLOSED_UNMERGED / IPHONEOS_UNSIGNED_PACKAGE_VALIDATED / GITHUB_APPLE_CREDENTIAL_EXECUTION_RETIRED / TVC_APP_STORE_CONNECT_PROVIDER_AND_SKAP_PATH_MERGED / TVC_PRIMARY_8765_SKAP_8775_COLLISION_REPAIR_MERGED_VALIDATED / VERIFIED_TVC_SOURCE_TO_SAME_PRIMARY_RUNTIME_PROMOTION_MERGED / PRIVATE_SOURCE_POST_PROMOTION_HOOK_MERGED / AUTHENTIC_RESIDENT_SOURCE_PROMOTION_CONSUMPTION_NOT_OBSERVED / AUTHENTIC_TVC_MATERIALIZATION_AND_RESTART_NOT_OBSERVED / LIVE_APPLE_OWNER_INGRESS_READY_NOT_OBSERVED / APPLE_DEVELOPER_MEMBERSHIP_OBSERVED_ACTIVE_THROUGH_2027-09-09 / APP_STORE_CONNECT_TERMS_GATE_BLOCKED / APPLE_TEAM_API_KEY_NOT_CREATED_OR_NOT_OBSERVED / SAME_DEVICE_SIGNING_SOURCE_IMPLEMENTED_RUNTIME_NOT_OBSERVED / AUTHENTIC_CURRENT_IPHONE_INSTALL_LISTENER_DISCOVERY_PENDING`
