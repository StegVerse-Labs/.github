# Current User iOS Interaction Serialization Mirror Handoff

Updated: 2026-09-03
Repository: StegVerse-Labs/.github
Issue: #922

## Problem

Repository work claims serialize source/dependency ownership, but they do not serialize human-facing page manipulation against the single current StegVerse iOS node. Concurrent sessions have independently issued different current-iPhone action sequences. That can advance the same IndexedDB journal in different orders and invalidate receipt/hash preconditions even when every individual action is otherwise valid.

## Canonical control

`control/current-user-ios-interaction-queue.json` is the organization-level non-authorizing serialization record for all human/device mutations on the current StegVerse iOS node.

It is NOT:
- a scheduler;
- a WorkerCoordinator replacement;
- a claim/fence authority;
- an InTr authority;
- a TV/TVC authority;
- a custody or execution authority.

It only answers one question: **which exact human-facing device mutation, if any, may a session instruct next?**

## Immediate state

```text
state = HOLD_PENDING_FRESH_JOURNAL_RECONCILIATION
state-mutating page instructions = PROHIBITED
read-only inspection/replay/export = PERMITTED
last known journal = 59 entries
last known tail = 0725a8208f709b19027b9434cd089cdff0efc01b2ed5f2571036ae6ad8695d0c
last known tail fresh enough for a new mutation = NO
```

The old tail is retained only as provenance. It must not be used as the expected predecessor for a new mutation until the current device performs a fresh journal replay.

## Session rule

Before telling the user to tap, submit, commit, run, admit, activate, import, save, or otherwise mutate the current iOS StegOS page, every session must:

1. read this handoff and the queue;
2. verify queue state;
3. register/reconcile its desired action;
4. require a fresh journal tail if the queue is frozen or the predecessor is stale;
5. proceed only if its exact `action_id` is `ADMITTED_FOR_USER_EXECUTION`;
6. after execution, obtain fresh replay/export evidence before another action may be admitted.

A session that has not acquired the admitted interaction slot may continue machine/source work, but it may not give competing page-manipulation instructions.

## Terminal transition rule

Terminal or exactly-once transitions must never be rerun merely to restore an expected journal order. Downstream idempotent continuation must consume the retained terminal receipt instead.

## Current candidates

Known concurrent intent includes:
- Master Records custody of the already-terminal SV001 cycle;
- a DE-006/current-iPhone continuation from another active session whose exact next mutation must be reconciled before admission.

No order is asserted yet. Fresh journal state plus canonical task prerequisites determine the order.

## Authority

```text
credential authority = TV/TVC
GitHub token runtime authority = NONE
HB authority effect = NONE
interaction queue authority effect = NONE_HUMAN_DEVICE_INSTRUCTION_SERIALIZATION_ONLY
second user-operated machine required = false
```
