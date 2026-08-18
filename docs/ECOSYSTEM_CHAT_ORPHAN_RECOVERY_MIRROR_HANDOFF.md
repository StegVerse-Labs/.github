# Ecosystem Chat Orphan Recovery Mirror Handoff

Updated: 2026-08-18T17:19:00-05:00

## Authority and scope

This handoff is canonical for recovery task `RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28` and its deterministic return to parent task `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`.

```text
repository: StegVerse-Labs/.github
branch: main
canonical carrier: separated heartbeat v12
ended parent claim: SHWP-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-G20
ended parent fence: 20
recovery task: RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28
recovery worker: ecosystem-chat-orphan-recovery-worker
credential authority: TV/TVC
local model credential requirement: NONE
primary runtime/provider: StegVerse
third-party role: CONTROL_OR_FALLBACK_ONLY
github token runtime authority: NONE
archive_dependency: true
```

The recovery worker cannot revive G20, reuse fence 20, execute the parent inference task, create a second heartbeat, create a second scheduler, or introduce a provider/runtime credential path.

## Current corrected runtime state

HB31 exists and carrier continuity is proven:

```text
control/heartbeat-carrier-runtime-state.json: ACTIVE HB31 / generation31
control/worker-runtime-state.json: observed carrier 31/31
legacy control/heartbeat-state.json: immutable HB29
state reconstruction: PASS
no duplicate claim/fence: PASS
```

But the only current HB31 WorkerCoordinator evidence is observation-only:

```text
observation_mode: CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION
task_adapters_invoked: 0
```

Therefore the old `RELEASE_COMPLETE` interpretation cannot satisfy the runtime goal. The corrected release state is:

```text
carrier continuity: PROVEN
worker task-capable cycle: NOT OBSERVED
runtime release: WORKER_TASK_CAPABLE_CYCLE_PENDING
```

Canonical correction:

```text
scripts/refresh_heartbeat_transition_receipt.py
  130c18fb9e87682400d8b9e43c836ad322b803eb

tests/test_heartbeat_transition_integrity_hardening.py
  5d728a928de9ed5b5f4d24d474bb1e4252725591

receipts/heartbeat-transition-continuity/release-hardening-20260818T1719-0500.json
  ac25265839eba094bcf1250fd04ec4b640947784

scripts/restart_sovereign_ephemeral_node.py
  73578a3a8b3d600077e86e43cfd2e3ad7e74bbea

tests/test_ephemeral_separated_runtime_supervision.py
  90450ff986a1f2051193b466602150a8be3ee23c
```

The sovereign restart supervisor now fails closed unless the real `run_worker_runtime.py --continuous` process advances the worker-runtime tick after spawn. PID presence alone is insufficient.

## Historical recovery source

Orphan recovery source remains released and valid:

```text
StegVerse-Labs/.github PR #78
merge: 477b0d5e3737662a4d51fe87538bbbc2d4acc99e
recovery dry-run fence: 23 > ended fence 20
```

Historical G20 custody remains available in Master Records:

```text
master-records/orchestration PR #27
merge: 4c6f4679c20c7fc70a65753cf4f87e6b929f09ef
MR-ECOSYSTEM-CHAT-G20-ORPHAN-CUSTODY-025: COMPLETE_RELEASED
pinned checkpoint/event reconstruction: PASS
```

TV/TVC no-GitHub-token authority cleanup remains released; hosted validation does not grant runtime authority.

## Recovery design

The recovery task is continuity reconstruction only. It requires a new fence strictly greater than 20 and may operate only after the real WorkerCoordinator is task-capable.

Required sequence:

```text
#122/#12 resident StegVerse supervisor starts/restarts task-capable worker runtime
-> WorkerCoordinator task-capable event at HB31+
-> already-bound G18 consumes terminal result and releases fence18
-> carrier transition release re-evaluates to RELEASE_COMPLETE under corrected predicate
-> recovery task receives fresh fence >20
-> Master Records G20 custody reconstruction PASS
-> recovery COMPLETED
-> parent becomes HANDOFF_READY
-> parent receives fresh fence >20
-> StegVerse local/private model launch + proof
-> TVC ROUTE_ADMITTED / credential_requirement NONE
-> exact LLM-adapter execution
-> measured E1 -> model -> E2 usage
-> same-execution Master Records provider-usage + transition reconstruction PASS
```

No manual chat claim/fence may replace this sequence.

## Current claim state

```yaml
release_hardening:
  task_id: SHWP-WORKER-TASK-CAPABLE-RELEASE-HARDENING-001
  claim_ref: control/session-implementation-claim-2026-08-18-worker-task-capable-release-hardening.json
  state: CLAIMED_FOR_VALIDATION_AND_INTEGRATION

recovery:
  task_id: RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28
  owner: resident WorkerCoordinator + ecosystem-chat-orphan-recovery-worker
  state: MACHINE_OWNED_REQUIRED_EXECUTION
  manual_execution_allowed: false
  release_condition: recovery COMPLETED under fresh fence >20

parent:
  task_id: SHWP-ECOSYSTEM-CHAT-INFERENCE-001
  owner: resident WorkerCoordinator -> TVC -> LLM-adapter -> Master Records
  state: MACHINE_OWNED_AFTER_RECOVERY
  manual_execution_allowed: false
  release_condition: immutable same-execution sovereign activation evidence
```

## Collision boundaries

1. Do not reset HB31.
2. Do not reuse G18 or G20 authority outside their existing admitted scopes.
3. Do not manually mint recovery or parent fences.
4. Do not create a second heartbeat/WorkerCoordinator/scheduler.
5. Do not use GitHub Actions or any hosted provider as production activation authority.
6. StegVerse remains PRIMARY; third parties remain fallback/control only.
7. TV/TVC remains sole credential authority.

## Machine-observable release conditions

Before recovery may be called active execution:

- `events/worker-runtime.jsonl` contains a non-observation WorkerCoordinator event at HB31+;
- corrected transition receipt evaluates `worker_task_capable_cycle_observed=true`;
- G18 is terminal and no longer projected as an active lease;
- recovery receives a fresh fence >20.

Before parent completion:

- real private StegVerse model process observed;
- TVC route admitted with credential requirement NONE;
- exact LLM-adapter path executed;
- measured usage persisted;
- provider-usage and transition reconstruction PASS;
- `same_execution=true`;
- no non-TV/TVC secret/token authority.

## Validation state

```text
recovery source validation: historical PASS
release-hardening source installed: YES
release-hardening hosted validation directly observed: NO
task-capable WorkerCoordinator live cycle: NO
recovery live execution: NO
fresh parent inference execution: NO
same-execution activation proof: NO
```

## Archive rule

Archive is prohibited. HB31 carrier continuity is not the terminal goal. This work remains open until the task-capable worker, recovery, parent inference, and same-execution evidence actually occur and are consumed.
