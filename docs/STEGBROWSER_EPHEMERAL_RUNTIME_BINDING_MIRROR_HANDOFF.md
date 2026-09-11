# StegBrowser Ephemeral Runtime Binding Mirror Handoff

Updated: 2026-09-11

## Task pointer

- Goal Task ID: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV vector: `40000100100000`
- Canonical record: `data/canonical-task-records/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`
- Native app-target handoff: `StegVerse-Labs/StegOS/docs/STEGBROWSER_IOS_RESIDENT_APP_TARGET_MIRROR_HANDOFF.md`
- TVC Apple handoff: `StegVerse-Labs/TVC/docs/APP_STORE_CONNECT_TV_TVC_SKAP_MIRROR_HANDOFF.md`

## Active objective

The Goal remains ACTIVE and is not superseded. The immediate objective is one authentic current-iPhone StegBrowser resident instance. Native StegSocials publication remains downstream of that proof.

```text
canonical Site SV-NODE
-> current-iPhone owner ingress
-> live TVC App Store Connect recipient + InTr route
-> Device -> KV -> SKAP sealed credential custody
-> secret-free TVC Apple operations
-> same-device IPA signing
-> TVC native Build Upload
-> TestFlight install
-> canonical same-device resident discovery
-> runtime evidence receipt
```

## Canonical Apple credential path

The prior GitHub-hosted `ASC_*` credential path is retired. The preferred path is current-iPhone local sealing -> InTr -> Device/KV/SKAP -> callback-only TVC provider operation. The real `.p8` must not be placed in GitHub, logs, artifacts, task payloads or chat.

Merged TVC implementation includes:

```text
#356/#357  exact App Store Connect credential class + callback-only provider boundary
#358       exact Apple SKAP recipient class
#360       exact Apple InTr route contract
#361       native App Store Connect Build Upload transaction
#364       executable Apple ciphertext ingress + separate custody + Device->KV->SKAP receipts
#365       same-epoch public-only Site recipient/route exporter
#367       tvc.app_store_connect_skap.activate primary-runtime task registration
#368       RESOLVE_APP_RESOURCE_ID inside authenticated TVC session
#369       Apple tunnel active-repo-root rendering
#370       bounded Apple SKAP bootstrap during normal TVC primary activation
#378       current-main listener/root convergence; merge 1853cb632ff8cf97deed5b08ec4f0964d1ef4978
#379       Apple SKAP runtime-handoff reconciliation; merge adb1c48f1b0459c38ed9d519b0a18bc8039de7ef
#386       verified immutable TVC materialization -> existing primary-runtime promotion bridge; merge 2e1bda01699439731569dce45d5d7b4c5b342424
#387       successful private-source read -> separate transient promotion dispatch; merge aef6b6f5dc99d2a531718ca475d20858ae8e68a6
```

Canonical listener topology:

```text
TVC primary provider-operation runtime: 127.0.0.1:8765
shared SKAP ciphertext ingress:          127.0.0.1:8775
Coinbase SKAP local upstream:            http://127.0.0.1:8775
App Store Connect SKAP local upstream:   http://127.0.0.1:8775
```

## Exact TVC source promotion path

TVC #386 and #387 close the source-level gap between exact TVC private-source materialization and the already-existing primary runtime service.

The immutable TVC source selected for the first resident promotion remains:

```text
repository: StegVerse-Labs/TVC
exact SHA: aef6b6f5dc99d2a531718ca475d20858ae8e68a6
contains: #386 + #387 promotion chain
materialization id: stegbrowser-tvc-runtime-aef6b6f5
```

The promotion bridge requires an immutable TVC materialization under `/var/lib/stegverse/private-source-read/materialized`, exact `git HEAD` equality, and a matching private-source execution receipt. It then invokes that materialization's existing `install_tvc_primary_runtime_service.py --activate`, re-rendering/restarting the same fixed `stegtvc-primary-runtime.service`. No second primary runtime is created.

## Resident request source

The canonical resident request/consumer projection is now merged and validated through `.github` PR #1358:

```text
PR: #1358
head: a6b6c9928e21f3b8eb41017ee8a26336ecda197d
merge: 9776ceba4877f8c213af534176f277c28ec58d39
request: control/resident-execution-request.d/stegbrowser-tvc-source-promotion-001.json
consumer: control/resident-execution-request.d/consume-stegbrowser-tvc-source-promotion.py
dispatcher selector: stegbrowser_tvc_source_promotion
private-source handoff: <runtime>/tvc-handoff/private-source-request.json
```

All five observed exact-head GitHub checks for #1358 completed successfully. GitHub Actions validation remains source/transport evidence only; it does not prove resident execution.

The consumer performs no network source fetch and starts no system service. It stages only the exact TVC `IMMUTABLE_COMMIT` request. An unrelated occupied private-source slot yields `HANDOFF_READY`; same-identity restaging is constrained to the exact pinned coordinate.

The stale pre-convergence PR #1206 was closed unmerged on 2026-09-11 because it was non-mergeable and projected an obsolete canonical task state.

## Current authentic runtime evidence

No canonical source currently contains the runtime receipt expected at:

```text
receipts/sovereign-host/stegbrowser-tvc-source-promotion-request-consumption.latest.json
```

The only canonical match is the consumer source defining that receipt path. Therefore the following must remain unclaimed:

```text
resident dispatcher consumed stegbrowser_tvc_source_promotion: NOT OBSERVED
exact TVC request staged by authentic resident:               NOT OBSERVED
pinned TVC materialization executed:                          NOT OBSERVED
#387 transient promotion executed:                            NOT OBSERVED
#386 same-primary-runtime restart executed:                    NOT OBSERVED
simultaneous 8765/8775 listeners observed:                    NOT OBSERVED
Apple recipient/liveness/InTr OWNER_INGRESS_READY:            NOT OBSERVED
```

No new scheduler, heartbeat, hosted fallback, second runtime, or second user-operated machine should be introduced to manufacture these predicates.

## Device/KV/SKAP convergence

StegOS #326 and #327 compose and verify the four-leg Universal InTr chain:

```text
DEVICE_SYSTEM -> KV -> SKAP_VAULT -> KV -> DEVICE_SYSTEM
```

These are source/validation capabilities. Authentic Apple credential custody remains unobserved.

## Current-iPhone signing

The StegOS current-iPhone WASM signing implementation has advanced beyond the old generic `NOT_IMPLEMENTED` wording: merged source includes the pinned WASM signing core, in-memory IPA transformation, same-session private-key custody, independent verification, and zero-input TVC app-resource resolution. Authentic current-iPhone signing and signed IPA evidence remain unobserved, so source completion must not be promoted into runtime completion.

## Apple account state

Owner-provided iPhone evidence confirms Apple Developer Program Account Holder membership active through `2027-09-09`.

App Store Connect remains externally gated by the observed Terms/account UI defect on the current iPhone. Therefore:

```text
Apple Team API key: NOT_CREATED_OR_NOT_OBSERVED
real Apple credential SKAP custody: NOT_OBSERVED
```

SKAP does not bypass Apple's Terms gate. Once the Team API key can be generated, intended ingress remains current-iPhone local sealing into SKAP, never GitHub Actions secrets.

## Authentic closure sequence

```text
resident dispatcher visits stegbbrowser_tvc_source_promotion
-> exact TVC aef6b6f5 request staged when private-source slot is available
-> existing private-source path/timer consumes request
-> exact immutable TVC source materialized and verified
-> #387 post-hook launches separate transient promotion unit
-> #386 bridge rebinds/restarts same stegtvc-primary-runtime.service
-> primary TVC listener observed on 8765
-> shared SKAP listener observed simultaneously on 8775
-> Apple recipient key + liveness
-> Apple InTr carrier + public health
-> OWNER_INGRESS_READY
-> public-only Site projection
```

No source merge or hosted CI result substitutes for those host observations.

## Remaining sequence

1. Obtain authentic resident source-uptake evidence for the already-merged #1358 request/consumer.
2. Observe the pinned TVC materialization and same-primary-runtime restart receipts.
3. Obtain authentic simultaneous 8765/8775 listener evidence and Apple recipient/liveness/route `OWNER_INGRESS_READY` evidence.
4. Resolve the external Apple Terms/account gate, generate the Team API key, and seal it from the current iPhone directly into SKAP.
5. Observe authentic Device -> KV -> SKAP custody receipts and execute TVC Apple identifier/capability/resource/provisioning operations.
6. Execute and verify authentic same-device IPA signing, TVC Build Upload, TestFlight install, and canonical same-device discovery.
7. Only after working-instance proof continue native StegSocials publication/readback.

## README disposition

The repository `README.md` Canonical Work ingress section was reviewed during this reconciliation. Its architecture remains accurate: registered requests reuse the existing resident consumer, Task Registry does not mint execution authority, and runtime execution still requires authentic downstream evidence. No README text change is required for this state-only reconciliation.

## Current state

`ACTIVE_NOT_SUPERSEDED / CANONICAL_RESIDENT_SOURCE_MERGED_VALIDATED / RESIDENT_EXACT_TVC_SOURCE_REQUEST_MERGED_VALIDATED_1358 / STALE_PR_1206_CLOSED_UNMERGED / IPHONEOS_UNSIGNED_PACKAGE_VALIDATED / GITHUB_APPLE_CREDENTIAL_EXECUTION_RETIRED / TVC_APP_STORE_CONNECT_PROVIDER_AND_SKAP_PATH_MERGED / TVC_PRIMARY_8765_SKAP_8775_COLLISION_REPAIR_MERGED_VALIDATED / VERIFIED_TVC_SOURCE_TO_SAME_PRIMARY_RUNTIME_PROMOTION_MERGED / PRIVATE_SOURCE_POST_PROMOTION_HOOK_MERGED / AUTHENTIC_RESIDENT_SOURCE_PROMOTION_CONSUMPTION_NOT_OBSERVED / AUTHENTIC_TVC_MATERIALIZATION_AND_RESTART_NOT_OBSERVED / LIVE_APPLE_OWNER_INGRESS_READY_NOT_OBSERVED / APPLE_DEVELOPER_MEMBERSHIP_OBSERVED_ACTIVE_THROUGH_2027-09-09 / APP_STORE_CONNECT_TERMS_GATE_BLOCKED / APPLE_TEAM_API_KEY_NOT_CREATED_OR_NOT_OBSERVED / SAME_DEVICE_SIGNING_SOURCE_IMPLEMENTED_RUNTIME_NOT_OBSERVED / AUTHENTIC_CURRENT_IPHONE_INSTALL_LISTENER_DISCOVERY_PENDING`
