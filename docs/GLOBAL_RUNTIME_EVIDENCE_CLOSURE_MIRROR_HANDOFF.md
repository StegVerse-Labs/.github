# Global Runtime Evidence Closure Mirror Handoff

Goal Task ID: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
Canonical issue: `StegVerse-Labs/.github#1260`
COSV: `50000000100000`
Status: `ACTIVE / ALL_18_RUNTIME_LANES_HB32_NODE_PROFILED / STEGCLAW_AND_VACC_EXECUTABLE_PROFILES_MERGED / PRECISE_FAILURE_BOUNDARY_RESPONSES_IMPLEMENTED / DE006_EXECUTABLE_REBIND_NEXT / AUTHENTIC_PROFILED_CONVERGENCE_RECEIPT_PENDING`

## Purpose

Converge all source-ready StegVerse capabilities that still require authentic runtime execution/evidence, custody/reconstruction, runtime-bound validation, or downstream propagation proof. Preserve each child task identity and resume it from the first unresolved subject-bound predicate.

## Retained-node runtime model

The reusable ecosystem loop is now:

```text
runtime/node profile resolution
-> retained profile-derived StegOS node identity + continuity
-> immutable source-device HB lineage + fresh current HB observation
-> exact ephemeral task/request/COSV binding and consumption
-> ephemeral WorkerCoordinator claim/fence
-> ephemeral Interlock/InTr admission
-> ephemeral transport/provider/lease
-> exact component execution or re-execution
-> exact receipt commitment into retained node lineage
-> Master Records same-execution custody/reconstruction
-> required downstream propagation verification
```

Node identity/evidence/HB lineage persists. Claims/fences, InTr invocations, transports, provider/browser/model/action sessions, credentials, and task execution processes remain bounded and ephemeral. HB remains observability/freshness/correlation only and grants no authority.

## Global profile convergence

`.github` PR #1288 merged at `c22f0f347bb91e77b81d78e6e5e9b9ce7eea7409`, establishing exactly 18 `HB32 / RETAINED_STEGOS_NODE / EPHEMERAL_OR_BOUNDED_RUNTIME_LEASE` task profiles. Resident source-refresh propagation merged at `64a8f9156255593fcd75ec029b50dc4612f282db`, carrying the profile registry/builders/runners/observability sources into the already-local resident root while preserving mutable runtime state.

StegClaw executable profile PR #1290 merged at `fa4cc25500775e0f75daeb05474429ff8d91a83f`.

VACC executable profile PR #1291 merged at `b948d9a56e70d5ad919e5fbd0895907e0f72ae58`. VACC is no longer a generic profile-only bridge: `workers/vacc_profiled_resident_execution.py` reuses the existing Ecosystem Chat/local-model/TVC/Master Records chain and performs one bounded real VACC request against the exact live loopback runtime before retaining a subject-bound execution receipt.

## Precise failure/error response instrumentation

Active branch:

```text
fix/runtime-failure-boundary-responses-20260909
```

The resident-refreshable worker tree now contains:

```text
workers/runtime_failure_boundaries.py
```

It defines ten stable typed failure boundaries:

```text
01 RUNTIME_PROFILE_RESOLUTION
02 PERSISTENT_NODE_CONTINUITY
03 EPHEMERAL_REQUEST_CONSUMPTION
04 WORKERCOORDINATOR_CLAIM_FENCE
05 EPHEMERAL_INTERLOCK_INTR_ADMISSION
06 EPHEMERAL_TRANSPORT_PROVIDER_LEASE
07 COMPONENT_EXECUTION
08 EXACT_RECEIPT_COMMITMENT
09 MASTER_RECORDS_RECONSTRUCTION
10 DOWNSTREAM_PROPAGATION
```

Each boundary emits one `stegverse.runtime-failure-response/v1` containing task/lane identity, exact stage index/name/code, raw child state, reason/evidence reference when available, next predicate-specific action, `subject_bound=true`, `heartbeat_grants_authority=false`, and `authority_effect=NONE_DIAGNOSTIC_ONLY`.

`run_global_runtime_node_profile_convergence.py` now annotates every lane with:

```text
boundary_trace[]
first_failure
first_failure_stage_index
first_failure_code
```

and emits a global `failure_boundary_summary` with exact stage/code counts.

Child runtime implementations may provide explicit `stage_observations`; the classifier always selects the earliest actual failed/unobserved stage. When a child does not yet emit stage observations, the canonical `resume_stage` remains the non-regressive fallback first boundary. Existing later-stage evidence is not moved backward.

The classifier resides under `workers/`, which is already copied as a static resident source directory by `refresh_sovereign_worker_runtime_source.py`; no separate refresh path or scheduler is introduced.

Focused injected regressions live at:

```text
tests/test_runtime_failure_boundaries.py
```

They force all ten failure codes, verify every current global resume label maps to the intended canonical stage, verify explicit stage observations override projected resume points at the first true failure, verify terminal success emits no failure, verify boundary-count summaries, and verify resident-refresh materialization of the classifier.

## Remaining exact runtime repair

DE-006 remains the last formerly generic-unwired lane without an executable profile wrapper. It already has authentic device-local inference + same-execution reconstruction evidence, but still requires exact parent rebinding/re-execution through its existing parent continuation path. That repair must not promote prior device-local evidence into DE-006 completion by inference.

## Test / merge gate

Before merge, the failure-boundary branch must pass the exact-head organization control, deterministic repository suite, and Heartbeat validation. After merge/source refresh, the authentic resident profile convergence cycle must emit `global-runtime-node-profile-convergence.latest.json`; its `failure_boundary_summary` becomes the measured overlay for the 18 lanes.

## README review

`README.md` was reviewed. Existing retained-identity, bounded-execution, exact-evidence, single-resident-path, and subject-bound failure semantics cover this instrumentation. No README mutation is required for the diagnostic response format.

## Manual work

None currently required.
