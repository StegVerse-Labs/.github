# Current User iOS Interaction Serialization Mirror Handoff

Updated: 2026-09-05
Repository: StegVerse-Labs/.github
Issue: #922

## Problem

Repository work claims serialize source/dependency ownership, but they do not serialize human-facing page manipulation against the single current StegVerse iOS node. Concurrent sessions have independently issued different current-iPhone action sequences. That can advance the same IndexedDB journal in different orders and invalidate receipt/hash preconditions even when every individual action is otherwise valid.

## Canonical control

`control/current-user-ios-interaction-queue.json` is the organization-level non-authorizing serialization record for true human/device mutations on the current StegVerse iOS node.

It is NOT:
- a scheduler;
- a WorkerCoordinator replacement;
- a claim/fence authority;
- an InTr authority;
- a TV/TVC authority;
- a custody or execution authority;
- an approval queue for machine-owned entity transitions.

It only answers one question: **which exact human-facing device mutation, if any, may a session instruct next?**

## Machine-owned transition exclusion — 2026-09-04

Canonical progression contract:

- `docs/ENTITY_AUTONOMOUS_GOVERNED_PROGRESSION_MIRROR_HANDOFF.md`
- `control/entity-autonomous-governed-progression-contract.json`

The interaction queue MUST NOT serialize, approve, or gate a transition merely because the transition executes on the current iPhone.

Execution surface is not authority class.

A transition performed by the resident/service-worker/entity runtime remains machine-owned when its exact current transition is contemporaneously governed by Interlock/InTr (and TV/TVC where credential authority is required).

Machine-owned progression is:

```text
entity proposes exact transition
-> current governance ALLOW/DENY
-> ALLOW carried by InTr
-> resident/service-worker consumes
-> receipt retained
-> entity continues
```

No human interaction slot is inserted.

Only an exact transition whose authority class is explicitly `HUMAN_ONLY`, `USER_ONLY`, `LEGAL_PERSON_SIGNATURE`, `OWNER_EXPLICIT_CONSENT`, or equivalent enters this queue.

Therefore:

```text
machine transition on CURRENT_USER_IPHONE != human/device mutation
human-facing button exists != human authority required
consequential transition != manual approval required
```

This correction preserves per-transition governance. It does not infer or reuse authority.

## Session rule for true human mutations

Before telling the user to tap, submit, sign, broadcast, explicitly consent, or otherwise perform a transition that actually requires human authority on the current iOS StegOS page, every session must:

1. read this handoff and the queue;
2. verify the transition's authority class is genuinely human-only/user-only;
3. verify queue state;
4. register/reconcile its desired human action;
5. require a fresh journal tail when required by that exact human action;
6. proceed only if its exact `action_id` is `ADMITTED_FOR_USER_EXECUTION`;
7. after execution, obtain the receipt/replay evidence required by that transition.

A session MUST NOT route a machine-owned transition into this process merely because it lacks a direct runtime call in that session.

## Terminal transition rule

Terminal or exactly-once transitions must never be rerun merely to restore an expected journal order. Downstream idempotent continuation must consume the retained terminal receipt instead.

## Historical reconciliation retained

The prior queue history, including SV001 G23/G24 lineage reconciliation, remains provenance. G23 is canonical custody-eligible and G24 remains retained non-custodial duplicate evidence. Further SV001 terminal execution remains prohibited.

## SV001 Master Records custody reclassification — 2026-09-05

Issue `#1036` resolved the formerly admitted `IPHONE-MR-SV001-CUSTODY-001` action against the canonical ownership classifier and the already-existing Master Records/Site implementation.

The exact transition is:

```text
transition_id = SV001_MASTER_RECORDS_CUSTODY_AND_RECONSTRUCTION
authority_class = MACHINE_GOVERNED
execution_surface = CURRENT_USER_IPHONE
human_interaction_required = false
route = ENTITY_MACHINE_GOVERNANCE_LOOP
```

Evidence:

- `control/entity-transition-ownership-evaluations/sv001-master-records-custody.json`
- `scripts/evaluate_entity_transition_ownership.py`
- `master-records/orchestration:portable/stegverse001-autonomy-custody-package.json`
- `StegVerse-Labs/Site:docs/MR_SV001_CURRENT_IPHONE_CUSTODY_MIRROR_HANDOFF.md`

The portable Master Records module already owns custody authority and can be invoked through the existing current-iPhone service-worker carrier. The Site role remains exact source materialization/persistence carrier only; the existence of the visible `Commit Master Records Custody` control does not create a human authority class.

Therefore the former SV001 custody action is removed from the human interaction queue. Its earlier `ADMITTED_FOR_USER_EXECUTION` record is historical provenance only and is explicitly superseded. No session may instruct the user to perform that custody transition as a human-authority action.

This reclassification does **not** authorize custody. The next transition still requires contemporaneous Interlock/InTr governance for the exact custody/reconstruction transition, and TV/TVC remains the credential authority where applicable. The retained G23 receipt is input evidence; it does not authorize the next transition.

The current queue may remain fail-closed for true human-authority mutations while machine-owned entity progression continues independently.

## Authority

```text
credential authority = TV/TVC
GitHub token runtime authority = NONE
HB authority effect = NONE
interaction queue authority effect = NONE_HUMAN_DEVICE_INSTRUCTION_SERIALIZATION_ONLY
machine transition authority = current Interlock/InTr decision for exact transition
prior receipt authority effect on next transition = NONE
second user-operated machine required = false
```
