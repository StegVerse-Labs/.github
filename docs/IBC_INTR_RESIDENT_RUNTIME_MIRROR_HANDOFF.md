# IBC InTr Resident Runtime Mirror Handoff

Updated: 2026-09-10
Organization: `StegVerse-Labs`
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
COSV ID: `10100000100000`
State: `IBC_LAUNCH_SOURCE_BOUND_TO_CURRENT_IPHONE_SUCCESSOR / SITE_ALLOCATION_TVC_PROVIDER_EXECUTION_SIGNED_DEVICE_DELIVERY_AND_AUTHENTIC_DEVICE_CONSUMPTION_PENDING`

## Purpose

Carry the retained, independently verified Cosmos Hub -> Osmosis acknowledgement evidence through the actual StegOSMobile native iOS build and the existing canonical sovereign resident coordination substrate without creating a second runtime, scheduler, credential lane, transition path, or custody path.

The canonical Task Registry retains `STEGVERSE-CANONICAL-WORK-COORDINATION-001` as the parent identity; the checked source state remains non-activated/non-terminal and no dedicated IBC task is registered. This remains a bounded continuation under that task identity.

Canonical references:

- `docs/CANONICAL_WORK_COORDINATION_SYSTEM_MIRROR_HANDOFF.md`
- `docs/CANONICAL_RESIDENT_CARRIER_MIRROR_HANDOFF.md`
- `StegVerse-Labs/StegOS/docs/IBC_INTR_INTEROPERABILITY_MIRROR_HANDOFF.md`
- `StegVerse-Labs/StegOS/README_IBC_VERIFIED_INTR_ACK_INGRESS.md`

## Established external evidence

The StegOS IBC lineage retains authentic public Cosmos Hub acknowledgement proof material for `transfer/channel-141`, sequence `999999`, independent ICS-23 membership verification, an accepted StegOS verification record, verified classic-IBC evidence, and a canonical `heterogeneous-interop` `ACKNOWLEDGE` transport receipt.

Exact proof/root binding:

```text
producer_chain_id: cosmoshub-4
counterparty_chain_id: osmosis-1
port/channel: transfer/channel-141
sequence: 999999
proof_height: 4-32887306
trusted_app_hash_header_height: 32887307
trusted_app_hash: sha256:2871a37e07449d753776d47966e7dba63605c86f5c50c55acd49e993a082b7db
```

## Native iOS build implementation

StegOS PR #296 merged at:

```text
3b09eb8e6240e67753328494462fbbdfcb04610f
```

`IBCVerifiedACKNativeResident` is compiled directly into the real `StegOSMobile` target through:

```text
mobile/ios/StegOSMobile/MobileServiceActivation.swift
mobile/ios/StegOSMobile.xcodeproj
scheme: StegOSMobile
```

The native implementation validates the retained ICS-23 verification/classic evidence, enforces the exact chain/channel/sequence/proof/root bindings, rejects transition/execution/claim/custody widening, and atomically writes:

```text
Documents/ibc-verified-intr-ack-request-consumption.latest.json
```

PR #296 validation:

```text
iOS Device Package Validation 13 / 34352947552: PASS
StegOS CI 1071 / 34352947574: PASS
iOS Apple Toolchain Validation 58 / 34352947733: PASS
```

## Native launch reachability

StegOS PR #299 merged at:

```text
e810380ff8d991668c192b722c4369e05ff4147f
```

This closes the prior compiled-but-uninvoked gap. `StegOSMobileApp.swift` now calls `IBCVerifiedACKNativeLaunchCoordinator` from the actual SwiftUI application launch surface.

The coordinator:

1. reuses the existing canonical Site node binding stored at `stegos.sv001.resident.activation-binding`;
2. requires its `nodeRef` to match `^SV-NODE-[0-9a-f]{24}$`;
3. embeds immutable exact copies of the already independently verified ICS-23 result and verified classic IBC evidence directly in compiled native source;
4. requires no Python interpreter, GitHub/source fetch, evidence-file import, network fetch, or second machine at runtime;
5. calls the compiled `IBCVerifiedACKNativeResident.consume(...)` implementation directly;
6. writes the native consumption receipt into app-local Documents storage when all checks pass;
7. stops at `WAITING_FOR_CANONICAL_NODE_BINDING` instead of inventing a node identity if the canonical binding is absent.

PR #299 exact head `b1d7a026efc6d5032d8228ccc0029e06ef6955fe` passed:

```text
StegOS CI 1081 / 34354443044: PASS
iOS Device Package Validation 14 / 34354443058: PASS
iOS Apple Toolchain Validation 62 / 34354443157: PASS
```

The exact launch-bound source therefore compiles with Apple tooling and produces a successful unsigned `iphoneos` package.

## Existing resident coordination

`.github` PR #1254 merged at:

```text
ec4b122c46d80109d95e788e51afd73ba04193b1
```

It retains the canonical resident request/dispatcher projection:

```text
control/resident-execution-request.d/ibc-verified-intr-ack-resident-001.json
scripts/consume_ibc_intr_resident_request.py
scripts/dispatch_resident_execution_requests.py
selector: ibc_verified_intr_ack
```

This coordination surface does not replace the native iPhone implementation.

## Zero-input TestFlight delivery handoff

TVC PR #368 merged at:

```text
9923d9f54a1a348a62b916f1329686a035060610
```

It added authenticated, read-only `RESOLVE_APP_RESOURCE_ID` support so App Store Connect resource discovery occurs inside the existing TVC/SKAP provider session rather than through human transcription.

StegOS PR #307 implemented the corresponding zero-input path but became integration-stale after current-iPhone/TVC signer work advanced independently on `main`. Its exact head remained green, but GitHub reported merge conflicts against the later mainline. It was therefore **not** merged.

A current-main reconciliation was created as StegOS PR #330. Exact head:

```text
f15bd9ebf1936b17f10e20f883a9bd543f8067b4
```

Exact-head validation:

```text
StegOS CI #1231 / run 34546094309: PASS
Apple TVC Credential Boundary Validation #10 / run 34546094332: PASS
```

PR #330 merged at:

```text
8bf316765d7467659f3df8e23def23d34b551c5f
```

The merged repository contract establishes zero human-supplied App Store Connect resource ID, TVC `RESOLVE_APP_RESOURCE_ID`, TV/TVC + SKAP credential custody, no GitHub Apple credential access, and no second user-operated machine. StegOS PR #307 is closed as `REPLACED_BY_330`; this does not supersede the Goal Task.

Repository task README evidence was updated on StegOS main at commit:

```text
ba1370c55709aa3efdaf8042d5b4466485a8dc53
```

## Canonical current-iPhone execution surface

The preferred signing execution surface is the already-merged current-iPhone path, not a second Mac/Xcode executor.

```text
execution_surface: CURRENT_USER_IPHONE
executor_class: SAME_DEVICE_BROWSER_WASM_IPA_SIGNER
credential_authority: TV/TVC
App Store Connect credential custody: SKAP_SEALED_TV_TVC_OWNED
private signing key: opaque ephemeral WASM session on current iPhone
private-key export/persistence: forbidden
second user-operated machine: forbidden
```

TVC PR #373 merged at `01fbf9bcb22857db01e421bcc27e6eab6ec7488c` and exact-head Current iPhone Provider CORS Validation run `34398658506` passed, allowing only `https://stegverse.org` to call the canonical TVC provider route without consumer credentials.

## Exact Site successor binding

The canonical Site allocator already has a distinct task for publishing the current-iPhone TestFlight successor:

```text
allocator task: TASK-2026-0010
execution surface: CURRENT_USER_IPHONE
release surface: site:current-iphone-testflight-static-bootstrap
status in portable package: queued
fresh allocator claim/fence required: true
mutation before fresh claim: false
```

This IBC trajectory must reuse that allocation and must not create a competing Site claim.

The exact successor package is:

```text
StegVerse-Labs/StegOS/release/current-iphone-site-projection/successors/current-iphone-testflight-static-bootstrap.json
successor_id: STEGOS-CURRENT-IPHONE-TESTFLIGHT-STATIC-BOOTSTRAP-001
asset_package_commit: 57f32a9e8b9dfbc70e66e0df3cb7de419fc0701b
unsigned IPA source commit: 32115e32d701e783af2c2659a900e4bc90460fd2
unsigned IPA sha256: 557d559082bdefca5fcc69c86f342d8cc035c2d803d154de5ed45b5677f80c35
unsigned IPA bytes: 389564
WASM sha256: 699dc3054788d779ba7920e332c661ef7eac001156f93ab7b1fe1b64ee5a4b93
```

Git comparison proves the unsigned IPA source commit `32115e32...` is 49 commits ahead of IBC launch-reachability merge `e810380f...` with `behind_by=0`. Therefore the exact successor IPA is descendant source containing the merged IBC launch coordinator; no separate IBC-specific IPA build is required before signing.

The Site portable allocator package independently names `TASK-2026-0010` as the immediate target and binds the same unsigned IPA SHA-256. The current Site main does not yet contain `stegos-bootstrap/current-iphone-testflight.html`, so publication/runtime must not be claimed until the allocator trajectory completes its fresh claim/fence and projection.

## TVC provider runtime and credential boundary

TVC source for the App Store Connect class, SKAP resolver, provider-operation broker, current-iPhone CORS exposure, resource resolution, provisioning, and native Build Upload is merged/validated.

Authentic provider execution still requires current TVC runtime/credential evidence. The TVC App Store Connect handoff currently records:

```text
authentic sovereign-host execution of current TVC source: NOT_OBSERVED
live Apple recipient/route projection: NOT_OBSERVED
real Apple credential SKAP custody: NOT_OBSERVED
provider-backed app_store_connect_app_id: NOT_OBSERVED
TestFlight upload through TVC: NOT_OBSERVED
```

It also records an external Apple account condition: App Store Connect Terms acceptance was not usable on the current iPhone at the last observation, so no real Team API key is claimed created or admitted to SKAP. This condition does not invalidate the completed source work; it gates authentic provider execution and credential custody.

## Current evidence boundary

Authentically established:

```text
authentic Cosmos Hub ACK captured: true
independent ICS-23 proof verification: true
verified StegOS classic evidence projection: true
canonical workflow ACK ingress: true
native iOS implementation compiled into StegOSMobile: true
native application-launch invocation compiled into StegOSMobile: true
exact retained verification/evidence embedded in native build: true
unsigned iphoneos package successfully built with launch path: true
canonical resident coordination integration merged: true
zero-input TestFlight handoff contract merged: true
TVC App Store Connect resource-resolution contract merged: true
current-iPhone WASM signing path merged: true
current-iPhone TVC provider client/CORS path merged and validated: true
exact Site successor package contains descendant IBC launch source: true
TASK-2026-0010 is canonical Site projection target: true
```

Not yet authentically established:

```text
TASK-2026-0010 fresh allocator claim/fence: pending in its owner trajectory
Site publication of current-iPhone TestFlight successor: pending
TVC current provider runtime epoch: pending
real Apple credential SKAP custody: pending
TVC resident RESOLVE_APP_RESOURCE_ID execution: pending
Apple App Store Connect resource ID returned by provider: pending
current-iPhone signing execution: pending
TVC Build Upload execution: pending
signed/TestFlight delivery of the launch-bound build: pending
physical iPhone execution of the launch-bound IBC consumer: pending
app-local RESIDENT_INTR_ACK_CONSUMED receipt from physical iPhone: pending
original_ibc_packet_relay_observed: false
transition_admission_observed: false
application_execution_observed: false
workercoordinator_claim_fence_observed: false
credential_minted: false
custody_result_minted: false
```

## Next work

1. allow the existing `TASK-2026-0010` owner trajectory to obtain the fresh allocator claim/fence and project the exact successor package; do not create a competing claim from this task;
2. once projected, use the exact current-iPhone successor bound above rather than rebuilding an IBC-specific signing package;
3. independently continue TVC runtime evidence work: materialize/observe the canonical current TVC provider runtime and current Apple recipient/route epoch without introducing Render or a second provider broker;
4. resolve the external Apple Terms/account condition and admit the real Team API credential through current-iPhone -> KV -> SKAP only when Apple exposes a usable credential-creation path;
5. execute TVC `RESOLVE_APP_RESOURCE_ID`, provisioning, current-iPhone WASM signing, exact signed-IPA verification and TVC Build Upload;
6. install/open the resulting exact build on the bound current iPhone;
7. allow app launch to consume the embedded verified IBC evidence using the already-established canonical Site node binding;
8. inspect `Documents/ibc-verified-intr-ack-request-consumption.latest.json`;
9. retain/reconcile that exact physical-device receipt through the applicable runtime evidence / Master Records path;
10. advance only predicates directly proven by authentic receipts.

No separate evidence-file placement or IBC-specific rebuild is required. The canonical current-iPhone successor already contains the IBC launch-bound source.

## Human action

None required at this moment for this IBC coordination lane. The separate Apple account/Terms condition may later require owner action in App Store Connect; when that UI becomes actionable, the exact step is to accept the applicable Apple terms, create the Team API key, and immediately use the current-iPhone SKAP ingress without placing the `.p8` in GitHub, chat, logs, or artifacts.
