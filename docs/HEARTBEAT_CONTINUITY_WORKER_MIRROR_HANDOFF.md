# Heartbeat Continuity Worker Mirror Handoff

## Authority

This scoped handoff is subordinate to `docs/ORG_MIRROR_HANDOFF.md` and `StegVerse-Labs/.github#12`. It is the canonical continuation for the single-heartbeat worker/continuity implementation slice. `management/SHWP_SESSION_EXECUTION_INVENTORY.json` is the session execution inventory.

No separate scheduler, worker heartbeat, conversational trigger, GitHub Actions schedule, cron schedule, Render schedule, or third-party wake service is normative authority for this lane.

## Active goal and claim

```text
goal_id: STEGVERSE-HEARTBEAT-WORKER-PROTOCOL-001
repository: StegVerse-Labs/.github
branch: main
canonical_owner: issue #12
implementation_claim: BLOCKED_ON_DURABLE_RUNTIME_ACTIVATION
claim_created_at: 2026-08-08T03:40:00Z
claim_release_condition: durable writable heartbeat state backend + long-lived process host can run scripts/run_heartbeat_runtime.py --continuous and preserve state across restart without an external scheduler owning cadence
validation_claim: MACHINE_OWNED by repository validation workflows
collision_boundary: one heartbeat only; no parallel scheduler/epoch owner; no Audit Kit reactivation
```

## Canonical model

StegVerse has one heartbeat. `heartbeat_runtime.engine_v3.HeartbeatRuntime.cycle()` is now the sole epoch owner. Within the same epoch it issues organization claim assertions, receives active-worker transition responses, evaluates HANDOFF/worker-registry state, performs bounded fenced checkout when eligible, records cost evidence, and emits lifecycle events. The heartbeat itself never grants execution authority.

`heartbeat_runtime/org_assertions.py` accepts an already-owned epoch and cannot advance it. Legacy `scripts/issue_heartbeats.py` is diagnostic-only and explicitly cannot advance heartbeat state. The former 8-hour GitHub Actions heartbeat schedule has been removed; `.github/workflows/org-heartbeat.yml` is validation-only.

`python scripts/run_heartbeat_runtime.py --continuous --interval-ms <internal-cycle-delay>` runs the internal machine-cycle loop. The host keeps the process alive; it does not determine heartbeat cadence or execution authority.

## Installed runtime and executor surfaces

```text
heartbeat_runtime/engine_v3.py
heartbeat_runtime/engine_v2.py
heartbeat_runtime/org_assertions.py
heartbeat_runtime/process_adapter.py
heartbeat_runtime/__init__.py
scripts/run_heartbeat_runtime.py
scripts/issue_heartbeats.py
control/process-worker-adapters.json
schemas/process-worker-adapters.schema.json
control/worker-registry.json
schemas/worker-registry.schema.json
workers/heartbeat_receipt_canary.py
handoffs/SHWP-NATIVE-PROCESS-CANARY-001.json
cost-basis/worker-runtime/native-process-canary.json
control/worker-cost-observations.json
scripts/estimate_worker_cost_basis.py
scripts/project_heartbeat_workers.py
scripts/reconcile_heartbeat_continuity.py
```

## Real native executor proof — COMPLETE

`SHWP-NATIVE-PROCESS-CANARY-001` used an enabled provider-neutral process adapter and a real local executable restricted to `receipts/native-worker-canary/**`.

```text
workflow: Native Process Worker Canary
run: 31237212782
job: 93051843063
result: SUCCESS
source evidence commit: 365581b79665e211fcc8f1b935ef464476ed2075
claim: SHWP-SHWP-NATIVE-PROCESS-CANARY-001-G6
fence: 6
HB2: CANARY_CHECKPOINT sequence 1
HB3: CANARY_COMPLETE sequence 2
worker released: true
claim released: true
external cost: 0
```

This proves a real process executor, same-HB responses, bounded mutation, fencing, completion and release. It does not grant general autonomous coding authority. `.github#13` is CLOSED / COMPLETE.

## Master Records lifecycle custody — COMPLETE

Canonical owner: `master-records/orchestration`.

```text
v2 custody record: custody/worker-lifecycle/SHWP-CUSTODY-NATIVE-PROCESS-CANARY-001-G6-001.json
record hash: 313ae32e1fabeb6879f7c84e7dcb9a1e3af69f819176c49fb9f8039e99e42efd
lineage: custody/worker-lifecycle-lineage/SHWP-LINEAGE-NATIVE-PROCESS-CANARY-001-G6.json
lineage hash: e00111e611b5f8f6af49c7ba3036430bdba2d3d62228b258266a908400ba711c
terminal event hash: 80f6f5f74e0cfbaad493a9254cd3daa815d8e878eb4ec75205b2f152758cb3db
validation run: 31237511378
job: 93052660913
result: SUCCESS
reconstruction: PASS
authority_effect: NONE
```

The event vocabulary supports TASK_ADMITTED, ACTIVATION_REQUESTED, WORKER_AUTHORIZED, TASK_CHECKED_OUT, HEARTBEAT_ACCEPTED, CHECKPOINT_COMMITTED, AUTHORIZATION_RENEWED, WORKER_BLOCKED, AUTHORIZATION_EXPIRED, HANDOFF_EMITTED, TASK_RECLAIMED, TASK_COMPLETED and CLAIM_RELEASED. A successful lineage records only events that actually occurred. `.github#14`, #37 and #52 are CLOSED / COMPLETE.

## Unified heartbeat carrier proof — COMPLETE

```text
workflow: Organization heartbeat validation
run: 31237675041
job: 93053122793
result: SUCCESS
```

Direct proof:
- legacy heartbeat issuer cannot advance epoch;
- v3 unified dry-run owns the next epoch without mutating live state;
- organization assertions and worker evaluation are in the same v0.3 cycle;
- three internal cycles advanced the single epoch 4 -> 5 -> 6;
- with no eligible work, no worker was initiated on any cycle.

`.github#30` is CLOSED / COMPLETE.

## Cost basis

The engine refuses activation when an evidenced expiry basis is unavailable. The deterministic canary supplied the first real native HB-relative runtime observations: two transitions, zero external cost. The general estimator remains conservative and does not infer external-entity costs or production task-class expiry from unrelated samples. Broader empirical calibration remains ongoing under the parent goal and resource/cost children.

## StegGate / StegCore truth

```text
STEGGATE-AUDITKIT-001: COMPLETED / archive eligible / never reactivate
ara PR #1: open draft at c2df13fbbf51144f20ee8c46ff27653e7336c17d
ara issues #2/#23/#66: complete
StegCore#54: complete/released
STEGGATE-FIRST-BOUNDARY-001: BLOCKED / UNCLAIMED
```

First-boundary release is machine-observable: durable `consequential_target_ref` + `authority_model_ref`, ara activation state READY, and `tools/validate_first_boundary_activation.py` PASS. `.github#24` is CLOSED as superseded because its original unfinished-Audit-Kit premise is no longer true.

## Remaining exact implementation work

### Parent #12 production activation blocker

The continuous runtime exists and is validated, but no durable always-on process/state host is currently activated.

Connected deployment inspection on 2026-08-08 found no existing service with correct control-plane ownership. Reusing `StegVerse-SCW`'s background worker would improperly transfer `.github` control-plane ownership. Reusing unrelated LLM/HIL services would also violate ownership. The available Render create-service control cannot provision the required persistent disk/background-worker combination, so creating a stateless web service would not satisfy continuity.

```text
owner: StegVerse-Labs/.github#12
state: BLOCKED_RUNTIME_ACTIVATION
release_condition:
  1. a replaceable long-lived process host is available to StegVerse-Labs/.github;
  2. heartbeat state / registry / event / cost state are durably writable and survive process restart/deploy;
  3. host runs scripts/run_heartbeat_runtime.py --continuous;
  4. runtime itself controls machine-scale cadence; host supplies liveness only;
  5. restart proof preserves/increments one epoch with no duplicate claim/fence;
  6. no ChatGPT/GitHub cron/Render cron or other external scheduler is required.
next_action: activate the continuous runtime only when all six conditions can be met without changing canonical ownership or losing persistent state.
```

### Still-open protocol proofs

- #18/#35/#36: authority expiry/renewal/orphan-recovery semantics must be reconciled to the one-HB model; no second heartbeat deadline may be introduced.
- #38/#46: typed activation-request versus execution-authorization negative proof remains distinct from the existing worker-activated event.
- #42: successor reacquisition from checkpoint + Master Records must still be proven; reconstruction of the completed canary alone is not successor acquisition.
- #51: general mutation-capable workers need centralized scope/fence enforcement; canary-local path enforcement is not general proof.

## Validation commands

```bash
python -m unittest -v tests.test_heartbeat_runtime
python -m unittest -v tests.test_worker_cost_basis_estimator
python scripts/run_heartbeat_runtime.py --dry-run --cycles 1
python scripts/project_heartbeat_workers.py --check
python scripts/reconcile_heartbeat_continuity.py --write
```

Master Records:

```bash
python scripts/verify_worker_lifecycle_custody.py
python scripts/verify_worker_lifecycle_lineage.py
```

## Session consolidation / archive

All unique session knowledge is durably represented in repository state, but the session is not archive-safe because the governing objective requires unfinished work to advance without conversational prompting and the continuous runtime is not yet actively hosted on durable state.

```text
session_state: BLOCKED_RETAIN_TEMPORARILY
thread_archive_ready: false
machine_observable_release_condition: durable persistent process/state host satisfies parent #12 activation conditions above
```

## Completion assessment

```text
canonical_capability_tasks: 12
complete: 10
partially_complete_or_blocked: 2
task_completion: 83%
canonical developed-file set: 28/28
scaffolding_or_stubs: 0
validation classes: 12/12
integration classes: 10/11
goal_activation: 91%
session_consolidation: 10/10 durable goal records
```
