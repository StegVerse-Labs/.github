# Heartbeat Continuity Worker Mirror Handoff

## Authority

This scoped handoff is subordinate to `docs/ORG_MIRROR_HANDOFF.md` and `StegVerse-Labs/.github#12`. It is the canonical continuation for the single-heartbeat worker/continuity implementation slice. `management/SHWP_SESSION_EXECUTION_INVENTORY.json` is the session execution inventory.

No separate scheduler, worker heartbeat, conversational trigger, GitHub Actions schedule, cron schedule, Render schedule, or third-party wake service is normative authority for this lane.

## Canonical model

StegVerse has one heartbeat. Each heartbeat epoch is the common relative timing and coordination frame. The heartbeat evaluates HANDOFF/worker-registry state; no eligible work means no worker. Eligible work may be atomically/fenced checked out only when bounded authority, a resolvable worker adapter, dependencies, and an evidenced expiry basis are present. Active workers return relative transition state on that same heartbeat.

Expected/observed transitions and correlated signals produce delta-HB evidence. Missing, late, unchanged, or non-following transitions are observations, not by themselves evidence that continuity is lost.

Known HB-relative expiry plus absence of the required Master Records final worker report is a lifecycle inconsistency: the expired parent is blocked, a distinct recovery task is admitted, and the old worker path cannot silently reactivate. Investigation may require sandbox testing; only validated remediation is admitted as executable work.

## Native runtime installed

Canonical runtime files:

```text
heartbeat_runtime/__init__.py
heartbeat_runtime/engine_v2.py
scripts/run_heartbeat_runtime.py
schemas/worker-registry.schema.json
scripts/project_heartbeat_workers.py
scripts/reconcile_heartbeat_continuity.py
control/worker-registry.json
control/worker-status.json
control/heartbeat-continuity.json
```

Implemented semantics:

- one internal HB epoch for scheduling and worker transition responses;
- host/provider-agnostic runtime engine;
- atomic cycle lock;
- capability + adapter matching;
- dependency gating;
- exactly-one activation per cycle;
- claim ID + fencing generation;
- HB-relative worker timing;
- no arbitrary expiry: activation is deferred when no evidenced cost basis exists;
- worker cost observations retained per HB transition;
- completion releases worker and claim;
- expiry without required Master Records finalization blocks parent and creates recovery work;
- dry-run is non-mutating;
- blocked/unclaimed tasks remain valid blocked state and are not misclassified as active workers.

The superseded first engine was removed after hosted testing exposed a real same-cycle reactivation defect in its expiry path. The hardened engine blocks the expired parent on the recovery task instead.

## Cost-basis integration

Canonical files:

```text
schemas/worker-runtime-cost-basis.schema.json
control/worker-cost-observations.json
scripts/estimate_worker_cost_basis.py
tests/test_worker_cost_basis_estimator.py
```

The estimator uses only completed HB-relative samples. With no completed live samples it emits no expiry estimate and confidence NONE. With samples it derives a conservative completed-sample median/p90 envelope and expiry candidate; confidence grows with sample count. Internal/external entity job classes and evidenced external costs are retained. Cost never overrides admissibility, authority, evidence fidelity, or reconstructability.

Current live observation ledger has zero task-class samples; therefore no production expiry estimate exists yet. This is intentional fail-closed behavior.

## StegGate canonical workload state

The old `STEGGATE-AUDITKIT-001` registry task was stale relative to live ara state and has been corrected to `COMPLETED`. Do not reactivate it.

Canonical successor:

```text
task_id: STEGGATE-FIRST-BOUNDARY-001
state: BLOCKED
executor_binding: UNBOUND
claim: NONE
source: StegVerse-Labs/ara-admissibility-interop#13
release condition: management/first-boundary-activation.json contains a durable consequential_target_ref and authority_model_ref, state READY, and tools/validate_first_boundary_activation.py PASS
```

The heartbeat must not activate this task while the blocker remains.

## Hosted proof

Strongest current validation:

```text
head: 262c829e052d5da6f9aba4542c7dcd543fe2db80
workflow: Heartbeat Worker Project
run: 31236519287
job: 93049882049
result: SUCCESS
```

Validated steps include:

- compile runtime/projectors/estimator;
- parse canonical JSON;
- 6/6 native HB runtime lifecycle tests PASS;
- 3/3 worker cost-basis estimator tests PASS;
- sparse live cost data -> no invented expiry PASS;
- live registry dry-run -> no false worker activation PASS;
- worker status projection PASS;
- heartbeat continuity projection PASS;
- completed Audit Kit + blocked/unclaimed first-boundary successor posture PASS.

Previous exact native-runtime proof before estimator integration:

```text
head: 4696a4cea187f96fcc36e8472dc433dce51c7c9d
run: 31236459790
result: SUCCESS
```

## Current worker truth

The former ChatGPT `StegVerse Worker Cycle` bootstrap automation is disabled and is not execution authority or the scheduler. No ChatGPT automation or monitoring was created for this session.

The native runtime core exists and is validated, but no legitimate production mutation-capable worker adapter is currently registered/bound. Therefore there is no claim that production autonomous repository mutation is active.

## Remaining exact work

### `.github#13` — production worker adapter/runtime binding

Required:

- choose/install a provider-agnostic mutation-capable worker adapter whose authority is independently admitted;
- register it using `worker.adapter_ref` and exact capabilities;
- bind only eligible registry work;
- prove a real worker responds on the same heartbeat across multiple cycles;
- prove fenced duplicate checkout rejection under real execution;
- retain checkpoint/final report evidence and release the claim correctly.

No synthetic adapter may satisfy the production completion condition.

### `.github#14` — native lifecycle custody

Exercise a real native worker lifecycle through Master Records, including checkpoint, expiry/finalization or completion, recovery when applicable, and reconstruction. The fixture-proven recovery semantics are not a substitute for live custody evidence.

### Empirical cost basis

Accumulate completed live HB-relative samples, including actual external-entity costs when external jobs exist. The estimator must remain fail-closed at confidence NONE when evidence is absent.

## Claim and collision state

```text
STEGVERSE-HEARTBEAT-WORKER-PROTOCOL-001: CLAIMED_FOR_IMPLEMENTATION by this session for native runtime/cost-basis slice until hosted proof + handoff transfer
STEGGATE-AUDITKIT-001: COMPLETE
STEGGATE-FIRST-BOUNDARY-001: BLOCKED / UNCLAIMED
StegCore#54: COMPLETE / RELEASED
```

After this handoff update, the native runtime/cost-basis implementation claim is released from this specific file slice; remaining production adapter and live custody work remain canonical under `.github#13/#14`, but this conversation still contains active execution responsibility until a genuine non-conversational native execution path is active or the remaining implementation is completed here.

## Validation commands

```text
python -m unittest -v tests.test_heartbeat_runtime
python -m unittest -v tests.test_worker_cost_basis_estimator
python scripts/estimate_worker_cost_basis.py --check
python scripts/run_heartbeat_runtime.py --dry-run --cycles 1
python scripts/project_heartbeat_workers.py --check
python scripts/reconcile_heartbeat_continuity.py --write
```

## Cross-repository dependencies

- `StegVerse-Labs/ara-admissibility-interop`: first-real-boundary successor; blocked/unclaimed.
- `master-records/orchestration`: native lifecycle custody/reconstruction owner.
- `StegVerse-Labs/StegCore`: no work from StegCore #54; completed canonical semantics must not be duplicated.
- Site/Publisher/wikis: no propagation from this implementation slice is currently authorized or release-ready.

## Session consolidation

```text
inventory: management/SHWP_SESSION_EXECUTION_INVENTORY.json
session_state: ACTIVE_UNIQUE_WORK_REMAINS
thread_archive_ready: false
```

Archive is denied because the provider-agnostic native engine is validated but no production mutation-capable adapter/live worker is bound and the live Master Records lifecycle has not been exercised by the native runtime.

## Completion assessment

For the current single-HB native-runtime/cost-basis implementation slice:

```text
developed_files: 17/17 canonical files installed
scaffolding_or_stubs: 0 counted as completed deliverables
validation: 9/9 current hosted validation classes pass
integration: 7/9 (native engine + registry + HB timing + recovery + status + continuity + estimator integrated; production adapter and live MR lifecycle remain)
goal_activation: 78% (runtime/control semantics operational and validated; production autonomous mutation not active)
session_consolidation: 8/8 identified session goals durably inventoried/transferred, but session remains active because remaining production execution is not yet archive-safe
```
