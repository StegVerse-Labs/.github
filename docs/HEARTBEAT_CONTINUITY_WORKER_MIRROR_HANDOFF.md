# Heartbeat Continuity Worker Mirror Handoff

## Authority

This scoped handoff is subordinate to `docs/ORG_MIRROR_HANDOFF.md` and `StegVerse-Labs/.github#12`. It is the canonical continuation for the single-heartbeat worker/continuity implementation slice. `management/SHWP_SESSION_EXECUTION_INVENTORY.json` is the machine-readable session inventory.

No separate scheduler, worker heartbeat, conversational trigger, GitHub Actions schedule, cron schedule, Render schedule, or third-party wake service is normative authority for this lane.

## Active goal and claim

```text
goal_id: STEGVERSE-HEARTBEAT-WORKER-PROTOCOL-001
repository: StegVerse-Labs/.github
branch: main
canonical_owner: issue #12
implementation_claim: ACTIVE_FOR_REMAINING_PROTOCOL_PROOFS; runtime activation separately BLOCKED
validation_claim: MACHINE_OWNED by repository validation workflows
collision_boundary: one heartbeat only; no parallel scheduler/epoch owner; no Audit Kit reactivation
runtime_activation_release_condition: durable writable heartbeat state backend + long-lived process host can run scripts/run_heartbeat_runtime.py --continuous and preserve state across restart without an external scheduler owning cadence
```

## Canonical model

StegVerse has one heartbeat. `heartbeat_runtime.engine_v3.HeartbeatRuntime.cycle()` is the sole epoch owner. Within the same epoch it issues organization claim assertions, receives active-worker transition responses, evaluates HANDOFF/worker-registry state, performs bounded fenced checkout when eligible, records cost evidence, and emits lifecycle events. The heartbeat itself never grants execution authority.

`heartbeat_runtime/org_assertions.py` accepts an already-owned epoch and cannot advance it. Legacy `scripts/issue_heartbeats.py` is diagnostic-only. The former eight-hour GitHub heartbeat schedule is removed; `.github/workflows/org-heartbeat.yml` is validation-only. `scripts/run_heartbeat_runtime.py --continuous` owns internal process cadence; a host supplies liveness only.

## Completed runtime/executor/custody proofs

### Real native executor

```text
workflow: Native Process Worker Canary
run/job: 31237212782 / 93051843063 SUCCESS
source evidence commit: 365581b79665e211fcc8f1b935ef464476ed2075
claim: SHWP-SHWP-NATIVE-PROCESS-CANARY-001-G6
fence: 6
HB2: CANARY_CHECKPOINT seq1
HB3: CANARY_COMPLETE seq2
claim + worker released: true
```

`.github#13` is CLOSED COMPLETE. The canary proves bounded real execution only; it does not grant general autonomous coding authority.

### Master Records lifecycle custody

```text
owner: master-records/orchestration
record hash: 313ae32e1fabeb6879f7c84e7dcb9a1e3af69f819176c49fb9f8039e99e42efd
lineage hash: e00111e611b5f8f6af49c7ba3036430bdba2d3d62228b258266a908400ba711c
terminal event hash: 80f6f5f74e0cfbaad493a9254cd3daa815d8e878eb4ec75205b2f152758cb3db
validation run/job: 31237511378 / 93052660913 SUCCESS
reconstruction: PASS
authority_effect: NONE
```

`.github#14`, #37 and #52 are CLOSED COMPLETE.

### Unified one-heartbeat carrier

```text
workflow: Organization heartbeat validation
run/job: 31237675041 / 93053122793 SUCCESS
```

It proves legacy issuer no longer owns the clock, organization assertions and worker evaluation share one epoch, three internal process cycles advanced HB4 -> HB5 -> HB6, and no eligible work initiated no worker. `.github#30` is CLOSED COMPLETE.

## Activation request / execution authority separation — COMPLETE

Installed:

```text
schemas/heartbeat-activation-request.schema.json
schemas/executable-handoff.schema.json
heartbeat_runtime/engine_v2.py
tests/test_heartbeat_runtime.py
```

Every eligible HANDOFF discovery emits `stegverse.heartbeat-activation-request/v0.1` with task/goal, handoff hash/ref, required capabilities, current fence generation, authority source, and `execution_authority=false`. Checkout fails closed unless the HANDOFF is separately `AUTHORIZED` and has a durable `authorization_ref`. Heartbeat discovery alone cannot create a claim or invoke an executor.

```text
hosted proof: Heartbeat Worker Project 31239408656 / 93057709920 SUCCESS
negative proof: test_discovery_event_never_grants_execution_authority PASS
```

`.github#38` and #46 are CLOSED COMPLETE.

## Successor reconstruction — COMPLETE

Installed:

```text
schemas/worker-reconstruction-proof.schema.json
schemas/executable-handoff.schema.json continuity.reconstruction_ref
heartbeat_runtime/engine_v2.py
tests/test_heartbeat_runtime.py
```

A successor with `parent_task_id` cannot acquire a new claim from authorization alone. It must present a PASS reconstruction proof binding task/goal/parent, authority source and policy version, last valid fence, checkpoint ref/hash, Master Records refs, evidence lineage, unresolved work, and `execution_authority=false`. The new registry generation/fence must be greater than the reconstructed prior fence. Generated expiry-recovery tasks are explicitly `SUCCESSOR_RECONSTRUCTION_REQUIRED` until this proof exists.

```text
hosted proof: Heartbeat Worker Project 31239557101 / 93058118640 SUCCESS
runtime tests: 9/9 PASS
negative: authorized successor without reconstruction cannot checkout
positive: reconstructed successor resumes without chat state and acquires fence 6 > prior fence 4
```

`.github#42` is CLOSED COMPLETE.

## Organization control-plane integrity — REPAIRED

The historical TASK-2026-0001 check-in was valid to its schema; `scripts/reconcile_checkins.py` was incorrect. It now validates terminal delivery states inside `repository_results[]` and requires merge commit evidence for merged delivery.

```text
corrective commit: 994ae85f1d678f1387d78b8909df47d2859bc7b5
Validate organization control plane: 31238008341 / 93054063188 SUCCESS
```

No outstanding organization-control-plane integrity blocker remains from that finding.

## StegGate / StegCore truth

```text
STEGGATE-AUDITKIT-001: COMPLETED / never reactivate
ara PR #1: open draft at last verified c2df13fbbf51144f20ee8c46ff27653e7336c17d
ara issues #2/#23/#66: complete
StegCore#54: complete/released
STEGGATE-FIRST-BOUNDARY-001: BLOCKED / UNCLAIMED
```

First-boundary release is machine-observable: durable `consequential_target_ref` + `authority_model_ref`, ara activation READY, and `tools/validate_first_boundary_activation.py` PASS. `.github#24` is CLOSED superseded because its unfinished-Audit-Kit premise is obsolete.

## Remaining exact implementation work

### #51 mutation scope/fence enforcement

The current process adapter has pre-admitted command selection, but general mutation-capable workers are not yet centrally constrained at the filesystem commit boundary. Required: execute mutations in an isolated workspace, compute the candidate delta, verify every changed path against admitted scope and current fence, deny and record out-of-scope/stale-fence proposals, and project only accepted changes to the authoritative workspace. Post-hoc observation after uncontrolled mutation is insufficient.

### #18/#35/#36 expiry, renewal, orphan recovery

Reconcile these children to the one-heartbeat model. There must be no second heartbeat deadline. Renewal is a separately admitted transition and cannot be an automatic liveness side effect. Missed/unchanged worker transitions must produce observable degradation/recovery behavior while stale fences remain unable to mutate.

### Parent #12 durable runtime activation

The continuous runtime exists and is validated, but no durable always-on process/state host is currently activated. Connected deployment inspection found no correctly owned existing service, and the available Render creation control cannot provision the required persistent-state/background-worker combination.

```text
owner: StegVerse-Labs/.github#12
state: BLOCKED_RUNTIME_ACTIVATION
release_condition:
  1. replaceable long-lived process host available to .github;
  2. heartbeat/registry/event/cost state survives restart/deploy;
  3. host runs scripts/run_heartbeat_runtime.py --continuous;
  4. runtime controls machine-scale cadence; host supplies liveness only;
  5. restart preserves one epoch lineage and no duplicate claim/fence;
  6. no ChatGPT/GitHub cron/Render cron or external scheduler is required.
```

### Empirical cost history

The estimator is implemented and fail-closed. Broader task-class cost history must accumulate from actual native work after durable activation; external costs are observed, never invented. This is not a reason to fabricate an expiry basis now.

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

All design decisions through activation authority and successor reconstruction are durable. The session remains active because #51 and the #18/#35/#36 lifecycle cluster still contain executable implementation work, and parent #12 durable runtime activation remains blocked on a machine-observable hosting/state boundary.

```text
session_state: ACTIVE_UNIQUE_WORK_REMAINS
thread_archive_ready: false
```

## Completion assessment

Denominator is now 15 canonical capability tasks: the previous 12 plus activation-authority separation, typed activation request, and successor reconstruction.

```text
canonical_capability_tasks: 15
complete: 13
partially_complete_or_blocked: 2
task_completion: 87%
canonical developed-file set: 30/30
scaffolding_or_stubs: 0
validation classes: 15/15
integration classes: 13/14
goal_activation: 93%
session_consolidation: 13/13 durable session requirements transferred or complete
```
