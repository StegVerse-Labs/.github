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
source correction: BRANCH IMPLEMENTED / VALIDATION PENDING
live sovereign-node declaration: NOT OBSERVED
G18 runtime activation: BLOCKED ON DEPLOYMENT-LOCAL ELIGIBLE SURFACE
relay SOVEREIGN_RELAY_LEASE_OPEN: NOT OBSERVED
relay RELAY_NODE_KV_CONTINUITY_VERIFIED: NOT OBSERVED
```
