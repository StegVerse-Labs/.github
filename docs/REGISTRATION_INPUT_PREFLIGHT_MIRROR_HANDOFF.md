# Registration input preflight mirror handoff

Existing owner: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`, canonical G326/122, PROPOSED, completion false/false, only INGRESS_ADMITTED, authentic WorkerCoordinator claim/fence null. This source proposal does not change that state or mint a component Goal/COSV. Existing draft PR: StegVerse-Labs/.github#3479.

The expired source-repair claim `.github#3444/7206708041` was requeued after its explicit November 26, 2026, 21:00 America/Chicago expiry. CODEX P3 reader `.github#3444/7208985739` and claim `.github#3444/7208985961` own only source repair on the existing branch. Expiry is not evidence of the old claimant's completion.

## Change and validation boundary

Eight request inputs used `stegverse.dual-scope-seal/v1` where the existing request contract requires `stegverse.goal-scope-seal/v1`. Each edit changes only `sealed_scope.schema`. Scope payload, scope digest, finish point, supersession, record, vector inputs, generation, and authority fields are preserved. The eight requests are banking-system, lane-self-funding, pair-carrier-services, rail-harness, scan-carrier, social-posting, socials-hostname-binding, and strategy-carrier.

`goal_scope_seal.make_sealed_scope` constructs new request inputs using the existing canonical `scope_of`, `digest`, schema constant, and validator. It requires an explicit testable finish point and does not normalize an existing mismatched scope or write a seal.

`registration_input_preflight.py` reads request JSON and calls the existing request validator and canonical seal validator. It does not call registration `run`, `plan`, `apply`, or `verify`, inspect or mutate the live Registry, derive a COSV, write a seal, dispatch, or grant a native claim. Its positive result is `input_status=VALID`, with `registration_proven=false` and `authority_effect=NONE_INPUT_PREFLIGHT_ONLY`. Validation of an input is not registration.

The existing read-only workflow runs input preflight before its unchanged live-base registration verification for changed requests. Invalid input receives a six-field repair path; actual registration is still checked separately. The existing registration gates are retained. A request-only PR can continue to report REGISTRATION_NOT_APPLIED until an authorized registrar produces and verifies the required canonical outputs.

## Existing unresolved input

`skap-hostname-binding-001.json` uses a scope shaped as queue_item/method/addressed_lane/discharge_predicates/task_id/title rather than goal/targets/expected_evidence_predicates/finish_point. Its top-level task_id is SKAP-HOSTNAME-BINDING-001 while record.task_id is SKAP-PLACEMENT-AND-RELEASE-001, an additional semantic identity mismatch requiring the original owner. Its input preflight remains INVALID. Its scope, digest, and finish point are not invented or rewritten by this change. The existing request owner must supply the intended canonical record-bound scope and explicit testable finish point through its established source route, then rerun input preflight. This residual does not invalidate the conservation proof for the eight tag-only fixes.

## Continuation

Review the exact PR head and its source tests. The original existing-branch README and banking handoff additions are preserved, and current-main changes are retained through a history-preserving commit with an expected-head lease. No protected merge or native registration is performed by this proposal. The authorized registrar owns fresh-base derivation, canonical record/aggregate/vector/seal readback, and all authentic native authority and admission requirements. Preserve the original banking B-7/B-8/B-9 counsel and aggregate determination gates.

## Source checks (CODEX P3)

57 affected source/synthetic-fixture tests passed. Three existing tests that inspect or derive against the live Registry were deliberately excluded from this local source-only run; exact-head CI owns the full existing workflow. The 13 new controls passed in normal, `-O`, and `-OO` Python (39 checks). Inventory input preflight returned 20 VALID and one INVALID (the separately preserved SKAP scope-shape defect), with registration_proven false throughout. All eight edited requests differ from pinned main only in sealed_scope.schema; scope digests and all other JSON fields are equal. These are author-side source checks, not independent acceptance or native registration.
