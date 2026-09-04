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


## Reconciliation update — 2026-09-03

The apparent DE-006 competing phone action has been resolved from canonical evidence.
PR #921 / merge `bc871ebca8a04646f043e467a170c068f9eef140` verified a later
CURRENT_USER_IPHONE DE-006 evidence bundle:

```text
reconstruction = PASS
same_execution = true
replay relation = VALID_APPEND_ONLY_DESCENDANT
journal tail = 897b9c70e704243939659009ef8d2e9d5ba984d1c4d0edd835afdaf26c5f4b69
parent execution proven = false
parent fence promoted = false
```

Its next transition is resident request consumption plus a fresh parent fence >22.
That is machine-owned and requires no additional human/device mutation, so the
placeholder DE-006 mutation has been removed from the interaction queue.

The `897b...` tail is a later verified descendant than the original `0725...`
tail, but it is still not treated as the present device head because other concurrent
sessions may have acted after that export.

Current canonical explicit mutation inventory contains one candidate:

`IPHONE-MR-SV001-CUSTODY-001`

It remains `WAITING_FOR_FRESH_JOURNAL_HEAD`; it is not admitted.

New deterministic tooling:
- `scripts/check_current_user_ios_interaction_queue.py` validates queue invariants;
- `scripts/evaluate_current_user_ios_interaction_admission.py` evaluates a fresh
  read-only journal replay/export against a registered candidate without granting
  or mutating any authority.

The SV001 executable handoff is explicitly subordinated to this queue. Its
task-specific page action text is descriptive only until the exact action ID is
the sole `ADMITTED_FOR_USER_EXECUTION` queue entry.


## Master Records custody prerequisite reconciliation — 2026-09-03

Machine/source prerequisites for `IPHONE-MR-SV001-CUSTODY-001` are now satisfied:

```text
Site custody projection: #956 / 0b4cd7dc13cb43ffa9feec3c4badc21524efccd2
full-proof import repair: #959 / 11ffa8fc712569a07edb45397baf2e3427947294
immutable terminal cycle receipt: sha256:81a078eeeacffb8fc86d287d7aaa8a9904c6f53973471dad7f6d7c3fa6818a35
SV001 rerun required: false
```

This does **not** admit the mutation. The queue remains fail-closed because the present device journal head has not been freshly replayed/exported after concurrent-session activity. The only permitted next device interactions remain read-only replay/export/inspection. A state-mutating custody instruction is prohibited until the fresh evidence is evaluated and the exact action becomes the sole `ADMITTED_FOR_USER_EXECUTION` entry.


## Fresh-device reconciliation exposed duplicate SV001 terminal lineage — 2026-09-03

A fresh CURRENT_USER_IPHONE evidence export reports:

```text
journal replay = PASS
entries = 69
tail = 897b9c70e704243939659009ef8d2e9d5ba984d1c4d0edd835afdaf26c5f4b69
```

The fresh head is not admissible for custody because it contains two distinct completed
SV001 terminal lineages:

```text
G23 / fence 23 -> SV001_BOUNDED_AUTONOMY_CYCLE_COMPLETED
cycle receipt = sha256:81a078eeeacffb8fc86d287d7aaa8a9904c6f53973471dad7f6d7c3fa6818a35
TVC consumption = observed

G24 / fence 24 -> SV001_BOUNDED_AUTONOMY_CYCLE_COMPLETED
cycle receipt = sha256:6bcc1976793657ea849a3678fa324c69134d2b59481e0bc9994c6baa6c4aff79
TVC consumption = observed
journal terminal/reconstruction/consumption = sequences 67/68/69
```

Journal integrity is not the failure: replay is PASS. The failure is downstream identity
selection. Master Records must not silently treat either earliest or latest terminal
execution as canonical. The queue therefore moves to
`HOLD_DUPLICATE_TERMINAL_LINEAGE_RECONCILIATION`.

No further SV001 execution is allowed. No Master Records custody action is admitted.
Canonical SV001 lineage disposition must occur first.

## Current canonical queue state — 2026-09-04

Issue #987 reconciles this handoff to the newer machine-readable queue state on current main.

Canonical lineage reconciliation is complete:

```text
.github#942 = CLOSED_COMPLETED
G23 / fence 23 / cycle sha256:81a078eeeacffb8fc86d287d7aaa8a9904c6f53973471dad7f6d7c3fa6818a35
  disposition = CANONICAL_CUSTODY_ELIGIBLE

G24 / fence 24 / cycle sha256:6bcc1976793657ea849a3678fa324c69134d2b59481e0bc9994c6baa6c4aff79
  disposition = DUPLICATE_TERMINAL_EXECUTION_NON_CUSTODIAL
  retained = true
```

Canonical terminal re-execution prevention is source-installed:

```text
.github#946 / merge 3448807c50a4f9d3bd07ce83c0d4c2c315617b6f
Site#963 / merge cfd0f02cfca5034e57be23083ece6fcb70bf1e70
Site validator successor repair #965 / #973 / merge 6a4b0e3c5432d1a091768deebfc83493cb49d647
completed validator-claim release #983 / merge bf42acd5fa1c813dc0eb82c18454040d1b958e8f
```

These merges do not prove public propagation or device-runtime enforcement.

The current authoritative queue now reads:

```text
state = HOLD_UI_ORCHESTRATION_CONFLICT
state-mutating page instructions = PROHIBITED
read-only inspection/replay/export = PERMITTED
candidate = IPHONE-MR-SV001-CUSTODY-001
candidate queue_state = REVOKED_PENDING_UI_SINGLE_ACTION_GUARD
active_action_id = null
next_required_observation = SITE_UI_SINGLE_ACTION_GUARD_RELEASED_AND_PUBLICLY_OBSERVED
```

The freeze reason is a user-visible orchestration conflict: multiple mutation controls remained exposed and non-JSON checkout-module text was present in the Master Records input while the page displayed `FAIL_CLOSED / Invalid JSON`.

Therefore the next legitimate implementation target is not another SV001 execution and not direct custody admission. It is the governed Site UI single-action guard that consumes the shared interaction manifest and enforces:

```text
all mutation controls default disabled
at most one mutation control enabled
read-only controls remain separate
parse/binding failure revokes the action locally
stale session instructions cannot override the manifest
```

That Site work must first pass Site repository orchestration/admission. Until it is source-installed, publicly propagated, and independently observed on the current device, `IPHONE-MR-SV001-CUSTODY-001` remains revoked and no session may instruct a state-mutating phone action.

Authority remains unchanged:

```text
credential authority = TV/TVC
GitHub token runtime authority = NONE
HB authority effect = NONE
interaction queue authority effect = NONE_HUMAN_DEVICE_INSTRUCTION_SERIALIZATION_ONLY
second user-operated machine required = false
further SV001 execution permitted = false
```
