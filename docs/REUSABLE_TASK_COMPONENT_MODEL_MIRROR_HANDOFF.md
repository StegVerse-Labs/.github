# Reusable Task Component Model Mirror Handoff

Updated: 2026-09-13
Repository: `StegVerse-Labs/.github`
Canonical merge: `StegVerse-Labs/.github#1652` -> `b9f8e5153aa1651f2d7f043fb902eacb7c113ed9`
Status: `ACTIVE / SOURCE MODEL MERGED + VALIDATED / ECOSYSTEM ADOPTION ACTIVE`

## Purpose

The Reusable Task Component Model converts repeated StegVerse orchestration subflows into reusable, authority-preserving capability components that canonical Goal Tasks compose from declared requirements. The owning Goal Task remains the goal and evidence owner; reusable components are capabilities, not automatically new Goal Tasks.

Canonical model:

```text
data/reusable-task-component-model.json
```

Canonical decomposition policy:

```text
data/reusable-task-component-decomposition-policy.json
```

Deterministic non-authorizing evaluator:

```text
scripts/evaluate_reusable_task_componentization.py
```

## Composition rule

A Goal Task declares the capabilities it requires. Composition derives only the necessary reusable components, preserves governed order, allows repeatable components where the task declares repeated transitions or round trips, and does not force optional components into unrelated tasks.

Every reusable component exposes or resolves a stable interface covering capability, inputs, outputs, preconditions, expected evidence, authority owner/effect, failure classes, retry/reentry semantics, and version/schema binding.

A missing required component fails closed. Reusing a component never mints execution, user-verification, credential, transition, custody, publication, or completion authority.

## Automatic decomposition process

The decomposition policy is evaluated when a task is created or materially expanded and again at key continuation points, including before prompt count 10 and before release-ready classification. Signals include repeated subflows, multiple authority crossings, multiple round trips, repository/org spread, duplicated generic adapter work, growing handoff sequences, branching remediation, independently reusable subprocesses, optional subprocesses, and independently verifiable evidence predicates.

Disposition thresholds remain:

```text
0-4   KEEP_COMPOSED_AND_REEVALUATE_AT_NEXT_EVALUATION_POINT
5-8   SEARCH_EXISTING_REUSABLE_COMPONENTS_AND_RECORD_REUSE_ANALYSIS
9-12  COMPONENTIZATION_REQUIRED_UNLESS_EXPLICIT_NON_REUSE_JUSTIFICATION_EXISTS
13+   STOP_SCOPE_GROWTH_AND_DECOMPOSE_BEFORE_ADDING_MORE_TASK_SPECIFIC_ORCHESTRATION
```

Stopping task-specific scope growth does not stop the Goal Task. It requires reuse, extension, or creation of the appropriate reusable component and then continuation under the same Goal Task identity and COSV unless genuinely independent goal-level completion semantics exist.

## Component families

The model recognizes reusable families for transport, runtime observation, governed ingress, execution materialization, credential/session handling, evidence validation, custody/reconstruction, framework/provider translation, callback correlation, release/propagation, failure-remediation classification, and terminal cleanup/entropy recovery.

The first materialized family is transport:

```text
data/reusable-transport-component-contract.json
docs/REUSABLE_GOAL_TASK_TRANSPORT_COMPONENTS_MIRROR_HANDOFF.md
```

Goal Tasks may additionally project their full composition using task-specific component profiles while reusing existing canonical owners rather than creating parallel implementations.

`SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004` consumes the model through:

```text
data/goal-task-transport-profiles/SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004.json
data/goal-task-component-profiles/SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004.json
docs/SDK_WORKSPACE_EXTCOLLAB_COMPONENT_MODEL_MIRROR_HANDOFF.md
```

## Authority invariants

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority.
- KV/SKAP Vault: sole user-verification authority.
- StegOS devices: interchangeable transport/execution nodes, not user verifiers.
- TV/TVC: credential/provider/release authority.
- Interlock/InTr: governed transition/admission authority.
- Master Records: observed reality, custody, and reconstruction authority.
- HeartBeat: synchronization/timing/freshness/liveness/state-correlation/observability only.
- GitHub: no runtime authority.

A component receipt proves only the event/observation represented by that receipt. It does not authorize the next component. Runtime subject binding, node identity, Secure Enclave identity, and transport identity do not become user-verification authority.

## Goal Task and prompt-count rule

Componentization does not reset prompt counters or manufacture new Goal Task IDs. The existing Goal Task continues unless remaining work is genuinely separable and independently completable.

## Merge and validation evidence

PR #1652 final exact head `075b1e71d0ebe3591899db03d570da79eed5e916` passed:

```text
Validate organization control plane: 34730323940 PASS
Deterministic Repository Suite: 34730323942 PASS
Heartbeat Worker Project validation: 34730323876 PASS
validate-deepseek-resident: 34730323965 PASS
```

PR #1652 merged at `b9f8e5153aa1651f2d7f043fb902eacb7c113ed9`.

These are source/process-architecture facts only. They do not prove authentic resident runtime execution, provider operation, transition execution, publication, custody, or end-to-end completion.

## Ecosystem adoption rule

Before substantive continuation, an active Goal Task must reconcile its current implementation/execution process against this model when decomposition signals are present. Reuse exact existing components/owners first; stop extending functionally equivalent task-specific orchestration. Preserve the Goal Task's own completion predicates and authentic runtime/evidence requirements separately from component source validation.

## README impact

The root README was updated as part of #1652 because the model materially changes StegVerse task-composition behavior. Task-specific component-profile reconciliations do not require another README mutation unless they independently change repository function.

## Human action

None.
