# StegBrowser Ephemeral Runtime Binding Mirror Handoff

Updated: 2026-09-10

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

Merged TVC implementation now includes:

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

PR #378 fixes the resident listener collision:

```text
TVC primary provider-operation runtime: 127.0.0.1:8765
shared SKAP ciphertext ingress:          127.0.0.1:8775
Coinbase SKAP local upstream:            http://127.0.0.1:8775
App Store Connect SKAP local upstream:   http://127.0.0.1:8775
```

The shared SKAP ingress and tunnel systemd units render from the active TVC `@REPO_ROOT@`; `/opt/stegverse/TVC` is no longer the fixed runtime assumption for those services.

## Exact TVC source promotion path

TVC #386 and #387 close the source-level gap between exact source materialization and the already-existing primary service.

The exact source promotion bridge requires an immutable TVC materialization under `/var/lib/stegverse/private-source-read/materialized`, exact `git HEAD` equality, and a matching private-source execution receipt. It then invokes that materialization's existing `install_tvc_primary_runtime_service.py --activate`, which re-renders and restarts the same fixed `stegtvc-primary-runtime.service`. No second primary runtime is created.

The private-source oneshot now has a post-materialization dispatcher. It is a no-op for unrelated reads. For an exact `StegVerse-Labs/TVC` IMMUTABLE_COMMIT receipt whose `consumer_task` is this Goal Task, it launches the promotion bridge in a separate transient systemd oneshot so restarting the primary service cannot terminate the promotion transaction before its receipt is written.

The immutable TVC source selected for first resident promotion is:

```text
repository: StegVerse-Labs/TVC
exact SHA: aef6b6f5dc99d2a531718ca475d20858ae8e68a6
contains: #386 + #387 promotion chain
materialization id: stegbrowser-tvc-runtime-aef6b6f5
```

## Resident request source

The canonical resident control plane now carries a dedicated request and consumer for this exact source promotion:

```text
request: control/resident-execution-request.d/stegbrowser-tvc-source-promotion-001.json
consumer: control/resident-execution-request.d/consume-stegbrowser-tvc-source-promotion.py
dispatcher selector: stegbrowser_tvc_source_promotion
private-source handoff: <runtime>/tvc-handoff/private-source-request.json
```

The request consumer performs no network source fetch and starts no system service. It stages only the exact TVC IMMUTABLE_COMMIT request. If the single private-source handoff slot is occupied by another task, it records `HANDOFF_READY` as its outcome and does not overwrite the other task. If the existing request belongs to the same StegBrowser/TVC source identity, it may restage only the exact pinned coordinate.

Both the request and consumer live under the already-materialized `control/resident-execution-request.d` directory, so no new source-refresh directory or transport is introduced.

## Device/KV/SKAP convergence

StegOS #326 and #327 compose and verify the full four-leg Universal InTr chain:

```text
DEVICE_SYSTEM -> KV -> SKAP_VAULT -> KV -> DEVICE_SYSTEM
```

The verifier requires exact receipt-hash chaining and current Interlock/InTr posture binding. These are source/validation capabilities; authentic Apple credential custody has not yet been observed.

## Current-iPhone signing

The same-device signing executor contract/orchestrator remains merged. The actual StegOS-owned same-device cryptographic transformation engine remains a separate downstream implementation requirement before a real signed IPA can be produced without a second user-operated machine.

## Apple account state

Owner-provided iPhone evidence confirms Apple Developer Program Account Holder membership active through `2027-09-09`.

App Store Connect is currently blocked by an Apple Terms/account UI defect: the Terms checkbox can be selected, but no usable acceptance control is rendered on the current iPhone across multiple browsers. Therefore:

```text
Apple Team API key: NOT_CREATED_OR_NOT_OBSERVED
real Apple credential SKAP custody: NOT_OBSERVED
```

SKAP does not bypass Apple's Terms gate. Once the Team API key can be generated, the intended ingress is the current-iPhone SKAP page, not GitHub Actions secrets.

## Remaining bootstrap boundary

The exact source request, private-source materializer, post-materialization promotion hook and same-service restart bridge now exist in source. Authentic evidence still does not establish that the sovereign resident has refreshed to this `.github` request/consumer set or executed the pinned TVC materialization.

The existing TVC self-heal `run_once()` re-installs the private-source watcher family on every admitted sovereign-runtime locator cycle. Therefore once its TVC control source contains #387, it can refresh the installed private-source unit without requiring a primary-process restart first. Source merge alone does not prove that host control tree has advanced.

Current authentic closure sequence:

```text
resident dispatcher visits stegbrowser_tvc_source_promotion
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

1. Validate and merge the resident exact-TVC-source request/consumer projection.
2. Resolve the remaining authentic resident source-uptake boundary and observe the pinned TVC materialization plus same-service restart receipts.
3. Obtain authentic simultaneous 8765/8775 listener evidence and Apple recipient/liveness/route `OWNER_INGRESS_READY` evidence.
4. Resolve the external Apple Terms/account gate, generate the Team API key, and seal it from the current iPhone directly into SKAP.
5. Observe authentic Device -> KV -> SKAP custody receipts and execute TVC Apple identifier/capability/resource/provisioning operations.
6. Complete same-device cryptographic IPA signing, TVC Build Upload, TestFlight install and canonical same-device discovery.
7. Only after working-instance proof continue native StegSocials publication/readback.

## Current state

`ACTIVE_NOT_SUPERSEDED / CANONICAL_RESIDENT_SOURCE_MERGED_VALIDATED / IPHONEOS_UNSIGNED_PACKAGE_VALIDATED / GITHUB_APPLE_CREDENTIAL_EXECUTION_RETIRED / TVC_APP_STORE_CONNECT_PROVIDER_AND_SKAP_PATH_MERGED / TVC_PRIMARY_8765_SKAP_8775_COLLISION_REPAIR_MERGED_VALIDATED / VERIFIED_TVC_SOURCE_TO_SAME_PRIMARY_RUNTIME_PROMOTION_MERGED / PRIVATE_SOURCE_POST_PROMOTION_HOOK_MERGED / RESIDENT_EXACT_TVC_SOURCE_REQUEST_IMPLEMENTED_VALIDATION_PENDING / APPLE_DEVELOPER_MEMBERSHIP_OBSERVED_ACTIVE_THROUGH_2027-09-09 / APP_STORE_CONNECT_TERMS_GATE_BLOCKED / APPLE_TEAM_API_KEY_NOT_CREATED_OR_NOT_OBSERVED / AUTHENTIC_TVC_MATERIALIZATION_AND_RESTART_NOT_OBSERVED / LIVE_APPLE_OWNER_INGRESS_READY_NOT_OBSERVED / SAME_DEVICE_CRYPTOGRAPHIC_SIGNING_ENGINE_REMAINS_DOWNSTREAM / AUTHENTIC_CURRENT_IPHONE_INSTALL_LISTENER_DISCOVERY_PENDING`
