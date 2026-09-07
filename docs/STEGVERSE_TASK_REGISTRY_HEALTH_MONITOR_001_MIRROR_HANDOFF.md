# StegVerse Task Registry Health Monitor Mirror Handoff

Status: ACTIVE / CHECKED_OUT
Repository: `StegVerse-Labs/.github`
Task ID: `STEGVERSE-TASK-REGISTRY-HEALTH-MONITOR-001`
COSV profile: `task.v1`
COSV vector: `20010000100000`

## Goal

Provide a canonical monitor that:

1. reports task counts by monitor posture: ACTIVE, INACTIVE, COMPLETED, RETIRED, SUPERSEDED, INVALID;
2. reviews every checked-out task for worker-return symptoms that may not yet be reflected in the task registry;
3. reconciles expected worker expiry/history-return obligations against Master Records observations;
4. uses retry counters as resilience/diagnostic signals but not as sole proof of failure;
5. derives a deduplicated StegHealth recovery task when evidence shows RETURN_OVERDUE, WORKER_NONREPORT, or a task-at-risk reconciliation failure;
6. reports findings under this Task ID + COSV pair.

## Canonical semantics

`INACTIVE` is a monitor reporting posture, not a lifecycle state.

Canonical lifecycle remains:

```text
ACTIVE
COMPLETED
RETIRED
SUPERSEDED
INVALID
```

`RETIRED` remains terminal and cannot be reopened by this monitor. Recovery related to a retired task requires a new Task ID linked by provenance.

## Worker-return model

Normal loop:

```text
task claimed
→ worker executes / bounded retries
→ worker returns work history/evidence
→ worker expires
→ Master Records records returned history
→ task continuation/closure reconstructs from canonical evidence
```

Failure detection is based on a bound expected worker-return obligation whose matching Master Records return is absent after the governed expectation. Silence without a bound expectation is not failure proof.

## StegHealth recovery derivation

Where recovery is warranted, the monitor must generate a unique StegHealth recovery-task specification preserving the source Task ID/COSV, root correlation, worker-return obligation, claim/execution reference, Master Records subject binding, and failure evidence. Equivalent existing recovery work must be reused instead of duplicated.

## Current state

- lifecycle: ACTIVE
- checkout: CHECKED_OUT
- report_complete: false
- recovery_derivation_enabled: true
- terminal: false

## Next admissible work

Implement and execute the registry census + checked-out worker-return reconciliation and persist the first monitor report.
