# IBC InTr Resident Runtime Mirror Handoff

Updated: 2026-09-09
Organization: `StegVerse-Labs`
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
State: `NATIVE_IOS_BUILD_REACHABLE_VALIDATED / SIGNED_DEVICE_DELIVERY_AND_AUTHENTIC_DEVICE_CONSUMPTION_PENDING`

## Purpose

Carry the retained, independently verified Cosmos Hub -> Osmosis acknowledgement evidence through the actual StegOSMobile native iOS build and the existing canonical sovereign resident coordination substrate without creating a second runtime, scheduler, credential lane, transition path, or custody path.

The canonical Task Registry remains generation 17 with `STEGVERSE-CANONICAL-WORK-COORDINATION-001` in `PROPOSED` state. No dedicated IBC task is registered. This remains a bounded continuation under that task identity.

Canonical references:

- `docs/CANONICAL_WORK_COORDINATION_SYSTEM_MIRROR_HANDOFF.md`
- `docs/CANONICAL_RESIDENT_CARRIER_MIRROR_HANDOFF.md`
- `StegVerse-Labs/StegOS/docs/IBC_INTR_INTEROPERABILITY_MIRROR_HANDOFF.md`

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
```

Not yet authentically established:

```text
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

1. carry the exact launch-bound StegOSMobile source through the existing signed/TestFlight build and TVC App Store Connect delivery path;
2. install/open that build on the bound current iPhone;
3. allow app launch to consume the embedded verified evidence using the already-established canonical Site node binding;
4. inspect `Documents/ibc-verified-intr-ack-request-consumption.latest.json`;
5. retain/reconcile that exact physical-device receipt through the applicable runtime evidence / Master Records path;
6. advance only predicates directly proven by that receipt.

No separate evidence-file placement step remains: the verified evidence inputs are now compiled into the same native app build that executes them.

## Human action

None currently required for source/build integration. Physical-device execution depends on completion of the existing signed StegOSMobile/TestFlight delivery path.
