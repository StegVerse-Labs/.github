# Blocker Resolution Runtime Mirror Handoff

## Status

```text
goal_id: WORKER-BLOCKER-REMEDIATION-001
owner: StegVerse-Labs/.github#65
state: IMPLEMENTED_MAIN_HOSTED_VALIDATED
hosted_validation: Heartbeat Worker Project run 31335403988 SUCCESS
archive_ready: false
```

## Canonical invariant

A blocker is not permission to wait. A blocker means the current solution is insufficient and a different solution or workaround is required.

Third-party dependencies are never StegVerse blockers. Provider credentials, SaaS quotas, hosted inference, external schedulers, vendor outages, and similar external conditions may make one candidate path unavailable, but the worker must remain active on solution selection and pursue a StegVerse-owned/federated or otherwise admitted alternate path.

## Runtime enforcement

- `control/blocker-resolution-policy.json` is the machine-readable policy.
- `heartbeat_runtime/blocker_policy.py` validates worker blocker contracts.
- `heartbeat_runtime/process_adapter.py` rejects passive `BLOCKED` responses and rejects any `BLOCKED` response whose dependency class is `THIRD_PARTY`.
- Every legitimate constraint response must state the problem, `solution_required=true`, one or more workaround candidates, and the next solution action.
- A third-party condition must be represented as an active workaround-selection/execution transition, not a passive stopping state.
- Repeating an unchanged third-party or internal blocker observation does not count as progress.

## Active worker corrections

- `workers/steggate_rendezvous_deployment_worker.py`: missing/rejected Cloudflare credentials and Cloudflare deployment failure now return `ACTIVE / THIRD_PARTY_WORKAROUND_REQUIRED` and name alternate sovereign/admitted rendezvous paths.
- `workers/sovereign_runtime_activation_worker.py`: missing sovereign runtime evidence now reports active solution/escalation semantics with concrete native-node activation alternatives.
- `workers/ecosystem_chat_sovereign_inference_worker.py`: missing local inference evidence reports an active sovereign inference solution requirement, including smaller/alternate local model options rather than hosted-provider fallback.
- `control/organization-task-registry.json`: AaCT-E connector write authority is represented as `WORKAROUND_REQUIRED`; internal no-repository conditions retain explicit repository/relay construction alternatives.
- `workers/organization_federation_readiness_worker.py`: validates the distinction between workaround-required and internal constraint conditions.

## Hosted validation

Heartbeat Worker Project run `31335403988` completed `SUCCESS` on the blocker-remediation head. The hosted run passed:

- compile of the heartbeat runtime, blocker policy, process adapter, and active workers;
- canonical JSON parsing;
- executable handoff validation;
- `tests.test_blocker_resolution_policy` proving no-third-party-blocker and resolution-contract semantics;
- native heartbeat, worker coordination, executor discovery, blocker/authority, lineage, resource authority, checkpoints, capability profiles, fail-closed convergence, mutation-scope, lifecycle authority, cost-basis, and sovereign-host tests;
- non-mutating live dry-run proof;
- canonical status/convergence and continuity projection refresh;
- current StegGate successor posture proof;
- final derived-projection commit step.

An earlier hosted run correctly failed because the first version of the new test file used pytest-style free functions while the repository invokes `unittest`; that test-harness defect was corrected before the successful run. The successful run therefore proves executed tests rather than compile-only acceptance.

## Completion condition

The runtime policy-remediation implementation and hosted validation are complete, but issue #65 remains an active execution owner because the execution goal is larger than the policy change. Critical-path workers must continue into measurable solution execution or derive/escalate successor work rather than merely record constraints.

## Execution ownership and collision partition

Standard: `StegVerse-Labs/Continuity/docs/REPOSITORY_HANDOFF_STANDARD.md` / `stegverse.handoff-execution-ownership/v1`.

### MANUAL / SESSION-STARTABLE

No implementation task in this handoff is implicitly manual-startable. A distinct validation/reconciliation lane may be manually claimed only outside the active worker implementation/runtime scopes.

### WORKER-OWNED / DO NOT COMPETE

```yaml
- task_id: WORKER-BLOCKER-REMEDIATION-001-ACTIVE-SCOPE
  execution_owner: StegVerse-Labs/.github#65 + canonical heartbeat workers
  claim_state: MACHINE_OWNED
  worker_registry_ref: control/worker-registry.json + control/blocker-resolution-policy.json + StegVerse-Labs/.github#65
  manual_execution_allowed: false
  manual_allowed_role: observation
  collision_scope: blocker/constraint classification, worker workaround selection, successor task derivation, worker runtime transitions, and remediation receipts for tasks already bound to canonical workers
  release_condition: canonical worker/registry explicitly completes, supersedes, or releases the affected task scope
  next_executable_action: current worker executes a solution candidate or emits the resolution/escalation contract that creates the next active task
```

### ESCALATED / AUTHORITY-OWNED

```yaml
- task_id: WORKER-CONSTRAINT-AUTHORITY-ESCALATION
  execution_owner: canonical v13 oscillator/WorkerCoordinator authority chain
  claim_state: ESCALATED
  worker_registry_ref: docs/FAIL_CLOSED_RESOLUTION_ESCALATION_MIRROR_HANDOFF.md + control/worker-registry.json
  manual_execution_allowed: false
  manual_allowed_role: NONE
  collision_scope: constraints that the current worker cannot lawfully solve within its authority ceiling
  release_condition: next capable authority resolves the constraint or explicitly assigns a bounded human-authority action
  next_executable_action: derive/register RESOLVE or ESCALATE task rather than returning the original task to an arbitrary manual claimant
```

### COMPLETED / SUPERSEDED

- Blocker-resolution policy implementation: complete.
- Hosted policy validation: complete.
- Passive third-party blocker semantics: superseded.
- Constraint-to-solution/escalation invariant: canonical.

No chat history is required to reconstruct this rule. Historical `BLOCKED` wording is evidence of past attempts only and does not release worker-owned work for manual implementation.


## 2026-08-27 G18 sovereign-node derivation reconciliation

A live-state inspection found a source-version drift in `workers/sovereign_node_repository_resolution_worker.py`: repository-local eligibility still treated the historical `heartbeat_runtime/engine_v11.py` plus two installer/verifier files as the canonical runtime surface, while the current runtime-separation handoff and `scripts/bootstrap_sovereign_runtime.py` define the canonical carrier as `heartbeat_runtime.engine_v13.HeartbeatRuntime` with the independent oscillator, WorkerCoordinator, transition producer, registries, and continuity contract present.

This reconciliation branch narrows the resolver to that existing canonical v13 surface rather than introducing a new node mechanism. It also aligns the derived marker to `stegverse.sovereign-node-declaration/v0.4` and preserves:

```text
continuity_model: INDEPENDENT_OSCILLATOR_CONTINUITY
canonical_carrier_runtime: heartbeat_runtime.engine_v13.HeartbeatRuntime
heartbeat_progression_dependency: OSCILLATOR_ONLY
heartbeat_event_trigger_required: false
always_on_external_host_required: false
credential_authority: TV/TVC
github_token_required: false
third_party_runtime_required: false
authority_effect: RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY
```

Validation adds an explicit rejection for the stale v11-only source surface. Hosted environments remain ineligible and cannot produce a sovereign-node declaration. This source correction does **not** claim that a deployment-local node has been observed, that G18 is task-capable, or that either StegOS relay runtime receipt exists.

Current execution boundary remains:

```text
source correction: MERGED / PR #341 / f57e2c6cb82541347580b0c00b2f14fabf02108c
repository-owned validation: 33137722412 SUCCESS; 33137722340 SUCCESS
live sovereign-node declaration: NOT OBSERVED
G18 runtime activation: BLOCKED ON DEPLOYMENT-LOCAL ELIGIBLE SURFACE
relay SOVEREIGN_RELAY_LEASE_OPEN: NOT OBSERVED
relay RELAY_NODE_KV_CONTINUITY_VERIFIED: NOT OBSERVED
```


## 2026-08-27 G18 execution-path reconciliation

Live inspection after the v13 node-resolver merge found a second stale G18 binding: the canonical `workers/sovereign_runtime_activation_worker.py` still attempted the historical HB29 -> v12 state-transition producer even though HeartBeat is already terminal `ACTIVE_PROTOCOL_VERIFIED` and `SHWP-DURABLE-RUNTIME-ACTIVATION` is now strictly the separate sovereign WorkerCoordinator/runtime-substrate goal.

The current correction reuses existing source only:

```text
G18 existing claim/fence
-> workers/sovereign_runtime_activation_entrypoint.py
-> workers/sovereign_runtime_activation_worker.py
-> scripts/bootstrap_sovereign_runtime.py
-> derived stegverse.sovereign-node-declaration/v0.4 when local eligibility passes
-> existing native separated runtime installer
-> scripts/verify_sovereign_runtime_activation.py
-> deployment-local stegverse.sovereign-runtime-activation-proof/v1
-> worker_task_capable_cycle_observed=true required
-> G18 terminalization only if every activation predicate passes
```

Removed from the current G18 execution path:

```text
historical HB29 -> HB30 transition execution
engine_v12 as canonical G18 carrier
HeartBeat transition completion as G18 runtime activation
refresh_heartbeat_transition_receipt.py as a G18 completion guard
```

Preserved invariants:

```text
heartbeat progression dependency: OSCILLATOR_ONLY
heartbeat dependency for G18: false
additional physical machine required: false
always-on external host required: false
hosted environments: validation-only / rejected as runtime evidence
credential authority: TV/TVC
GitHub-token runtime authority: NONE
post-bootstrap StegFin activation from G18: explicitly skipped
runtime proof: deployment-local only
```

Branch state:

```text
PR: #344
merge: 72e9315e557fdcc6e9d5c94c370993da6a2f7f88
validation: 33138207844 SUCCESS; 33138207869 SUCCESS
source correction: IMPLEMENTED / VALIDATED / MERGED
live sovereign runtime activation: NOT OBSERVED
task-capable WorkerCoordinator proof: NOT OBSERVED
relay SOVEREIGN_RELAY_LEASE_OPEN: NOT OBSERVED
authority effect: NONE_SOURCE_AND_REGISTRY_ONLY_NO_RUNTIME_OBSERVATION_NO_RUNTIME_OBSERVATION
```

This is a direct correction of the existing G18 executor and does not create a second runtime, worker scheduler, HeartBeat, node mechanism, credential lane, route authority, broker, or transport authority.


## 2026-08-27 G18 resident request active-resolution registration

The one-shot resident execution request was source-complete but still depended on a later local filesystem event before its consumer could run. Under blocker-resolution policy v2, that passive wait is not sufficient machine progress.

Registered goal-preserving resolution task:

```text
task: RESOLVE-G18-RESIDENT-REQUEST-CONSUMPTION-001
state: HANDOFF_READY
authority domain: INDEPENDENT_TASK_CONTROL
fresh resolution fence: >22
parent G18 claim reused by task: NO
target existing G18 claim validated by consumer:
  SHWP-SHWP-DURABLE-RUNTIME-ACTIVATION-G18
target existing G18 fence:
  18
worker:
  g18-resident-request-consumption-resolution-worker
adapter:
  process:g18-resident-request-consumption-resolution-v1
```

Execution:

```text
eligible non-hosted resident
-> verify resident WorkerCoordinator registry
-> verify exact existing G18 fence18 claim
-> refresh already-local canonical source into resident runtime
-> invoke existing consume_g18_resident_execution_request.py directly
-> existing RESUME_EXISTING_CLAIM bridge
-> existing G18 worker
```

This removes the filesystem-event wait as a prerequisite. It performs no network source fetch, requires no GitHub/provider credential, creates no second machine/runtime/HeartBeat, and cannot mint or replace the existing G18 claim/fence.

If the resident runtime or exact G18 claim is absent, the resolution worker emits a fail-closed blocker with `may_remain_blocked=false` and an explicit next escalation level so WorkerCoordinator can derive/register the next goal-preserving resolution task.

Branch state:

```text
PR: #355
merge: 713dd687173900f164fa006aa93327f7c943f870
validation: 33141763517 SUCCESS; 33141763569 SUCCESS
resolution source: IMPLEMENTED / VALIDATED / MERGED
registry state: HANDOFF_READY
resident consumption: NOT OBSERVED
G18 activation: NOT OBSERVED
authority effect: NONE_SOURCE_ONLY
```
