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
#378       current-main listener/root convergence; validated and merged at 1853cb632ff8cf97deed5b08ec4f0964d1ef4978
#379       Apple SKAP runtime-handoff reconciliation; merged at adb1c48f1b0459c38ed9d519b0a18bc8039de7ef
```

PR #378 fixes two authentic deployment blockers that source review exposed:

```text
TVC primary provider-operation runtime: 127.0.0.1:8765
shared SKAP ciphertext ingress:          127.0.0.1:8775
Coinbase SKAP local upstream:            http://127.0.0.1:8775
App Store Connect SKAP local upstream:   http://127.0.0.1:8775
```

The shared SKAP ingress and tunnel systemd units now render from the active TVC `@REPO_ROOT@`; `/opt/stegverse/TVC` is no longer the fixed runtime assumption for those services. Current Apple validation and the newer POST_RETURN SKAP lane both passed against the #378 head.

## Device/KV/SKAP convergence

StegOS #326 and #327 now compose and verify the full four-leg Universal InTr chain:

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

## Current sovereign-runtime blocker

TVC already contains a released primary-runtime installer that restarts the same `stegtvc-primary-runtime.service` so it imports the current local TVC checkout. The existing private-source resident path can also materialize and verify an exact immutable TVC checkout.

Those two capabilities are not yet connected by an observed resident operation. Current authentic evidence does not establish that the sovereign host has materialized TVC main containing #378/#379 and restarted the existing primary service from that source.

This is now the first SKAP runtime closure target:

```text
resident exact-source request for current TVC
-> TVC private-source service materializes and verifies exact immutable TVC commit
-> bounded existing-primary-service source rebind/restart
-> primary TVC listener observed on 8765
-> shared SKAP listener observed simultaneously on 8775
-> Apple recipient key + liveness
-> Apple InTr carrier + public health
-> OWNER_INGRESS_READY
-> public-only Site projection
```

No source merge or hosted CI result substitutes for those host observations.

## Remaining sequence

1. Close the resident exact-TVC-source -> existing-primary-runtime restart handoff without creating a second runtime or requiring a second user-operated machine.
2. Obtain authentic simultaneous 8765/8775 listener evidence and Apple recipient/liveness/route `OWNER_INGRESS_READY` evidence.
3. Resolve the external Apple Terms/account gate, generate the Team API key, and seal it from the current iPhone directly into SKAP.
4. Observe authentic Device -> KV -> SKAP custody receipts and execute TVC Apple identifier/capability/resource/provisioning operations.
5. Complete same-device cryptographic IPA signing, TVC Build Upload, TestFlight install and canonical same-device discovery.
6. Only after working-instance proof continue native StegSocials publication/readback.

## Current state

`ACTIVE_NOT_SUPERSEDED / CANONICAL_RESIDENT_SOURCE_MERGED_VALIDATED / IPHONEOS_UNSIGNED_PACKAGE_VALIDATED / GITHUB_APPLE_CREDENTIAL_EXECUTION_RETIRED / TVC_APP_STORE_CONNECT_PROVIDER_AND_SKAP_PATH_MERGED / TVC_PRIMARY_8765_SKAP_8775_COLLISION_REPAIR_MERGED_VALIDATED / ACTIVE_TVC_REPO_ROOT_RENDERING_MERGED_VALIDATED / STEGOS_DEVICE_KV_SKAP_FOUR_LEG_CHAIN_MERGED_VALIDATED / APPLE_DEVELOPER_MEMBERSHIP_OBSERVED_ACTIVE_THROUGH_2027-09-09 / APP_STORE_CONNECT_TERMS_GATE_BLOCKED / APPLE_TEAM_API_KEY_NOT_CREATED_OR_NOT_OBSERVED / AUTHENTIC_CURRENT_TVC_SOURCE_RESTART_NOT_OBSERVED / LIVE_APPLE_OWNER_INGRESS_READY_NOT_OBSERVED / SAME_DEVICE_CRYPTOGRAPHIC_SIGNING_ENGINE_REMAINS_DOWNSTREAM / AUTHENTIC_CURRENT_IPHONE_INSTALL_LISTENER_DISCOVERY_PENDING`
