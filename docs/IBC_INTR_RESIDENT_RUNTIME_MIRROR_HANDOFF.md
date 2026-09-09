# IBC InTr Resident Runtime Mirror Handoff

Updated: 2026-09-09
Organization: `StegVerse-Labs`
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
State: `NATIVE_IOS_BUILD_MERGED_VALIDATED / AUTHENTIC_DEVICE_CONSUMPTION_PENDING`

## Purpose

Carry the retained, independently verified Cosmos Hub -> Osmosis acknowledgement evidence through the actual StegOSMobile native iOS build and the existing canonical sovereign resident coordination substrate without creating a second runtime, scheduler, credential lane, transition path, or custody path.

## Canonical parent

The canonical Task Registry remains generation 17 with `STEGVERSE-CANONICAL-WORK-COORDINATION-001` in `PROPOSED` state. No dedicated IBC task is registered. This is a bounded continuation under that task identity.

Canonical references:

- `docs/CANONICAL_WORK_COORDINATION_SYSTEM_MIRROR_HANDOFF.md`
- `docs/CANONICAL_RESIDENT_CARRIER_MIRROR_HANDOFF.md`
- `StegVerse-Labs/StegOS/docs/IBC_INTR_INTEROPERABILITY_MIRROR_HANDOFF.md`

## Established external evidence

The StegOS IBC lineage already retains:

- authentic public Cosmos Hub acknowledgement proof material for `transfer/channel-141`, sequence `999999`;
- independent ICS-23 membership verification;
- accepted StegOS verification record;
- verified classic-IBC evidence projection;
- canonical `heterogeneous-interop` `ACKNOWLEDGE` transport receipt.

Exact trusted proof/root binding:

```text
producer_chain_id: cosmoshub-4
counterparty_chain_id: osmosis-1
port/channel: transfer/channel-141
sequence: 999999
proof_height: 4-32887306
trusted_app_hash_header_height: 32887307
trusted_app_hash: sha256:2871a37e07449d753776d47966e7dba63605c86f5c50c55acd49e993a082b7db
```

## Native iOS build correction

The prior Python/control-plane resident consumer remains useful for canonical resident coordination, but it is no longer treated as the build implementation.

StegOS PR #296 merged at:

```text
3b09eb8e6240e67753328494462fbbdfcb04610f
```

The actual build implementation is compiled directly into:

```text
mobile/ios/StegOSMobile/MobileServiceActivation.swift
mobile/ios/StegOSMobile.xcodeproj
scheme: StegOSMobile
```

`MobileServiceActivation.swift` is an explicit source member of the native iPhone target. The merged `IBCVerifiedACKNativeResident` implementation therefore compiles into the app itself rather than existing as detached source or scaffolding.

The native implementation:

1. reads `ack-sequence-999999.ics23-verification.json` and `ack-sequence-999999.verified-classic-evidence.json` from app-local Documents storage;
2. requires `result=accepted` and `proof_verified=true`;
3. requires the exact Cosmos Hub/Osmosis chain, channel, sequence, proof height, trusted-root height, and trusted app hash listed above;
4. rejects any classic-evidence widening of transition admission, execution, claim/fence, or custody;
5. computes SHA-256 bindings over the exact local verification/evidence bytes;
6. persists `ibc-verified-intr-ack-request-consumption.latest.json` atomically in app-local Documents storage;
7. emits `state=RESIDENT_INTR_ACK_CONSUMED` only after all native checks pass;
8. records `residentRuntimeExecutionObserved=true` while preserving original IBC relay, transition admission, application execution, claim/fence, custody, and credential minting as false.

No Python interpreter is required for this native consumption path.

## Native build validation

Exact PR #296 head `cdec02ffab0fe690841c69e891ea0c2efbf47197` passed:

```text
iOS Device Package Validation
run: 34352947552
run_number: 13
result: PASS

StegOS CI
run: 34352947574
run_number: 1071
result: PASS

iOS Apple Toolchain Validation
run: 34352947733
run_number: 58
result: PASS
```

The Apple toolchain lane compiled `StegOSMobile` and both embedded extensions. The device-package lane built the unsigned `iphoneos` product and produced deterministic unsigned package evidence. These are actual build results, not source-only validation.

## Existing canonical resident coordination

`.github` PR #1254 merged at:

```text
ec4b122c46d80109d95e788e51afd73ba04193b1
```

It registers:

```text
control/resident-execution-request.d/ibc-verified-intr-ack-resident-001.json
scripts/consume_ibc_intr_resident_request.py
scripts/dispatch_resident_execution_requests.py
selector: ibc_verified_intr_ack
```

That path remains the canonical resident coordination/dispatch projection. It does not replace the native iOS build implementation.

## Current evidence boundary

Authentically established:

```text
native iOS implementation compiled into StegOSMobile: true
unsigned iphoneos package built successfully: true
Apple toolchain compilation passed: true
canonical resident request/dispatcher integration merged: true
authentic Cosmos Hub ACK evidence retained and independently verified: true
```

Not yet authentically established:

```text
physical iPhone execution of IBCVerifiedACKNativeResident: pending
app-local ibc-verified-intr-ack-request-consumption.latest.json from physical iPhone: pending
original_ibc_packet_relay_observed: false
transition_admission_observed: false
application_execution_observed: false
workercoordinator_claim_fence_observed: false
credential_minted: false
custody_result_minted: false
```

## Next work

1. deliver/install a signed StegOSMobile build on the current iPhone through the existing Apple/TestFlight path;
2. place or materialize the exact retained verification/evidence JSON into StegOSMobile app-local storage through the established StegVerse evidence-delivery path;
3. execute `IBCVerifiedACKNativeResident` on the physical iPhone;
4. inspect the native `ibc-verified-intr-ack-request-consumption.latest.json` receipt;
5. retain/reconcile that exact receipt through the applicable Master Records/runtime-evidence path;
6. advance only the predicates directly proven by that physical-device receipt.

## Human action

None currently required for source/build completion. Physical-device execution remains dependent on the existing signed StegOSMobile/TestFlight delivery path.
