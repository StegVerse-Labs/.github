# KV-SKAP-VAULT-FUNCTIONAL-001 mirror handoff (PROPOSED identity, registration request only)

This file projects a **request**. It is not the Task Registry, it mints no authority and it bumps no registry generation. The identity `KV-SKAP-VAULT-FUNCTIONAL-001` is a proposal (`NONE_PROPOSAL_ONLY`). It becomes canonical only when `scripts/canonical_task_registration_transition.py` applies it, after its collision check-in reaches CONTINUE.

- Request: `tests/fixtures/canonical_task_registration/i1-goal-manifests/KV-SKAP-VAULT-FUNCTIONAL-001.request.json` (NEW_IDENTITY)
- Allocation request: `control/goal-task-allocation-requests/lane-d-kv-skap-vault-2026-10-23.json` (cosv_task_vector null; the transition derives the vector from the declared exact metrics)
- Source: the owner's priority for after the operating-mode ladder, a functional KV with a SKAP Vault inside KV, relayed by Coordination on 2026-10-23 under StegVerse-org/.github#160
- Sealed scope (GOAL_SCOPE_SEALED): `sha256:95f060fcc2b2455908c838fbcada36eb80b05cad2bf15b8a0b9607cd4672d9dc`. Changing the goal, the targets, the predicates or the finish point needs a new digest and a `control/goal-scope-supersede-requests/` entry.
- Resealed for LC-KV-09 (class A; StegVerse-Labs/.github#3330 `scoped-tasks/LC-KV-09.json` @7fb472a2). Four constraints are now sealed predicates, placed before `FINISH_POINT_VERDICT_REACHED_AT_E0_WITHOUT_LLM`: `KV_REACHABLE_ONLY_VIA_INTR_FROM_HEALTHY_NODE`, `SKAP_VAULT_REACHABLE_ONLY_FROM_INSIDE_KV` (renamed in the reseal below), `SKAP_ACCESS_REQUIRES_PRIOR_LAYER1_KV_ACCESS_RECEIPT` and `ENDPOINT_NOT_A_GITHUB_ORGANIZATION_MEMBER`. The previous digest was `sha256:d68e239bd1eeabe6558b52928632e9e1df35656e55b3f899755924e66b862ada`. No seal exists on main, so `supersedes_scope_digest` stays null. The paired `runtime.kv_skap_vault` `SCOPE_DIGEST`/`PREDICATES` change is in StegVerse-Labs/continuity-vault-kit#263.
- Resealed again, no intra-org InTr hop (class A; Coordination's rule relayed on StegVerse-org/.github#167: InTr runs only between distinct orgs, never inside one org; the SKAP Vault sits inside KV, so KV reaching it is an in-KV gate, not an InTr crossing). The layer-2 predicate that named an InTr hop from KV is renamed `SKAP_VAULT_REACHABLE_ONLY_FROM_INSIDE_KV`; nothing else in the scope changes. The previous digest was `sha256:d4a98dc0c0ff9db7dbc05b1b97d93573dda7b59dcd2a7628e2cf6620e26c7ef2`, and no seal exists on main, so `supersedes_scope_digest` stays null. Kept: KV is reachable only through InTr from an admitted healthy node (layer 1); SKAP access requires a prior layer-1 KV access receipt, enforced by the in-KV gate; the SKAP Vault, inside KV, is the only PII and credential store for every user, the ecosystem included. The paired `runtime.kv_skap_vault` change is in StegVerse-Labs/continuity-vault-kit (branch `laned/kv-skap-no-intra-org-intr`).

## Finish point (test-verifiable)

- Acceptance test: `StegVerse-Labs/continuity-vault-kit:tests/test_kv_skap_vault_finish_point.py::KvSkapVaultFinishPoint::test_finish_point_verdict`
- Predicate `KV_SKAP_VAULT_FINISH_POINT`: `python -m runtime.kv_skap_vault finish-point` returns `ALLOW`, which means every expected evidence predicate is ALLOW over one receipt-hash lineage. Until then it returns a six-field FAIL_CLOSED that names each unmet predicate.
- Lowest supported mode: E0 (ecosystem only, no LLM, Python stdlib)

## Authority (unchanged, not duplicated)

- KV/SKAP Vault is the only user verifier.
- TV/TVC is the credential authority and the sole writer of SKAP ciphertext custody. The vault holds custody-key references only.
- Interlock/InTr is the transition authority.
- WorkerCoordinator owns claims and fences.

## Adjacent, not equivalent

- STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001 is the shell that consumes this goal.
- STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001 is the single-device lane. This goal depends on it.
- TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001 owns the durable sovereign-KV custody location (provider-neutral write and exact-hash readback). This goal consumes it as a class B dependency and does not re-implement it. The vault's KV_DURABLE_CUSTODY_LOCATION_NOT_BOUND item names it as owning_existing_goal.
- SS-KV-SKAP-SOCIAL-RELEASE-001 consumes KV/SKAP for StegSocials release grants. It does not own it.

Coordination ruled this adjacency class D (adjacent, not a duplicate) on 2026-10-23. The ruling is conditional on three checks, all verified:
(a) the component sets are disjoint;
(b) the finish-point test exercises none of the three goals' components. continuity-vault-kit#258's test loads only `runtime.kv_skap_vault` and `runtime.secret_field_policy`;
(c) the custody relationship is a consumes-dependency.

The evidence is in the request's `collision_analysis` and in MANIFEST.json `coordination_adjacency_ruling`.

The collision check-in has no input for a ruling, so it still returns COORDINATE_CONVERGENCE with the three goals (see MANIFEST.json `expected_plan`). Applying the identity needs either that ruling admitted at apply time or a ruling input in the check-in. Both are owned by STEGVERSE-CANONICAL-WORK-COORDINATION-001.


## 2026-10-29 read-only reconciliation (proposal remains unregistered)

All 234 diagnostic input Git blobs were verified at
`3d4c7c163ecc75fd41feb9d003ef61c54ef096de`; they are unchanged at observed main
`7582e93b69548a8bd831ebd89d7dd49492281bce`. Native plan evaluated all 214 shard
files, 120 aggregate rows and 16 omitted owner-held collision guards. Registry
generation remains 322. The current task returns `STOP_NOT_REGISTERED`.
The scratch-derived successor returns `COORDINATE_CONVERGENCE`, zero hard
collisions, with these three adjacent tasks:

- `TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001`
- `SS-KV-SKAP-SOCIAL-RELEASE-001`
- `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001`

Scope digest remains
`sha256:95f060fcc2b2455908c838fbcada36eb80b05cad2bf15b8a0b9607cd4672d9dc`.
The derived COSV is a plan only; no canonical COSV is assigned by this note.
The native planner used its intentionally empty CI session-event ledger;
mechanical all-shard coverage is not semantic owner approval or native apply.

Recovered Coordination ruling:
https://github.com/StegVerse-org/.github/issues/167#issuecomment-6392179558.
It confirms CONSUMES_DEPENDENCY, not FOLD, for the protected custody adapter.
This corrects the earlier absence of an observed ruling reference; it does not
constitute current native admission. Registry/Coordination must bind authentic
ruling evidence and reconcile current pins in the existing native transition,
serialize against #3380 and successors, apply only after CONTINUE, and read back
the admitted row, vector, scope seal and organization receipt.

Consumer repair and exact-source evidence:
https://github.com/StegVerse-Labs/continuity-vault-kit/issues/279.
The locally prepared TVC authenticity containment patch passes 40 relevant
tests. README and CVK handoff updates are prepared in that owner patch.
The original TVC, StegOS, LLM-adapter and CVK owners retain their work; tests or
reference-only receipts do not establish native custody or runtime completion.

Still unobserved: admitted registration/COSV, WorkerCoordinator claim/fence,
sovereign KV __51 write plus exact-hash readback, and a manifest-bound real-node
finish-point ALLOW with native organization receipt. No native apply, merge,
sovereign KV write, new authority or new machine occurred in this reconciliation.
Session Prompt Count: 1. Cumulative Goal Prompt Count: unverified; add this one
qualifying prompt to the existing count without resetting it.


## 2026-10-29 continuation: reviewable repair and corrected dependencies

Session Prompt Count: 2; cumulative Goal Prompt Count remains unverified and is
not reset. Labs main `6b13c3a749b2940d6142644196a8302823c1f45a` retains all 234
previously verified Registry input blobs unchanged (generation 322, 120 rows,
214 shard files). The canonical task row, COSV and lifecycle state remain
unassigned; do not project this proposed identity as an admitted task.

The consumer repair is now a draft source PR:
https://github.com/StegVerse-Labs/continuity-vault-kit/pull/280
Head `7b55199ceb59569f5d71c8784ec4213dba631c18`; base
`b1a66008dccad0d301a7e892e6619f47002ec26d`. All 40 selected local tests pass.
Six new authenticity regressions are folded into the existing finish-point
suite and its existing CI runner. Runtime, tests, README and CVK handoff are
committed on that review branch. Hosted CI and independent review must be
read at the exact current head; no merge or runtime authority is implied.

Correction to earlier coordination plans: LLM-adapter #431 was explicitly
closed unmerged as superseded, and Org #249 removed the organization-to-adapter
edge at `89558cd333c311924e7f282a1ab97e113adb7a23`. Do not initialize the retired
namespace or rebuild that route. Lane B must reconcile #430's stale #431
admission-order/genesis references with the retained healthy-node-to-adapter-
to-SDK path, preserving the existing evaluator and authority boundaries.
Sources: https://github.com/StegVerse-org/LLM-adapter/pull/431#issuecomment-6391809461
and https://github.com/StegVerse-org/.github/pull/249.

New browser-node observations are reported in Labs #3402 and its paired
CLAUDE_NODE_KV_SESSION__RECORD__01.md coordination file. They are not
independently verified runtime completion or native KV authority. The report
includes profile-local continuity and service-worker repair findings; route
those to the existing Site/StegOS owners without treating a second device or
resident process as a requirement. Its two-hop SKAP wording must be reconciled
by Coordination with the current sealed no-intra-org-InTr predicate; this
document does not silently change the goal or scope digest.

Parallel work: Registry owner binds authentic ruling/current pins and reaches
CONTINUE before native apply/readback; TVC owner supplies authenticated live
custody issuance; CVK owner reviews #280; StegOS/adapter owners reconcile and
review their retained lanes; WorkerCoordinator owns claim/fence after admission;
the native custody owner supplies sovereign KV __51 exact-hash readback.
Coordination-folder writes are projections only, never substitutes for __51.
