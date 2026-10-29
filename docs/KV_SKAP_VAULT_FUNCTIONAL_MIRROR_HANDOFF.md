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

The registration transition already accepts `--adjacency-ruling` and `--finish-point-root` through `checkin_with_ruling`. It may clear COORDINATE_CONVERGENCE only after recomputing the ruling conditions and covering every collision candidate; STOP_COLLISION is not cleared. Remaining owner work is to authenticate Coordination provenance, reconcile current source pins and candidate coverage, commit the approved native request, and serialize plan/apply/verify against the accepted Registry tip. Source support does not itself register this identity or grant execution authority. See scripts/canonical_task_registration_transition.py on main and the recovery-session-2 reconciliation below.


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
Head `d127e2dc3de1c81f99b3a6e8381541fad5e6157d`; base
`b1a66008dccad0d301a7e892e6619f47002ec26d`. All 45 combined finish-point and E0 witness tests pass locally.
Six new authenticity regressions are folded into the existing finish-point
suite and its existing CI runner. The initial CI run exposed obsolete E0 witness ALLOW assertions, now repaired
to require FAIL_CLOSED without appending; the guard is unchanged.
Runtime, tests, README and CVK handoff are
committed on that review branch. Hosted CI at that head reports 50/50 successful check runs (run 40876524643).
Independent review remains pending; CI success implies no merge or runtime authority.

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

## 2026-10-29: independent public InTr readback (session prompt 5)

Executed TVC evidence branch replay.sh against anonymously fetched public ledgers.
Source heads: Labs 6b13c3a749b2940d6142644196a8302823c1f45a;
Org 0b50df09f620304319f99de58af081aa8902c37e. Ledger commits:
Labs b2d90fc301fe0ced4fd5d68dc0734342e59f8cea;
Org 07307cb748e93283fbd236047f8c13cbd1d8002f.
Four native readbacks and four end-to-end results match all eight published
SHA256SUMS byte digests. Both Labs-to-Org and Org-to-Labs return ALLOW under both
verifiers. This is independently executed public route evidence, not a new
transition, private-ledger warrant, KV issuance witness, task admission, fence,
sovereign KV __51 or vault finish-point ALLOW. No full mesh rerun is claimed.

Reproducer and expected outputs:
https://github.com/StegVerse-Labs/TVC/tree/claude/intr-readback-evidence-20261029/evidence/intr-readback-2026-10-29

New adjacent custody finding is independently reported in Labs #2810 comment
6497851220: complete-chain organization custody reader refuses a sealed test-suite
source schema at f840271e. Existing custody owner must migrate its pinned reader
seam consistently, preserving seal/digest/identity checks and regenerating pins;
public route ALLOW does not repair that distinct reader failure.

CVK#280 current head ab66f0eb50cd05280a14f5668ec700ea556bb560 has 45 selected tests
and 50 successful checks from the previous verified run; still draft/unmerged.
Claude's source review applies to parent d127e2d, with follow-up review outstanding.
Canonical Registry remains gen322/120 with no proposed goal row. Native registration
and COSV remain unassigned. Cumulative Goal Prompt Count remains UNVERIFIED.

## Session10 clean handoff — 2026-10-29

CVK#280 is MERGED at acfd2be5763fea22ea7c859cf493dab24f1f3ac8, now CVK main.
GitHub compare against reviewed ab66f0e has zero changed files, one merge commit
ahead and zero behind. All43 returned merge-head check runs succeeded. This
retires the source-integration wait for the authenticity containment; it does
not provide native TVC issuance or finish-point ALLOW. CVK issue279 remains open.

Custody repair packet session9 is the latest candidate: native-generated one-entry
manifest update, unchanged dependency closure, historical P1 vendor preserved,
and regressions in the existing catalog-selected suite.100tests+8subtests pass.
Fresh-base application check on6b13c3a7 reconstructs all7 candidate files exactly.
Patch SHA256d4ff0f33a5afb04b07010f8249cd01c7c5b31afea83d5bbd606d73304dc31236.
Original custody owner must review/commit it and obtain hosted CI and authorized
integration. Do not apply superseded session7/8 packets. Source evidence and
owner steps: Labs#2810 comment6502739653. No candidate custody authority inferred.

Registry generation322 still lacks the proposed goal. Original Registry owner
owns ruling/current-pin authentication, three-adjacency convergence, serialized
native apply and COSV readback. TVC537 issuance/verifier, retained adapter route
and3402 scope clarification remain parallel; then task-bound WorkerCoordinator
fence, sovereign KV__51 and real-node finish-point/organization receipt.

Public InTr8/8 evidence remains verified historical route evidence. Shared
coordination writes through session6 succeeded; session7 packet/note uploads
were rejected by automatic approval review. Session7-9 source transfers were not
retried and are not present/read back in the shared directory. Specific sharing
approval remains outstanding. Do not confuse this with sovereign KV custody.

Session Prompt Count10. Goal Prompt CountUNVERIFIED, not reset; native Goal/COSV
unassigned. Continue from current Registry and owner replies, preserving evidence
classes and existing owners. No native admission, fence, sovereign write or
finish-point ALLOW was performed by this session.


## Session12 handoff — 2026-10-29

Current-truth correction: existing custody owner PR3376 at
`d810644ddc6ce290dd1a21f75c7c12d8c3fe05df` is the convergence target, stacked on
#3290. The separate session9 candidate is comparison evidence, not a competing
integration instruction. The earlier sentence directing its review/commit is
superseded by this section. Original owner retains source and integration control.

Read the public owner parity suite at that exact head: it covers valid sealed
readback/batch/export, missing seal, forged source, empty head identity, schema
rejection, resealed binding/class/operation mismatches, and canonical-only Master
Records handling. Further review should locate coverage for missing retained
source, organization seal/owner rejection, every binding field and each empty
identity component across existing suites before adding tests. These are scoped
coverage questions, not demonstrated vulnerabilities or claims of missing global
coverage. No rejected patch payload is included or transferred here.

Docs PR3404 at d8a2efaa4b8bd3afd01c875c598e50a437640bfd had all six check runs
completed SUCCESS, including ratchet and required-verification. This handoff
update creates a new head requiring its own checks; prior success is historical.
CVK280 containment remains merged; do not repeat that integration wait.

Parallel owner work remains Registry ruling/pins/adjacencies and serialized
admission/COSV; TVC537 authenticated issuance; CVK279 consumer verifier; custody
3376 convergence; StegOS426 identity contract; adapter430/429/428 producer and
health integration;3402 scope/node findings; independent docs review. StegOS and
adapter placement text still naming retired431 must be reconciled with Org249
and the retained healthy-node-to-adapter-to-SDK path before integration. No new
node registration or repair attempt is authorized by3402's observation record.
Actual WorkerCoordinator fence, sovereign KV__51 and real-node ALLOW follow the
required native admission/evidence; preparation can proceed concurrently.

Live main6b13c3a749b2940d6142644196a8302823c1f45a: Registry322,120rows, proposed
KV identity absent. Goal/COSV/lifecycle and cumulative count remain unverified.
Session Prompt Count12; resume in a new session using current Registry and this
handoff. Session11 inventory: org#167 comment6503932798. Native registration,
claim/fence, sovereign mutation and runtime ALLOW were not performed.
Shared source-packet/note transfer remains unperformed after the prior automatic
approval rejection; exact payload/destination approval remains required. Do not
retry through another transport. Existing shared checkpoints stop at session6.


## Recovery session 1 — 2026-10-29 (after prior session 12)

Live main remains `6b13c3a749b2940d6142644196a8302823c1f45a`.
Read Registry blob `ea0c6d61881da8b19398e7becbb62d9e727a4379` through
Git data because the contents endpoint returned an empty body. The actual
Registry is generation 322 with 120 rows; this proposed identity is absent
from both the aggregate and the canonical-record shard inventory. Goal ID,
COSV and canonical lifecycle remain unassigned. Session Prompt Count resets
to 1; cumulative contribution is at least 13 prompts from the recovered
12 plus this prompt, not a reset or a reconciled canonical Goal Prompt Count.
The Registry owner must reconcile the total when admitting the identity.

All six checks on docs head `3b03211a4943484d748c3395d61ed41b611fe5bd`
completed SUCCESS, including ratchet and required-verification. This retires
that CI-pending item. This documentation update creates a new head whose
checks must be evaluated separately. The existing COMMENT review is at
`d141afef`; no current-head independent APPROVE or protected merge is claimed.

The session-12 custody coverage questions were narrowed against existing
owner PR #3376 at `d810644ddc6ce290dd1a21f75c7c12d8c3fe05df`:

- Existing canonical-source tests cover missing retained source in readback
  and export; an existing batch test covers organization-receipt hash tampering.
- The shared verifier checks the organization seal/hash, schema and owner
  before selecting its sealed-source branch.
- The sealed parity suite directly covers three of five nullable binding
  fields and empty head_sha. Focused cases not located in the nine inspected
  relevant test files are non-null repo_transition_id and
  subject_or_correlation_id, empty receipt_kind/repository, and a correctly
  re-sealed wrong organization owner. These are bounded coverage opportunities,
  not demonstrated defects or claims about all repository tests.
- Preserve existing production code and pins. Any additional cases belong in
  the existing owner's parity parametrizations, with valid controls and
  re-sealing so the intended guard is reached. No competing patch was created.

Detailed source references and exact owner steps:
https://github.com/StegVerse-Labs/.github/issues/2810#issuecomment-6504630611.
This is source inspection; prior local/hosted test results were not re-executed.

Independently read TVC main-push run `40917305561`, job `123600841295`,
head `dbfccec958c107b97177fe28865e5ef7a2aea46e`. Parsed the actual Labs
receipt and recomputed its canonical SHA256, matching
`2e0ec2ddf99dd53b8a42d8bd2f1f4253871da2b3a7068ce69027b3ffdf1a5ed2`.
Receipt disposition ALLOW: 25 tests, zero failures/errors/skips; job reports
nine subtests. It explicitly declares candidate=true and
appended_by_this_job=false. The published Labs ledger ref remains
`b2d90fc301fe0ced4fd5d68dc0734342e59f8cea`. This is TVC conformance evidence,
not SKAP custody issuance or organization-ledger acceptance.

The existing #3183 comment6504428668 supplies the prepared ingest-request
preflight to the original writer. Next: authenticate provenance, use the
existing ingest route with genuine supplied epoch, read back the published
append and native consumer result, then evaluate #3290 -> #3376 required
verification and protected integration. Current #3376 still has six successful
and two failed check runs. No gate is weakened or receipt fabricated.

Other existing owners retain Registry ruling/pins/admission, TVC537 issuance,
CVK279 verification, StegOS426 identity and adapter430 healthy-node integration.
No newer responses were observed in those checked issue threads. Native
claim/fence, sovereign KV __51 and real-node finish-point ALLOW remain unobserved.
The prior optional source-packet/note sharing approval remains outstanding;
no transfer was retried and no shared-folder or sovereign KV write is claimed.


## Recovery session 2 — 2026-10-29: corrected admission path and TVC consumer containment

Session Prompt Count: 2. Cumulative contribution recovery lower bound: 14;
canonical Goal Prompt Count remains unreconciled, not reset. Main remains
`6b13c3a749b2940d6142644196a8302823c1f45a`; Registry322/120 still has no KV row.
All six checks on docs head `2e611f345329f4478a5764f45b2d12cbac34044e` passed.
This update requires separate exact-head checks and original-owner ratification.

The opening ruling-input paragraph was corrected against the implemented native
entrypoint. Source support is complete; provenance/current-pin/candidate
reconciliation and an approved native request remain the Registry owner's work.
The ruling still pins CVK9d56bc7b while current CVK main isacfd2be5; re-derive,
do not blindly change the pin. Open3380/3403 do not reserve a generation.
https://github.com/StegVerse-Labs/.github/pull/3324#issuecomment-6505523334

Retired coverage-discovery work: EC9 already executed the seven supplemental
sealed-source probes at3376d810644d (reported7PASS). Their retained code was
inspected, not re-executed here. These resolve the specific prior questions;
permanent folding remains the existing custody owner's source update.
https://github.com/StegVerse-Labs/.github/issues/2810#issuecomment-6505523865

New executed consumer evidence: actual TVC537 issuer/verifierc87272cf combined
with main custody gate dbfccec9, twelve exact Git source/config blobs verified,
and existing test-only ledger/signer/reader/producer/client fixtures. The actual
issuer/verifier was not mocked. Reference-only issuance for matching/unrelated
principal, unrelated task, and a self-rehashed BOUND assertion reaches gate ALLOW.
The manifest currently has no task field; no existing task-field mismatch is
claimed. Final regression baseline:4expected failures/3passes. A local candidate
returns six-field TVC_CUSTODY_ISSUANCE_AUTHENTICITY_NOT_PROVEN after integrity
verification and before client/admission use:7/7focused tests pass.
No client place/read calls or live runtime/credential access occurred.

Full patch, test, hashes and owner README/TVC-handoff addenda:
https://github.com/StegVerse-Labs/TVC/pull/537#issuecomment-6505597487
Cross-consumer coordination:
https://github.com/StegVerse-Labs/continuity-vault-kit/issues/279#issuecomment-6505604924
Patch SHA256:22f5d0cb858592c771f37a2372d73d97b799b11179e191ca84b6499b2a8cd8b5.

This is a local unmerged containment proposal, not full-suite green or
merge-ready. It intentionally removes the ALLOW path until the existing TVC
owner supplies authentic issuance linkage to principal/manifest/task/reference,
live slot and current revocation state. No caller flags, new callbacks, trust
roots or task-schema fields were invented. Existing fake-positive suites require
explicit component-test migration;22fixture consumers were inventoried for
review, not demonstrated as22failures. Current production prerequisites remain
absent and fail closed; this is not a live exploit or native custody claim.

Parallel owner actions: Registry admission/ruling/current pins and counts;
original writer3183 accepts the already prepared TVC-main conformance receipt
using genuine supplied epoch, then3290->3376 required checks/integration;
TVC537 reviews containment and authentic issuance contract, with CVK279 consuming
the same authority; StegOS426/adapter430 reconcile retained node placement and
health; Coordination3402 resolves scope observations; docs3404 gets independent
ratification. Published Labs ledger ref remainsb2d90fc3; no repeat replay on
unchanged input, no native admission/fence/sovereign__51/finish-point ALLOW.

The earlier optional S9 source-packet transfer remains unperformed. It is not
needed to deliver this new public-source finding or continue the owner work.
The new coordination note contains public status/issue links only, not that
rejected packet or note. Coordination-folder writes remain projections, never
sovereign KV custody.
