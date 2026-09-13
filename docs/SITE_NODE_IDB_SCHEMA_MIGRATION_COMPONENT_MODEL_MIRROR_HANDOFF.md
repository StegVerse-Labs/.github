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

The original iPhone observation remains historical provenance only. It does not establish a named-device completion requirement. Canonically, compatible StegOS devices are interchangeable execution/transport nodes and KV/SKAP Vault remains the sole user-verification authority.

Required composition:

1. `RTC-BROWSER-LOCAL-STATE-SCHEMA-MIGRATION-V1` — required. Inputs are database identity, canonical version/store set, legacy shapes, continuity records, and runtime opener inventory. Outputs are the migration binding, opener alignment, preservation result, and idempotent reopen result. The component is non-authorizing.
2. Existing Site evidence-validation workflows — required. They validate source and exact-head compatibility only.
3. Existing StegOS Node Public Observation — required and already satisfied by run `34617268914` for merge `a3bd73f0ced551738f37a6222b3ca933c3433fdf`. It is observation only.
4. Authentic runtime re-entry — required and pending. Any compatible interchangeable StegOS browser execution node may produce the remaining authentic runtime evidence. The legacy component ID `AUTHENTIC-CURRENT-DEVICE-RUNTIME-REENTRY` is retained only for continuity and does not define a device class, verifier role, or named-device requirement.
5. Governed ERL admission — conditional after the repair is confirmed; owned by Interlock/InTr and belongs to the parent standard flow, not to the schema-repair completion predicate.
6. Master Records custody/reconstruction — conditional only when an authentic custody path actually records the observation; it is never inferred from source, CI, or a screenshot.

No provider credential/session operation is required for the browser-local re-observation. No new user-authentication event is required for schema-repair completion, and device/node identity cannot be treated as such an event.

## Duplicate orchestration superseded

Do not add another task-specific schema migration/opener-alignment chain equivalent to `RTC-BROWSER-LOCAL-STATE-SCHEMA-MIGRATION-V1`. Do not add another bespoke live-propagation probe equivalent to the existing StegOS Node Public Observation owner. Do not impose a named-device completion requirement on authentic runtime evidence. Historical implementation and evidence remain provenance.

## Source/runtime distinction

Source construction, CI, merge state, and public-source observation are already satisfied. They do not prove the remaining authentic runtime predicate.

Remaining Goal Task-specific predicate:

`AUTHENTIC_INTERCHANGEABLE_NODE_RUNTIME_NO_MISSING_OBJECT_STORE_FAILURE`

Next admissible work is `REQUEST_AUTHENTIC_INTERCHANGEABLE_NODE_RUNTIME_REOBSERVATION`, followed by `OBSERVE_REPAIRED_DEVICE_KV_DIRECTORY_READBACK`. Evidence may originate from any compatible interchangeable StegOS execution node. If confirmed, control returns to `SS-EVIDENCE-COMPARISON-001` for the parent ERL standard flow.
