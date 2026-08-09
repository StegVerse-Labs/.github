# All-Organization Heartbeat Federation Mirror Handoff

## Authority

This handoff is subordinate to `docs/ORG_MIRROR_HANDOFF.md`, `StegVerse-Labs/.github#12`, and the existing all-organization response-network owner `StegVerse-Labs/Site#234`.

It is the canonical continuation for expanding the proven single-heartbeat/subsignal/worker/task-registry readiness model across every organization in the current StegVerse organization inventory.

## Goal

```text
goal_id: ALL-ORG-HEARTBEAT-FEDERATION-001
repository: StegVerse-Labs/.github
branch: main
canonical heartbeat owner: StegVerse-Labs/.github#12
canonical response-network owner: StegVerse-Labs/Site#234
organization denominator: 14
scheduler authority: single StegVerse heartbeat
wall-clock scheduler authority: false
transport/subsignal authority effect: false
```

## Canonical state

Machine-readable state is owned by:

```text
control/organization-federation.json
control/organization-task-registry.json
control/heartbeat-subsignals.json#organization_federation
control/worker-registry.json
control/worker-status.json
```

The federation denominator is the 14-organization inventory already established and hosted-validated by Site issue #234. The personal `StegVerse` account is excluded from the organization denominator.

Current federation state before the first federation worker cycle:

```text
registered organizations: 14/14
heartbeat-response verified nodes: 10/14
federated subsignal-ready organizations: 10/14
machine-blocked organizations: 4/14
unassigned organizations: 0/14
```

The four machine-blocked organizations are `AaCT-E`, `ECAT-ICAT-Formal`, `Infrastructure-Continuity-Ventures`, and `Triad-Test`. Each has an explicit release condition and next heartbeat recheck action in both federation registries.

## Readiness dimensions

Every organization is now represented across these dimensions:

```text
heartbeat_response
subsignal
worker
task_registry
evidence
release_condition
next_action
```

`READY` means represented and machine-owned for observation/reconciliation under the canonical heartbeat. It does not grant destination-specific execution authority.

`BLOCKED` means the task remains visible and machine-owned with an explicit release condition. Missing repository/write authority is not converted into success.

## Subsignal integration

`control/heartbeat-subsignals.json` now carries `organization_federation` as a first-class heartbeat subsignal with:

```text
state: ACTIVE_PARTIAL_COVERAGE
organization_count: 14
ready_count: 10
blocked_count: 4
unassigned_count: 0
recheck_policy: ON_EACH_ADMITTED_HEARTBEAT_WHILE_ANY_ORGANIZATION_IS_BLOCKED_OR_CHANGED
progress_rule: ONLY_ADMITTED_STATE_TRANSITIONS_ADVANCE_PROGRESS
authority_effect: false
```

This is a subsignal of the existing heartbeat, not another scheduler or heartbeat plane.

## Heartbeat-owned worker

```text
task: SHWP-ALL-ORG-FEDERATION-001
handoff: handoffs/SHWP-ALL-ORG-FEDERATION-001.json
authorization: authorizations/SHWP-ALL-ORG-FEDERATION-001.json
worker: workers/organization_federation_readiness_worker.py
adapter: process:organization-federation-readiness-v1
capability: bounded_repository_mutation
allowed mutation: receipts/organization-federation/** only
```

The worker validates the 14-organization denominator, rejects unowned/invalid task states, requires explicit release conditions for every blocker, and writes a bounded federation receipt. It has no cross-organization mutation, publication, deployment, custody, or policy authority.

## Existing response-network convergence

The older response network is not duplicated. `StegVerse-Labs/Site#234` remains authoritative for SENT -> RECEIVED -> RESPONDED -> RECOVERED -> REPEAT transport and the MEMORY/ACTION/AWARENESS/AUTHORITY/EVIDENCE/BLOCKER/CAPABILITY/CONTEXT information classes.

This federation layer adds canonical readiness projections for subsignals, workers, and task ownership around that already-validated response mesh.

## Archive condition

This goal is archive-safe only after:

1. the federation worker is actually claimed and executed through the canonical heartbeat;
2. a durable receipt records all 14 organizations, zero unassigned rows, and the current blocked set;
3. worker registry/status records a real claim, fence, worker instance, heartbeat timing, and next transition;
4. remaining blocked organizations are machine-owned with release conditions and require no chat session.

Durable ownership alone is not completion.

## Completion assessment

```text
federation registry: installed
authoritative organization denominator: 14/14
task-registry projection: 14/14
subsignal integration: installed
worker implementation: installed
worker heartbeat activation: pending first federation cycle
unassigned organizations: 0
```
