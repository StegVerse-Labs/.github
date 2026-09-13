# Site Node IndexedDB Schema Migration — Component Model Reconciliation

Goal Task ID: `SITE-NODE-IDB-SCHEMA-MIGRATION-001`
Parent Goal Task ID: `SS-EVIDENCE-COMPARISON-001`
COSV: `40000100100000`
Goal status: `ACTIVE / CLAIMED_INTEGRATION`

Canonical model: `data/reusable-task-component-model.json`
Decomposition policy: `data/reusable-task-component-decomposition-policy.json`
Composition profile: `data/goal-task-component-profiles/SITE-NODE-IDB-SCHEMA-MIGRATION-001.json`
Reusable schema component: `data/reusable-browser-local-state-schema-migration-component-contract.json`

## Reconciliation

The existing Goal Task remains valid and retains the same identity and COSV. The policy evaluation scores 21, so further task-specific orchestration is stopped in favor of reusable component bindings. This does not close or rename the Goal Task.

## Device-role invariant

All iPhones, phones, browsers, StegOS nodes, and other device instances are interchangeable execution/transport nodes. None is a user verifier or user-identity authority. Device identity, runtime-subject binding, transport identity, Secure Enclave identity, node registration, or Receipt #1 must not be treated as user verification.

KV/SKAP Vault remains the sole user-verification authority.

The current iPhone is named in this Goal Task only because it is the authentic runtime environment where the missing-object-store defect was observed and is therefore the selected environment for the single repair re-observation. That is an evidence-continuity constraint, not a special device class and not an authority assignment. An equivalent failure on another interchangeable node would be classified under the same reusable runtime-reentry capability.

## Required composition

1. `RTC-BROWSER-LOCAL-STATE-SCHEMA-MIGRATION-V1` — required. Inputs are database identity, canonical version/store set, legacy shapes, continuity records, and runtime opener inventory. Outputs are the migration binding, opener alignment, preservation result, and idempotent reopen result. The component is non-authorizing.
2. Existing Site evidence-validation workflows — required. They validate source and exact-head compatibility only.
3. Existing StegOS Node Public Observation — required and already satisfied by run `34617268914` for merge `a3bd73f0ced551738f37a6222b3ca933c3433fdf`. It is observation only.
4. Authentic interchangeable-device runtime re-entry — required and pending. It consumes preserved local runtime state plus the merged/propagated repair and produces the one authentic node-local retry observation needed by this Goal Task. For this task, the current iPhone is merely the selected observation node because it carries the original failure state.
5. Governed ERL admission — conditional after the repair is confirmed; owned by Interlock/InTr and belongs to the parent standard flow, not to the schema-repair completion predicate.
6. Master Records custody/reconstruction — conditional only when an authentic custody path actually records the observation; it is never inferred from source, CI, or a screenshot.

No provider credential/session operation is required for this local retry. No new user-verification event is required for this schema-repair completion.

## Duplicate orchestration superseded

Do not add another task-specific schema migration / opener-alignment chain equivalent to `RTC-BROWSER-LOCAL-STATE-SCHEMA-MIGRATION-V1`. Do not add another bespoke live-propagation probe equivalent to the existing StegOS Node Public Observation owner. Historical implementation and evidence remain provenance.

## Source/runtime boundary

Source construction, CI, merge state, and public-source observation are already satisfied. They do not prove the remaining authentic node-local predicate.

Remaining Goal Task-specific predicate:

`AUTHENTIC_CURRENT_IPHONE_RETRY_NO_MISSING_OBJECT_STORE_FAILURE`

The predicate names the current iPhone only to preserve continuity with the original runtime failure observation; it does not assign verification authority or special device semantics.

Next admissible work remains `REQUEST_SINGLE_CURRENT_IPHONE_RETRY`, followed by `OBSERVE_REPAIRED_DEVICE_KV_DIRECTORY_READBACK`. If confirmed, control returns to `SS-EVIDENCE-COMPARISON-001` for the parent ERL standard flow.
