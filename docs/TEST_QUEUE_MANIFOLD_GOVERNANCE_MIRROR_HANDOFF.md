# Test Queue Manifold Governance Mirror Handoff

Updated: 2026-08-26T14:53:00-05:00
Repository: `StegVerse-Labs/.github`
State: `PLANNED / IMPLEMENTATION_NOT_STARTED`

## Scope

This handoff captures the generalized clustered-test queue design discussed for StegVerse. It is a planning/source-of-truth record only. No scheduler, queue controller, runtime activation, tag, or release is claimed by this document.

The design applies to generic users/evaluators and machine clients. ODA3, Eduardo, GLM/EVIDE, and future users/evaluators remain experiment/configuration consumers of generalized SDK/test contracts; they do not receive person-specific queue lanes.

## Governing separation

A single test must remain directly executable without HeartBeat, G18, or WorkerCoordinator as a prerequisite.

When multiple tests arrive in clusters, HeartBeat may provide observation cadence/reference sampling for a test-queue manifold controller. HeartBeat does not authorize a test, choose credentials, mint claims/fences, or become the execution clock.

```text
heartbeat role: observation / reference sampling
heartbeat grants test authority: FALSE
snapshot grants test authority: FALSE
execution authority: independent admitted claim/fence or applicable canonical executor
credential authority: TV/TVC ONLY
person-specific test lanes: PROHIBITED
```

## Test manifold model

The queue is modeled as an evolving set of generalized test descriptors rather than a FIFO-only list. Descriptor dimensions may include goal/transition, source/target state, transition class, required capabilities/evidence, dependencies, authority class, cost/capacity, urgency, expected information gain, coherency group, canonical input/hash identity, and lifecycle state.

The controller may derive, without granting authority: coherency groups, admissibility/readiness matrices, state/queue gradients, cost/capacity pressure, expected information gain, minimum distinguishing test sets, and candidate transition bundles.

A test may leave the pending set only through an evidenced transition such as `SUPERSEDED_BY_EVIDENCE`, `SATISFIED_BY_BUNDLE`, `NO_LONGER_APPLICABLE`, `EXECUTED`, or another versioned canonical state. Optimization may not silently delete requested tests.

## HeartBeat sampling loop

```text
HB(n) observation
-> acquire queue manifold Q(n)
-> compare with Q(n-1)
-> derive state/coherency/gradient changes
-> update admissibility/readiness
-> select candidate executable bundle
-> independent execution authority/fence
-> execute admitted tests
-> retain results/receipts
-> next observation samples the changed manifold
```

Queue pressure may inform capacity decisions or a future phase-shifted observation lane, but it must not alter the independent base oscillator or convert HeartBeat into scheduler/approval authority.

## Relationship to current Test Lanes

Canonical direct 9-lane execution remains governed by `docs/STEGVERSE_TEST_LANES_DIRECT_RUN_MIRROR_HANDOFF.md`. That experiment explicitly requires no HeartBeat/G18/WorkerCoordinator prerequisite. This manifold work is a future orchestration layer for clustered arrivals; it must not reintroduce those dependencies into individual test execution.

The SDK remains generalized ingress for users/evaluators; queue/manifold scheduling belongs downstream of SDK experiment declaration.

## Related canonical surfaces

- `StegVerse-Labs/.github/docs/GATE_PASSBAND_REFERENCE_SNAPSHOT_MIRROR_HANDOFF.md` — non-authorizing reference snapshot/reacquisition semantics.
- `StegVerse-Labs/.github/docs/HEARTBEAT_RUNTIME_SEPARATION_MIRROR_HANDOFF.md` — oscillator/runtime authority separation.
- `StegVerse-Labs/.github/docs/STEGVERSE_TEST_LANES_DIRECT_RUN_MIRROR_HANDOFF.md` — heartbeat-independent individual 9-lane execution.
- `StegVerse-org/StegVerse-SDK/SDK_MIRROR_HANDOFF.md` and `docs/EVALUATION_RELATIONSHIP_MIRROR_HANDOFF.md` — generalized user/evaluator ingress; no person-specific evaluator route.
- `GCAT-BCAT-Engine/workflows/experiments/stegverse-test-lanes` — portable Test Lanes experiment/evidence owner.
- `StegVerse-Labs/TVC` — credential/provider execution authority where required.
- Master Records / applicable receipt custody surfaces — durable reconstruction of queue decisions and test outcomes.

## Implementation discipline

User requirement: this feature MUST NOT be implemented directly on `main`.

Required implementation lifecycle:

1. freeze exact baselines for every affected repository;
2. create dedicated feature branch(es);
3. implement generalized schemas/controller/fixtures without evaluator-specific routes;
4. validate focused and cross-repository behavior on branch heads;
5. merge only after complete validation and collision review;
6. record exact merged commits;
7. construct a new exact aggregate release set for every affected released repository;
8. tag/release exact merged commit set; do not move/reuse historical tags;
9. activate only after release/evidence verification.

Existing frozen release candidates must not be rewritten to absorb this future feature. A later queue/manifold implementation requires a new release-set identity if it changes released surfaces.

## Planned validation requirements

Future implementation must prove at minimum: individual test execution remains heartbeat-independent; clustered grouping is deterministic and versioned; no test is silently dropped; minimum-distinguishing-set decisions are reconstructable; stale queue instructions are invalidated by state changes; HeartBeat/reference snapshots cannot grant execution/credential authority; claims/fences remain independently admitted; queue decisions/results can be replayed/reconstructed; capacity scaling does not change semantics/authority; and ODA3/Eduardo/GLM/EVIDE use generalized contracts rather than bespoke lanes.

## Current completion accounting

```text
design captured: COMPLETE
canonical scoped handoff: THIS FILE
implementation: NOT STARTED
validation of future implementation: NOT STARTED
integration: NOT STARTED
merge of future implementation: NOT STARTED
release/tag of future implementation: NOT STARTED
runtime activation: NOT STARTED
user action required now: NONE
```

## Next executable boundary

Before implementation, identify the exact affected repository set and current release baselines, then create implementation feature branches. Do not mutate `main` for this feature.
