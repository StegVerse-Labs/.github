# SDK Untrusted Dependency Execution Boundary — Mirror Handoff

Updated: 2026-09-23
Goal Task ID: `SDK-UNTRUSTED-DEPENDENCY-EXECUTION-BOUNDARY-001`
COSV: `71000000111111` (existing SDK experiment task-family vector; canonical registration validation pending)
Status: ACTIVE / HANDOFF_READY (coordination only); no WorkerCoordinator claim, runtime authority, deployment or authentic proof.

## Scope and ownership
Distinct security test for *untrusted executable supply-chain ingress*: package install/build hooks, recursively fetched or substituted dependencies, IDE workspace tasks/settings, AI-generated code and external repository bootstrap. An authorized SDK manifest or worker does not confer implicit install-script, host filesystem, credential, network, shell, or consequential-tool authority. Protect existing SDK and StegBrowser/StegOS worker ingress without another execution engine, sandbox, scheduler, dispatcher, authority plane, credential issuer, ledger or device prerequisite.

Collision neighbors:
- `ECOSYSTEM-INGRESS-AI-BOUNDARIES-001` is ACTIVE/CHECKED_OUT and owns the reusable component-011 AI defensive envelope, existing TVC SES representative isolated-process probe and resident dispatcher. Reuse this capability boundary. Do not edit its owned sources, duplicate its probe, or claim SES is proven arbitrary-code OS containment.
- `SDK-MICRO-NODE-COMMIT-TIME-ADMISSIBILITY-001` owns independent multiworker commit-time evaluation and the SDK #309 non-authorizing source contract; do not duplicate its worker or standing logic.
- `SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001` owns constitutive WorkerCoordinator claim/fence, TV/TVC warrant, InTr ACTIVATE+CREATE_AND_BIND, canonical Master Records closure, retirement and records-only reconstruction. Consume exact authentic receipts, not fixture assertions.
- `CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001` and `ORGANIZATION-BATCH-CUSTODY-REPLAY-001` own immediate-predecessor and organization/global custody.

## Source facts to preserve
Existing SDK release dependency alignment verifies exact VCS pins for governed-test dependencies, but pins identify bytes, not safety or scoped authority. The SDK's reproducible-release documentation explicitly says its private governed-test dependency set is not anonymously installable. Existing component-011 TVC SES stdio probe demonstrates a bounded source-tested candidate boundary and denied sample filesystem/network/environment probes; authentic resident consumption, general arbitrary install-script containment and external-provider origin are not established.

## Threat model and manifest compatibility
Freeze `source_revision`, `workspace_tree_digest`, declared direct/transitive dependency identities and immutable artifact digests, build-system hook inventory, trust provenance and target operation before any candidate executes. Treat missing lock/digest, dependency substitution, dynamic nested fetches, executable package hooks, IDE auto-tasks and model-generated commands as separately attributable candidate execution transitions. A repository, manifest, successful lint/build, developer consent or valid WorkerCoordinator claim alone is not installation authority.

Use *existing* SDK manifest extension fields for declared purposes, operation intents and evidence; require explicit distinct TV/TVC-issued, scope-bounded operation warrant and present Interlock/InTr standing at each consequential boundary. Validate that the selected existing execution substrate can actually deny filesystem/network/process/environment/credential access. If isolation is not evidenced, mark `UNKNOWN` and do not execute the untrusted candidate. Never use a receipt as containment proof or grant authority by a package lock hash alone.

## Proposed source-level falsification matrix
1. Harmless pinned dependency install without hooks; confirm only the exact admitted operation and permitted paths.
2. Package install lifecycle hook attempts out-of-scope file write and secret/environment read; refuse execution, preserve denied-operation evidence without exposing secret contents.
3. Nested/transitive dependency substitution or digest mismatch; deny *before* executing any hook.
4. Workspace trust/IDE task that requests automatic shell execution; never auto-grant install or task execution.
5. AI-generated script asks for network egress, tool invocation or credential use beyond explicit warrant; deny and retain independent per-operation evidence.
6. Stale/withdrawn policy or warrant after review but before commitment; re-evaluate current standing and refuse if absent.
7. Unobserved effect, missing evidence, shared-custodian self-attestation or missing exact predecessor; retain UNKNOWN; prohibit ALLOW and terminal proof promotion.
8. Known-good bounded operation followed by worker expiry: stale-fence re-invocation denied; records-only replay reconstructs without re-executing side effects.

Negative controls are inert fixtures with canary paths and non-secret synthetic tokens only. Keep security test execution separate from actual third-party installation and production credentials.

## Required receipt lineage
Per boundary retain operation and package/workspace source digests, exact manifest/policy/current-state and warrant identities, worker claim/fence, declared/requested versus actually granted capabilities, denied attempts, containment method and observer independence, precise source of observations, individual UNKNOWN/dissent, current InTr disposition, egress result, and immediately prior canonical Master Records receipt reconstructed at each successor emission. For closure demand RECORDED, reconstruction_status=PASS, required_evidence_validation_status=PASS, and exact receipt_sha256==reconstructed_receipt_sha256. Organization ledger preserves worker-level and denied-operation provenance; global custody follows existing organization-batch contract. Absence of an OS-level observation cannot prove absence of malicious activity.

## Acceptance and next implementation
First inspect current SDK Manifest Builder/run-manifest extensions, installation paths and hook execution; TVC SES component-011, existing WorkerCoordinator/Interlock/InTr and organization ledger receipts. Implement only the missing adapter/contract validation and nonexecuting negative fixtures where ownership permits; the current component-011 owner must handle any change to its checked-out shared envelope. Add positive/negative source tests and validate exact head. Authentic end-to-end closure additionally requires actual admitted containment evidence, exact TV/TVC and InTr decision at runtime, worker expiry, organization receipts and Master Records reconstruction. CI and source fixtures cannot establish these runtime predicates.

## Current evidence and remaining predicates
Verified from canonical main at Task Registry generation 205: existing component-011 task is ACTIVE/CHECKED_OUT, micro-node task is ACTIVE/HANDOFF_READY with COSV 71000000111111, and existing SDK three-worker non-authorizing contract was reported merged in PR #309. No install-script/IDE-project execution boundary, arbitrary-code sandbox containment, fresh runtime claim/fence, InTr admission or Master Records proof has been observed for this new test. Registry registration merged via .github PR #2597 (squash 7fac73d0821b4410d5fddb79ebd1452eab0d7240) at generation 206. Five exact-head workflows passed: KV AI Memory 35929392397, Cross-Task Coordination 35929392385, Deterministic Repository Suite 35929392329, DeepSeek 35929392365 and Purpose-Bound Lifetime 35929392367. This follow-up proposes generation 207 ACTIVE/HANDOFF_READY coordination; post-activation exact collision check-in, implementation and authentic runtime proof remain pending.

Manual work: None. Do not require a second device or connected-device inventory.


## SDK-only source implementation and canonical evaluator check-in — 2026-09-23

The original registration/activation is merged at canonical generation 207 (ACTIVE/HANDOFF_READY). Exact source reconciliation: SDK `pyproject.toml` declares default dependency version floors and optional exact Git pins for governed-test; `stegverse/release_dependency_alignment.py` verifies declared VCS commit alignment, not install-hook safety, transitive integrity or containment. Existing `stegverse/manifest_contract.py` validates source manifests but explicitly does not grant execution authority. The existing component-011 task owns the TVC SES bounded representative probe, not generalized arbitrary code isolation; no change was made to its checked-out envelope.

SDK draft PR [#310](https://github.com/StegVerse-org/StegVerse-SDK/pull/310) adds `stegverse/untrusted_dependency_review.py`, inert positive/negative `tests/test_untrusted_dependency_review.py`, and wires the exact-head Manifest Builder source-validation workflow. The module accepts descriptor metadata only and always returns `NON_AUTHORIZING_LOCAL_REVIEW_ONLY`; it cannot execute scripts or authorize any operation. The exact head `9105144c3c08273975379cf2e3db259d5c8baf7f` completed twelve source workflows successfully, including fourteen focused inert tests in Manifest Builder run `35932313948`. This is CI/SOURCE evidence only, not executed dependency or independent containment proof.

Read-only source reconstruction of `scripts/evaluate_task_registry_collision_checkin.py` with current registry generation 207 and exact proposed SDK-only component `sdk:untrusted-dependency-contract-and-inert-tests` returns `COORDINATE_CONVERGENCE` because of adjacent Richard, SDK micro-node and canonical MR/org-custody tasks and existing SDK repository co-ownership; no hard checked-out component conflict surfaced for the scoped new module/tests. An explicit owner coordination notice was recorded on .github issue #1620 (comment 5804402084), without modifying shared component-011 source. The older component-011 shard is not currently a top-level row in the 207 canonical registry array; its checked-out status remains documented in its shard/handoff, so a registry-only collision check cannot silently de-scope it.

The separate .github source check-in PR adds `tests/test_sdk_untrusted_dependency_collision_checkin.py` to execute the **actual canonical evaluator** with the current registry generation and exact SDK-only component, retaining an ephemeral test event and asserting `COORDINATE_CONVERGENCE`, no hard collision and authority_effect NONE. The ephemeral CI event does **not** replace an authentic resident check-in or WorkerCoordinator claim/fence. Shared SDK runtime implementation or owner-controlled envelope wiring requires subsequent canonical coordination/authorization. Actual TV/TVC warrant, present InTr admission, independent OS boundary observation, organization-level denial/expiry receipts and exact Master Records closure remain UNKNOWN_NOT_AUTHENTICALLY_OBSERVED. No new runtime, scheduler, ledger, credential or device requirement.


### Exact check-in falsification and canonical null-lineage repair

On draft PR #2599 initial exact-head Cross-Task Coordination run `35932733740` FAILED: the actual canonical evaluator returned `STOP_COLLISION` where the read-only JS reconstruction had expected `COORDINATE_CONVERGENCE`. Investigation found the first concrete false-positive in `scripts/evaluate_task_registry_collision_checkin.py`: its lineage set included `parent_task_id=None` for unrelated top-level tasks, so unrelated root tasks shared the null sentinel and a checked-out neighbor became a false hard lineage collision. This is an evaluator source defect, not evidence of an actual shared component or authorized runtime claim. The PR now excludes absent/blank identities before lineage intersection, while retaining true shared task/parent/root identity collisions; dedicated regressions cover unrelated null-parent roots and genuine same-parent siblings. Repeat the **actual** scoped evaluator CI test with ephemeral event history on the repaired head; do not claim `COORDINATE_CONVERGENCE` or merge until that exact-head rerun succeeds. An authentic resident collision event/claim and runtime remain unproven.
