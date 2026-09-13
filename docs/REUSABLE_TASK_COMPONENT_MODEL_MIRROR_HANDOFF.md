# Reusable Task Component Model Mirror Handoff

Updated: 2026-09-12
Repository: `StegVerse-Labs/.github`
Consuming Goal Task: `SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004`
COSV: `71000000100110`
Status: `ACTIVE / SOURCE MODEL PROPOSED / VALIDATION PENDING`

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

Every reusable component must expose a stable interface including its capability, inputs, outputs, preconditions, expected evidence, authority owner/effect, failure classes, retry/reentry semantics, and version/schema binding.

A missing required component fails closed. Reusing a component never mints execution, user-verification, credential, transition, custody, publication, or completion authority.

## Automatic decomposition process

The decomposition policy is evaluated when a task is created or materially expanded and again at key continuation points. Signals include repeated subflows, multiple authority crossings, multiple round trips, repository or organization spread, duplicated generic adapter work, growing handoff sequences, branching remediation paths, independently reusable subprocesses, optional subprocesses, and independently verifiable evidence predicates.

The deterministic score yields four dispositions:

```text
0-4   KEEP_COMPOSED_AND_REEVALUATE_AT_NEXT_EVALUATION_POINT
5-8   SEARCH_EXISTING_REUSABLE_COMPONENTS_AND_RECORD_REUSE_ANALYSIS
9-12  COMPONENTIZATION_REQUIRED_UNLESS_EXPLICIT_NON_REUSE_JUSTIFICATION_EXISTS
13+   STOP_SCOPE_GROWTH_AND_DECOMPOSE_BEFORE_ADDING_MORE_TASK_SPECIFIC_ORCHESTRATION
```

Stopping task-specific scope growth does not stop the Goal Task. It requires the session to reuse, extend, or create the appropriate reusable component and then continue the same goal under its existing identity and COSV continuity.

## Component families

The initial model recognizes reusable families for transport, runtime observation, governed ingress, execution materialization, credential/session handling, evidence validation, custody/reconstruction, framework/provider translation, callback correlation, release/propagation, failure-remediation classification, and terminal cleanup/entropy recovery.

The first materialized family is transport:

```text
data/reusable-transport-component-contract.json
docs/REUSABLE_GOAL_TASK_TRANSPORT_COMPONENTS_MIRROR_HANDOFF.md
```

`SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004` consumes that family through:

```text
data/goal-task-transport-profiles/SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004.json
```

## Authority invariants

The model preserves existing separation:

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority.
- KV/SKAP Vault: sole user-verification authority.
- StegOS devices: interchangeable transport nodes.
- TV/TVC: credential/provider/release authority.
- Interlock/InTr: governed transition authority.
- Master Records: observed reality, custody, and reconstruction authority.
- HeartBeat: timing/freshness/correlation/carriage only.
- GitHub: no runtime authority.

A receipt from one component proves only the event/observation represented by that receipt. It does not authorize the next component.

## Goal Task and prompt-count rule

Componentization is not a mechanism for resetting prompt counters or manufacturing new Goal Task IDs. The existing Goal Task continues unless remaining work is genuinely separable. A new Goal Task is appropriate only for independently ownable work with its own completion predicates and canonical continuation path.

## Validation boundary

This change is source/process architecture. It does not prove an authentic resident runtime, provider operation, transition, publication, custody event, or end-to-end execution. The model and its first transport-family composition must pass the repository's existing deterministic validation lanes before merge.

## README impact

The root README must describe this model because it changes how future canonical Goal Tasks are expected to compose reusable capabilities and when growing orchestration must be decomposed.

## Human action

None.