# StegVerse-Labs Organization Mirror Handoff

## Authority

This is the canonical StegVerse-Labs organization continuation/exit record. Repository-local `*_MIRROR_HANDOFF.md` files remain authoritative for repository-local implementation evidence. Machine-readable state under `control/`, `handoffs/`, `management/`, `receipts/`, `checkpoints/`, `authorizations/`, `schemas/`, and `events/` supersedes chat history.

## Active goal and ownership

```text
goal_id: ECOSYSTEM-CHAT-SOVEREIGN-ACTIVATION
repository: StegVerse-Labs/.github
canonical_branch: main
active_runtime_owner: StegVerse-Labs/.github#59 + resident sovereign heartbeat
active_progress_remediation_owner: StegVerse-Labs/.github#65 + resident sovereign heartbeat
active_inference_owner: StegVerse-Labs/.github#60 + resident sovereign heartbeat
active_constraint_resolution_runtime: heartbeat_runtime.engine_v11.HeartbeatRuntime
state: ACTIVE_DISTINCT_SUPPORT / ACTIVE_MACHINE_WORKERS
thread_archive_ready: false
archive_active_reason: PRODUCTION_ACTIVATION_GOALS_REMAIN_ACTIVE_AND_RESIDENT_CARRIER_HAS_NOT_YET_ADVANCED_BEYOND_HB29
```

Operational-state invariant: unresolved work is never an idle terminal `BLOCKED` task. It is either actively owned by the current work session, actively owned by a documented StegVerse worker/machine lane, or complete/superseded. A fail-closed or conditional worker response may describe a constraint, but engine v11 must preserve the governing goal by deriving a RESOLVE/ESCALATE task and advancing through the authority chain until solved or explicitly escalated.

Canonical state policy: `control/active-worker-state-policy.json` / issues #83, #84, #85.
Canonical fail-closed resolution handoff: `docs/FAIL_CLOSED_RESOLUTION_ESCALATION_MIRROR_HANDOFF.md` / merged PR #82 at `e0500245085f7dcdabd87c801b5654a619264ca4`.

## Canonical architecture

```text
heartbeat runtime: heartbeat_runtime.engine_v11.HeartbeatRuntime
heartbeat runner: scripts/run_heartbeat_runtime.py
worker registry: control/worker-registry.json
worker coordination: control/heartbeat-subsignals.json
Master Records projection: control/heartbeat-master-records-projection.json
last directly observed heartbeat epoch: 29
last cycle: 2026-08-10T20:51:11Z
resident carrier post-HB29 advance: NOT OBSERVED
SHWP-DURABLE-RUNTIME-ACTIVATION claim: SHWP-SHWP-DURABLE-RUNTIME-ACTIVATION-G18
fencing token: 18
runtime operational state: ACTIVE_WORKER
runtime solution state: ACTIVE_SOLUTION_EXECUTION
current constraint: SOVEREIGN_NODE_DECLARATION_NOT_PRESENT
constraint class: PHYSICAL_RESOURCE
human_action_required: false
missing_implementation: false
next_solution_action: SOVEREIGN_RUNTIME_SOLUTION_EXECUTION
```

There is one canonical heartbeat and one canonical worker registry. No GitHub-hosted workflow may substitute for the resident sovereign carrier.

## Completed protocol capabilities

```text
formal local model: COMPLETE_RELEASED
local runtime discovery/launch/inference/proof: COMPLETE_RELEASED
persistent private endpoint proof: COMPLETE_RELEASED
heartbeat local-model lifecycle integration: COMPLETE_MERGED
heartbeat -> TVC invocation: COMPLETE_MERGED
TVC route evaluator / credential NONE: SOURCE_COMPLETE
LLM-adapter exact route executor task 020: COMPLETE_RELEASED
Master Records historical G20 custody task 025: COMPLETE_RELEASED
orphan recovery source implementation: COMPLETE_RELEASED
GitHub-token production/control-plane authority retirement: COMPLETE_RELEASED
fail-closed resolution task derivation/escalation: COMPLETE_MERGED / PR #82
active-worker state policy and validator: INSTALLED
live same-carrier activation: ACTIVE_MACHINE_WORK / NOT YET COMPLETE
```

Canonical local-model handoff: `StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md`.
Canonical runtime activation handoff: `handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json`.
Canonical Ecosystem Chat recovery/activation handoff: `docs/ECOSYSTEM_CHAT_ORPHAN_RECOVERY_MIRROR_HANDOFF.md`.
Canonical fail-closed escalation handoff: `docs/FAIL_CLOSED_RESOLUTION_ESCALATION_MIRROR_HANDOFF.md`.

## TV/TVC credential authority and no-GitHub-token production boundary

```text
credential authority: TV/TVC
local-model credential requirement: NONE
route authority: StegVerse-Labs/TVC
model/runtime: StegVerse-002/micro-node-runtime
transport/evidence: StegVerse-org/LLM-adapter
custody/reconstruction: master-records/orchestration
GitHub token production authority: NONE
GitHub Actions production activation role: NONE
GitHub Actions heartbeat persistence role: NONE
```

PR #79 retired the token-bearing hosted activation path. Current sovereign validation requires credential requirement `NONE`, strips GitHub authentication variables from sovereign child execution, and rejects legacy `TC/TVC` as current reconstructed authority. Historical immutable records may retain legacy wording as provenance only.

## Validation evidence

Retained source/control-plane evidence includes:

```text
Ecosystem Chat no-token validation: run 31453552033 SUCCESS
Heartbeat Worker Project no-token validation: run 31453552032 SUCCESS
Organization control-plane no-token validation: run 31453552110 SUCCESS
Org Continuation no-token validation: run 31464416581 SUCCESS
Sovereign Runtime hosted-authority retirement: run 31464631729 SUCCESS
Native runtime activation/proof path: Heartbeat Worker Project run 31338817754 SUCCESS
Active sovereign worker semantics: run 31620645190 SUCCESS
Fail-closed resolution/escalation implementation: PR #82 merged at e0500245085f7dcdabd87c801b5654a619264ca4
Organization handoff render after PR #82: run 31620715890 SUCCESS
```

A hosted validation run may validate source and policy but never grants production activation authority.

## Physical-resource execution boundary — durable runtime activation

```text
runtime owner issue: StegVerse-Labs/.github#59
progress-remediation issue: StegVerse-Labs/.github#65
handoff: handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json
constraint record: management/SHWP_RUNTIME_ACTIVATION_BLOCKER.json
worker: workers/sovereign_runtime_activation_worker.py
installer: scripts/install_sovereign_heartbeat_service.py
verifier: scripts/verify_sovereign_runtime_activation.py
operational state: ACTIVE_WORKER
solution state: ACTIVE_SOLUTION_EXECUTION
current constraint: SOVEREIGN_NODE_DECLARATION_NOT_PRESENT
next_solution_action: SOVEREIGN_RUNTIME_SOLUTION_EXECUTION
eligible declaration: STEGVERSE_SOVEREIGN_NODE=1 OR /etc/stegverse/node.json OR ~/.stegverse/node.json
```

The missing node declaration is an input condition for the active worker, not an available stopping state. G18 must select/materialize an eligible StegVerse-owned/federated Linux/macOS/Windows carrier, promote an eligible StegVerse-002 micro-node, or construct a new sovereign node from the repository-local capsule. If all candidates collide with the worker authority ceiling, engine v11 must derive/escalate the resolution task to the next authority level. GitHub Actions, Render, Vercel, Cloudflare, or repository-only mutation are prohibited substitutes for the sovereign carrier.

Completion requires node-local `~/.stegverse/heartbeat/activation.latest.json` with all nine activation predicates true, heartbeat advancement beyond HB29, controlled restart continuity, no duplicate claim/fence, and Master Records reconstruction PASS.

## Fail-closed / conditional constraint execution

`heartbeat_runtime.engine_v11.HeartbeatRuntime` is canonical. A worker may return a fail-closed/conditional constraint for the attempted consequence, but the governing goal must remain active. The runtime derives a deterministic RESOLVE/ESCALATE task, releases the originating claim, moves the parent to `ACTIVATION_PENDING`, and escalates through:

```text
WORKER
-> REPOSITORY_OWNER
-> COMPONENT_AUTHORITY
-> ECOSYSTEM_GOVERNANCE
-> HUMAN_AUTHORITY
```

No executor at a machine level is itself a constraint collision and triggers escalation. No worker may resolve a collision by weakening the goal, bypassing StegGate, manufacturing credential/route authority, or making GitHub tokens production authority.

## Ecosystem Chat inference activation boundary

```text
owner issue: StegVerse-Labs/.github#60
worker task: SHWP-ECOSYSTEM-CHAT-INFERENCE-001
current product state: ACTIVE_MACHINE_CONTINUATION / NOT YET ACTIVATED
source implementation: COMPLETE/RELEASED across model -> heartbeat -> TVC -> LLM-adapter -> Master Records
live completion condition: immutable same-carrier zero-constraint activation evidence under a fresh authorized fence >20
```

The descriptive `select/execute local model` step is obsolete. The installed heartbeat path discovers locally materialized `StegVerse-002/micro-node-runtime`, launches and maintains the canonical private process through TVC admission, exact LLM-adapter execution, measured usage, and Master Records reconstruction. No GitHub token or hosted provider belongs to that production path.

## Cross-repository dependencies / propagation

```text
StegVerse-002/micro-node-runtime
-> StegVerse-Labs/.github resident heartbeat
-> StegVerse-Labs/TVC / TV/TVC
-> StegVerse-org/LLM-adapter
-> master-records/orchestration
-> StegVerse-Labs/Site
-> GCAT-BCAT-Engine/Publisher + admissibility-wiki + stegguardian-wiki
```

Propagation is not yet authorized because immutable same-execution live activation evidence is not yet present. The propagation work remains actively owned by canonical continuation tasks rather than an idle blocked state.

## Collision and authority boundaries

- One canonical heartbeat only.
- One canonical worker registry only.
- GitHub Actions is validation/evidence carriage only, not heartbeat cadence, claim allocation, activation, credential, or persistence authority.
- TV/TVC owns credential semantics.
- TVC route admission does not grant execution authority.
- Model output does not grant authority.
- Master Records reconstruction is evidence, not execution authority.
- Context transfer is not product activation.
- Session archival is not product activation.
- Do not create duplicate implementation for source-complete local model/runtime, TVC routing, LLM-adapter executor, or Master Records reconstruction.
- Constraints must produce active solution work or authority escalation; they may not terminate unfinished goals as passive work.

## Session consolidation

All unique local-model/runtime requirements are durably transferred. The requested no-GitHub-token rule is installed in TV/TVC and control-plane validation. The old descriptive local-runtime selection step is superseded by executable local discovery/launch/inference/proof. PR #82 is merged and owns fail-closed constraint-resolution mechanics. Issues #59/#65/#60 own remaining live activation work. Issues #83/#84 own broad historical state normalization while this migration completes.

```text
session_role: DISTINCT SUPPORT / ACTIVE INTEGRATION AND STATE NORMALIZATION
thread_archive_ready: false
archive_active_reason: LIVE_ACTIVATION_AND_REGISTRY_NORMALIZATION_WORK_REMAIN_ACTIVE
next_executable_transition: G18 SOVEREIGN_RUNTIME_SOLUTION_EXECUTION plus engine-v11 derived RESOLVE/ESCALATE tasks
archive_release_condition: all session-unique work complete/transferred and remaining unfinished goals demonstrably active under canonical workers with no unowned legacy constraint states
```

## Completeness

```text
developed_files: 23/23 scoped source/session deliverables
scaffolding_or_stubs: 0
missing_required_files: 0
source_validation: 18/19 pending final post-merge aggregation revalidation
source_integration: 12/12
session_consolidation: 23/23
product_activation: active machine work / incomplete
propagation: active continuation / not yet authorized
archive_readiness: false
```
