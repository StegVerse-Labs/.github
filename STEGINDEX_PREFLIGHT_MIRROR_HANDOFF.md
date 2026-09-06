# STEGINDEX_PREFLIGHT_MIRROR_HANDOFF.md

Status: ACTIVE
Updated: 2026-09-05
Organization: StegVerse-Labs
Repository: StegVerse-Labs/.github
Goal: STEGINDEX-MANDATORY-PREFLIGHT-CONSUMER

## Source of truth

StegIndex:
- repository: `StegVerse-Labs/StegIndex`
- handoff: `STEGINDEX_MIRROR_HANDOFF.md`
- purpose-aware preflight merge: `4d47439956341ea535e3e937d97c492b193daa51`

Organization consumer:
- `scripts/stegindex_preflight_gate.py`
- `management/stegindex-preflight-consumer-contract.json`

## Purpose

Bind organization/session/build entry logic to StegIndex resolution without turning StegIndex into an authority plane.

The adapter consumes an already-materialized StegIndex checkout and performs no network fetch. It invokes StegIndex's canonical `scripts/preflight.py`, verifies that the result remains resolution-only, and reduces the output to a bounded organization decision.

## Lawful decisions

- `CONTINUE_MACHINE_EXECUTION`
- `REUSE_OR_EXTEND_EXISTING`
- `NO_EXISTING_CAPABILITY_MATCH`
- `EXACT_BLOCKER_ONLY`

## Anti-stall invariant

If StegIndex returns `machine_continuation_required=true`, the organization adapter must return `CONTINUE_MACHINE_EXECUTION`.

A generic `runtime evidence missing` blocker is not permitted in that state.

If StegIndex is not locally materialized, the adapter does not fabricate a resolution and does not fetch it over the network. It emits the exact missing local dependency.

## Authority

This consumer grants NO:
- execution authority;
- admission authority;
- credential authority;
- routing authority;
- claim/fence authority;
- transition authority;
- publication authority;
- custody authority;
- consequence authority.

Actual execution remains owned by the canonical satisfier/worker/runtime identified by repository-local truth.

## Current continuation

source_adapter: IMPLEMENTED
StegIndex purpose-aware resolver: MERGED
organization preflight consumption: SOURCE_BOUND
README impact pre-work completeness: SOURCE_IMPLEMENTED / VALIDATION_PENDING
runtime execution claim: NONE
next_action: validate the README-impact extension and preserve it through concrete session/worker entry paths
manual_execution_allowed: true
user_action_required: false
thread_archive_ready: false

## Merge receipt — 2026-09-02

Organization consumer:
- PR #877
- merge: `63a3aa8e81c3d16fe8c7dfbc6e77d80d1bff8d27`

StegIndex resolver:
- PR #2
- merge: `4d47439956341ea535e3e937d97c492b193daa51`

Source-bound preflight consumption is now present on `main`. This is not evidence that every existing worker invokes the adapter, and it is not runtime activation evidence.

## Truth reconciliation consumer binding — 2026-09-02

StegIndex truth reconciliation source:
- StegVerse-Labs/StegIndex PR #3
- merge: `637b33c99adf08505b485c504512b4b1ba708141`

The organization adapter now treats `indexed_truth_usable=false` as `EXACT_BLOCKER_ONLY` with exact dependency `indexed_truth_reconciled`.

It MUST NOT return `REUSE_OR_EXTEND_EXISTING` or `CONTINUE_MACHINE_EXECUTION` from stale/contradictory indexed truth.

This preserves two independent fail-closed rules:
1. usable existing truth prevents duplicate implementation;
2. unusable indexed truth requires reconciliation before either reuse or new work.

## Concrete session/build pre-work entrypoint — 2026-09-02

Canonical entrypoint:
- `scripts/session_build_preflight.py`
- contract: `management/session-build-preflight-contract.json`

This is the organization pre-work boundary for deciding whether new implementation/task creation may even be considered.

Decision mapping:
- StegIndex `CONTINUE_MACHINE_EXECUTION` -> continue through canonical owner; new task creation prohibited.
- StegIndex `REUSE_OR_EXTEND_EXISTING` -> reuse existing capability; new task creation prohibited.
- StegIndex `EXACT_BLOCKER_ONLY` -> stop only at the exact dependency; new task creation prohibited.
- StegIndex `NO_EXISTING_CAPABILITY_MATCH` -> new work may be considered, subject to all normal governance/authority rules.

This entrypoint performs no execution and grants no authority. It exists to prevent duplicate work and generic blocker creation before work is admitted.

## Session/build pre-work boundary receipt — 2026-09-02

Reconciliation-consumer merge:
- PR #881 -> `376d48b2ac9aa672920ab169ad6b6d2e62349d43`
- validation-only organization control plane: `33713433913` SUCCESS
- validation-only Heartbeat Worker Project: `33713434257` SUCCESS

Concrete pre-work entrypoint:
- PR #885 -> `9ac197a019f695f3a5344b6b7498d4e2c1683836`
- `scripts/session_build_preflight.py`
- `management/session-build-preflight-contract.json`

New work is now permitted by this boundary only when StegIndex reports `NO_EXISTING_CAPABILITY_MATCH`. Existing capability reuse, machine-continuation availability, exact external dependency, and stale/contradictory indexed truth all prohibit duplicate task creation.

Remaining integration is worker-entry-specific; the sovereign resident executor itself is not made dependent on StegIndex materialization.

## Capability-risk organization consumer binding — 2026-09-03

StegIndex unified preflight source:
- StegVerse-Labs/StegIndex PR #8
- merge: `e32982f5983bf123f145e691e4ca236074584532`

The organization adapter now passes through StegIndex's bounded `capability_risk` object alongside the existing capability/predicate decision.

Preserved invariants:
- organization decision mapping is unchanged;
- capability-risk metadata grants no execution or transition authority;
- no runtime dependency or network fetch is introduced;
- no external payload content is copied;
- trusted publisher/signature/local availability does not imply authority;
- stale/contradictory canonical capability truth remains fail-closed exactly as before.

The session/build pre-work entrypoint already nests the organization gate result, so this bounded metadata becomes visible there without adding another execution plane.

Runtime activation claim: NONE.
Authority effect: NONE.

## Continuous-discovery organization gate — 2026-09-03

Canonical organization pre-work behavior now recognizes StegIndex continuous-discovery guards.

New fail-closed mappings:
- `REVIEW_DISCOVERED_CANDIDATE_BEFORE_NEW_WORK` -> `EXACT_BLOCKER_ONLY` / `candidate_reconciled`;
- `COMPLETE_SOURCE_DISCOVERY_BEFORE_NEW_WORK` -> `EXACT_BLOCKER_ONLY` / `source_discovery_complete`.

These states MUST NOT fall through to `NO_EXISTING_CAPABILITY_MATCH` and MUST NOT permit new task creation.

The organization gate also resolves an already-local StegIndex checkout from:
1. explicit `--stegindex-root`;
2. `STEGINDEX_ROOT`;
3. `STEGVERSE_REPO_ROOTS_JSON["StegVerse-Labs/StegIndex"]`.

No network source fetch is introduced. The repository-root map is a non-secret local locator only and grants no authority.

Session/build pre-work remains non-authorizing:
- task creation is permitted only after canonical StegIndex returns a true no-match state with complete source discovery;
- discovered candidates require reconciliation/promotion or rejection first;
- incomplete source discovery requires source materialization/observation first;
- capability-risk metadata remains advisory/index-only;
- authority effect remains NONE.

## README-impact pre-work completeness — 2026-09-05

The organization session/build preflight now carries the same functional-change completeness invariant already enforced at WorkerCoordinator admission.

New CLI declaration:
- `--readme-impact-required`
- `--material-function-change true|false`
- `--readme-updated-in-change-set`
- `--readme-path <path>`
- `--no-readme-update-reason <reason>`
- repeatable `--readme-evidence-ref <ref>`

Fail-closed rules:
1. if README impact is required but materiality is undeclared, stop at `STOP_AT_README_IMPACT_DEPENDENCY`;
2. if `material_function_change=true`, a README update, README path, and evidence refs are mandatory;
3. if `material_function_change=false`, an explicit no-update reason and evidence refs are mandatory;
4. an incomplete README-impact determination overrides any otherwise permissive StegIndex/coordination result and prohibits task creation;
5. legacy/nonfunctional invocations that do not enter the README-impact gate retain prior behavior.

This extension creates no new scheduler, execution path, claim/fence authority, credential authority, route authority, transition authority, or runtime-truth claim. It is a pre-work completeness predicate only.

README impact for this change itself: MATERIAL. `README.md` is included in the same change set.
