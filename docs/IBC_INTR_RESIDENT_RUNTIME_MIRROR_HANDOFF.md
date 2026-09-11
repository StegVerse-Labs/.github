# IBC InTr Resident Runtime Mirror Handoff

Updated: 2026-09-10
Organization: `StegVerse-Labs`
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
COSV ID: `10100000100000`
State: `ZERO_INPUT_TESTFLIGHT_HANDOFF_MERGED_VALIDATED / TVC_PROVIDER_EXECUTION_SIGNED_DEVICE_DELIVERY_AND_AUTHENTIC_DEVICE_CONSUMPTION_PENDING`

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

The merged path now establishes:

```text
manual workflow-dispatch inputs: 0
manual App Store Connect app-resource ID input: forbidden
App Store Connect resource discovery: TVC RESOLVE_APP_RESOURCE_ID
canonical bundle: org.stegverse.stegosmobile
Apple credential authority: TV/TVC
Apple credential custody: SKAP_SEALED_TV_TVC_OWNED
GitHub Actions Apple credential access: false
GitHub Actions signing private-key custody: false
second user-operated machine: forbidden
```

StegOS PR #307 is closed as `REPLACED_BY_330`; this does not supersede the Goal Task.

Repository task README evidence was updated on StegOS main at commit:

```text
ba1370c55709aa3efdaf8042d5b4466485a8dc53
```

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
zero-input TestFlight signing handoff merged: true
TVC App Store Connect resource-resolution contract merged: true
exact zero-input reconciliation CI: PASS
```

Not yet authentically established:

```text
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

1. execute the merged zero-input `ios-signed-testflight-build.yml` handoff without supplying an App Store Connect app ID;
2. retain the exact generated unsigned-artifact bindings and TVC `RESOLVE_APP_RESOURCE_ID` request;
3. carry that request into the existing authenticated TVC/SKAP App Store Connect provider session;
4. observe authentic TVC resource-resolution evidence and only then continue provisioning/signing/Build Upload;
5. install/open the resulting exact build on the bound current iPhone;
6. allow app launch to consume the embedded verified IBC evidence using the already-established canonical Site node binding;
7. inspect `Documents/ibc-verified-intr-ack-request-consumption.latest.json`;
8. retain/reconcile that exact physical-device receipt through the applicable runtime evidence / Master Records path;
9. advance only predicates directly proven by authentic receipts.

No separate evidence-file placement step remains: the verified IBC evidence inputs are compiled into the same native app build that executes them.

## Human action

None currently required for repository/source integration. Any later Apple/TestFlight interaction or current-iPhone installation step is not to be claimed until the corresponding provider/device evidence exists.
