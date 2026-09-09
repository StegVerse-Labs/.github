# IBC InTr Resident Runtime Mirror Handoff

Updated: 2026-09-09
Organization: `StegVerse-Labs`
Repository: `StegVerse-Labs/.github`
Goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
State: `RESIDENT_CONSUMER_SOURCE_MERGED_VALIDATED / AUTHENTIC_RESIDENT_CONSUMPTION_PENDING`

## Purpose

Carry the already-retained, independently verified Cosmos Hub -> Osmosis acknowledgement evidence through the existing canonical sovereign resident WorkerCoordinator/dispatcher substrate without creating a second runtime, scheduler, credential lane, transition path, or custody path.

## Canonical parents

- `docs/CANONICAL_WORK_COORDINATION_SYSTEM_MIRROR_HANDOFF.md`
- `docs/CANONICAL_RESIDENT_CARRIER_MIRROR_HANDOFF.md`
- `StegVerse-Labs/StegOS/docs/IBC_INTR_INTEROPERABILITY_MIRROR_HANDOFF.md`

The canonical Task Registry remains generation 17 with `STEGVERSE-CANONICAL-WORK-COORDINATION-001` in `PROPOSED` state. No dedicated IBC task is registered. This resident experiment remains a bounded continuation under that task identity.

## Merged StegOS dependency

StegOS PR #295 merged at:

```text
ca45fec7c0c39a86dbbd6f027d3b68688295c3d7
```

The verified ACK materializer now exposes only these explicit execution-context classifications:

```text
WORKFLOW_EXECUTED_CANONICAL_INTR_TRANSPORT_CONFORMANCE_RECEIPT
SOVEREIGN_RESIDENT_EXECUTED_CANONICAL_INTR_TRANSPORT_RECEIPT
```

The workflow class remains the default. Resident dispatch must explicitly select the resident class and write output into the resident runtime tree. Arbitrary observation classes fail closed.

## Merged resident source

`.github` PR #1254 merged at:

```text
ec4b122c46d80109d95e788e51afd73ba04193b1
```

Merged resident source:

```text
control/resident-execution-request.d/ibc-verified-intr-ack-resident-001.json
scripts/consume_ibc_intr_resident_request.py
scripts/dispatch_resident_execution_requests.py
scripts/refresh_sovereign_worker_runtime_source.py
scripts/refresh_and_dispatch_resident_requests.py
tests/test_ibc_intr_resident_consumer.py
README_IBC_INTR_RESIDENT_RUNTIME.md
```

Canonical dispatcher selector:

```text
ibc_verified_intr_ack
```

The request is propagated by the existing static `control/resident-execution-request.d/` refresh. The consumer script is included in the local-only source refresh. The targeted one-shot refresh-and-dispatch bridge also admits `ibc_verified_intr_ack` without visiting unrelated work.

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

## Final-head validation evidence

The exact final PR #1254 head `f921f504e26ca3b18cdc0f0d6179bee168c58462` passed all triggered validation lanes before merge:

```text
Validate organization control plane - No GitHub Token Authority
run: 34332523888
run_number: 2597
result: PASS

Deterministic Repository Suite - Diagnostic Evidence Only
run: 34332522996
run_number: 136
result: PASS

Heartbeat Worker Project - Validation Only / No GitHub Token Authority
run: 34332524531
run_number: 2880
result: PASS

Cross-Framework Current-Basis Resident Request Validation (Non-Authorizing)
run: 34332523203
run_number: 279
result: PASS

validate-deepseek-resident
run: 34332524532
run_number: 78
result: PASS

Workspace DEVICE_KV Validation Only
run: 34332523461
run_number: 227
result: PASS
```

The Heartbeat lane compiled runtime/workers/scripts, parsed canonical JSON, validated executable handoffs/runtime surfaces, and passed the complete deterministic repository test suite. This is source/control validation only, not resident runtime execution evidence.

## Existing event-driven bridge

The already-existing rootless local source-refresh watcher monitors the canonical local source tree, including `control/resident-execution-request.d/`. On a local source refresh it immediately runs the generic resident dispatcher. It performs no network source fetch and does not create another scheduler, heartbeat, or runtime.

Therefore no additional IBC-specific timer/runtime is required. Once canonical `.github` source is materialized into an active sovereign resident source tree, the existing refresh/dispatch path can visit `ibc_verified_intr_ack`.

## Post-merge runtime observation

Immediately after PR #1254 merged, canonical GitHub `main` was checked for:

```text
receipts/sovereign-host/ibc-verified-intr-ack-request-consumption.latest.json
receipts/sovereign-host/ibc-verified-intr-ack-transport.latest.json
receipts/sovereign-host/resident-request-dispatch.latest.json
```

All three were **NOT OBSERVED** on canonical GitHub `main` at that check.

This does not prove that the resident runtime is absent; resident receipts are first written to the sovereign runtime tree and require their own retention/custody/projection path before appearing in canonical GitHub state. No local resident execution is inferred from source merge or GitHub absence.

## Evidence boundaries

Authentically established:

```text
resident consumer source merged: true
resident consumer source validated: true
resident request registered: true
canonical dispatcher registered: true
local source refresh propagation registered: true
targeted refresh-and-dispatch selector registered: true
```

Not yet authentically established:

```text
resident_runtime_execution_observed: false / pending authentic receipt
original_ibc_packet_relay_observed: false
transition_admission_observed: false
application_execution_observed: false
workercoordinator_claim_fence_observed: false
credential_minted: false
custody_result_minted: false
```

A successful authentic resident consumption receipt may establish only the resident execution of the verified external ACK through the canonical StegOS InTr ingress source. Original IBC relay, transition, application execution, claim/fence, credentials, and Master Records custody remain independently gated.

## Next work

1. allow the existing local-only source-refresh/dispatcher substrate to materialize and visit the merged request on an actual sovereign resident;
2. inspect `receipts/sovereign-host/ibc-verified-intr-ack-request-consumption.latest.json` when authentic runtime evidence becomes available;
3. advance `resident_runtime_execution_observed` only if the receipt reports `RESIDENT_INTR_ACK_CONSUMED` with `resident_runtime_execution_observed=true`;
4. retain/reconcile that receipt through the applicable Master Records/runtime-evidence path;
5. leave original packet relay, transition, application execution, claim/fence, credential, and custody predicates unchanged unless separately observed.

## Human action

None currently required.
