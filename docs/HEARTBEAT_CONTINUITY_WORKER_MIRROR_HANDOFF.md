# Heartbeat Continuity Worker Mirror Handoff

## Authority and source of truth

This is the canonical scoped handoff for sovereign-heartbeat production activation in `StegVerse-Labs/.github`. It is subordinate to `docs/ORG_MIRROR_HANDOFF.md`. Live default-branch state, task registries, claims, fences, checkpoints, receipts, issues, and direct sovereign-node observations supersede chat and historical projections.

```text
goal_id: SOVEREIGN-HEARTBEAT-PRODUCTION-ACTIVATION
repository: StegVerse-Labs/.github
canonical_branch: main
canonical_owner: StegVerse-Labs/.github#12
runtime: heartbeat_runtime.engine_v11.HeartbeatRuntime
carrier: single_stegverse_heartbeat
credential_authority: TV/TVC
route_authority_owner: StegVerse-Labs/TVC
policy_authority_owner: StegVerse-Labs/TV
local_model_credential_requirement: NONE
github_token_runtime_dependency: PROHIBITED
hosted_model_provider_dependency: NONE
product_activation: ACTIVE_MACHINE_WORK / INCOMPLETE
session_role: DISTINCT_VALIDATION_RECONCILIATION_SUPPORT
thread_archive_ready: false
archive_gate: live product activation or durable release of every newly discovered session-specific support defect
```

## Completed source capabilities

```text
formal local model/runtime: COMPLETE_RELEASED
actual local discovery/launch/inference/proof: COMPLETE_RELEASED
persistent local endpoint proof: COMPLETE_RELEASED
heartbeat local-model lifecycle: COMPLETE_MERGED
heartbeat -> TVC route: COMPLETE_MERGED
LLM-adapter exact execution: COMPLETE_RELEASED
Master Records same-execution verification: COMPLETE_RELEASED
StegFin Inventory N heartbeat consumer: COMPLETE_MERGED_VALIDATED
exact StegFin worker binding: COMPLETE_MERGED_VALIDATED
TV/TVC semantic reconciliation: COMPLETE_MERGED_VALIDATED
GitHub-token production authority: RETIRED
fail-closed RESOLVE/ESCALATE runtime: COMPLETE_MERGED
active-worker invariant + normalization: COMPLETE_RELEASED
```

The descriptive `select/execute local model` step is obsolete. The installed path discovers locally materialized `StegVerse-002/micro-node-runtime`, launches/proves the private model process, passes through TVC with `credential_requirement=NONE`, executes the exact LLM-adapter route, persists measured usage, and requires exact Master Records reconstruction.

## Credential / hosted-platform boundary

```text
credential_authority: TV/TVC
github_token_production_authority: NONE
github_actions_production_role: NONE
Render/Vercel/Cloudflare production carrier role: NONE
external hosted inference dependency: NONE
```

GitHub-hosted validation may prove source/policy only. It is not heartbeat cadence, claim allocation, runtime activation, persistence, credential, release, or custody authority.

## Active runtime continuation

### Durable sovereign carrier

Owner records:

```text
StegVerse-Labs/.github#59
StegVerse-Labs/.github#65
handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json
```

Current durable state:

```text
fencing_token: 18
operational_state: ACTIVE_WORKER
solution_state: ACTIVE_SOLUTION_EXECUTION
last directly observed heartbeat: HB29
constraint: SOVEREIGN_NODE_DECLARATION_NOT_PRESENT
constraint_class: PHYSICAL_RESOURCE
human_action_required: false
missing_implementation: false
next_solution_action: SOVEREIGN_RUNTIME_SOLUTION_EXECUTION
```

Completion requires a StegVerse-owned/federated carrier with node-local `~/.stegverse/heartbeat/activation.latest.json` satisfying all nine activation predicates, canonical heartbeat advancement beyond HB29, controlled restart continuity, no duplicate claim/fence, and Master Records reconstruction PASS.

### Ecosystem Chat inference

Owner:

```text
StegVerse-Labs/.github#60 + resident heartbeat
```

The already-authorized orphan-recovery continuation is registered in:

```text
control/worker-registry.d/ecosystem-chat-orphan-recovery-hb28.json
```

After recovery completes, a fresh authorized parent fence >20 executes the installed local-model -> TVC -> LLM-adapter -> Master Records chain and must produce immutable same-execution activation evidence.

### StegFin live Base entry

Canonical owner/task:

```text
StegVerse-Labs/stegfin-governance/task-state/STEGFIN-LIVE-ENTRY-003.json
```

Continuation:

```text
resident heartbeat post-HB29 claim/fence
-> fresh Inventory N
-> TV/TVC/vault provider capability
-> USER_ONLY 12.50 USDC -> WETH signature/broadcast
-> settlement
-> successor inventory
-> governed exit
-> replay/P&L
-> production sizing
```

No wallet-signing or transaction-broadcast authority belongs to the heartbeat or this handoff.

### StegFin sovereign internal trading proof — local capsule discovery support

Hosted dry-run evidence at the previous control-plane head reached the registered `SHWP-STEGFIN-SOVEREIGN-TRADING-001` worker and produced the fail-closed transition `STEGFIN_SOVEREIGN_CAPSULE_NOT_MATERIALIZED`. Inspection showed the worker only searched workload directories, while other released StegVerse workers also recognize canonical local source trees.

A bounded source-support repair was installed without touching wallet, provider, custody, signing, broadcast, settlement, or GitHub credential authority:

```text
947ac121dbfb1d01ded5cc3762569783f2356907
  workers/stegfin_sovereign_trading_worker.py
  adds discovery of ~/.stegverse/source/stegfin-governance and /var/lib/stegverse/source/stegfin-governance
  retains existing workload discovery
  accepts STEGVERSE_STEGFIN_SOURCE_ROOT in worker logic as a non-secret local source locator
  child execution environment remains PATH/PYTHONPATH/LANG/LC_ALL only
  terminal receipts explicitly record non_tv_tvc_secret_or_token_used=false

bb51e9015fae972a7c7daea2eeb0fe4c4650e895
  tests/test_stegfin_sovereign_trading_worker.py
  proves canonical local source discovery and explicit local source resolution without network or credentials
```

Hosted validation:

```text
Heartbeat Worker Project run 31731705788: SUCCESS
organization control-plane run 31731705800: FAILURE only because docs/STEGFIN_CONTINUITY_CARRIER_MIRROR_HANDOFF.md had regressed from the required ownership-section heading
```

The unrelated handoff-format regression was then repaired at:

```text
f52948fcff95fcfc9bd3e2640ed287ebde6c084b
```

Revalidation at that head:

```text
Validate organization control plane run 31731915312: SUCCESS
Heartbeat Worker Project run 31731915333: SUCCESS
```

This source repair removes one repository-owned discovery gap. It does not assert that the sovereign capsule is actually materialized on the live carrier. The persisted heartbeat state remains HB29 until a production-authorized heartbeat advances it; hosted dry-run HB30 is nonpersistent and nonauthorizing.

## Active-worker normalization evidence

```text
#83 COMPLETE — normalize unresolved states to ACTIVE/MACHINE_OWNED
#84 COMPLETE — bind/supersede unowned constraint tasks
#85 COMPLETE — active-worker state invariant validator
canonical aggregation validation: 31622026042 PASS
```

The canonical validation records no detected unresolved unowned task. Historical raw response labels may remain immutable provenance but are not operational stopping states.

## Validation evidence

```text
31338817754 native runtime activation/proof source path SUCCESS
31453552032 heartbeat no-token validation SUCCESS
31453552033 Ecosystem Chat no-token validation SUCCESS
31453552110 organization no-token validation SUCCESS
31464631729 hosted-authority retirement SUCCESS
31620645190 active sovereign worker semantics SUCCESS
31622026042 active-worker canonical graph aggregation PASS
31731705788 StegFin sovereign local-source discovery source validation SUCCESS
31731915312 ownership/control-plane revalidation SUCCESS
31731915333 heartbeat source validation after ownership repair SUCCESS
PR #82 e0500245085f7dcdabd87c801b5654a619264ca4 fail-closed resolution/escalation merged
```

Canonical local commands:

```text
python -m compileall -q heartbeat_runtime workers scripts
python scripts/validate_executable_handoffs.py
python scripts/validate_handoff_execution_ownership.py
python -m unittest discover -v tests
python scripts/run_heartbeat_runtime.py --dry-run --cycles 1
python tools/validate_active_worker_states.py
```

## Cross-repository ownership

```text
model/runtime: StegVerse-002/micro-node-runtime
credential policy: StegVerse-Labs/TV
route authority: StegVerse-Labs/TVC
provider execution: StegVerse-org/LLM-adapter
custody/reconstruction: master-records/orchestration
trading: StegVerse-Labs/stegfin-governance
post-activation projection: StegVerse-Labs/Site
post-activation publication/verification: GCAT-BCAT-Engine/Publisher, admissibility-wiki, stegguardian-wiki
```

Propagation remains a machine-owned successor condition after immutable activation evidence; it is not current chat-session work.

## Execution ownership and collision partition

Standard: `StegVerse-Labs/Continuity/docs/REPOSITORY_HANDOFF_STANDARD.md` / `stegverse.handoff-execution-ownership/v1`.

### MANUAL / SESSION-STARTABLE

No heartbeat, carrier, Ecosystem Chat, or StegFin live operation in this handoff is manually startable. A session may take a distinct source-validation/reconciliation role only after a machine receipt identifies a repository-owned defect outside the runtime claim/fence and financial authority scope.

```text
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.json
collision_scope: all live heartbeat claims/fences, provider capability, wallet action, settlement and custody
release_condition: a separately identified repository-owned source defect is repaired and hosted-validated, or canonical machine owner releases a bounded support scope
next_executable_action: observe canonical machine evidence; repair only nonoverlapping source/control defects
```

### WORKER-OWNED / DO NOT COMPETE

```yaml
- task_id: SOVEREIGN-HEARTBEAT-PRODUCTION-ACTIVATION
  execution_owner: resident sovereign heartbeat + canonical worker registry
  claim_state: MACHINE_OWNED
  worker_registry_ref: control/worker-registry.json + StegVerse-Labs/.github#59/#65/#60
  manual_execution_allowed: false
  manual_allowed_role: observation
  collision_scope: heartbeat runtime state, claims/fences/leases, sovereign carrier activation, Ecosystem Chat recovery/inference, and worker-owned successor activation tasks
  release_condition: current registry owners complete/supersede/release the specific task or explicitly assign a nonoverlapping manual role
  next_executable_action: resident heartbeat executes active tasks and derives/escalates any unsolved constraint through engine v11

- task_id: STEGFIN-LIVE-ENTRY-003
  execution_owner: resident sovereign heartbeat + StegFin runtime + TV/TVC/vault + USER_ONLY wallet authority
  claim_state: MACHINE_OWNED
  worker_registry_ref: StegVerse-Labs/stegfin-governance/task-state/STEGFIN-LIVE-ENTRY-003.json
  manual_execution_allowed: false
  manual_allowed_role: observation
  collision_scope: live inventory, governed trade entry/exit orchestration, provider capability, settlement observation, replay/P&L; USER_ONLY signing remains a separate human authority boundary
  release_condition: canonical StegFin task-state completes or explicitly releases a distinct scope
  next_executable_action: canonical task continues after resident heartbeat and provider capability predicates are satisfied

- task_id: SHWP-STEGFIN-SOVEREIGN-TRADING-001
  execution_owner: resident sovereign heartbeat + stegfin-sovereign-trading-worker
  claim_state: MACHINE_OWNED_ON_ADMISSION
  worker_registry_ref: control/worker-registry.d/stegfin-sovereign-trading-001.json
  manual_execution_allowed: false
  manual_allowed_role: source validation only after fail-closed repository defect
  collision_scope: internal sovereign market activation, local Master Records reconstruction and E2 binding
  release_condition: exact local activation runner reaches STEGFIN_SOVEREIGN_TRADING_ACTIVATED under a persisted authorized heartbeat claim, or machine owner releases/supersedes the task
  next_executable_action: live carrier resolves locally materialized StegFin source with the released discovery logic and reruns the bounded worker; no network checkout or credential widening
```

### ESCALATED / AUTHORITY-OWNED

```yaml
- task_id: SOVEREIGN-HEARTBEAT-CONSTRAINT-RESOLUTION
  execution_owner: engine-v11 authority chain
  claim_state: ESCALATED
  worker_registry_ref: control/worker-registry.json + docs/FAIL_CLOSED_RESOLUTION_ESCALATION_MIRROR_HANDOFF.md
  manual_execution_allowed: false
  manual_allowed_role: NONE
  collision_scope: physical-resource, capability, custody, route, or authority constraints that current workers cannot resolve
  release_condition: next capable authority resolves the constraint or explicitly assigns bounded HUMAN_AUTHORITY_REQUIRED work
  next_executable_action: derive/register RESOLVE or ESCALATE work rather than expose worker scope to manual implementation
```

### COMPLETED / SUPERSEDED

```text
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.json
collision_scope: descriptive local-model selection, GitHub-token runtime authority, completed source-normalization and completed local-source discovery defect
release_condition: completed/released source validation cited above
next_executable_action: none for completed source work; machine runtime consumes released implementations
```

- Formal local model/runtime: complete/released.
- Local discovery/launch/inference/proof: complete/released.
- GitHub-token production authority: retired.
- Fail-closed resolution runtime: complete/merged.
- Active-worker normalization: complete/released.
- StegFin sovereign local-source discovery defect: source repaired/hosted-validated.

Pending or incomplete product state does not imply manual availability. Current registry/claim/fence/lease records override stale prose.

## Session consolidation and archive state

The original local-model/runtime implementation requirements are completed and released. The newly surfaced StegFin sovereign local-source discovery defect is now implemented, hosted-validated, and durably recorded here. Remaining live execution is still owned by the resident heartbeat, TV/TVC, StegFin machine workers, Master Records, and USER_ONLY wallet authority.

Because the current request explicitly requires continuing until finished tasks are activated and the persisted production heartbeat is still HB29, this active support session is not declared archive-ready solely from hosted source validation. A later turn may archive only after live machine evidence shows activation progress or the canonical owner durably releases all remaining support scope without requiring this thread.

## Completeness

```text
developed_files: 23/23 scoped source/support files
scaffolding_or_stubs: 0
missing_required_files: 0
source_validation: 21/21 scoped source/support requirements
source_integration: 13/13
session_consolidation: 23/23 source requirements transferred
product_activation: active machine work / incomplete
archive_readiness: false for this active support session
```


## ARA Microsoft Graph runtime execution

Canonical provider capability owner:

```text
StegVerse-Labs/TVC#86
StegVerse-Labs/TVC/tasks/TVC-ARA-GRAPH-RUNTIME-EXECUTION-086.json
```

The ARA Graph source/control lane is complete in TVC through merge `e36dc36f697afc27936403db171f23a6cc45edf3`. Remaining execution is independently admitted to the existing sovereign worker runtime; heartbeat is reference-only and does not grant execution or credential authority.

Registered machine lane:

```text
task_id: SHWP-ARA-GRAPH-RUNTIME-086
handoff: handoffs/SHWP-ARA-GRAPH-RUNTIME-086.json
registry: control/worker-registry.d/ara-graph-runtime-086.json
adapter: control/process-worker-adapters.d/ara-graph-runtime-086.json
worker: workers/ara_graph_runtime_worker.py
receipt: receipts/ara-graph-runtime/SHWP-ARA-GRAPH-RUNTIME-086.json
credential_authority: TV/TVC
github_token_runtime_authority: NONE
heartbeat_grants_execution_authority: false
```

Execution sequence:

```text
existing sovereign resident worker runtime
-> locate already-local clean TVC source containing e36dc36f697afc27936403db171f23a6cc45edf3
-> python tools/task_dispatcher.py tvc.ara_graph.activation_preflight
-> require READY_FOR_RESIDENT_INTAKE
-> registered worker child declares STEGTV_ARA_GRAPH_RUNTIME_AUTHORITY=TV/TVC
-> python tools/task_dispatcher.py tvc.ara_graph.execute_once
-> require PROVIDER_OPERATION_RESULT_RECORDED
-> persist secret-free worker receipt
```

Collision boundaries:
- no network source fetch or source mutation;
- no GitHub Actions/Render/Vercel/Cloudflare runtime authority;
- no Microsoft credential acquisition, reading, hashing, logging, copying, or transport by the worker;
- no new provider broker/OAuth broker/service/runtime;
- no ARA release authority;
- `TVC-CAPABILITY-RUNTIME-002` remains the separately claimed HTTPS observer and is not duplicated.

Current lifecycle:
- TVC source/control: COMPLETE / VALIDATED / MERGED
- sovereign worker source/registry: IMPLEMENTED / VALIDATION PENDING
- resident task claim/execution: NOT OBSERVED
- Graph SEND/FETCH/MARK_READ runtime evidence: NOT OBSERVED


### ARA Graph worker registration merge — 2026-08-27

The machine-owned ARA Graph runtime lane is now validated and merged into the existing sovereign worker runtime.

```text
stale PR #345: CLOSED / superseded
current-base PR #350
validated head: 38465ac35df52505f9497e569b2f0e4233775fae
Heartbeat Worker Project run: 33138546012 SUCCESS
Validate organization control plane run: 33138546141 SUCCESS
merge: 23c39a16516eeb8f1d96a11f703c0d5dd875a77a
```

Installed machine surfaces:
- `handoffs/SHWP-ARA-GRAPH-RUNTIME-086.json`
- `control/worker-registry.d/ara-graph-runtime-086.json`
- `control/process-worker-adapters.d/ara-graph-runtime-086.json`
- `workers/ara_graph_runtime_worker.py`
- `tests/test_ara_graph_runtime_worker.py`
- `control/admissible-existence-retrospective-conformance.d/ara-graph-runtime-086.json`

Admissible-Existence state:
`stegverse:capability:ara-graph-runtime-execution:v1 = ADMISSIBLE`

No ACTIVATED claim is made. The activation proof remains absent until a resident worker execution records real bounded provider evidence.

Machine lifecycle:
- worker source: IMPLEMENTED / VALIDATED / MERGED
- executable handoff: IMPLEMENTED / VALIDATED / MERGED
- worker registry/adapter: IMPLEMENTED / VALIDATED / MERGED
- AE conformance: VALIDATED / MERGED
- sovereign task claim: NOT OBSERVED
- resident preflight READY: NOT OBSERVED
- provider operation result: NOT OBSERVED
- capability ACTIVATED: NO

The session has no remaining implementation, validation, integration, credential, runtime, claim, or fence authority in this lane. Live continuation belongs to the registered sovereign worker + TV/TVC runtime authority.


### ARA Graph resident request bridge — 2026-08-27

The already-merged `SHWP-ARA-GRAPH-RUNTIME-086` task is being connected to the existing sovereign local-source refresh watcher through an intent-only task-specific resident request.

Canonical request:
`control/resident-execution-request.d/ara-graph-runtime-086.json`

Consumer:
`scripts/consume_ara_graph_resident_execution_request.py`

Existing execution bridge:
`scripts/refresh_and_execute_resident_task.py --task-id SHWP-ARA-GRAPH-RUNTIME-086`

Authority invariants:
- request grants no claim, fence, credential, provider-operation, release, scheduler, network-source, or heartbeat authority;
- source refresh performs no network fetch and preserves mutable runtime claim/fence/receipt state;
- the consumer is at-most-once per request id + content hash;
- GitHub/hosted execution is blocked;
- only non-secret ARA policy/locator values may cross the generic resident bridge: `STEGVERSE_ARA_MAIL_SENDER`, `STEGVERSE_ARA_MAIL_RECIPIENT`, and `STEGVERSE_VAULT_AGENT_SOCKET`;
- Microsoft client secrets/access tokens/refresh tokens remain prohibited;
- provider success or capability activation is never inferred from request consumption;
- the existing WorkerCoordinator remains the sole claim/fence execution gate;
- no second machine is required.

Lifecycle:
- resident request artifact: IMPLEMENTED
- task-specific consumer: IMPLEMENTED
- refresh copy / watcher hook / non-secret bridge allowlist: IMPLEMENTED
- validation: PENDING
- merge: PENDING
- authentic resident request consumption: NOT OBSERVED
- ARA Graph provider operation: NOT OBSERVED


### ARA Graph resident request bridge merge — 2026-08-27

The ARA Graph resident request bridge is validated and merged.

```text
PR #353
validated head: 010b0299fd8deb430beebe6f7bc5a7226fc94965
Heartbeat Worker Project: 33141631865 SUCCESS
Validate organization control plane: 33141631864 SUCCESS
merge: ef85edcea0fa40f91ae80399a587898d42e4f176
```

Merged resident surfaces:
- `control/resident-execution-request.d/ara-graph-runtime-086.json`
- `scripts/consume_ara_graph_resident_execution_request.py`
- `scripts/refresh_and_execute_resident_task.py` ARA non-secret locator forwarding
- `scripts/refresh_sovereign_worker_runtime_source.py` consumer refresh binding
- `scripts/install_sovereign_worker_source_refresh_service.py` request-consumer hook
- `tests/test_ara_graph_resident_execution_request.py`
- source-refresh regression coverage

The request remains intent-only and cannot grant execution authority. On an eligible sovereign local-source refresh it may ask the existing WorkerCoordinator to execute `SHWP-ARA-GRAPH-RUNTIME-086`; claim/fence admission remains inside the existing WorkerCoordinator.

Source/control + machine registration + resident request wiring: COMPLETE / VALIDATED / MERGED.
Authentic resident request consumption: NOT OBSERVED.
ARA Graph provider operation: NOT OBSERVED.
Capability activation: NOT OBSERVED.


## 2026-08-28 native bootstrap resident-request dispatch repair

Live source inspection found two shared resident-runtime integration gaps after the individual request bridges were already merged:

1. the native sovereign bootstrap materialized carrier/WorkerCoordinator source but not the complete resident-request consumer/dispatcher execution surface;
2. the Linux source-refresh watcher invoked each consumer as a separate `ExecStartPost`, so one fail-closed consumer could prevent later independent requests from being visited.

Bounded repair branch:

```text
claim: SOVEREIGN-RUNTIME-BOOTSTRAP-RESIDENT-DISPATCH-20260828
branch: fix/bootstrap-resident-request-dispatch-20260828
dispatcher: scripts/dispatch_resident_execution_requests.py
dispatcher receipt: receipts/sovereign-host/resident-request-dispatch.latest.json
authority effect: NONE_DISPATCH_ONLY
credential authority: TV/TVC
GitHub-token runtime authority: NONE
heartbeat grants execution authority: false
second user machine required: false
runtime execution observed: false
```

The dispatcher visits the already-existing Ecosystem Chat, G18, HIL, ARA Graph, and SV-DN1 resident consumers independently. Each consumer retains its own request validation, exactly-once semantics, and claim/fence authority boundary. A fail-closed request is recorded in `request_failures` but does not starve later independent requests.

The source-refresh watcher now performs one local source refresh followed by one dispatcher invocation rather than chaining request consumers as separate `ExecStartPost` commands.

The native v13 bootstrap now requires/materializes the dispatcher and its consumer execution dependencies. Only after `verify_sovereign_runtime_activation.py` proves every canonical activation predicate does bootstrap invoke the resident dispatcher. Hosted environments, incomplete activation proof, source merge, or CI validation cannot reach the dispatch step.

Current branch state:

```text
source repair: IMPLEMENTED / VALIDATION PENDING
merge: PENDING
native sovereign bootstrap execution: NOT OBSERVED
resident request dispatch receipt: NOT OBSERVED
Ecosystem Chat execution: NOT OBSERVED
HIL receiver execution: NOT OBSERVED
G18 resident consumption: NOT OBSERVED
ARA Graph provider operation: NOT OBSERVED
SV-DN1 sovereign round: NOT OBSERVED
```

This repair removes a shared source-side dispatch deadlock only. It does not activate HeartBeat, G18, HIL, Ecosystem Chat, ARA Graph, SV-DN1, Math, or any downstream product.


### Native bootstrap resident-request dispatch merge — 2026-08-28

The shared dispatch deadlock repair is now exact-head validated and merged:

```text
PR: #373
validated head: c810f49f006e18eb7182e5ae2473af7a3f7b3bb5
Validate organization control plane: 33228499508 / 99036791405 SUCCESS
Heartbeat Worker Project: 33228499527 / 99036791752 SUCCESS
merge: cb6c5a4ee3a809936e34afc67ef98bf204287b1e
bounded source claim: RELEASED_SOURCE_REPAIR
```

Validation passed the complete deterministic repository suite, executable-handoff validation, ownership partitions, heartbeat/runtime semantic separation, independent oscillator tests, canonical JSON parsing, and no-GitHub-token authority checks.

Merged behavior:
- native runtime materialization now includes the dispatcher and all current resident request consumers/dependencies;
- verified native bootstrap invokes the dispatcher only after all sovereign activation predicates PASS;
- source-refresh watcher invokes one dispatcher instead of a failure-sensitive `ExecStartPost` consumer chain;
- each request remains independently admitted and exactly-once;
- one fail-closed request does not prevent later request consumers from being visited;
- dispatcher grants no claim, fence, credential, heartbeat, route, publication, custody, or app activation authority.

Current runtime truth remains:

```text
native bootstrap source dispatch capability: IMPLEMENTED / VALIDATED / MERGED
resident-request dispatch receipt: NOT OBSERVED
G18 resident consumption: NOT OBSERVED
Ecosystem Chat parent execution: NOT OBSERVED
HIL receiver execution: NOT OBSERVED
ARA Graph provider operation: NOT OBSERVED
SV-DN1 sovereign round: NOT OBSERVED
user action required: false
second user machine required: false
```

The next state-changing event must come from an eligible non-hosted native sovereign runtime. Hosted CI cannot satisfy that evidence boundary.


## 2026-08-28 native materialization mutable-state boundary repair

Inspection after the resident-request dispatcher merge found an inconsistency between fresh native materialization and the later local source-refresh contract.

The refresh contract already treats these paths as mutable resident evidence and refuses to copy them from source:

```text
receipts/
checkpoints/
events/
heartbeats/
```

However, `scripts/install_sovereign_heartbeat_service.py` still copied those four checked-in directories into a newly materialized resident runtime. That could not satisfy the nine live activation predicates by itself, but it could contaminate exactly-once consumption history or downstream runtime observations with historical/source artifacts.

Bounded repair:

```text
claim: NATIVE-RUNTIME-MUTABLE-STATE-MATERIALIZATION-20260828
branch: fix/native-materialization-mutable-state-20260828
explicit control bootstrap seeds: unchanged
source receipts/checkpoints/events/heartbeats copied: false
credential authority: TV/TVC
GitHub-token runtime authority: NONE
heartbeat authority effect: NONE
runtime execution observed: false
```

Fresh materialization now copies only static runtime/control/handoff/authorization/worker/schema/cost-basis source plus explicitly enumerated scripts. Runtime evidence directories are created only by the resident runtime as it actually executes.

Regression coverage requires:
- all four mutable directories absent from source copy inputs;
- a fresh materialization has no source-derived checkpoints/events/heartbeats;
- its initial `receipts/` contains only `receipts/sovereign-host/materialization.latest.json`;
- explicit bootstrap seeds `control/heartbeat-state.json` and `control/worker-registry.json` remain present;
- the v13 carrier and resident-request dispatcher remain materialized.

Current state: IMPLEMENTED / VALIDATION PENDING / MERGE PENDING. No resident execution or activation claim is made.


### Native materialization mutable-state boundary merge — 2026-08-28

The source/runtime evidence-contamination repair is exact-head validated and merged:

```text
PR: #377
validated head: aa9e3de62601d1b196facbf12ecdf6514659cf45
Organization Control Plane: 33228672633 / 99037294850 SUCCESS
Heartbeat Worker Project: 33228672616 / 99037294917 SUCCESS
merge: 1ab2a2cc534dc2e1acc8015adcea5d087366cbc7
bounded source claim: RELEASED_SOURCE_REPAIR
```

The Heartbeat validation passed the complete deterministic repository suite, native-process/canary retention checks, legacy HB29 replay protection, current oscillator-anchor proof, carrier/worker separation, and workflow non-authority.

Merged invariant:

```text
source receipts copied into fresh runtime: false
source checkpoints copied into fresh runtime: false
source events copied into fresh runtime: false
source heartbeats copied into fresh runtime: false
explicit control bootstrap seeds retained: true
initial runtime receipt: receipts/sovereign-host/materialization.latest.json only
credential authority: TV/TVC
GitHub-token runtime authority: NONE
runtime execution observed: false
```

This closes source-derived mutable-evidence contamination for fresh native materialization. It does not provide a sovereign-node execution receipt or alter any app activation state.


## 2026-08-28 native materialization mutable-control boundary repair

The prior mutable-directory repair removed source `receipts/checkpoints/events/heartbeats` from fresh native materialization. A second bounded inconsistency remained because the complete source `control/` directory was still copied.

The source-refresh contract already preserves these resident-generated files rather than overwriting them:

```text
control/heartbeat-carrier-runtime-state.json
control/worker-runtime-state.json
control/worker-control-plane-coordination.json
control/worker-status.json
```

Runtime inspection confirmed:
- the carrier creates/advances `heartbeat-carrier-runtime-state.json`;
- WorkerCoordinator initializes `worker-runtime-state.json` when absent and writes it every resident cycle;
- the worker control-plane projection is reconstructed from the current carrier when absent;
- these are observations/runtime state, not canonical bootstrap intent.

The explicit bootstrap seeds remain unchanged:

```text
control/heartbeat-state.json       # immutable legacy HB29 bootstrap seed
control/worker-registry.json       # initial canonical task/claim registry seed
```

The materializer now excludes the four resident-generated control snapshots from source copy. Because copy ignores them rather than deleting target files, re-materialization preserves an already-running resident's current mutable state.

Current state: IMPLEMENTED / VALIDATION PENDING / MERGE PENDING. Runtime execution remains NOT OBSERVED.


### Native mutable-control materialization merge — 2026-08-28

The resident-generated control-state preservation repair is exact-head validated and merged:

```text
PR: #381
validated head: b16c3bab04965a53c10ddeaecf518c448fdae1ce
Organization Control Plane: 33228785453 / 99037619703 SUCCESS
Heartbeat Worker Project: 33228785608 / 99037620245 SUCCESS
merge: 83a7d714d1b97faae8f37a16633020e4cfa6225b
bounded source claim: RELEASED_SOURCE_REPAIR
```

Merged invariant:
- source `heartbeat-carrier-runtime-state.json`: excluded from fresh resident copy;
- source `worker-runtime-state.json`: excluded;
- source `worker-control-plane-coordination.json`: excluded;
- source `worker-status.json`: excluded;
- existing resident copies of those files survive re-materialization;
- legacy `control/heartbeat-state.json` HB29 seed remains materialized;
- initial `control/worker-registry.json` remains materialized.

Full deterministic repository validation, oscillator/replay protection, carrier/worker separation, and no-token authority checks passed. Runtime execution remains NOT OBSERVED.


## 2026-08-28 native materialization static-dependency parity repair

After mutable runtime/control contamination was removed, comparing fresh native materialization with the canonical resident source-refresh manifest exposed missing static dependencies.

Registered/runtime code already requires:
- `state_language/` for semantic state preclaim revalidation;
- `management/` contracts such as `COSV_HEARTBEAT_STATE_PACKET_CONTRACT.json`;
- `scripts/materialize_live_cosv_packet.py`, `cosv.py`, and `cosv_state_packet.py` for the admitted COSV live packet worker;
- `scripts/project_worker_control_plane_from_carrier.py` when current carrier state exists but worker control-plane projection is absent;
- `scripts/verify_iphone_heartbeat_transition_receipt.py` for the already-defined portable fallback verifier path.

Those sources were available to later local source refresh but were not present in a fresh native materialization. A task could therefore be correctly registered/admitted yet fail from missing static source.

Bounded repair:

```text
claim: NATIVE-RUNTIME-STATIC-DEPENDENCY-PARITY-20260828
branch: fix/native-materialization-static-parity-20260828
state_language materialized: true
management contracts materialized: true
COSV live packet scripts materialized: true
worker control-plane projector materialized: true
portable receipt verifier materialized: true
mutable runtime evidence copied: false
mutable resident control snapshots copied: false
credential authority: TV/TVC
runtime execution observed: false
```

Regression coverage now requires a freshly materialized runtime to contain these dependencies and checks parity with the static source-refresh contract. Current state: IMPLEMENTED / VALIDATION PENDING / MERGE PENDING.


### Native static-dependency parity merge — 2026-08-28

The fresh-native static dependency closure repair is exact-head validated and merged:

```text
PR: #385
validated head: e667b4d1a5eb5f88edf6a71acaf93beeed1ae8e3
Organization Control Plane: 33228914056 / 99037976525 SUCCESS
Heartbeat Worker Project: 33228914053 / 99037976470 SUCCESS
merge: a3e8dc0dc480b172dc191dea662b7ec5df44c654
bounded source claim: RELEASED_SOURCE_REPAIR
```

The first validation attempt failed only because the new test searched for a quoted tuple value; runtime/source behavior itself was not failing. The assertion was corrected without weakening any gate, and the full deterministic suite then passed.

Fresh native materialization now includes:
- `state_language/`;
- full static `management/` contracts;
- COSV live-packet materializer and COSV packet tooling;
- worker control-plane projector;
- portable heartbeat receipt verifier;
- previously merged resident-request dispatcher and consumers.

It still excludes source-derived mutable runtime evidence and mutable resident control snapshots. Runtime execution remains NOT OBSERVED.


## 2026-08-29 bootstrap task-execution prime repair

Live reconciliation after the Universal InTr migration confirmed that the native
service installer could return success while process supervision was still
asynchronously bringing up the separated carrier/WorkerCoordinator. Bootstrap
then dispatched resident requests immediately. On a fresh resident, an SV-DN-1
consumer could therefore reach its sovereign chain before
`control/heartbeat-carrier-runtime-state.json` existed, return
`HANDOFF_READY`, and receive no second dispatch unless an unrelated source
refresh later occurred.

That race explains the persistent repository-observed state:

```text
heartbeat: ACTIVE_PROTOCOL_VERIFIED
worker runtime: CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION
SV-DN1 source-materialization receipt: NOT OBSERVED
```

Bounded repair branch:

```text
branch: fix/sovereign-bootstrap-task-execution-prime-20260829
source: scripts/bootstrap_sovereign_runtime.py
test: tests/test_bootstrap_resident_request_dispatch.py
authority effect: NONE_EXECUTION_PRIME_ONLY
credential authority: TV/TVC
GitHub-token runtime authority: NONE
second machine required: false
```

After native service registration succeeds, bootstrap now explicitly invokes
one already-materialized local WorkerCoordinator cycle before resident-request
dispatch:

```text
install native separated services
-> run_worker_runtime.py --root <resident-runtime> --cycles 1
-> require/record carrier + worker runtime observation
-> dispatch bounded resident requests
-> run final activation verifier
```

The prime does not mint authority outside WorkerCoordinator. It merely forces
the existing claim/fence evaluator to run on the same eligible non-hosted
resident instead of depending on asynchronous service timing or a future
filesystem event. Credentials are scrubbed exactly as for the existing
bootstrap child processes. Hosted environments remain rejected.

For SV-DN-1 this means the first independently admitted task,
`SV-DN1-SOURCE-MATERIALIZATION-001`, can now be reached during the same native
bootstrap opportunity. Its authentic completion still requires the sovereign
worker to emit:

```text
~/.stegverse/state/sv-dn1-source-materialization/receipts/latest.json
transition_id: SV_DN1_EXACT_SOURCE_MATERIALIZATION_COMPLETE
```

No runtime receipt, Hugging Face observation, Universal InTr traversal, SDK
admission, or product activation is claimed by this source repair. Those remain
authentic resident evidence gates.


## CMC-028 root-custody worker current-main rematerialization — 2026-08-29

Current-main source was re-read after the WorkerCoordinator bootstrap-prime repair at `426097b5bda53be742c68dbf43233597237d782c`. Stale PR #372 and branches r5-r8 were not merged or force-updated. Their bounded CMC-028-specific artifacts were rematerialized on fresh branch `cmc-028-root-custody-worker-r9`, while the shared workflow, COSV index/coverage, denominator test, and this handoff were merged into current content.

```text
task_id: SHWP-CMC028-ROOT-CUSTODY-EVIDENCE-001
TVC required ancestor: dd3734084eba4887c0c08e2e47eab3a20565c820
worker command: tvc.certificate_root_custody.observe
credential authority: TV/TVC
GitHub-token runtime authority: NONE
heartbeat grants execution authority: false
hosted runtime: BLOCKED
network source fetch: false
source mutation: false
protected material read/hash/export: false
certificate issuance/signing authority: false
worker source/registry state: IMPLEMENTED / VALIDATION PENDING
runtime evidence: NOT OBSERVED
CUSTODY_RECOVERY_EVIDENCE_VERIFIED: NOT OBSERVED
```

The live-denominator test derives the worker count from `control/worker-registry.json` plus every `control/worker-registry.d/*.json` fragment. Aggregate COSV counts were recomputed from the current base rather than copied from stale branches. Completion remains impossible unless an eligible sovereign TV/TVC resident supplies authentic secret-free public identity and recovery-continuity receipts while the worker never reads, hashes, or exports protected objects.


### CMC-028 live-denominator correction on PR #412

The exact-head full suite enumerated 56 live unique worker task IDs after CMC-028, not 55. The extra pre-existing current-main task is `SV-DN1-PRODUCTION-SOURCE-PREP-001`, which is `HANDOFF_READY` and unvectorized. Coverage is corrected to 56 registered / 34 indexed / 15 active worker gaps / 29 total active gaps. The dedicated CMC-028 test and all preceding authority, JSON, handoff, and runtime-boundary steps passed; the failed run was aggregate-denominator evidence and did not represent CMC-028 runtime execution.


## CMC-028 resident request dispatch wiring — 2026-08-30

PR #412 merged the CMC-028 WorkerCoordinator task but did not place that task in the
resident-request dispatcher. A sovereign bootstrap could therefore refresh and prime
the worker registry without ever selecting CMC-028. The bounded successor adds:

```text
request: control/resident-execution-request.d/cmc028-root-custody-001.json
consumer: scripts/consume_cmc028_resident_execution_request.py
target: SHWP-CMC028-ROOT-CUSTODY-EVIDENCE-001
mode: TARGETED_INDEPENDENT_TASK_CONTROL
request authority effect: NONE_REQUEST_ONLY
protected material allowed in request: false
second machine required: false
```

The request is copied by both native materialization and already-local runtime refresh,
and is visited independently by `dispatch_resident_execution_requests.py`. Its consumer
uses exactly-once request-id/content-hash semantics, strips key/recovery/GitHub-token
environment values, blocks hosted execution, and invokes only the already-admitted task
through `refresh_and_execute_resident_task.py`. A recorded attempt is not custody proof.
CMC-028 remains incomplete until the task itself emits authentic resident
`CUSTODY_RECOVERY_EVIDENCE_VERIFIED` evidence without protected-material read, hash, or
export and without issuance or signing authority.


## Universal Governance bootstrap eligibility closure — 2026-08-31

The native bootstrap source-completeness gate now requires `scripts/consume_universal_governance_enforced_reference_request.py`. A resident can no longer self-declare eligible, install services, or proceed through bootstrap source validation while omitting this required resident consumer.

This aligns bootstrap eligibility with the native installer materialization contract and the continuous WorkerCoordinator resident-request sweep. No hosted execution authority or runtime observation is inferred.
