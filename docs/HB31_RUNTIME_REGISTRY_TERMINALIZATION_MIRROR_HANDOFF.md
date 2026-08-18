# HB31 Runtime Continuity Architecture Correction Mirror Handoff

Updated: 2026-08-18T18:04:00-05:00

## Authority and scope

This handoff corrects an architectural error introduced after HB31 continuity was already proven. G18 registry terminalization and a task-capable WorkerCoordinator cycle are **not** prerequisites for heartbeat completion and must not become downstream activation gates merely because a stale G18 projection still exists.

```text
goal_id: SHWP-DURABLE-RUNTIME-ACTIVATION
repository: StegVerse-Labs/.github
canonical_branch: main
canonical_issue: StegVerse-Labs/.github#59
canonical_handoff: handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json
carrier_runtime: heartbeat_runtime.engine_v12.HeartbeatRuntime
worker_runtime: heartbeat_runtime.worker_runtime.WorkerCoordinator
credential_authority: TV/TVC
github_token_runtime_authority: NONE
third_party_role: FALLBACK_ONLY
render_allowed: false
```

## Directly observed heartbeat state

```text
legacy control/heartbeat-state.json: HB29 / generation 29 / immutable
carrier control/heartbeat-carrier-runtime-state.json: HB31 / generation 31 / ACTIVE
worker control/worker-runtime-state.json: observed HB31 / generation 31
transition receipts/heartbeat-transition-continuity/latest.json: CARRIER_TRANSITION_COMPLETE
transition release_state: RELEASE_COMPLETE
all_release_predicates_pass: true
state_reconstruction_pass: true
no_duplicate_claim_or_fence: true
```

Heartbeat continuity is therefore **released and complete at HB31**.

## Corrected architecture

The heartbeat carrier and WorkerCoordinator are separated concerns. The carrier does not wait for worker-registry lifecycle cleanup to become complete, and downstream tasks do not inherit stale worker bookkeeping as a prerequisite.

The following are now explicitly prohibited as heartbeat-completion or downstream-activation prerequisites:

1. G18 becoming terminal in `control/worker-registry.json`;
2. G18 disappearing from `control/worker-control-plane-coordination.json`;
3. a task-capable WorkerCoordinator cycle occurring merely to prove heartbeat completion;
4. advancing the carrier merely to force G18 cleanup;
5. waiting for another machine, hosted runtime, or third-party provider.

The existing G18 projection may be reconciled later by worker-registry maintenance, but that reconciliation is housekeeping only. It does not gate the already-released carrier and does not gate model, inference, trade, or other downstream tasks.

## Downstream continuation

Downstream work may consume the existing HB31 `RELEASE_COMPLETE` evidence directly under its **own** task authority, claim, fence, and TV/TVC route/credential rules.

For Ecosystem Chat / sovereign inference this means the next required execution is the task's own recovery/fresh-authority path and then:

```text
StegVerse local model
-> TVC ROUTE_ADMITTED / credential requirement NONE
-> LLM-adapter execution
-> measured usage
-> same-execution Master Records reconstruction
```

No downstream task may require successful G18 cleanup unless that task independently defines and justifies such a dependency in its own contract.

## Stale G18 projection

`control/worker-registry.json` and `control/worker-control-plane-coordination.json` may still show G18/fence18. That is a stale lifecycle projection, not a heartbeat blocker. Do not manually mutate the live registry or fabricate worker responses from a chat/session lane.

Permitted treatment:

```text
registry maintenance / stale-projection reconciliation: allowed under its own authority
gating heartbeat release on that reconciliation: prohibited
gating downstream activation on that reconciliation: prohibited
manual claim/fence mutation from this session: prohibited
```

## Collision and authority boundary

```text
manual heartbeat epoch fabrication: PROHIBITED
legacy heartbeat-state.json rewrite: PROHIBITED
GitHub Actions production/runtime/control-plane authority: PROHIBITED
NON-TV/TVC secrets/tokens: PROHIBITED
Render: PROHIBITED
third-party fallback promoted to required dependency: PROHIBITED
```

## Completion predicate

Heartbeat completion is already satisfied by the persisted HB31 transition and release evidence:

```text
carrier HB31 ACTIVE
AND transition CARRIER_TRANSITION_COMPLETE
AND release_state RELEASE_COMPLETE
AND state_reconstruction_pass true
AND no_duplicate_claim_or_fence true
```

G18 registry terminalization is **not** part of this predicate.

The session remains open only for genuinely unfinished adjacent goals such as sovereign inference activation, Site #388 exact publication proof, and current-phone trade proof—not for G18 cleanup.
