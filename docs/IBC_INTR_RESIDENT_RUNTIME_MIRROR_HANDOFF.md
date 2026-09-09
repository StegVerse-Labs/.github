# IBC InTr Resident Runtime Mirror Handoff

Updated: 2026-09-09
Organization: `StegVerse-Labs`
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
State: `RESIDENT_CONSUMER_SOURCE_COMPLETE / VALIDATION_PENDING / AUTHENTIC_RESIDENT_CONSUMPTION_PENDING`

## Purpose

Carry the already-retained, independently verified Cosmos Hub -> Osmosis acknowledgement evidence through the existing canonical sovereign resident WorkerCoordinator/dispatcher substrate without creating a second runtime, scheduler, credential lane, transition path, or custody path.

## Canonical parents

- `docs/CANONICAL_WORK_COORDINATION_SYSTEM_MIRROR_HANDOFF.md`
- `docs/CANONICAL_RESIDENT_CARRIER_MIRROR_HANDOFF.md`
- `StegVerse-Labs/StegOS/docs/IBC_INTR_INTEROPERABILITY_MIRROR_HANDOFF.md`

The canonical Task Registry remains generation 17 with `STEGVERSE-CANONICAL-WORK-COORDINATION-001` in `PROPOSED` state. No dedicated IBC task is registered. This resident experiment is therefore a bounded continuation under that task identity.

## Established StegOS dependency

StegOS PR #295 merged at:

```text
ca45fec7c0c39a86dbbd6f027d3b68688295c3d7
```

That merge makes the verified ACK materializer execution context explicit and fail-closed. The same canonical source now supports only these observation classes:

```text
WORKFLOW_EXECUTED_CANONICAL_INTR_TRANSPORT_CONFORMANCE_RECEIPT
SOVEREIGN_RESIDENT_EXECUTED_CANONICAL_INTR_TRANSPORT_RECEIPT
```

The workflow class remains the default. Resident dispatch must explicitly select the resident class and supply an output path in the resident runtime tree. Arbitrary observation classes fail closed.

## Resident source now implemented

```text
control/resident-execution-request.d/ibc-verified-intr-ack-resident-001.json
scripts/consume_ibc_intr_resident_request.py
scripts/dispatch_resident_execution_requests.py
scripts/refresh_sovereign_worker_runtime_source.py
scripts/refresh_and_dispatch_resident_requests.py
tests/test_ibc_intr_resident_consumer.py
README_IBC_INTR_RESIDENT_RUNTIME.md
```

The canonical dispatcher selector is:

```text
ibc_verified_intr_ack
```

The local-only source refresher now copies the consumer script, while `control/resident-execution-request.d/` already propagates the request as a static control directory. The targeted refresh-and-dispatch bridge explicitly allows only this registered selector when requested.

## Resident experiment contract

The resident consumer:

1. executes only through the existing canonical dispatcher substrate;
2. requires `STEGVERSE_SOVEREIGN_NODE` before resident execution can be claimed;
3. requires a locally materialized StegOS root via `STEGVERSE_STEGOS_ROOT`;
4. performs no GitHub/source/network fetch during resident dispatch;
5. verifies the local retained ICS-23 result is accepted and proof-verified;
6. verifies the local classic evidence preserves transition/execution/custody false flags;
7. executes canonical StegOS `ACKNOWLEDGE` ingress with `SOVEREIGN_RESIDENT_EXECUTED_CANONICAL_INTR_TRANSPORT_RECEIPT`;
8. writes the inner transport artifact to `receipts/sovereign-host/ibc-verified-intr-ack-transport.latest.json`;
9. writes the task-specific consumption receipt to `receipts/sovereign-host/ibc-verified-intr-ack-request-consumption.latest.json`;
10. preserves `TV/TVC` credential authority and `NONE` GitHub-token runtime authority.

Without `STEGVERSE_SOVEREIGN_NODE`, the consumer returns:

```text
SOVEREIGN_NODE_MARKER_REQUIRED
resident_runtime_execution_observed: false
runtime_execution_attempted: false
```

This prevents CI/source validation from manufacturing resident-runtime evidence.

## Evidence boundaries

A successful authentic resident consumption receipt may establish:

```text
resident_runtime_execution_observed: true
```

for the local sovereign execution of the verified external ACK through the canonical StegOS InTr ingress source.

It still does not establish or mint:

```text
original IBC packet relay
transition admission
application execution
WorkerCoordinator claim/fence
credentials
Master Records custody/reconstruction
```

Those predicates remain separately gated and false unless their own evidence appears.

## Validation posture

Source implementation is complete on `feature/ibc-intr-resident-consumer`. Deterministic tests cover both the fail-closed nonresident case and successful sovereign-context result validation, plus dispatcher, local-source refresh, and targeted bridge wiring.

Source/CI/merge remain non-runtime evidence. Authentic resident completion requires the canonical sovereign dispatcher to consume the request on an actual resident runtime after the source is merged and locally refreshed.

## Next work

1. validate and merge the `.github` resident consumer slice;
2. locally refresh canonical `.github` source into the existing sovereign resident runtime;
3. targeted-dispatch `ibc_verified_intr_ack`;
4. retain and inspect the task-specific sovereign-host receipt;
5. only then advance the resident-runtime predicate, while leaving original packet relay, transition, execution, claim/fence, credential, and custody predicates unchanged unless separately observed.

## Human action

None currently required.
