# Global Runtime Evidence Closure Mirror Handoff

Goal Task ID: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
Canonical issue: `StegVerse-Labs/.github#1260`
Canonical PR: `StegVerse-Labs/.github#1261` (merged) plus current repair PR from `fix/global-runtime-selector-convergence-1260`
COSV: `50000000100000`
Status: `ACTIVE / PARTIAL_SOLUTIONS_MACHINE_PROJECTED_ACROSS_18_MEMBERS / RESIDENT_CONVERGENCE_WIRED / STALE_VACC_ID_REPAIRED / ENDPOINT_FANOUT_ROUTE_REPAIRED / GADI_EXISTING_RUNTIME_WRAPPER_REUSED / STEGOS_RETAINED_NODE_AND_EPHEMERAL_EXECUTION_CLASSES_PROJECTED / AUTHENTIC_RESIDENT_CONVERGENCE_EXECUTION_NEXT`

## Purpose

Converge all StegVerse ecosystem capabilities that are implemented or integration-ready but still require authentic runtime execution/evidence, receipt custody, reconstruction, runtime-bound validation, or downstream propagation proof. The umbrella preserves child Goal Task IDs and resumes each child from its first genuinely unresolved evidence predicate instead of restarting completed stages.

## Canonical registration

The umbrella is registered under issue #1260 and merged source from PR #1261. Canonical source includes:

- `data/canonical-task-records/GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001.json`
- `control/task-vectors/GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001.json`
- `control/task-vector-index.d/GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001.json`
- `docs/GLOBAL_RUNTIME_EVIDENCE_CONVERGENCE_MATRIX.md`
- `control/runtime-partial-solution-projections/GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001.json`
- `tools/validate_runtime_partial_solution_projection.py`
- `scripts/run_global_runtime_evidence_convergence.py`
- `tests/test_global_runtime_evidence_convergence_execution.py`
- this handoff

The task record is `ACTIVE / CLAIMED_INTEGRATION` with task.v1 COSV `50000000100000`.

## Reusable solution classes

The 18-member projection now uses nine reusable mechanism classes:

1. `HIL_G25_BROWSER`
2. `HF_UNIVERSAL_INTR`
3. `VACC_LOCAL_RUNTIME`
4. `DE006_SAME_EXEC_RECONSTRUCTION`
5. `SV001_POST_TERMINAL_CONTINUATION`
6. `EXACT_RESIDENT_REQUEST`
7. `RUNTIME_PROFILE_MAP`
8. `STEGOS_RETAINED_NODE_CONTINUITY`
9. `STEGBROWSER_EPHEMERAL_EXECUTION`

Cross-task evidence is never treated as substitute evidence; exact subject binding remains required.

### StegOS retained-node continuity solution class

The 2026-09-09 StegBrowser/StegOS implementation milestone establishes a source/CI-level mechanism in which canonical StegOS node identity, genesis commitment, non-secret state commitment, continuity generation, and admitted evidence commitments survive bounded browser/session teardown while browser cookies, provider sessions, credential material, navigation history, and temporary page state remain disposable.

This is projected as `STEGOS_RETAINED_NODE_CONTINUITY` across all 18 current members because it can provide a stable same-device subject identity and rendezvous anchor for resident observation, task/request binding, restart continuity, and evidence correlation without itself claiming request consumption, WorkerCoordinator claim/fence, InTr admission, component execution, or custody completion.

The class is particularly relevant to the early shared failure band around `AUTHENTIC_RESIDENT_PROCESS_OBSERVED` and subject binding. If authentic current-iPhone proof shows the same retained node before and after session teardown/restart, Runtime Profile Map and each task-specific resident receipt can bind against one continuity anchor rather than repeatedly rediscovering an ambiguous resident subject.

Current evidence remains implementation/source evidence, not authentic physical runtime proof. The required runtime milestone is the same retained node observed before a bounded session, after session teardown, and after a subsequent app/session restart with no persistence of session credentials/cookies.

### StegBrowser ephemeral-execution solution class

`STEGBROWSER_EPHEMERAL_EXECUTION` is separately projected only to browser-compatible lanes: HIL, Hugging Face/SV-DN1, SDK/Ecosystem Chat, and StegBrowser itself.

Its purpose is to reuse a retained StegOS node while creating short-lived lease-bounded browser/provider execution state for external operations, then destroy session material while retaining admitted evidence commitments. This class targets later external/browser execution and readback boundaries; it does not replace the resident node, grant execution authority, or solve non-browser component execution by itself.

Keeping these two classes separate is required: persistent node continuity is a substrate/identity mechanism, while ephemeral browser execution is an execution-session mechanism.

## Resident convergence execution

The Canonical Runtime Profile Map remains the common diagnostic trigger. `scripts/install_and_run_canonical_work_event_bootstrap.py` performs the ordinary task-specific Canonical Work bootstrap and, for `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001`, invokes `scripts/run_global_runtime_evidence_convergence.py` against the same resident root.

The convergence runner reuses the existing resident dispatcher and existing bounded task-specific runtime wrappers. It does not create a second scheduler or dispatcher. It writes `receipts/sovereign-host/global-runtime-evidence-convergence.latest.json` with per-lane execution route/state and unresolved resume-stage counts.

## 2026-09-09 routing repair after PR #1261

Fresh repository reconciliation exposed three concrete defects in the merged umbrella wiring and they are repaired on `fix/global-runtime-selector-convergence-1260`:

1. **VACC stale task identity** — the umbrella still pointed at historical `VACP-ADAPTER-AUTHORIZED-EXECUTION-005`, which canonical LLM-adapter records mark `SUPERSEDED`. The projection now points at current `VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023` owned by `StegVerse-org/LLM-adapter#142`.
2. **Endpoint Fanout false NO_SELECTOR classification** — `SHWP-ENDPOINT-FANOUT-SOVEREIGN-RUNTIME-001` is already part of `scripts/consume_stegos_kv_intr_chain_request.py`; the convergence runner now routes it through existing selector `stegos_kv_intr_chain` instead of reporting it unwired.
3. **GADI false NO_SELECTOR classification** — canonical source already contains `scripts/dispatch_gadi_resident_execution.py`, which enforces GADI preflight then invokes the exact resident consumer. The convergence runner now reuses that existing bounded wrapper rather than reporting GADI as having no runtime path.

After this repair, explicit unwired convergence members are reduced to:

- current sovereign VACC provider task `VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023` pending exact cross-repository resident binding from LLM-adapter;
- `DATA-CONTINUATION-STEGCLAW-P4` pending a direct registered resident path;
- `DECISION-ENVELOPE-DE006` pending exact parent rebinding/re-execution path integration.

The endpoint-fanout and GADI lanes must now produce their real task-local state during the next resident convergence visit rather than being pre-classified as unwired.

## Current member routing

- CryptoBot -> Canonical Work request consumption.
- HIL -> ESRL `LEASE_OPEN`.
- Hugging Face / SV-DN1 -> `sv_dn1` + publication resident selectors.
- SDK / Ecosystem Chat -> `ecosystem_chat`.
- VACC -> current `VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023`; cross-repository resident binding still required.
- DEVICE_KV / MyKV -> `stegos_kv_intr_chain`.
- Endpoint Fanout -> same existing `stegos_kv_intr_chain` exact chain after authentic DEVICE_KV parent.
- StegVerse-001 -> current-device continuation.
- SV002 -> public-observation resident selector.
- StegClaw -> resident path still unwired.
- GADI -> existing `scripts/dispatch_gadi_resident_execution.py` preflight + exact consumer path.
- Governed Multilane Manifold -> existing manifold selector.
- GLM 5.3 Sovereign -> existing GLM resident selector.
- SV-011 Phase 5 -> source-materialization + phase-5 selectors.
- Runtime Profile Map -> CanonicalWork ingress then map lifecycle selectors.
- Native Email -> native email resident selector.
- StegBrowser -> Canonical Work ingress/browser path.
- DE-006 -> exact parent rebinding/re-execution integration still required.

## Failure comparison

The next resident convergence execution now has materially fewer artificial `NO_REGISTERED_SELECTOR` outcomes. It can distinguish actual runtime states for Endpoint Fanout and GADI, while VACC/StegClaw/DE-006 remain explicit integration work rather than being confused with resident process failure.

The retained-node class adds a new high-value diagnostic: after authentic current-iPhone node continuity is observed, any lane still failing at `AUTHENTIC_RESIDENT_PROCESS_OBSERVED` must distinguish between failure to observe the shared retained StegOS node and failure of task-specific request consumption. That should compress the left-side failure map if node identity/session-reset ambiguity has been contributing to repeated resident failures.

## README review

`README.md` was reviewed against this repair. The repository-level documented semantics already require one existing resident dispatcher, task-specific fail-closed consumers/wrappers, exact task/COSV continuity, autonomous machine continuation, and reusable ephemeral constructs. The new classes reuse those semantics and do not introduce a second scheduler, dispatcher, credential route, or execution authority. No README text change is required for this correction.

## Validation and next execution

The repair branch must pass the same organization-control, deterministic repository-suite, and Heartbeat validation surfaces before merge. After merge, the existing resident Runtime Profile Map path should execute the repaired convergence visitor. The highest-value next source repair remains the current VACC sovereign provider binding, followed by authentic retained-node continuity observation and a new convergence run that measures whether the early resident/subject-binding failure band collapses.

## Manual work

None currently required.
