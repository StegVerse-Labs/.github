# Global Runtime Evidence Closure Mirror Handoff

Goal Task ID: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
Canonical issue: `StegVerse-Labs/.github#1260`
COSV: `50000000100000`
Status: `ACTIVE / 18 HB32 PROFILE-DERIVED NODES / PRECISE FAILURE BOUNDARIES / DEFINITIVE MEASUREMENT HARDENING MERGED / AUTHENTIC ONE-PASS MEASUREMENT NEXT`

## Canonical runtime model

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

## Merged implementation state

- StegBrowser retained-node/HB-lineage implementation: merged.
- StegOS profile-derived retained node, outward source-HB lineage, and receipt-to-transition implementation: merged.
- 18 HB32 runtime-node profiles plus profiled convergence runner: merged.
- StegClaw executable profile: merged.
- VACC executable profile: merged.
- typed ten-stage first-failure responses: PR #1292 merged at `e64c5d518af05dac6b9d09c3355d38d75bc27295`.
- definitive measurement hardening: PR #1293 merged at `44c6d88abb42351ec26a576e3136caec3400a613` after exact-head organization-control, deterministic repository-suite, and Heartbeat checks all completed successfully.

## Definitive measurement contract

`workers/runtime_convergence_measurement.py` freezes one measurement identity before execution containing:

- unique `run_id`;
- start timestamp;
- local source git head when available;
- exact runtime-node profile registry SHA-256;
- exact partial-solution projection SHA-256;
- `measurement_only=true`;
- `same_run_remediation_allowed=false`;
- `automatic_retry_after_first_failure=false`;
- per-profile before snapshots of known canonical-work/subject receipts and any node/profile/genesis/source-HB/current-HB/state/transition commitments present in those receipts.

The same evidence surfaces are captured after the run. This makes `same retained node + advanced lineage` distinguishable from unrelated output.

`run_global_runtime_node_profile_convergence.py` now distinguishes:

```text
PASS_CURRENT_RUN
PASS_HISTORICAL_EVIDENCE
FAILED_CURRENT_RUN
NOT_REACHED
```

Historical non-regression evidence is retained but is never represented as current-run passage. Child-supplied explicit stage observations must be contiguous through the first reported failure; if an earlier required predicate is missing, that missing predicate becomes the first unobserved boundary. Readiness/liveness states are not terminal completion, and `NOT_REACHED` is downstream flow state rather than a failure.

## Same-run remediation suppression

During measurement the runner exports `STEGVERSE_CONVERGENCE_MEASUREMENT_ONLY=1`.

VACC honors that flag: when the frozen baseline has no verified VACC loopback runtime, it reports the transport/provider predicate failure and does not invoke the Ecosystem Chat parent repair during the same measurement pass. Ordinary non-measurement repair behavior remains available for later remediation runs.

The convergence layer does not automatically retry a lane after its first measured failure. Repairs occur only after the measurement receipt is inspected.

## Failure response shape

Every lane receives an ordered ten-stage `boundary_trace`, `first_failure`, exact stage index/code, reason/evidence reference where present, and an aggregate `failure_boundary_summary`.

The ten canonical boundaries remain:

1. runtime profile resolution;
2. persistent node continuity;
3. ephemeral request consumption;
4. WorkerCoordinator claim/fence;
5. ephemeral Interlock/InTr admission;
6. ephemeral transport/provider/lease;
7. component execution;
8. exact receipt commitment;
9. Master Records reconstruction;
10. downstream propagation.

Classification is diagnostic only and grants no execution, claim/fence, Interlock/InTr, credential, custody, publication, or completion authority.

## Authentic next action

1. refresh the already-local sovereign runtime source so the merged measurement worker, hardened boundary classifier, VACC measurement behavior, and profiled convergence runner are materialized together while mutable resident state is preserved;
2. execute exactly one authentic Runtime Profile Map/profiled convergence measurement;
3. do not repair or automatically retry a lane after its first failure during that run;
4. retain `receipts/sovereign-host/global-runtime-node-profile-convergence.latest.json`;
5. compare its measured first-failure histogram with the prior projection;
6. inspect before/after retained-node/HB/transition commitments to determine which node instances actually advanced;
7. begin remediation only in subsequent executions.

DE-006 remains expected to expose exact parent rebinding/re-execution until authentic evidence proves otherwise; readiness must not hide that boundary.

## README impact

Repository README semantics already cover retained identity, bounded/ephemeral execution, exact evidence, subject-bound failure behavior, non-authorizing HB, and functional-change documentation requirements. No additional README mutation is required for this diagnostic measurement hardening.

## Manual work

None before the machine-executable authentic measurement attempt.
