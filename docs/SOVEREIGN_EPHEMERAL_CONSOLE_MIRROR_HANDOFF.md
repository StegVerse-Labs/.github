# Sovereign Ephemeral Console Mirror Handoff

Updated: 2026-09-06T13:20:00-05:00

## Source of truth

This is the subordinate source/validation handoff for `SHWP-SOVEREIGN-EPHEMERAL-CONSOLE-002`. It does not replace the parent G18 activation handoff, fencing token, heartbeat authority, TV/TVC authority, Master Records custody, or wallet boundaries.

```text
goal_id: SHWP-SOVEREIGN-EPHEMERAL-CONSOLE-002
repository: StegVerse-Labs/.github
branch: main
parent_goal: SHWP-DURABLE-RUNTIME-ACTIVATION
parent_handoff: handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json
live_owner: G18 / SHWP-DURABLE-RUNTIME-ACTIVATION fencing token 18
source_claim: COMPLETE_RELEASED
credential_authority: TV/TVC
non_tv_tvc_secret_or_token_allowed: false
github_token_runtime_authority: NONE
Render production runtime: PROHIBITED
physical_host_cardinality_default: 1
physical_additional_machine_required: false
third_party_machine_or_service_required: false
```

## Global sovereignty invariant

Canonical policy: `control/sovereign-runtime-platform-policy.json`.

A StegVerse deployment is sovereign only when every required production process, scheduler, runtime, state store, validation execution boundary, control-plane executor and continuity dependency is satisfied by the deployment's own sovereign physical host and StegVerse-controlled logical boundaries on that host.

```text
ONE deployment = ONE sovereign physical host by default
additional physical machine required: FALSE
third-party process host required: FALSE
third-party scheduler required: FALSE
third-party state host required: FALSE
third-party control-plane executor required: FALSE
hosted validation may create production authority: FALSE
```

## Purpose and topology

The implementation corrects the prior tendency to escalate independent-peer proof toward additional physical machines. The proof requirement is independent execution/state boundaries, not possession of a second or third physical computer.

```text
THE deployment's sovereign StegVerse host
-> canonical persistent StegVerse runtime
-> G18 native self-bootstrap attempt
-> when independent-peer proof is required or native service proof is incomplete:
   scripts/run_sovereign_ephemeral_console.py
-> isolated logical nodes 1, 2 and 3
-> distinct identities, runtime roots, state trees, receipt trees and process PIDs
-> controlled restart
-> state reconstruction/non-regression
-> collision/fencing isolation
-> canonical nine-predicate proof
-> validation peers terminate
-> primary local carrier may remain active
```

No additional physical computer, hosted provider or third-party machine/service is a valid required predicate.

## Implemented surfaces

```text
scripts/run_sovereign_ephemeral_console.py
scripts/restart_sovereign_ephemeral_node.py
scripts/verify_sovereign_runtime_activation.py
scripts/bootstrap_sovereign_runtime.py
scripts/install_sovereign_heartbeat_service.py
scripts/refresh_sovereign_worker_runtime_source.py
workers/sovereign_runtime_activation_worker.py
tests/test_sovereign_ephemeral_console.py
tests/test_g18_self_bootstrap_worker.py
tests/test_g18_ephemeral_dependency_parity.py
.github/workflows/sovereign-ephemeral-console.yml
control/session-implementation-claim-2026-08-15-sovereign-ephemeral-console.json
receipts/preflight/G18-EPHEMERAL-DEPENDENCY-PARITY-001.json
```

The historical verifier correction moved the materialization path forward from obsolete heartbeat runtimes. Current G18 activation and same-host fallback are bound to `heartbeat_runtime.engine_v13.HeartbeatRuntime` and the separate `heartbeat_runtime.worker_runtime.WorkerCoordinator` process.

## Logical-node proof invariants

Each validation node has an independent node identity, runtime root, heartbeat-state tree, worker-registry copy, checkpoint tree, receipt tree, process PID and restart lifecycle. The console proves distinct roots/PIDs, sentinel write isolation, controlled restart, state reconstruction, non-regression and claim/fence isolation. Validation identities grant no Node Sovereign membership or route/credential authority.

The canonical predicate name `native_service_active` remains for schema compatibility. The verifier may satisfy it through a supported deployment-local native or bounded same-host supervision mode only when the canonical proof contract is met. Hosted Actions execution is validation-only and cannot count as production activation.

## 2026-09-06 G18 runtime-recovery regression repair

The already-released G18 topology requires the existing same-host ephemeral console to be attempted when canonical native v13 bootstrap completes without a qualifying activation proof. A later `workers/sovereign_runtime_activation_worker.py` revision retained the native bootstrap call but no longer invoked `scripts/run_sovereign_ephemeral_console.py`, causing the previously solved runtime-recovery condition to reappear as a generic sovereign-runtime constraint.

The repaired G18 worker restores the existing ordering without creating a new runtime path:

```text
G18 existing claim/fence
-> scripts/bootstrap_sovereign_runtime.py
-> if canonical activation proof is COMPLETE: stop; fallback not required
-> otherwise, on the same eligible non-hosted sovereign host:
   scripts/run_sovereign_ephemeral_console.py
-> require COMPLETE console proof
-> require all logical nodes pass
-> require all isolation predicates pass
-> require primary local carrier + WorkerCoordinator retained
-> require canonical activation proof promoted and every G18 activation predicate true
-> only then classify G18 activation complete
```

The fallback uses the same physical host and the existing source implementation. It may not execute on a hosted validation runner as production evidence. It forwards no GitHub/TVC token or other secret material, requires no second user-operated machine, creates no second WorkerCoordinator authority plane, and does not make HeartBeat or the oscillator an execution authority. HeartBeat remains the 10 ms / 100 Hz reference/carrier substrate with `OSCILLATOR_ONLY` progression semantics; WorkerCoordinator retains claim/fence authority and TV/TVC remains credential authority.

If both native bootstrap and same-host ephemeral recovery remain incomplete, G18 fails closed with the exact fallback outcome recorded. It must not jump directly back to the old generic runtime blocker without first evaluating the existing same-host recovery implementation.

Regression coverage is in `tests/test_g18_self_bootstrap_worker.py`: native success skips fallback; incomplete native proof invokes fallback automatically; hosted execution invokes neither; an incomplete fallback remains fail-closed; and secret/token values are not propagated.

README impact for this repair is material because runtime failure/recovery behavior changes back to the canonical topology. `README.md` is updated in the same change set.

Source/merge/CI validation of this wiring is not authentic resident runtime execution. Current activation still requires deployment-local receipts from the existing G18 lifecycle.

## 2026-09-06 fallback dependency-parity repair

The G18 worker's recovered ordering exposed a remaining propagation defect: the worker could be refreshed/materialized while the existing fallback script itself was absent. That made the recovery path source-correct but not resident-dependency-complete.

The bounded parity repair reuses the existing fallback and adds no runtime mechanism:

```text
scripts/bootstrap_sovereign_runtime.py::REQUIRED_SOURCE_FILES
  -> requires scripts/run_sovereign_ephemeral_console.py
scripts/install_sovereign_heartbeat_service.py::COPY_FILES
  -> copies scripts/run_sovereign_ephemeral_console.py
fresh materialization post-check
  -> requires the copied fallback to exist
scripts/refresh_sovereign_worker_runtime_source.py::_validate_roots
  -> rejects canonical source missing the fallback
scripts/refresh_sovereign_worker_runtime_source.py::STATIC_FILES
  -> refreshes the fallback into an existing resident runtime
```

Therefore bootstrap source eligibility, fresh native materialization, and local-only source refresh can no longer report a complete G18 recovery surface while omitting the already-canonical fallback dependency. The repair does not change G18 claim/fence ownership, create a scheduler/worker/runtime, require another physical machine, alter HB oscillator semantics, or expand Master Records beyond custody/reconstruction. README impact is material and is documented in the same change set.

`tests/test_g18_ephemeral_dependency_parity.py` provides negative controls for omitted fallback source and asserts parity across all three propagation/completeness surfaces.

## Released validation evidence

Canonical historical source validation recorded by the parent blocker:

```text
workflow: .github/workflows/sovereign-ephemeral-console.yml
run: 31922398210
job: 95104297651
conclusion: SUCCESS
hosted_execution_role: VALIDATION_ONLY
production_activation_claimed: false
```

The workflow itself was later found omitted from `control/workflow-surface-registry.json`. The 2026-08-16 bounded hygiene repair registers it as `REVIEW_REQUIRED` under G18 ownership; registration grants no retention, production, runtime, credential, route or heartbeat authority.

## Current live boundary

Repository-local fallback behavior is implemented. Dependency-parity repair is source-complete pending exact-head validation/merge. Live execution remains a parent G18 responsibility and is not implied by workflow PASS.

```text
canonical protocol progression: OSCILLATOR_ONLY / 10 ms / 100 Hz
parent live state: MACHINE_OWNED_BOUND_G18
current constraint: SOVEREIGN_LOCAL_RUNTIME_LIVE_PROOF_NOT_YET_OBSERVED
runtime recovery implementation missing: false
same-host fallback wiring regression: REPAIRED_MERGED
same-host fallback dependency parity: REPAIRED_PENDING_VALIDATION_AND_MERGE
human_action_required: false
```

Machine completion requires `~/.stegverse/heartbeat/activation.latest.json` to report all canonical activation predicates true. If the console fallback is used, `ephemeral-console.latest.json` must additionally prove all nodes and all isolation predicates pass with no additional physical machine required, and the retained primary must include both carrier and WorkerCoordinator process evidence.

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```yaml
- task_id: SHWP-SOVEREIGN-EPHEMERAL-CONSOLE-METADATA-VALIDATION
  execution_owner: bounded hygiene/validation session only when explicitly claimed under StegVerse-Labs/.github#165
  claim_state: CLAIMED_FOR_VALIDATION_REPAIR_2026_08_16
  worker_registry_ref: NONE_SOURCE_METADATA_ONLY
  manual_execution_allowed: true
  collision_scope: handoff/workflow registration metadata only; excludes console behavior, G18 runtime execution, heartbeat state, worker registry, activation receipts and production process control
  release_condition: workflow-surface hygiene and handoff-execution-ownership validators pass and the bounded validation claim is released
  next_executable_action: validate metadata repair, then release the validation claim without touching live G18 execution
```

### WORKER-OWNED / DO NOT COMPETE

```yaml
- task_id: SHWP-DURABLE-RUNTIME-ACTIVATION
  execution_owner: resident sovereign heartbeat + sovereign-runtime-activation-worker / G18 fencing token 18
  claim_state: MACHINE_OWNED_BOUND_G18
  worker_registry_ref: control/worker-registry.json#SHWP-DURABLE-RUNTIME-ACTIVATION
  manual_execution_allowed: false
  collision_scope: native bootstrap, same-host ephemeral-console launch when required, heartbeat state, claim/fence, canonical activation receipts and restart/reconstruction proof
  release_condition: node-local activation PASS or canonical fail-closed resolution/escalation releases/supersedes G18
  next_executable_action: G18 executes the released single-host bootstrap and automatically evaluates the same-host logical-node fallback when native proof is incomplete
```

### ESCALATED / AUTHORITY-OWNED

```yaml
- task_id: SHWP-DURABLE-RUNTIME-ACTIVATION-CONSTRAINT-RESOLUTION
  execution_owner: current canonical heartbeat/runtime authority chain and applicable repository/component authority
  claim_state: ESCALATED_IF_G18_CANNOT_RESOLVE
  worker_registry_ref: docs/FAIL_CLOSED_RESOLUTION_ESCALATION_MIRROR_HANDOFF.md + control/worker-registry.json
  manual_execution_allowed: false
  collision_scope: any canonical-source, writable-state, local-process, service-activation or authority condition beyond G18's ceiling after existing native and same-host recovery paths are evaluated
  release_condition: the authority chain resolves the exact condition or explicitly assigns a bounded human-authority action
  next_executable_action: derive/register the next bounded RESOLVE/ESCALATE task rather than inventing another machine or hosted provider
- task_id: TV-TVC-CREDENTIAL-AND-ROUTE-AUTHORITY
  execution_owner: StegVerse-Labs/TV + StegVerse-Labs/TVC
  claim_state: AUTHORITY_OWNED
  worker_registry_ref: canonical TV/TVC handoffs and route task records
  manual_execution_allowed: false
  collision_scope: credential and route semantics only; ephemeral nodes grant no credential or route authority
  release_condition: TV/TVC emits the applicable admitted result for an exact proof
  next_executable_action: no action from this source handoff; TV/TVC evaluates only when a live proof reaches its authority boundary
```

### COMPLETED / SUPERSEDED

```yaml
- task_id: SHWP-SOVEREIGN-EPHEMERAL-CONSOLE-002-SOURCE
  execution_owner: StegVerse-Labs/.github source implementation lane
  claim_state: COMPLETE_RELEASED
  worker_registry_ref: NONE_COMPLETE_SOURCE
  manual_execution_allowed: false
  collision_scope: scripts, verifier correction, tests and validation-only workflow source
  release_condition: SATISFIED
  next_executable_action: NONE_DO_NOT_RECREATE
- task_id: ADDITIONAL-PHYSICAL-MACHINE-REQUIREMENT
  execution_owner: NONE
  claim_state: SUPERSEDED_PROHIBITED
  worker_registry_ref: NONE_SUPERSEDED
  manual_execution_allowed: false
  collision_scope: any attempt to make a second/third physical computer or third-party host a required proof dependency
  release_condition: PERMANENTLY_SUPERSEDED_BY_SINGLE_HOST_LOGICAL_ISOLATION_POLICY
  next_executable_action: NONE
```

## Cross-repository and release boundary

The console produces local runtime evidence only. It does not itself authorize TVC route admission, LLM-adapter execution, Master Records custody, StegFin trade preparation, signing, broadcast, release tagging or downstream Site/Publisher/wiki propagation.

Canonical live continuation remains:

`handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json` -> deployment-local G18 native bootstrap -> existing same-host fallback when needed -> activation proof -> existing downstream worker/authority chain.

## Completion accounting

```text
source implementation: COMPLETE_VALIDATED_RELEASED + G18 FALLBACK WIRING REPAIR MERGED + DEPENDENCY PARITY REPAIR PENDING VALIDATION/MERGE
primary implemented runtime solution: EXISTING / REUSED
scaffolding/stubs: 0
missing source files: 0 after dependency parity repair
additional physical machine requirement: FALSE
third-party production runtime requirement: FALSE
live G18 activation: PENDING_MACHINE_OWNED_AUTHENTIC_RUNTIME_EVIDENCE
product activation: NOT CLAIMED
```

## Archive condition

This handoff is not archive-ready while the parent G18 runtime objective remains open. The source repair does not itself prove authentic activation; live G18 execution must consume the merged recovery wiring and emit qualifying deployment-local evidence.
