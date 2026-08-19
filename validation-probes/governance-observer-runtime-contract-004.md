# Governance observer runtime contract validation probe

Validation-only branch marker for the current `main` implementation of `GOVERNANCE-SOVEREIGN-TASK-OBSERVER-001`.

Acceptance targets:

- `tests/test_governance_sovereign_task_observer.py` passes in full;
- executable handoff validation accepts `handoffs/GOVERNANCE-SOVEREIGN-TASK-OBSERVER-001.json`;
- worker response states and transition sequences are ProcessWorkerAdapter-compatible;
- missing TVC materialized source returns `HANDOFF_READY` without a duplicate resolution contract;
- real observer defects carry a valid sandbox-resolution contract;
- bound-state projection is limited to `observed/**` and `receipts/**`;
- cost basis resolves to a finite claim budget;
- no GitHub credential token is present in the validation environment.

This probe is non-authorizing and must not be merged. Hosted validation is source evidence only and does not prove TV/TVC materialization, sovereign execution, activation, CGE decision, or heartbeat effect.
