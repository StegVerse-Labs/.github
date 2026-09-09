# Global Runtime Evidence Closure Mirror Handoff

Goal Task ID: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
Canonical issue: `StegVerse-Labs/.github#1260`
COSV: `50000000100000`
Status: `ACTIVE / 18 HB32 PROFILE-DERIVED NODES / PRECISE FAILURE BOUNDARIES / DEFINITIVE MEASUREMENT HARDENING VALIDATING`

## Canonical runtime model

The ecosystem loop is:

```text
runtime/node profile
-> profile-derived retained StegOS node
-> immutable source-device HB lineage + current HB observation
-> ephemeral request consumption
-> ephemeral WorkerCoordinator claim/fence
-> ephemeral Interlock/InTr admission
-> ephemeral transport/provider/lease
-> component execution
-> exact receipt commitment
-> Master Records reconstruction
-> downstream propagation
```

Node identity/evidence/HB lineage persist. Claims/fences, InTr calls, transports, credentials, provider/browser/model/action sessions, and execution processes remain bounded and ephemeral. HB remains observability/freshness/correlation only.

## Merged prerequisites

- StegBrowser retained-node/HB lineage implementation merged.
- StegOS profile-derived retained-node, outward HB lineage and receipt-to-transition implementation merged.
- `.github` 18-lane HB32 runtime-node profile convergence merged.
- StegClaw executable profile merged.
- VACC executable profile merged.
- typed ten-stage failure responses merged in PR #1292 at `e64c5d518af05dac6b9d09c3355d38d75bc27295`.

## Definitive measurement hardening

Active branch:

`fix/runtime-failure-boundary-prerun-hardening-20260909`

The first definitive convergence run is now explicitly measurement-only.

`workers/runtime_convergence_measurement.py` freezes one run identity before execution containing:

- unique `run_id`;
- start timestamp;
- exact local source git head when available;
- exact runtime-node profile registry SHA-256;
- exact partial-solution projection SHA-256;
- `measurement_only=true`;
- `same_run_remediation_allowed=false`;
- `automatic_retry_after_first_failure=false`;
- per-profile before snapshots of known subject/canonical-work receipt files and retained node/HB/transition fields when present.

After execution the same evidence surfaces are snapshotted again. Before/after tracked fields include node/profile identity, genesis, source/current HB references, state generation/state commitment and prior/current transition commitments when present. This allows the measured run to distinguish `same node + advanced lineage` from unrelated component output.

`run_global_runtime_node_profile_convergence.py` now:

1. freezes that measurement context before visiting the 18 lanes;
2. exports `STEGVERSE_CONVERGENCE_MEASUREMENT_ONLY=1` during the run;
3. labels canonical earlier-stage evidence as `PASS_HISTORICAL_EVIDENCE`, never as current-run proof;
4. labels an exact predicate crossed in this run as `PASS_CURRENT_RUN`;
5. labels the first observed failure as `FAILED_CURRENT_RUN` and later stages `NOT_REACHED`;
6. accepts child-supplied explicit `stage_observations` and requires them to be contiguous through the reported failure;
7. emits the frozen measurement context, typed per-lane boundary trace and aggregate failure map into `receipts/sovereign-host/global-runtime-node-profile-convergence.latest.json`.

Readiness/liveness states are not terminal completion. `PROFILE_BOUND_PARENT_CHAIN_PRESENT_REEXECUTION_READY` and `PROFILE_BOUND_RUNTIME_LIVE_VERIFIED` therefore remain unresolved at the applicable later execution predicate. `NOT_REACHED` is downstream flow state and is never itself treated as a failure.

## Same-run remediation suppression

VACC previously could advance its Ecosystem Chat/local-model parent prerequisite when no verified VACC process existed. During the definitive convergence measurement that repair is disabled. If the frozen baseline has no verified VACC loopback process, VACC reports stage 6 transport/provider runtime failure and does not repair the parent during the same measurement pass. Outside measurement mode, the existing repair behavior remains available.

The measurement contract is diagnostic and grants no execution, claim/fence, InTr, credential, custody, publication or completion authority.

## Measurement interpretation

The definitive receipt must preserve three different meanings:

```text
PASS_CURRENT_RUN
PASS_HISTORICAL_EVIDENCE
NOT_REACHED
```

Historical evidence is retained by non-regression but cannot be represented as current-run passage. A later precise failure cannot be reported if an earlier required explicit observation is missing; that missing predicate becomes the first unobserved boundary.

The measured histogram is authoritative only for what the run actually observed. It must not be described as a runtime completion receipt.

## Remaining work before authentic run

1. pass exact-head organization-control, deterministic repository suite and Heartbeat validation for the hardening branch;
2. merge the hardening PR;
3. refresh the already-local sovereign runtime source so `workers/runtime_convergence_measurement.py`, the hardened failure classifier and profiled runner are materialized together;
4. execute one authentic Runtime Profile Map/profiled convergence measurement without same-pass repair/retry;
5. inspect the measured per-lane first-failure map and before/after node/HB transition commitments;
6. only after measurement, remediate discovered predicates in subsequent executions.

DE-006 still requires exact executable parent rebinding/re-execution; the measurement must report that truth rather than treating readiness as completion.

## README impact

The repository README already defines retained identity, bounded execution, exact evidence, subject-bound failure semantics, non-authorizing HB, and the functional-change invariant. This hardening changes diagnostic measurement semantics rather than execution authority or product behavior; no additional README text is required before the measurement PR is validated.

## Manual work

None while source validation and merge remain machine-executable.
