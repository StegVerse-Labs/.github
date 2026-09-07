# Reusable Task Ephemeral Construct Mirror Handoff

Updated: 2026-09-07

## Goal

Make every reusable task a durable identity whose invocation-specific parameters derive the exact manifest-bound RTG -> GTG -> TT construct and whose valid trigger automatically advances every declared machine-admissible internal step until completion or the first genuine authority, evidence, external-resource, human-decision, or unresolved-state boundary.

## Canonical source

- `data/reusable-task-registry.json`
- `data/reusable-task-ephemeral-construct-contract.json`
- `schemas/reusable-task-invocation-manifest.schema.json`
- `scripts/materialize_reusable_task_construct.py`
- `scripts/trigger_reusable_task.py`
- `scripts/refresh_sovereign_worker_runtime_source.py`
- `data/task-coordination-policy.json`
- `management/COSV_PROFILE_V1.json`
- `StegVerse-Labs/StegScholar:papers/rtg-gtg-tt/cross-layer-contract.md`

## Durable / ephemeral invariant

```text
Reusable identity = durable
Parameters = invocation-specific
TT/RTG/GTG construct = derived
Trigger = single bounded invocation
Machine-admissible internal transitions = automatic
Runner = ephemeral where possible
Evidence = durable
Canonical task/COSV identity = durable when tracking is needed
Manifest = bound
Receipts = chained
Recording = at necessary levels
```

The cross-layer semantic order remains canonical `RTG -> GTG -> TT`. This repository does not redefine RTG, GTG, or TT mathematics or collapse their authority boundaries.

## Trigger-once automation invariant

A reusable task is not a checklist that requires the coordinator to manually re-drive each ordinary internal transition. After one valid trigger, `scripts/trigger_reusable_task.py` materializes the canonical invocation manifest and advances only the runner templates already declared by that reusable identity.

```text
valid reusable-task trigger
-> resolve durable identity + parameters
-> verify optional task_id/COSV binding
-> bind RTG/GTG/TT + automation + runner manifest
-> automatically invoke declared existing runner steps in order
-> continue while the next step is machine-admissible
-> stop at completion or first real governed boundary
-> emit exact boundary/continuation receipt
```

The automation driver does not create a scheduler, WorkerCoordinator, claim/fence path, credential route, InTr authority, provider authority, or Master Records authority. A runner's success exit is not sufficient to manufacture completion; declared completion predicates remain evidence-driven.

When a reusable identity has no executable runner declaration, the trigger is still recorded but stops at `NO_EXECUTABLE_RUNNER_DECLARED`. That is now an explicit source-binding gap rather than a reason to manually coordinate otherwise automatable steps. Identities with declared runners advance automatically until those runners finish or surface their own boundary.

Independent downstream or parallel work may continue while a reusable task is at a boundary. Work that depends on its required completion evidence must wait for that evidence. This makes Time/dependency ordering explicit without allowing automation to manufacture Authority.

## Invocation lifecycle

```text
durable reusable identity
+ invocation parameters
+ task_id/COSV pointer when tracking is required
-> resolve existing canonical definition/equivalent work
-> derive RTG candidate envelope
-> derive GTG governance envelope
-> derive TT record/execution/observation envelope
-> bind invocation + automation manifest
-> trigger once
-> applicable WorkerCoordinator + Interlock/InTr admission
-> automatically advance declared bounded runner(s)
-> completion OR exact governed boundary receipt
-> execution and chained receipts
-> runner expiry
-> residual non-executing TT/RTG/GTG recording construct when recording remains
-> required operation/task/goal/aggregate recording
-> Master Records custody + reconstruction
-> entropy recovery
```

## Residual recording construct

After runner expiry, the remaining construct has no original execution purpose and no provider-operation, credential-acquisition, claim/fence, self-extension, or transition authority. It may only preserve invocation identity and manifest binding, carry chained receipts, project required COSV/task state, perform required scoped recording, carry evidence into Master Records, and support reconstruction verification.

## Entropy recovery

Entropy recovery is the final displacement of that residual non-executing construct after:

- the runner has expired;
- required recording levels are complete;
- the required receipt chain is complete;
- Master Records custody is accepted;
- Master Records reconstruction is confirmed; and
- no unrecorded successor/correction dependency still requires the residual construct.

Entropy recovery never deletes required evidence or Master Records history and never reactivates the original runner.

## Reusable identity families enrolled

Generation 2 of `data/reusable-task-registry.json` puts maintenance and external-interaction work on the same identity model, including:

- `RT-README-VALIDATION-001`
- `RT-MIRROR-HANDOFF-VALIDATION-001`
- `RT-STEGINDEX-VALIDATION-001`
- `RT-NATIVE-EMAIL-ACTION-MONITOR-001`
- `RT-CANONICAL-STATE-RECONCILIATION-001`
- `RT-SESSION-CLOSEOUT-001`
- `RT-INTR-PROTOCOL-ESTABLISH-001`
- `RT-EXTERNAL-ADAPTER-ESTABLISH-001`
- `RT-AI-ADAPTER-ESTABLISH-001`
- `RT-EXTERNAL-ENDPOINT-MONITOR-001`
- `RT-SOCIAL-PLATFORM-INTERACTION-001`

Distinct same-goal work discovered during invocation must first be reconciled against existing canonical work. Only genuinely new work derives a new adjacent canonical task + COSV identity.

## Resident propagation

The existing local-only WorkerCoordinator source refresher now carries the reusable-task registry, construct contract, deterministic constructor, and trigger driver into an already-materialized resident runtime. This is source propagation only: it performs no network fetch, credential acquisition, mutable-runtime-state replacement, claim/fence creation, or execution proof.

## Authority boundaries

Reusable identity, parameter binding, automation trigger, derived RTG/GTG/TT source envelopes, manifest hashes, runner invocation orchestration, and source validation grant no execution authority.

- Task Registry: work intent / coordination
- WorkerCoordinator: execution claim / fence
- Interlock/InTr: governed transitions
- TV/TVC: credential authority
- Master Records: observed reality / reconstruction
- COSV: compact state projection
- Trigger driver: non-authorizing dependency orchestration
- GitHub token runtime authority: `NONE`

## README impact

`README.md` must be updated in the same change set because this materially changes reusable-task invocation from lifecycle-only construction to trigger-once bounded automation, including runtime propagation and failure/boundary semantics.

## Current boundary

The source contract, manifest schema, deterministic constructor, trigger driver, and resident source-refresh propagation are implemented. Authentic resident execution of a reusable invocation, component-produced trigger receipts, chained runtime receipts, completion-evidence reconciliation, residual-recording operation, Master Records custody/reconstruction, and observed entropy recovery remain runtime evidence boundaries and must not be inferred from source state.
