# SV002 Experiment Rerun InTr Execution Mirror Handoff

Status: ACTIVE
Updated: 2026-09-17
Repository: StegVerse-Labs/.github

## Canonical coordination

- Goal Task ID: `STEGVERSE-002-EXPERIMENT-RERUN-001`
- COSV: `50000000107000`
- canonical task record: `data/canonical-task-records/STEGVERSE-002-EXPERIMENT-RERUN-001.json`
- canonical target-org handoff: `StegVerse-002/.github/docs/SELF_CHARACTERIZATION_EXECUTION_SURFACE_MIRROR_HANDOFF.md`
- tracking issue: `#2070`
- root experiment: `STEGVERSE-002-SELF-CHARACTERIZATION-001`

## Purpose

Consume exactly one admitted `SV002:SelfCharacterization` Universal InTr materialization through the already-existing execution order:

```text
registered StegVerseNode write-once outbox
-> shared Universal InTr admission
-> bounded EVENT_EPHEMERAL ESRL lease
-> fresh WorkerCoordinator claim/fence for STEGVERSE-002-EXPERIMENT-RERUN-001
-> exact admitted SDK request
-> existing StegVerse-org organization egress
-> existing StegVerse-002 organization boundary
-> frozen v0.3 target-owned principal
-> target governed egress/response packet
-> existing Master Records custody packet
-> master-records/.github custody + deterministic reconstruction
-> origin organization response consumption
```

The worker must not build a second SDK request. It consumes `sv002_request` from the exact admitted materialization and uses existing organization federation components.

## Authority boundaries

- Node continuity anchors the current-device request.
- Interlock/InTr admits packet movement and transitions.
- ESRL provides one bounded `EVENT_EPHEMERAL` runtime lease.
- WorkerCoordinator alone mints the task claim/fence.
- `StegVerse-002/.github` owns target execution.
- the frozen v0.3 principal remains `StegVerse-002/micro-node-runtime`.
- Master Records owns custody/reconstruction.
- TV/TVC remains credential authority.
- GitHub/CI runtime authority is `NONE`.

Ingress, carrier state, source merge, and the consumer do not mint claim/fence or prove principal execution.

## Same-execution evidence order

The retained evidence chain must correlate one materialization ID, one exact request hash, one Goal/COSV pair, one lease ID, one WorkerCoordinator claim/fence, one target packet ID, one principal RunID, one target egress response packet, one Master Records custody/reconstruction record, and one origin response record.

Predicates may become true only from retained evidence generated in this execution:
`REQUEST_BOUND`, `STEGVERSE_NODE_BOUND_TO_INVOCATION`, `INTERLOCK_BOUND_TO_NODE_AND_MANIFEST`, `INTR_MATERIALIZATION_ADMITTED`, `INVOCATION_SCOPED_LEASE_ESTABLISHED`, `EVENT_EPHEMERAL_RUNTIME_MATERIALIZED`, `EXECUTION_TIME_RUNTIME_IDENTITY_BOUND`, `CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED`, `AUTHENTIC_INTR_INGRESS_OBSERVED`, `T0_CAPTURED`, `PRINCIPAL_EXECUTION_TRANSITIONS_RETAINED`, `EGRESS_EMITTED`, `GOVERNED_RETURN_OBSERVED`, `MASTER_RECORDS_CUSTODY_OBSERVED`, `MASTER_RECORDS_RECONSTRUCTION_PASS`, and `ORIGIN_RETURN_OBSERVED`.

## Prohibited substitutions

No new runtime, scheduler, listener, host, Healer dependency, frozen-corpus prerequisite, generic browser observation principal, alternate authority path, hosted execution, credential-bearing GitHub runtime, or second user-operated device.

`SHWP-SV002-FROZEN-CORPUS-MATERIALIZATION-001` remains adjacent and explicitly non-prerequisite.

## Runtime prerequisites

Only already-local canonical source is eligible. Missing local source does not authorize network checkout; it remains a machine-observable nonterminal condition. The invocation must not ask the user for a second device or manual runtime evidence.

## Current evidence state

Source construction and validation do not promote runtime predicates. Until authentic current-device execution evidence is retained, the canonical task remains ACTIVE and incomplete.
