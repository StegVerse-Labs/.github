# Universal Governance ENFORCED Reference Boundary Mirror Handoff

Updated: 2026-08-31
Repository: StegVerse-Labs/.github
Issue: #690
Branch: feature/universal-governance-enforced-reference
Task: SHWP-UNIVERSAL-GOVERNANCE-ENFORCED-REFERENCE-001
State: SOURCE_MERGED_VALIDATED / RESIDENT_EXECUTION_PENDING
Credential authority: TV/TVC
Execution authority: bounded target consequence only after independent target-authority validation
GitHub token runtime authority: NONE
Non-TV/TVC secret/token allowed: false

## Goal

Execute the merged Universal Governance architecture as an authentic sovereign-runtime **reference ENFORCED boundary** using already-local source only.

This task is a reference-boundary runtime proof. It MUST NOT be reported as a real third-party external-system ENFORCED deployment.

## Required runtime chain

```text
resident WorkerCoordinator claim
 -> locally materialized StegCore source
 -> locally materialized Master Records source
 -> native reference action
 -> thin external governance adapter
 -> Universal InTr request
 -> Governance registered profile
 -> StegCore three-layer evaluation
 -> ALLOW / DENY / FAIL-CLOSED
 -> deterministic StegGate target-authority + credential + capability + commit gate
 -> bounded target mutation
 -> consequence observation
 -> canonical consequence evidence
 -> Universal InTr return
 -> Master Records source projection
 -> independent Master Records custody validation
 -> resident receipt
```

## Positive proof

The positive lane must demonstrate:

- exact candidate hash survives native action -> Governance -> consequence;
- request and return InTr chains complete;
- target credential ID/hash/subject binding matches;
- separate target authority reference matches;
- target mutation occurs exactly once;
- consequence observation is true;
- consequence evidence is canonical-hash valid;
- Master Records validation/custody completes;
- no repository writeback or hosted execution authority occurs.

## Bypass negative control

A direct/ungoverned bypass attempt against the bounded target must remain unable to produce the authorized mutation/evidence state.

The final receipt must state both:

```text
reference_enforced_boundary_observed=true
bypass_negative_control_passed=true
real_external_system_enforced_activation=false
```

## Source dependencies

Required local source roots:

```text
StegVerse-Labs/StegCore
master-records/core-lite
```

Source retrieval is separate authority. If exact local source is unavailable, return `HANDOFF_READY` with a source-materialization dependency; do not fetch from GitHub in the worker and do not fabricate receipts.

## Bound-state custody

All target mutation and produced runtime evidence must remain inside the worker's bounded state root.

Permitted bound-state paths:

```text
target/**
evidence/**
receipts/**
master-records/**
```

## Authority invariants

```text
Governance ALLOW != target authority
adapter != execution authority
Interlock/InTr/HB != execution authority
Master Records custody != execution authority
GitHub Actions runtime authority = NONE
credential authority = TV/TVC
repository writeback = false
Continuity minting = false
publication authority = false
```

## Lifecycle

```text
IMPLEMENTED: true
VALIDATED: true
MERGED: true
RESIDENT_ADMITTED: false
REFERENCE_ENFORCED_BOUNDARY_OBSERVED: false
BYPASS_NEGATIVE_CONTROL_OBSERVED: false
REAL_EXTERNAL_SYSTEM_ENFORCED_ACTIVATION: false
COMPLETE: false
```


## Resident targeted execution seam — issue #702

The existing resident refresh/one-shot path is the canonical execution surface. No new scheduler or request format is introduced.

```text
python scripts/refresh_and_execute_resident_task.py \
  --task-id SHWP-UNIVERSAL-GOVERNANCE-ENFORCED-REFERENCE-001
```

For deployments that require explicit source locators, the refresh bridge forwards only these non-secret paths:

```text
STEGVERSE_STEGCORE_SOURCE_ROOT
STEGVERSE_MASTER_RECORDS_SOURCE_ROOT
```

They survive `clean_exec_env()` while GitHub credential variables and hosted-runtime markers remain stripped.

The targeted execution path still requires the existing separated carrier reference and invokes exactly one independently admitted WorkerCoordinator task. Source refresh is not runtime execution and source materialization remains separately governed.

Current lifecycle remains:

```text
SOURCE_IMPLEMENTED: true
SOURCE_VALIDATED: true
SOURCE_MERGED: true
RESIDENT_TARGETABLE: true
RESIDENT_EXECUTION_OBSERVED: false
REFERENCE_ENFORCED_BOUNDARY_OBSERVED: false
REAL_EXTERNAL_SYSTEM_ENFORCED_ACTIVATION: false
```


## Resident request dispatch integration

A canonical one-shot request now targets the existing machine-owned task without creating a second scheduler or authority path.

```text
request: control/resident-execution-request.d/universal-governance-enforced-reference-001.json
consumer: scripts/consume_universal_governance_enforced_reference_request.py
dispatch selector: universal_governance_enforced_reference
execution target: SHWP-UNIVERSAL-GOVERNANCE-ENFORCED-REFERENCE-001
mode: TARGETED_INDEPENDENT_TASK_CONTROL
source locators:
  STEGVERSE_STEGCORE_SOURCE_ROOT
  STEGVERSE_MASTER_RECORDS_SOURCE_ROOT
request authority effect: NONE_REQUEST_ONLY
```

The request consumer invokes only the existing `refresh_and_execute_resident_task.py --task-id` path. Completion requires the worker's terminal transition plus the bound-state receipt proving the reference boundary, bypass negative control, and Master Records custody while `real_external_system_enforced_activation=false`.

Lifecycle after this source change:

```text
RESIDENT_REQUEST_DEFINED: true
RESIDENT_CONSUMER_DEFINED: true
RESIDENT_DISPATCH_REGISTERED: true
SOURCE_REFRESH_MATERIALIZES_CONSUMER: true
RESIDENT_EXECUTION_OBSERVED: false
REFERENCE_ENFORCED_BOUNDARY_OBSERVED: false
REAL_EXTERNAL_SYSTEM_ENFORCED_ACTIVATION: false
```
