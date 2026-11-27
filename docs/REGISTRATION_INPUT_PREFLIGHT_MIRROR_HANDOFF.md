# Registration input preflight mirror handoff

Existing owner: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`, canonical G326/122, PROPOSED, completion false/false, only INGRESS_ADMITTED, authentic WorkerCoordinator claim/fence null. This source proposal does not change that state or mint a component Goal/COSV. Existing draft PR: StegVerse-Labs/.github#3479.

The expired source-repair claim `.github#3444/7206708041` was requeued after its explicit November 26, 2026, 21:00 America/Chicago expiry. CODEX P3 reader `.github#3444/7208985739` and claim `.github#3444/7208985961` own only source repair on the existing branch. Expiry is not evidence of the old claimant's completion.

## Change and validation boundary

The initial eight request inputs used `stegverse.dual-scope-seal/v1` where the existing request contract requires `stegverse.goal-scope-seal/v1`. Each edit changes only `sealed_scope.schema`. Scope payload, scope digest, finish point, supersession, record, vector inputs, generation, and authority fields are preserved. The eight requests are banking-system, lane-self-funding, pair-carrier-services, rail-harness, scan-carrier, social-posting, socials-hostname-binding, and strategy-carrier.

`goal_scope_seal.make_sealed_scope` constructs new request inputs using the existing canonical `scope_of`, `digest`, schema constant, and validator. It requires an explicit testable finish point and does not normalize an existing mismatched scope or write a seal.

`registration_input_preflight.py` reads request JSON and calls the existing request validator and canonical seal validator. It does not call registration `run`, `plan`, `apply`, or `verify`, inspect or mutate the live Registry, derive a COSV, write a seal, dispatch, or grant a native claim. Its positive result is `input_status=VALID`, with `registration_proven=false` and `authority_effect=NONE_INPUT_PREFLIGHT_ONLY`. Validation of an input is not registration.

The existing read-only workflow runs input preflight before its unchanged live-base registration verification for changed requests. Invalid input receives a six-field repair path; actual registration is still checked separately. The existing registration gates are retained. A request-only PR can continue to report REGISTRATION_NOT_APPLIED until an authorized registrar produces and verifies the required canonical outputs.

## Existing unresolved input

`skap-hostname-binding-001.json` uses a scope shaped as queue_item/method/addressed_lane/discharge_predicates/task_id/title rather than goal/targets/expected_evidence_predicates/finish_point. Its top-level task_id is SKAP-HOSTNAME-BINDING-001 while record.task_id is SKAP-PLACEMENT-AND-RELEASE-001, an additional semantic identity mismatch requiring the original owner. Its input preflight remains INVALID. Its scope, digest, and finish point are not invented or rewritten by this change. The existing request owner must supply the intended canonical record-bound scope and explicit testable finish point through its established source route, then rerun input preflight. This residual does not invalidate the conservation proof for the eight tag-only fixes.

## Continuation

Review the exact PR head and its source tests. The original existing-branch README and banking handoff additions are preserved, and current-main changes are retained through a history-preserving commit with an expected-head lease. No protected merge or native registration is performed by this proposal. The authorized registrar owns fresh-base derivation, canonical record/aggregate/vector/seal readback, and all authentic native authority and admission requirements. Preserve the original banking B-7/B-8/B-9 counsel and aggregate determination gates.

## Source checks (CODEX P3)

57 affected source/synthetic-fixture tests passed. Three existing tests that inspect or derive against the live Registry were deliberately excluded from this local source-only run; exact-head CI owns the full existing workflow. The 13 new controls passed in normal, `-O`, and `-OO` Python (39 checks). Inventory input preflight returned 20 VALID and one INVALID (the separately preserved SKAP scope-shape defect), with registration_proven false throughout. All eight edited requests differ from pinned main only in sealed_scope.schema; scope digests and all other JSON fields are equal. These are author-side source checks, not independent acceptance or native registration.

## Follow-through: generated test inventory

At head 92eae7130c4c897402fe574061650c92355a0cab, full ratchet run45935219939 found exactly one new ratchet finding: TEST_SET_MANIFEST_STALE. It ran 6,184 passing and 144 failing tests, with existing baseline failures kept distinct. CODEX P4 reader7209279271 and source-worker claim7209279468 cover this repair. The unchanged generator and spec regenerate the inventory to855 sets, adding the input-preflight test and its two new dependency-graph nodes. Incremental generation reproduces the predecessor exactly and reparses changed nodes against the complete pinned Git path inventory; full exact-head CI independently regenerates the complete inventory and must compare equal. The test baseline, exclusions, test-selection policy and native-registration gate are unchanged.

## P5 current-main forward repair

Main a828cea5b3eb36b0ef05ba70ab948ef2746b3c0a introduced submission-release-001 with the same wrong schema tag. CODEX P5 reader7209685340 and source-worker claim7209685596 cover its exact tag-only correction as the ninth repaired input. All other input bytes and the original EOF are conserved; scope digest911bcad39340e6811266aa81c22fba6631e968b887d974dec8a57e6ca6fa5410 is unchanged. The current23-request input inventory is22 VALID/1 INVALID, with unchanged SKAP semantic/identity defects retained for its original owner. The same PR branch moves forward with old head b74646c and pinned main b96619df as parents, preserving both histories and foreign source. Test inventory855 is unchanged because no Python test, generator or selector source changed; full exact-head CI must still verify it. Shared canonical-constructor adoption by the original request producer remains an explicit owner action: this source repair does not pretend to modify a producer outside this repository.

P5 late-main guard: main b96619df6fd343ef2618878950dd30ed5f5d3df1 adds protocol-hostname-binding with the same schema-only defect; the tenth correction preserves scope digest50ad22cfd394dd928d4f2445dbebe99342b65393c3517d62aa26f6b1411352a9. The current merge retains both b74646c and b96619df parents. No current-main additions or prior branch history are dropped.


## P6 current-base request preparation

Existing source-worker reader3444/7209998972 and claim3444/7209999157 extend draft PR3479 over pinned main2c4e706a645736ee294d9bf5abdcd9107302490a, retaining oldhead4c13faab8ed16ad57caec5410d69423c15888b90 as first parent and fresh main as second. Three newly introduced requests (rail-bridge, registry-transition, standing-queue-evaluation) receive schema-tag-only corrections, bringing the total to13. All payloads/digests/finishpoints/authority/EOFs and foreign source remain. Current26 inputs:25 VALID/1 unchanged SKAP semantic/identity INVALID. No Python/test/generator/spec/baseline/exclusion/selector changes; inventory855 retained. Previous exacthead4c13 ratchet45939574323 SUCCESS:6185 passed,143 existing failures,0 new findings; newhead CI must be read independently. Registration143units/scopefreeze PASS do not replace the actual REGISTRATION_NOT_APPLIED requirement.

Original request producers must construct sealed_scope through goal_scope_seal.make_sealed_scope and run the read-only registration_input_preflight before filing; existing invalid semantic scope must never be rehashed into acceptance. This source preparation does not modify an external producer or perform the owner-side native Registry cut. See existing docs/REGISTRATION_INPUT_PREFLIGHT_MIRROR_HANDOFF.md and the three task registration handoffs. ParentG326 PROPOSED; component identities UNBOUND until authentic derivation/readback.


## CODEX P8 continuation (source proposal)

Source preparation: previous exactheadba24dcb173bd2ea44eda43e3fb1d40e4a9acc828 fullratchet45941517445 all3jobsSUCCESS,855/855sets/853runnable/0inputunavailable,6185passed/143existingfailures/18deselected/0requiredskipped/0NEWfindings. Registration45941517421 all143units+scopefreezePASS; nativeREGISTRATION_NOT_APPLIED remains. P8 sourceworker3444/7210270418 appends this continuation and prepares the new entry-read-and-act request with schema-tag-only correction(number14), conserving scope/digest/finishpoint/record/metrics/authority/EOF. Freshbase1fa77af69f48b3c45e0a1f97389fb58e902d96c1 retained with olddraftba24 as parents. Current27requestpreflight26VALID/1 unchangedSKAPsemantic/identityINVALID;13controlsPASS; no Python/test/spec/generator/baseline/exclusion/selector change, inventory855 retained. Read actual newhead CI before extending the previous grade.

Next actions: actualauthorizedregistrar owns fresh-base native transition and canonical output readbacks; centralLSP§4 still says owner-executed admission/protectedintegration, so sourcepreparation is not permission to cut. OriginalSKAP request owner must resolve scope/identity; originalrequestproducer must adopt make_sealed_scope+read-onlypreflight to stop recurring malformed tags. Existingfleetkeeper supplies socialsprobe proof; originalGemini producers cure newK5/SOCIALreturns; originalClaudeCode producer dispositions K1peer; sole registrymaintainer repairs capped routing; counter owner reconciles cumulative/admittedsuccessors. LiveDocEscrow8807/SKAP/stranger-paid/consent/funding/counsel work stays on its explicit existing surfaces and predicates. No newauthority/machine/dependency, protectedmerge, nativeapply, funding, counsel/PatentCenter submission or revenue claimed. Owner interventions: 0.


Full source-bound continuation: docs/CANONICAL_WORK_COORDINATION_SYSTEM_MIRROR_HANDOFF.md on this existing draft. Runtime Task Registry and protected-main admission remain unchanged.
