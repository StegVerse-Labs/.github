# Test Queue Manifold Governance Mirror Handoff

Updated: 2026-08-26T14:53:00-05:00
Repository: `StegVerse-Labs/.github`
State: `SOURCE_MERGED_VALIDATED / RELEASE_TAG_PENDING / NOT_ACTIVATED`

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


## 2026-08-27 feature-branch implementation

Implementation is occurring on the dedicated branch required by this handoff:

```text
branch: feature/test-queue-manifold-governance-v1
frozen main baseline: 4f9961780ef304a8930c7cae50b3d374597d2d52
direct implementation on main: false
affected repository set for first bounded slice: StegVerse-Labs/.github only
```

Branch source surfaces:

```text
control/test-queue-manifold-governance-baseline.json
control/session-implementation-claim-test-queue-manifold-governance-001.json
schemas/test-queue-manifold-descriptor-v1.schema.json
state_language/test_queue_manifold.py
tests/fixtures/test_queue_manifold.v1.json
tests/test_test_queue_manifold.py
```

Current source implements and tests:

- generalized, hash-bound test descriptors with no person-specific route;
- deterministic manifold snapshots and coherency groups;
- readiness from explicit dependencies, capabilities, and evidence;
- optional HeartBeat/governed-manifold observation as reference only;
- individual test execution with no HeartBeat dependency;
- candidate minimum-distinguishing bundles that never grant execution authority;
- explicit deferred-equivalent tests instead of silent deletion;
- stale bundle invalidation on manifold version or state-hash change;
- terminal lifecycle dispositions that require evidence;
- SATISFIED_BY_BUNDLE requiring explicit bundle identity and evidence;
- independently admitted claim/fence references for claimed tests;
- capacity scaling that cannot change authority semantics;
- credential_authority=TV/TVC;
- authority_effect=NONE.

Source commits on the feature branch:

```text
baseline: b5475ed0b1f53b1dbe4f14cf4c34a384c20d44a9
claim: 3e343c3ccc985600e19d145db5533d62251f9052
descriptor schema: 2221b90b679f5e487ec39594900423c97bc1b763
controller: be3329187e3104930ead7145e3e93cd1ff40af0c
fixtures: 7fe6938572e3c9ad8bf5204f60516ddcd2225c04
tests: 96102ef00d908f7a1a086ac9ce0545c148d1013c
```

No runtime, merge, release, tag, queue execution, claim/fence issuance, or activation is claimed. The next boundary is exact branch-head CI plus collision review. Merge remains prohibited until that evidence is complete.


## Exact-head validation and collision review — 2026-08-30

The feature branch test-discovery defect was repaired by renaming the test helper so `unittest` no longer attempts to execute a parameterized helper as a test case.

Validated branch head:

```text
head: b8070b33e13f959e0e21dbac1e913b8787722200
organization control plane: 33295942882 SUCCESS
Heartbeat Worker Project: 33295942923 SUCCESS
complete deterministic repository suite: PASS
known scoped scaffolding/stubs: 0
```

Collision review against current main found no existing implementation at the claimed new paths:

```text
state_language/test_queue_manifold.py: absent on main before merge
schemas/test-queue-manifold-descriptor-v1.schema.json: absent on main before merge
tests/fixtures/test_queue_manifold.v1.json: absent on main before merge
tests/test_test_queue_manifold.py: absent on main before merge
```

The implementation does not modify the direct Test Lanes executor, WorkerCoordinator claim/fence authority, TV/TVC credential authority, SDK evaluator ingress, or any person-specific route.

Source merge is now eligible under this handoff. Merge does not satisfy the separately required exact release/tag set or runtime activation.


## Source merge closure — 2026-08-30

The generalized test-queue manifold source is merged on canonical `main`.

```text
original draft PR: #318 CLOSED / SUPERSEDED_BY_NON_DRAFT_MERGE_PR
merge PR: #532
merge commit: 270ea59bec8dd06455a5edbdc59cda9e60d5677d
validated source head: 735480c2d9aa44ae9dfc90aa1b3d731681eaabee
organization control plane: 33296293558 SUCCESS
Heartbeat Worker Project: 33296293517 SUCCESS
known scoped scaffolding/stubs: 0
source implementation: COMPLETE_MERGED_VALIDATED
runtime activation: NOT CLAIMED
```

The remaining release boundary is intentionally separate from source merge:

```text
release tracking issue: #534
required release behavior: NEW EXACT AGGREGATE RELEASE/TAG IDENTITY
historical tag reuse or retarget: PROHIBITED
GitHub Actions runtime authority: NONE
credential authority: TV/TVC
release publication implies runtime activation: false
```

The connected repository tool surface does not expose Git tag or GitHub Release creation, so the exact release mutation is not executable from this session. The release issue is therefore the durable next owner rather than a chat-only task.

After the exact release coordinate exists, downstream pertinence must be verified against the current mirror handoffs in `StegVerse-Labs/Site`, `GCAT-BCAT-Engine/Publisher`, `StegVerse-Labs/admissibility-wiki`, and `StegVerse-002/stegguardian-wiki`. Current search shows no existing test-queue-manifold projection in those repositories, so no downstream mutation is justified before an actual release coordinate exists.


## 2026-09-02 frozen release coordinate

Release issue #534 now has a dedicated scoped handoff:

`docs/TEST_QUEUE_MANIFOLD_RELEASE_MIRROR_HANDOFF.md`

The immutable release coordinate is:

```text
tag: test-queue-manifold-governance-v1.0.0
target: 270ea59bec8dd06455a5edbdc59cda9e60d5677d
release name: Test Queue Manifold Governance v1.0.0
```

Current `main` is later than the source merge, so the tag must point to that exact merge and must not resolve symbolically to current `main`.

The connected GitHub mutation surface can inspect tags/releases but cannot create them. Once the exact tag + release are externally created and observable, issue #537 may proceed with downstream pertinence verification.
