# IBC InTr Resident Runtime Mirror Handoff

Updated: 2026-09-09
Organization: `StegVerse-Labs`
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
State: `RESIDENT_CONSUMER_SOURCE_VALIDATED / MERGE_PENDING / AUTHENTIC_RESIDENT_CONSUMPTION_PENDING`

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

That merge makes the verified ACK materializer execution context explicit and fail-closed. The same canonical source supports only these observation classes:

```text
WORKFLOW_EXECUTED_CANONICAL_INTR_TRANSPORT_CONFORMANCE_RECEIPT
SOVEREIGN_RESIDENT_EXECUTED_CANONICAL_INTR_TRANSPORT_RECEIPT
```

The workflow class remains the default. Resident dispatch must explicitly select the resident class and supply an output path in the resident runtime tree. Arbitrary observation classes fail closed.

## Resident source implemented

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

The local-only source refresher copies the consumer script, while `control/resident-execution-request.d/` propagates the request as a static control directory. The targeted refresh-and-dispatch bridge explicitly allows only this registered selector when requested.

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

for local sovereign execution of the verified external ACK through the canonical StegOS InTr ingress source.

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

## Validation evidence

The first complete validation cycle on source head `765c7ab8baff0bf55420ca2feabf3de3ae3fd78c` is green:

```text
Validate organization control plane - No GitHub Token Authority
run: 34332308707
run_number: 2596
result: PASS

Deterministic Repository Suite - Diagnostic Evidence Only
run: 34332308717
run_number: 135
result: PASS

Heartbeat Worker Project - Validation Only / No GitHub Token Authority
run: 34332308693
run_number: 2879
result: PASS

Cross-Framework Current-Basis Resident Request Validation (Non-Authorizing)
run: 34332308678
run_number: 278
result: PASS

validate-deepseek-resident
run: 34332308744
run_number: 77
result: PASS

Workspace DEVICE_KV Validation Only
run: 34332308742
run_number: 226
result: PASS
```

The Heartbeat lane compiled runtime/workers/scripts, parsed canonical JSON, validated handoffs and runtime surfaces, and passed the complete deterministic repository test suite. Organization-control and deterministic-diagnostics lanes are also green.

This validation proves source/control consistency only. It is not resident execution evidence.

## Merge gate

PR #1254 may merge only after the exact final handoff-reconciled head repeats the required validation successfully. The handoff reconciliation itself must not inherit the prior head's validation by assumption.

## Next work

1. require organization-control, deterministic-suite, and Heartbeat validation on the exact final head;
2. merge PR #1254 only after those final-head gates pass;
3. locally refresh canonical `.github` source into the existing sovereign resident runtime;
4. targeted-dispatch `ibc_verified_intr_ack`;
5. inspect `receipts/sovereign-host/ibc-verified-intr-ack-request-consumption.latest.json`;
6. advance the resident-runtime predicate only if the authentic receipt reports `RESIDENT_INTR_ACK_CONSUMED` with `resident_runtime_execution_observed=true`;
7. keep original packet relay, transition, application execution, claim/fence, credential, and custody predicates unchanged unless separately observed.

## Human action

None currently required.
