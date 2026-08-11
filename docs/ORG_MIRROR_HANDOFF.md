# StegVerse-Labs Organization Mirror Handoff

## Authority

This is the canonical StegVerse-Labs organization continuation/exit record. Repository-local `*_MIRROR_HANDOFF.md` files remain authoritative for repository-local implementation evidence. Machine-readable state under `control/`, `handoffs/`, `management/`, `receipts/`, `checkpoints/`, `authorizations/`, `schemas/`, and `events/` supersedes chat history.

## Active goal and ownership

```text
goal_id: ARCHIVE-GATE-PROGRESS-ENFORCEMENT-001
repository: StegVerse-Labs/.github
canonical_branch: main
canonical_owner: StegVerse-Labs/.github#64
state: ACTIVE_REMEDIATION / CURRENT TASK GRAPH NOT ARCHIVE READY
thread_archive_ready: false
archive_block_reason: UNMET_PRODUCTION_ACTIVATION_GOALS_WITH_DURABLE_CARRIER_STALLED_AT_HB29
latest session inventory: control/session-goal-inventory-2026-08-11-ecosystem-chat-local-model.json
```

Context transfer alone does not satisfy this organization gate.

## Non-negotiable archive invariant

Archive readiness requires either every originating and inherited successor/integration/activation/release goal to be terminal-success, or unfinished goals to be owned by canonical machine workers measurably advancing terminal predicates. `BUSY`, `CLAIMED`, `LEASED`, heartbeat carriage, checkpoints, or unchanged blocker rechecks are not progress by themselves.

## Canonical architecture

```text
heartbeat runtime: heartbeat_runtime.engine_v9.HeartbeatRuntime
heartbeat runner: scripts/run_heartbeat_runtime.py
worker registry: control/worker-registry.json
worker coordination: control/heartbeat-subsignals.json
Master Records projection: control/heartbeat-master-records-projection.json
last directly observed heartbeat epoch: 29
last cycle: 2026-08-10T20:51:11Z
resident carrier post-HB29 advance: NOT OBSERVED
```

There is one canonical heartbeat and one canonical worker registry. `SHWP-DURABLE-RUNTIME-ACTIVATION` remains installed and bound with claim `SHWP-SHWP-DURABLE-RUNTIME-ACTIVATION-G18`, fencing token 18, and blocker `handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json#block`. No GitHub-hosted workflow may substitute for the resident sovereign carrier.

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
live same-carrier activation: NOT COMPLETE
```

Canonical local-model handoff: `StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md`.

Canonical Ecosystem Chat recovery/activation handoff: `docs/ECOSYSTEM_CHAT_ORPHAN_RECOVERY_MIRROR_HANDOFF.md`.

Canonical session inventory: `control/session-goal-inventory-2026-08-11-ecosystem-chat-local-model.json`.

### TC/TVC credential authority and no-GitHub-token production boundary

```text
credential authority: TC/TVC
local-model credential requirement: NONE
route authority: StegVerse-Labs/TVC
model/runtime: StegVerse-002/micro-node-runtime
transport/evidence: StegVerse-org/LLM-adapter
custody/reconstruction: master-records/orchestration
GitHub token production authority: NONE
GitHub Actions production activation role: NONE
GitHub Actions heartbeat persistence role: NONE
```

PR `StegVerse-Labs/.github#79` merged at `f6265ff0f74a51adf79985da09691b871b7576dc` and retired the Ecosystem Chat token-bearing hosted activation path. Follow-on organization cleanup retired GitHub credential use or hosted mutation authority from the complete control-plane set encountered in this session:

```text
.github/workflows/activate-ecosystem-chat-sovereign-inference-worker.yml
.github/workflows/heartbeat-worker-project.yml
.github/workflows/org-control-plane-validate.yml
.github/workflows/org-continuation-check.yml
.github/workflows/archive-readiness-validate.yml
.github/workflows/org-allocator.yml
.github/workflows/all-org-heartbeat-federation.yml
.github/workflows/native-process-worker-canary.yml
.github/workflows/steggate-heartbeat-integration.yml
.github/workflows/activate-host-self-attest-worker.yml
.github/workflows/activate-sovereign-runtime-worker.yml
.github/workflows/org-heartbeat.yml
.github/workflows/org-heartbeat-watchdog.yml
.github/workflows/org-handoff-render.yml
.github/workflows/org-aggregation-check.yml
```

The mutation/activation lanes are now validation-only and cannot commit/push canonical heartbeat, claim, fence, or worker state. The read-only validation/diagnostic lanes use anonymous public git fetch and `permissions: {}`. Disposable temporary-directory heartbeat exercises are permitted only when they cannot mutate canonical repository state. GitHub Actions platform-internal metadata-read capability is not a StegVerse credential authority and is not consumed by project execution.

## Validation evidence

Retained passing evidence:

```text
Ecosystem Chat no-token validation: run 31453552033 SUCCESS
Heartbeat Worker Project no-token validation: run 31453552032 SUCCESS
Organization control-plane no-token validation: run 31453552110 SUCCESS
complete deterministic heartbeat suite: 97 tests PASS
Org Continuation no-token validation: run 31464416581 SUCCESS
Sovereign Runtime hosted-authority retirement: run 31464631729 SUCCESS
```

The first post-reconciliation continuation run failed only because required exact handoff headings were temporarily omitted; the required headings were restored. A later parser-only failure caused by a literal incomplete GitHub expression in a self-check was also corrected; no zero-job parser failure is represented as successful validation.

### Orphan recovery and higher-fence continuation

```text
StegVerse-Labs/.github PR #78
merge: 477b0d5e3737662a4d51fe87538bbbc2d4acc99e
Master Records custody PR #27
merge: 4c6f4679c20c7fc70a65753cf4f87e6b929f09ef
```

Dry-run validation proves recovery fence 23 is greater than ended fence 20. It is nonpersistent and is not a live activation claim.

Live continuation remains:

```text
resident heartbeat advances beyond HB29
-> recovery obtains a live fence >20
-> Master Records G20 custody resolves
-> recovery COMPLETED
-> parent returns HANDOFF_READY
-> parent obtains fresh live fence >20
-> local model discovered/launched/proven
-> TVC ROUTE_ADMITTED / credential_requirement NONE
-> released LLM-adapter task 020 executes exact endpoint
-> Master Records provider-usage reconstruction PASS
-> Master Records transition reconstruction PASS for same execution
-> immutable zero-blocker Ecosystem Chat activation evidence
```

## Human authority boundary — durable runtime activation

The native runtime implementation is complete, but activation requires a real StegVerse-owned/federated machine.

```text
handoff: handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json
receipt: receipts/sovereign-runtime-activation/SHWP-DURABLE-RUNTIME-ACTIVATION.json
worker: workers/sovereign_runtime_activation_worker.py
installer: scripts/install_sovereign_heartbeat_service.py
verifier: scripts/verify_sovereign_runtime_activation.py
state: BLOCKED_RUNTIME_ACTIVATION
reason: SOVEREIGN_NODE_DECLARATION_NOT_PRESENT
```

No GitHub-hosted runner, Render service, Vercel runtime, Cloudflare surface, or repository file may substitute for the sovereign physical carrier. Release requires node-local `~/.stegverse/heartbeat/activation.latest.json` with all nine activation predicates true: runtime materialization, native service activation, continuous liveness, heartbeat advance, worker-coordination checkpoint, controlled restart, non-regression, no duplicate claim/fence, and reconstruction PASS.

## Cross-repository dependencies / propagation

```text
StegVerse-002/micro-node-runtime
-> StegVerse-Labs/.github resident heartbeat
-> StegVerse-Labs/TVC / TC-TVC
-> StegVerse-org/LLM-adapter
-> master-records/orchestration
-> StegVerse-Labs/Site
-> GCAT-BCAT-Engine/Publisher + admissibility-wiki + stegguardian-wiki
```

Propagation remains blocked until immutable same-execution activation evidence exists. Other organization production goals retain their own handoffs, claims, blockers and collision boundaries.

## Collision and authority boundaries

- One canonical heartbeat only.
- One canonical worker registry only.
- GitHub Actions is validation/evidence carriage only, not heartbeat cadence, claim allocation, activation, credential, or persistence authority.
- TC/TVC owns credential semantics.
- TVC route admission does not grant execution authority.
- Model output does not grant authority.
- Master Records reconstruction is evidence, not execution authority.
- Context transfer is not product activation.
- Session archival is not product activation.

## Session consolidation

All unique Ecosystem Chat local-model/session requirements are durably transferred; `unique_chat_only_requirements_remaining=0` is recorded in the session inventory. The organization archive gate nevertheless remains `thread_archive_ready=false` because inherited production activation is not terminal and the sovereign durable carrier is stalled at HB29.

```text
thread_archive_ready: false
archive_gate: BLOCKED
archive_gate_reason: SOVEREIGN_DURABLE_CARRIER_NOT_ACTIVE_AND_INHERITED_PRODUCTION_GOALS_UNMET
current session role: DISTINCT SUPPORT / CANONICAL STATE RECONCILIATION AND ACTIVATION OBSERVATION
next executable transition: native sovereign carrier activation on a declared StegVerse-owned/federated node
```
