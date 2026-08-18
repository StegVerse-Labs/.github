# Sovereign Heartbeat Deployment Mirror Handoff

Updated: 2026-08-18T17:19:00-05:00

## Authority and active goal

```text
goal_id: SHWP-SOVEREIGN-DEPLOYMENT-NO-THIRD-PARTY-001
source_child: HEARTBEAT-HB29-CURRENT-MAIN-RECONCILE-197
repository: StegVerse-Labs/.github
branch: main
canonical_live_owners: StegVerse-Labs/.github#122/#12
credential_authority: TV/TVC
credential_requirement: NONE
non_tv_tvc_secret_or_token_allowed: false
github_token_runtime_authority: NONE
primary_runtime: StegVerse
third_party_runtime_role: FALLBACK_ONLY
source_release_state: COMPLETE_RELEASED
live_activation_state: CARRIER_HB31_CONTINUITY_PROVEN_TASK_CAPABLE_WORKER_RUNTIME_PENDING
archive_dependency: true
```

This handoff is canonical for sovereign carrier/worker deployment. The source refactor is released, but live deployment is not terminal until a task-capable `WorkerCoordinator` cycle is observed and all required downstream runtime state is consumed.

## Corrected completion rule

Carrier continuity and worker observation are not equivalent to task-capable worker runtime activation.

The previously recorded HB31 state proved:

```text
control/heartbeat-carrier-runtime-state.json: epoch 31 / generation 31 / ACTIVE
control/worker-runtime-state.json: observed carrier 31/31
receipts/heartbeat-transition-continuity/latest.json: historical CARRIER_TRANSITION_COMPLETE
legacy control/heartbeat-state.json: immutable HB29
state reconstruction: PASS
no duplicate claim/fence: PASS
```

However the worker observation was produced in:

```text
observation_mode: CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION
task_adapters_invoked: 0
```

Therefore the historical `RELEASE_COMPLETE` interpretation is superseded for **runtime-goal release**. HB31 continuity remains valid evidence, but runtime release now additionally requires a real task-capable WorkerCoordinator cycle.

Canonical correction evidence:

```text
scripts/refresh_heartbeat_transition_receipt.py
  130c18fb9e87682400d8b9e43c836ad322b803eb
  adds worker_task_capable_cycle_observed release predicate

tests/test_heartbeat_transition_integrity_hardening.py
  5d728a928de9ed5b5f4d24d474bb1e4252725591
  proves observation-only state cannot satisfy release

receipts/heartbeat-transition-continuity/release-hardening-20260818T1719-0500.json
  ac25265839eba094bcf1250fd04ec4b640947784
  preserves historical receipt and records corrected interpretation

scripts/restart_sovereign_ephemeral_node.py
  73578a3a8b3d600077e86e43cfd2e3ad7e74bbea
  restart now requires worker runtime tick advancement after task-capable runner spawn

tests/test_ephemeral_separated_runtime_supervision.py
  90450ff986a1f2051193b466602150a8be3ee23c
  proves PID-only restart cannot satisfy supervision
```

## Released production architecture

```text
heartbeat_runtime.engine_v12.HeartbeatRuntime
  non-authorizing carrier/reference frame

heartbeat_runtime.worker_runtime.WorkerCoordinator
  independent task/claim/fence/worker runtime

scripts/run_heartbeat_runtime.py
  carrier-only process

scripts/run_worker_runtime.py
  task-capable worker process

scripts/install_sovereign_heartbeat_service.py
  native materialization/supervision of both separated processes

scripts/restart_sovereign_ephemeral_node.py
  sovereign local restart path for both processes

scripts/verify_sovereign_runtime_activation.py
  node-local activation proof
```

No second heartbeat or worker coordinator is authorized.

## Current live state

```text
carrier: ACTIVE HB31 / generation31
carrier continuity: PROVEN
legacy HB29: unchanged
worker carrier observation: 31/31
worker observation mode: CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION
worker task-capable cycle at HB31+: NOT OBSERVED
G18 active lease projected: YES
G18 registry terminalization: NOT OBSERVED
resident materialization receipt: NOT OBSERVED at repository canonical path
resident task-capable worker supervision: NOT OBSERVED
```

The missing predicate is not HB30/HB31 anymore. It is the actual task-capable worker runtime.

## Required machine execution

Canonical owner: `StegVerse-Labs/.github#122/#12` resident StegVerse runtime.

Exact next execution:

```text
start or restart already-released task-capable scripts/run_worker_runtime.py
-> WorkerCoordinator cycle observes HB31+
-> invoke already-bound G18 under existing fence 18
-> G18 consumes carrier/continuity result
-> G18 returns COMPLETED / SOVEREIGN_RUNTIME_STATE_TRANSITION_VERIFIED
-> registry releases G18 claim/worker binding
-> control-plane projection removes G18 active lease
-> execute admitted orphan-recovery / parent sovereign-inference continuation
```

The carrier does not grant this authority. The existing WorkerCoordinator/G18 handoff does.

## Machine-observable release conditions

All are required:

1. `events/worker-runtime.jsonl` contains a non-observation WorkerCoordinator event at HB31 or later;
2. corrected transition refresh reports `worker_task_capable_cycle_observed=true`;
3. corrected transition release becomes `RELEASE_COMPLETE`;
4. `control/worker-registry.json` records G18 terminal and unbound;
5. `control/worker-control-plane-coordination.json` no longer projects G18 as active;
6. downstream orphan recovery receives a new fence greater than ended parent fence 20;
7. no GitHub/Render/Vercel/Cloudflare/provider token becomes runtime authority;
8. TV/TVC remains sole credential authority.

## Claims / collision boundaries

```yaml
source_release_197:
  state: COMPLETE_RELEASED_SOURCE
  manual_execution_allowed: false

runtime_live_122_12:
  state: MACHINE_OWNED_REQUIRED_EXECUTION
  manual_execution_allowed: false
  collision_scope: live carrier/worker supervision, active claims/fences/leases

release_hardening_001:
  claim_ref: control/session-implementation-claim-2026-08-18-worker-task-capable-release-hardening.json
  state: CLAIMED_FOR_VALIDATION_AND_INTEGRATION
  collision_scope: release validator, supervision validation, handoff reconciliation
  release_condition: direct validation + live task-capable worker evidence consumed
```

Do not reset HB31. Do not manually mint a fence. Do not invoke parent inference from chat. Do not create a second scheduler.

## Historical source release evidence

PR #200 merged the carrier/worker source reconciliation as `1f008696142d7bc78e5ff1e7a84d21234b6131d9` after final source validation. Historical PR #198/#199 provenance remains superseded. That source release remains valid; the defect corrected here is the live-release predicate and supervision proof, not the separated architecture itself.

## Validation state

```text
released architecture source validation: PASS historical
release-hardening source installed: YES
release-hardening hosted validation directly observed: NO
live task-capable WorkerCoordinator execution: NO
live G18 terminalization: NO
```

No workflow PASS is inferred from source presence.

## Downstream continuation

After G18 terminalization:

```text
RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28
-> fresh recovery fence >20
-> Master Records G20 custody reconstruction PASS
-> recovery COMPLETED
-> SHWP-ECOSYSTEM-CHAT-INFERENCE-001 fresh parent fence >20
-> StegVerse local model
-> TVC ROUTE_ADMITTED credential NONE
-> LLM-adapter exact execution
-> measured usage
-> same-execution Master Records reconstruction
-> Test Lanes conditional matrix may advance
```

## Completion accounting

```text
source/deployment developed surfaces: complete
scaffolding/stubs: 0
missing source files: 0
historical release validation: complete
release-hardening validation: pending direct observation
live carrier continuity: complete
live task-capable worker runtime: pending
G18 terminalization: pending
downstream sovereign activation: pending
archive: prohibited
```

This goal remains open until the task-capable runtime and downstream activation evidence actually exist.
