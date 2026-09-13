# Task Registry Completion Evidence-Class Invariant Mirror Handoff

Updated: 2026-09-12
Status: SOURCE IMPLEMENTATION IN PROGRESS
Scope: ALL_CANONICAL_TASKS_EXISTING_AND_NEW

## Problem

Unqualified `complete` / `completed` language can collapse distinct proof states and force a human to rediscover whether a task was source-implemented, merged, CI-validated, sandbox/runtime-observed, externally/provider-observed, Master Records reconstructed, or actually end-to-end complete. That ambiguity increases cognitive load and can cause repeated prompting or premature closure.

## Global invariant

`data/task-registry-global-invariants.json` now requires affirmative completion claims to identify an explicit evidence class and evidence references. Stronger completion classes may not be inferred from weaker classes.

Canonical evidence classes, weakest to strongest:

```text
SOURCE_IMPLEMENTED
MERGED
CI_VALIDATED
SANDBOX_RUNTIME_OBSERVED
EXTERNAL_PROVIDER_OBSERVED
MASTER_RECORDS_RECONSTRUCTED
END_TO_END
```

A Goal Task may declare its own `completion.terminal_evidence_class`. A completion claim is invalid when its proven evidence class is weaker than the declared terminal class.

`end_to_end_complete=true` requires `evidence_class=END_TO_END`.

## User-facing completion rule

Bare `complete` or `completed` is prohibited as a user-facing task status unless the declared terminal evidence class has actually been satisfied. When reporting a lower proof state, the evidence class must be stated in the same completion statement, for example:

```text
SOURCE_IMPLEMENTED: complete for source implementation; sandbox runtime remains unobserved.
CI_VALIDATED: source/CI proof complete; runtime proof remains pending.
END_TO_END: declared Goal Task terminal predicates satisfied with native evidence.
```

No source, merge, CI, runtime, provider, or reconstruction class may silently promote itself to a stronger class.

## Enforcement

Canonical enforcement surfaces:

- `data/task-registry-global-invariants.json`
- `scripts/validate_task_registry_global_invariants.py`
- `tests/test_task_registry_completion_evidence_class_invariant.py`

The validator fails closed when:

- `completion.claimed=true` or `completion.validated=true` lacks a permitted `completion.evidence_class`;
- affirmative completion lacks non-empty `completion.evidence_refs`;
- validated completion is not also claimed;
- a claimed evidence class is weaker than `completion.terminal_evidence_class`;
- `end_to_end_complete=true` is paired with anything other than `END_TO_END`.

## Authority

This invariant changes coordination/evidence semantics only. It grants no execution, transition, credential, provider, custody, reconstruction, or publication authority.

Task Registry remains coordination only. WorkerCoordinator retains claim/fence authority. Interlock/InTr retains governed transition authority. TV/TVC retains credential/provider/release authority. Master Records remains observed-reality/reconstruction authority.

## Completion semantics for this change

This invariant change is not complete merely because the policy text exists. Its source implementation is complete only after validator/test source is merged. It becomes CI_VALIDATED only after exact-head repository validation succeeds. No runtime or end-to-end ecosystem enforcement beyond repository validation is inferred unless separately observed.

## Human action

None.
