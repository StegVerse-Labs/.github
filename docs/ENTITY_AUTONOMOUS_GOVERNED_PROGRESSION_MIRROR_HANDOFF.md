# Entity Autonomous Governed Progression Mirror Handoff

Updated: 2026-09-04
Repository: `StegVerse-Labs/.github`
State: SOURCE_IMPLEMENTED / RUNTIME ADOPTION REQUIRED
Authority effect: NONE

## Problem being corrected

StegVerse entities must not depend on a human repeatedly reading transition sets and approving the next small group of machine-owned transitions.

That behavior is not governance. It is manual orchestration.

The governing invariant is:

```text
authority is never inferred
authority is never reused from a prior event
every state transition is governed contemporaneously
human approval is required only when the current transition's authority class is explicitly HUMAN_ONLY / USER_ONLY
```

A prior receipt proves a prior transition. It never authorizes the next transition.

## Canonical machine progression

For an entity-owned machine transition:

```text
entity observes current canonical state
-> entity proposes exactly one next transition
-> current Interlock/transition governor evaluates that exact transition
-> TV/TVC is consulted if the transition requires credential authority
-> ALLOW or DENY receipt is emitted for that exact transition
-> ALLOW: InTr carries the admitted action to the current receiver/runtime
-> receiver consumes it
-> state changes
-> execution/state receipt is retained
-> entity reconstructs/re-evaluates current state
-> entity proposes the next transition
```

The entity does not ask a human to authorize a machine-owned transition merely because the transition is consequential, new, or follows another transition.

Governance remains per-transition and contemporaneous.

## Human boundary

Human interaction is required only when the exact transition declares an authority class that cannot be exercised by the entity/runtime, including examples such as:

- `USER_ONLY` wallet signing or broadcast;
- explicit legal-person signature/e-signature consent;
- authenticated institutional submission when the institution requires the human principal;
- an explicit governance rule that names a human decision as a predicate.

The presence of a human-facing UI control does not convert a machine-governable transition into a human-authority transition.

The current-user iOS interaction queue serializes only true human/device mutations. It MUST NOT be used as a scheduler or approval queue for machine-owned resident/service-worker/entity transitions.

## Entity loop

An online StegVerse entity is expected to continuously work toward its admitted goals by repeating:

```text
OBSERVE
-> SELECT highest-priority unblocked nonduplicate goal
-> PROPOSE next exact transition
-> GOVERN transition now
-> if DENY: retain denial + choose an admissible repair/alternate transition
-> if ALLOW: execute through InTr/receiver
-> RETAIN receipt
-> RECONSTRUCT current state
-> CONTINUE
```

No human approval checkpoint is inserted between ordinary machine-owned cycles.

## Required fail-closed behavior

The entity stops only when:

1. governance returns DENY and no admissible repair/alternate transition is available;
2. the exact next transition is `HUMAN_ONLY` / `USER_ONLY`;
3. a required receiver/runtime is genuinely unavailable and no admitted local materialization path exists;
4. a current-state invariant cannot be reconstructed;
5. the entity has reached its terminal governed goal state.

`I need the user to approve the next transitions` is not a valid stop condition unless the exact transition contract requires human authority.

## Shared runtime relationship

This progression uses the existing canonical substrate:

- HB / HB-derived carrier: timing, freshness, correlation, carriage; no authority;
- Interlock/InTr: transition admission and movement;
- WorkerCoordinator: task-specific claim/fence where required;
- TV/TVC: sole credential authority;
- resident/current-device runtime: execution/consumption;
- Master Records: retained evidence and reconstruction.

No second heartbeat, scheduler, WorkerCoordinator, credential path, or runtime is introduced.

## Initial entity consumers

The contract applies immediately as a source/governance rule to:

- StegVerse-001 / Beta_Orionis bounded-autonomy consumer;
- StegVerse-002 organizational runtime/self-characterization and observation consumers;
- SV-011 governed autonomous entity consumer;
- future organizational AI entities deployed through `<ORG>/.github`.

Runtime adoption for each consumer requires its existing resident execution loop to call governance for each next transition rather than projecting a human approval step.

## Non-claims

This source rule does not prove any entity is currently alive, resident, supervised, or executing.

It does not grant authority.

It removes per-transition human approval as a default orchestration requirement and defines the correct machine-owned governance loop.
