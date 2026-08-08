# StegVerse-Labs Organization Mirror Handoff

## Authority

This is the primary organization continuation/exit record for `StegVerse-Labs` control-plane work. Repository-local `*_MIRROR_HANDOFF.md` files remain authoritative for repository-local implementation. Machine-readable state under `control/`, `handoffs/`, `management/`, `events/`, `checkpoints/`, `heartbeats/`, `receipts/`, and `schemas/` is authoritative over chat history.

## Active goal and ownership

```text
goal_id: STEGVERSE-HEARTBEAT-WORKER-PROTOCOL-001
originating_session_goal: make unfinished StegVerse work survive conversation retirement under one internal heartbeat without user/manual restart
repository: StegVerse-Labs/.github
branch: main
canonical_task_owner: StegVerse-Labs/.github#12
active_implementation_claim: NONE — all SHWP protocol child implementation is complete
active_validation_claim: NONE — latest full control-plane validation is green
claim_creation_time: N/A
claim_expiration_or_release_condition: N/A
scoped_handoff: docs/HEARTBEAT_CONTINUITY_WORKER_MIRROR_HANDOFF.md
session_inventory: management/SHWP_SESSION_EXECUTION_INVENTORY.json
runtime_activation_blocker: management/SHWP_RUNTIME_ACTIVATION_BLOCKER.json
state: BLOCKED_RUNTIME_ACTIVATION_AFTER_COMPLETE_PROTOCOL_IMPLEMENTATION
```

## Canonical architecture

StegVerse has **one heartbeat**. `heartbeat_runtime/engine_v8.py` is selected by `heartbeat_runtime/__init__.py` and is the canonical runtime. The same heartbeat is the scheduling, reconciliation, worker-relative timing, and general information carrier. Active workers answer that same heartbeat with relative transition information. There is no second worker heartbeat, scheduler heartbeat, cron clock, or conversation-owned timing plane.

Each epoch carries and evaluates registry/HANDOFF state, active-worker responses, expected/observed transitions, authority state, policy version, resource usage, capability profile, canonical checkpoints, nested worker/Master Records evidence, failure/recovery signals, goal convergence, and successor state. Heartbeat testimony never grants execution authority.

## Canonical runtime stack

```text
heartbeat_runtime/engine_v8.py            canonical capability-profile runtime
heartbeat_runtime/engine_v7_1.py          canonical checkpoint + worker-checkpoint preservation
heartbeat_runtime/engine_v7.py            policy drift/rebind and checkpoint primitives
heartbeat_runtime/engine_v6.py            persistent bounded resource authority
heartbeat_runtime/engine_v5.py            goal lineage, duplicate control, successor narrowing/expansion admission
heartbeat_runtime/engine_v4.py            BLOCKED/human-authority boundaries
heartbeat_runtime/engine_v3.py            one-HB assertions, renewal, orphan recovery
heartbeat_runtime/engine_v2.py            base activation, expiry, MR-final-report recovery
heartbeat_runtime/process_adapter.py      sandboxed fenced mutation commit boundary
scripts/run_heartbeat_runtime.py           bounded/continuous runtime entrypoint
scripts/project_heartbeat_workers.py       fail-closed canonical status projection
scripts/query_worker_status.py             deterministic observational status query
scripts/evaluate_goal_convergence.py       deterministic no-work/convergence projection
```

## Completed protocol capabilities

All SHWP child implementation issues are closed complete. Canonical capability set includes:

- empty registry -> no worker;
- eligible authorized HANDOFF -> exactly one worker;
- atomic fenced checkout and duplicate-claim prevention;
- bounded real process-worker execution;
- typed activation request distinct from execution authority;
- ambiguity-safe executor discovery;
- machine-resolvable BLOCKED recheck and `HUMAN_AUTHORITY_REQUIRED` separation;
- one-HB expiry, separately admitted renewal and orphan recovery;
- missing Master Records final worker report -> one deduplicated reconciliation task;
- successor reconstruction and higher-fence acquisition;
- bounded goals, lineage, successor depth and authority narrowing;
- separate authority-expansion admission;
- duplicate canonical lane quarantine;
- sandbox mutation path/fence enforcement;
- persistent action/retry/runtime/service/external-cost authority budgets;
- policy-drift stop and separately admitted policy rebind;
- control-plane canonical checkpoint/hash and tamper refusal;
- worker/Master Records checkpoint preserved inside canonical checkpoint;
- worker capability profiles for deterministic workflow, repository maintenance, code-change agent, deployment worker and read-only observer;
- availability/capability/profile match never equals authorization;
- fail-closed archive/mutation posture for structural/authority/checkpoint/fence/custody/successor ambiguity;
- stable repository-native worker-status read surface;
- deterministic observational status query including checkpoint/evidence refs;
- deterministic goal convergence/no-work surface preventing perpetual successor work.

Final overlooked children #45, #47, #49 and #53 were implemented and closed after a live open-issue consistency search. They must not be rediscovered as future work.

## Validation evidence

### Canonical runtime promotion

```text
canonical runtime promotion commit: 11c1b801af35c94d3d67c398a7c93b2fed776448
workflow: Heartbeat Worker Project
run/job: 31242636078 / 93066031288
result: SUCCESS
```

This proves the production-selected v8 runtime including policy/checkpoints/capability/resource/lineage/lifecycle/sandbox behavior.

### Final complete control-plane validation

```text
workflow: Heartbeat Worker Project
run/job: 31242995304 / 93066913610
result: SUCCESS
```

Substantive steps passed:

1. runtime/projector compilation through v8/v7.1;
2. all canonical JSON parsing;
3. executable HANDOFF validation;
4. core one-heartbeat runtime tests;
5. executor ambiguity refusal;
6. BLOCKED/human authority boundaries;
7. goal-lineage/duplicate/successor controls;
8. bounded resource authority;
9. policy continuity and canonical checkpoint/tamper tests;
10. capability-profile matching;
11. fail-closed status/query/convergence tests;
12. sandbox mutation scope/fence tests;
13. one-HB renewal/orphan recovery;
14. cost-basis/no-guess tests;
15. dry-run nonmutation;
16. worker-status, convergence and continuity projections;
17. observational status-query smoke;
18. current StegGate successor blocked/nonconverged posture.

## Canonical read/convergence surfaces

`control/worker-status.json` is `stegverse.heartbeat-worker-status/v0.3` and explicitly sets `query_is_observational=true` and `execution_authority_from_heartbeat=false`. Structural or authority validation errors force `archive_eligible=false`.

`scripts/query_worker_status.py` performs deterministic read-only filters by task, goal and lifecycle state. It returns state, archive posture/reasons, worker/claim/fence, last checkpoint, next authorized action and evidence refs; `execution_authority=false`.

`control/goal-convergence.json` is the canonical no-work projection. A root goal converges only when:

- root task is authoritatively COMPLETED;
- no unresolved descendant remains;
- no active claim/worker remains in the goal family;
- required custody/reconstruction is complete;
- no separately authorized remaining action exists.

Current Audit Kit convergence is false because `STEGGATE-FIRST-BOUNDARY-001` remains an unresolved blocked descendant. This is intentional and prevents false terminal closure.

## Canonical checkpoint / Master Records relationship

After every accepted worker response, the control plane writes `stegverse.worker-checkpoint/v0.1` under `checkpoints/workers/**`. `last_checkpoint_ref` points to that canonical envelope. A worker/Master Records checkpoint is retained inside it as `worker_checkpoint_ref`.

The canonical checkpoint binds task/goal, worker instance, claim/fence, heartbeat epoch, transitions, unresolved work, evidence, next authorized action, policy, authority source, HANDOFF hash, resource budget, `execution_authority=false`, and canonical SHA-256. Successor reconstruction checks hash/fence/policy and refuses tampering. Master Records remains custody/reconstruction evidence, not execution authority.

## Live registry and claims

```text
STEGGATE-AUDITKIT-001: COMPLETED / archive eligible / unclaimed
STEGGATE-FIRST-BOUNDARY-001: BLOCKED / non-archivable / unclaimed
SHWP-NATIVE-PROCESS-CANARY-001: COMPLETED / archive eligible / unclaimed
stegverse-worker-cycle: DISABLED historical bootstrap worker
native-process-canary-worker: AVAILABLE bounded repository-worker canary
active SHWP implementation claims: NONE
active SHWP validation claims: NONE
```

`control/worker-capability-profiles.json` binds registered worker classes. No completed child issue has an active competing claim.

## StegGate / StegCore continuation

`StegVerse-Labs/ara-admissibility-interop`:

```text
PR #1: separate canonical StegGate continuation
issues #2/#23/#66: COMPLETE
STEGGATE-AUDITKIT-001: COMPLETE — NEVER REACTIVATE
STEGGATE-FIRST-BOUNDARY-001: BLOCKED / UNCLAIMED
release condition: named consequential target + durable authority model + ara activation READY + validator PASS
```

`StegVerse-Labs/StegCore#54`: COMPLETE / RELEASED. No duplicate StegCore implementation is authorized.

## Active blocker — durable continuous runtime activation

The protocol implementation and read/convergence layer are complete. Parent #12 remains open only for durable runtime activation.

Canonical blocker receipt:

```text
management/SHWP_RUNTIME_ACTIVATION_BLOCKER.json
```

Connected Render inspection on 2026-08-08 directly established:

- no existing service correctly owned by `StegVerse-Labs/.github` is suitable;
- `stegverse-hil-receiver` has a 1 GB persistent disk but is owned by `StegVerse-org/LLM-adapter` and cannot be appropriated;
- `scw-worker` is a background worker but belongs to `StegVerse-Labs/StegVerse-SCW`;
- existing persistent KV stores are SCW/TVC subsystem stores and have no authority transfer to `.github`;
- no Postgres instance exists;
- connected Render creation controls expose web-service creation without a persistent-disk parameter and expose no background-worker creation action.

No stateless substitute, cross-subsystem service appropriation, provider-specific unproven state adapter, ChatGPT monitor, cron scheduler, or paid resource was created.

Release predicates:

```text
1. correctly owned long-lived replaceable process host available to StegVerse-Labs/.github
2. durable writable heartbeat/registry/event/cost/receipt/checkpoint state survives restart/deploy
3. host starts scripts/run_heartbeat_runtime.py --continuous
4. runtime v8 owns internal cadence; host supplies liveness only
5. restart preserves/increments one heartbeat epoch and creates no duplicate claim/fence
6. no ChatGPT automation, GitHub schedule, Render cron, or equivalent scheduler owns worker activation
```

Owner: `StegVerse-Labs/.github#12`.
State: `BLOCKED_RUNTIME_ACTIVATION`.
Next executable action: reinspect connected deployment controls when a correctly owned durable process-host capability or admitted provider-neutral durable host becomes machine-observably available; then deploy and run the restart proof.

## Cross-repository dependencies / propagation

- `master-records/orchestration`: lifecycle custody/reconstruction owner.
- `ara-admissibility-interop`: first-boundary continuation owner.
- `StegCore`: #54 complete; no duplicate work.
- Site / Publisher / admissibility-wiki / stegguardian-wiki: no propagation obligation arises solely from SHWP runtime implementation; no publication/release was implied.

## Validation commands

```text
python scripts/validate_executable_handoffs.py
python -m unittest -v tests.test_heartbeat_runtime
python -m unittest -v tests.test_executor_discovery
python -m unittest -v tests.test_block_boundaries
python -m unittest -v tests.test_goal_lineage
python -m unittest -v tests.test_resource_authority
python -m unittest -v tests.test_checkpoint_policy
python -m unittest -v tests.test_capability_profiles
python -m unittest -v tests.test_status_failclosed_convergence
python -m unittest -v tests.test_process_adapter_scope
python -m unittest -v tests.test_lifecycle_authority
python -m unittest -v tests.test_worker_cost_basis_estimator
python scripts/project_heartbeat_workers.py --write
python scripts/evaluate_goal_convergence.py --write
python scripts/query_worker_status.py --state BLOCKED
python scripts/run_heartbeat_runtime.py --dry-run --cycles 1
```

GitHub Actions is validation-only, not the heartbeat scheduler.

## Session consolidation

All session-specific architecture, implementation state, adjacent-goal state, blocker evidence and continuation authority are durable in:

```text
StegVerse-Labs/.github#12
docs/ORG_MIRROR_HANDOFF.md
docs/HEARTBEAT_CONTINUITY_WORKER_MIRROR_HANDOFF.md
management/SHWP_SESSION_EXECUTION_INVENTORY.json
management/SHWP_RUNTIME_ACTIVATION_BLOCKER.json
control/worker-registry.json
control/worker-status.json
control/goal-convergence.json
control/worker-capability-profiles.json
heartbeat_runtime/engine_v8.py
```

No protocol design or implementation fact remains unique to chat. The complete session is not archive-safe under the governing archive invariant because the unfinished continuous-runtime activation task has no active non-conversational executor/observer and is not yet at a human-authority terminal boundary.

## Completion assessment

```text
protocol/read-layer tasks: 22/22 = 100%
developed required protocol/read files: 47/47 = 100%
scaffolding/stubs: 0
validation classes: 25/25 = 100%
protocol/read integration classes: 27/27 = 100%
production goal activation including durable host: 27/28 = 96%
session goals transferred or complete: 18/19 = 95%
thread_archive_ready: false
```
