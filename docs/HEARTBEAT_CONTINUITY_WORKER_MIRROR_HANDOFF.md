# Heartbeat Continuity Worker Mirror Handoff

## Authority

This scoped handoff is subordinate to `docs/ORG_MIRROR_HANDOFF.md` and `StegVerse-Labs/.github#12`. It records the implementation slice that reconciles worker scheduling, heartbeat-relative transition timing, continuity observations, Master Records finalization gaps, and worker/job cost-basis inputs into the single StegVerse heartbeat model.

No separate scheduler, worker heartbeat, conversational trigger, GitHub Actions schedule, cron schedule, Render schedule, or third-party wake service is normative authority for this lane.

## Canonical model

StegVerse has one heartbeat. The heartbeat is the common relative timing and coordination frame across participating systems.

At each heartbeat epoch:

1. current HANDOFF / worker-registry state is evaluated;
2. eligible unclaimed work may be initiated under existing bounded authority and collision/fencing rules;
3. active workers return relative transition information on that same heartbeat;
4. expected versus observed transitions and correlated system signals produce delta-HB evidence;
5. a missing, late, or non-following transition is an observation, not by itself evidence that continuity is lost;
6. discrepancies requiring action become investigation/reconciliation work;
7. when appropriate, candidate remedies are sandbox-tested and only validated remedies are admitted as executable registry work;
8. Master Records retains required lifecycle evidence and reconstruction data.

## Cost-basis integration

Worker expiry and deployment policy must move away from arbitrary guessed timeout values toward evidence-derived heartbeat transition budgets.

The worker/job cost basis is ecosystem-wide and includes internal and external-entity jobs. It may accumulate, when evidenced:

- HB transitions to completion and idle-transition behavior;
- compute and token consumption;
- storage and network consumption;
- latency;
- operator burden;
- external provider / entity cost;
- failure, retry, investigation, sandbox, recovery, custody, and reconstruction cost;
- worker class / capability used;
- authority and admissibility constraints;
- external-entity job class and realized cost.

Cost does not override admissibility, authority, evidence fidelity, or reconstructability. Increasing sample history is intended to improve worker selection, expected completion envelopes, expiry estimates, recovery strategy, capacity planning, external-job costing, and future pricing strategy.

## Installed implementation slice

- `schemas/heartbeat-transition-observation.schema.json`
  - typed expected/observed transitions, supporting signals, delta-HB, continuity interpretation, and optional cost observations;
  - explicitly forbids declaring continuity lost from this observation record alone.
- `schemas/worker-runtime-cost-basis.schema.json`
  - task-class / external-entity-class runtime cost estimates;
  - heartbeat completion/idle/expiry estimates with confidence;
  - compute/token/storage/network/operator/external-cost/latency/failure/recovery dimensions;
  - cost never overrides admissibility.
- `schemas/worker-registry.schema.json`
  - adds `heartbeat_timing`, `cost_basis_ref`, and `external_entity_job_ref` while retaining legacy wall-clock lease values only as evidence-compatible fields.
- `scripts/project_heartbeat_workers.py`
  - projects worker state against the single organization heartbeat epoch;
  - active worker state now requires HB-relative timing;
  - reports delta-HB since response / transition and no longer treats legacy wall-clock lease timing as canonical worker timing.
- `scripts/reconcile_heartbeat_continuity.py`
  - deterministic continuity projection;
  - known HB-relative expiry plus missing Master Records final worker report yields a registry recovery-task candidate;
  - recovery candidate requests lifecycle reconciliation / investigation / sandbox validation before a validated remediation becomes executable work.
- `control/heartbeat-continuity.json`
  - current continuity projection; current StegGate workload has not yet established HB-relative worker timing.
- `.github/workflows/heartbeat-worker-project.yml`
  - validation only;
  - scheduled cron activation removed;
  - validates the single-HB posture and derived continuity state on repository changes or explicit dispatch only.

## Current worker truth

The previous `StegVerse Worker Cycle` ChatGPT automation is disabled. Therefore it is not current worker execution authority and is not the SHWP scheduler.

`control/worker-registry.json` generation 3 truthfully returns `STEGGATE-AUDITKIT-001` to `HANDOFF_READY / UNBOUND`. This avoids falsely representing the disabled bootstrap executor as active autonomous continuation.

The existing Master Records checkpoint remains retained as historical/custody evidence. A future heartbeat-bound worker must establish its own HB-relative transition state and subsequent lifecycle/finalization evidence.

## Current implementation boundary

This slice does not yet implement the native high-frequency heartbeat runtime that performs atomic worker initiation. It installs the data contracts and reconciliation semantics required for that runtime without introducing another scheduler.

The next implementation step under parent issue #12 is to compose the existing organization heartbeat issuance/return path with HANDOFF registry evaluation and worker transition returns in one internal heartbeat function, then prove:

- no eligible work -> no worker initiated;
- eligible HANDOFF -> exactly one fenced worker initiation;
- each active worker returns relative transition state on the same heartbeat;
- delta-HB is derived from expected/observed transition and signal behavior;
- known expiry plus missing required Master Records finalization -> recovery task admitted through normal registry rules;
- investigation may emit sandbox work and validated remediation work;
- cost-basis observations are accumulated for worker expiry/deployment estimation, including external-entity job costs;
- no third-party scheduler is necessary for normative operation.

## Collision boundary

All implementation remains part of `STEGVERSE-HEARTBEAT-WORKER-PROTOCOL-001`. Child issues are implementation details, not independent architectures. Any conflicting child description must be reconciled to parent issue #12 before implementation.

## Status

```text
goal_id: STEGVERSE-HEARTBEAT-WORKER-PROTOCOL-001
scope: single-HB continuity + worker timing + recovery + cost-basis integration
state: IMPLEMENTATION_ACTIVE
scheduler_dependency: NONE_NORMATIVE
chat_automation: DISABLED
native_worker_initiation: NOT_YET_PROVEN
HB_relative_worker_timing_contract: INSTALLED
continuity_delta_contract: INSTALLED
MR_missing_finalization_recovery_candidate: INSTALLED
worker_runtime_cost_basis_contract: INSTALLED
external_entity_job_cost_fields: INSTALLED
```
