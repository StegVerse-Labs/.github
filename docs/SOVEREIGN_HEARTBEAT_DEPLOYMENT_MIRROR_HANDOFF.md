# Sovereign Heartbeat Deployment Mirror Handoff

Updated: 2026-08-16T18:31:00-05:00

## Authority and active goal

```text
goal_id: HEARTBEAT-HB29-CURRENT-MAIN-RECONCILE-197
parent_goal: SHWP-SOVEREIGN-DEPLOYMENT-NO-THIRD-PARTY-001
originating_session_goal: activate the released StegVerse heartbeat/worker architecture without Render or non-TV/TVC credentials, preserve retained HB29 continuity, and keep trade/local-model continuation durable
repository: StegVerse-Labs/.github
branch: claim/heartbeat-hb29-main-reconcile-197-current
canonical_issue: StegVerse-Labs/.github#197
parent_owners: StegVerse-Labs/.github#122 and #12
implementation_claim: control/session-implementation-claim-2026-08-16-heartbeat-hb29-main-reconcile-197.json
implementation_claim_state: CLAIMED_FOR_INTEGRATION
validation_claim: SAME_BOUNDED_CURRENT_MAIN_LANE
claim_created_at: 2026-08-16T17:42:00-05:00
claim_release_condition: complete deterministic validation on current-main lineage, merge replacement PR, supersede stale #198/#199, and transfer live successor observation to #122/#12
credential_authority: TV/TVC
credential_requirement: NONE
non_tv_tvc_secret_or_token_allowed: false
github_token_runtime_authority: NONE
render_production_runtime_allowed: false
```

This handoff is authoritative for the bounded source/deployment/verifier reconciliation. It does not own or mutate live `control/heartbeat-state.json`, live `control/worker-registry.json`, active claims/fences/leases, resident process authority, provider/wallet state, or TV/TVC protected material.

## Current-main convergence preserved

The earlier reconciliation branch diverged while current `main` added the coherent signal-space candidate and formal-candidate worker. PR #199 therefore must not be force-merged. This replacement branch starts from current `main` and explicitly preserves:

```text
heartbeat_runtime/signal_space.py
workers/coherent_signal_formal_candidate_worker.py
control/process-worker-adapters.d/coherent-signal-formal-candidate-001.json
control/worker-registry.d/coherent-signal-formal-candidate-001.json
cost-basis/worker-runtime/coherent-signal-formal-candidate.json
handoffs/SHWP-COHERENT-SIGNAL-FORMAL-CANDIDATE-001.json
docs/COHERENT_SIGNAL_SPACE_TRANSITION_MANIFOLD_MIRROR_HANDOFF.md
```

The carrier remains an authority-neutral observation/reference mechanism. The coherent signal-space candidate remains evidence-led and explicitly not a completeness claim.

## Reconciled production source

```text
heartbeat_runtime.engine_v12.HeartbeatRuntime = canonical non-authorizing carrier
heartbeat_runtime.HeartbeatRuntime = engine_v11 compatibility export for historical worker consumers only
heartbeat_runtime.CarrierHeartbeatRuntime = explicit engine_v12 production carrier export
heartbeat_runtime.worker_runtime.WorkerCoordinator = separate worker/control-plane runtime
scripts/run_heartbeat_runtime.py = carrier-only runner
scripts/run_worker_runtime.py = independently supervised worker runner
scripts/install_sovereign_heartbeat_service.py = materializes and supervises carrier + worker processes separately
scripts/verify_sovereign_runtime_activation.py = node-local separated-state nine-predicate verifier
```

The worker coordinator uses `control/.worker-runtime.lock`; the carrier retains its independent heartbeat lock. A carrier process can therefore run while the worker coordinator performs a worker-runtime tick without either process falsely serializing the other through the historical combined lock.

## HB29 cutover contract

```text
legacy source: control/heartbeat-state.json
required legacy schema: stegverse.org-heartbeat-state/v1
required retained legacy epoch: 29
legacy file mutation by v12: PROHIBITED
first separated successor: HB30
separated state: control/heartbeat-carrier-runtime-state.json
carrier observation: control/heartbeat-carrier-observation.json
worker control plane: control/worker-control-plane-coordination.json
cutover receipt: receipts/heartbeat-schema-cutover/HB29.json
```

The first persistent v12 carrier cycle derives HB30 from exact retained HB29. Subsequent carrier cycles require the immutable cutover receipt; a separated carrier state without that receipt fails closed. Claim/fence/lease details remain in the worker control plane and never become heartbeat authority.

## Assignment and Master Records transition

The carrier may carry `stegverse.worker-assignment-trigger/v1` only as a non-authorizing observation. Independent worker authorization, eligibility, fencing, and cost-basis checks remain the worker coordinator's responsibility. On admitted assignment, the same packet identity transitions into the Master-Records-bound assignment record; no second transition packet is created.

```text
assignment timer unit: HB_UNIT
timer clock: WORKER_RUNTIME_INTERNAL
carrier epoch controls expiry: false
carrier presence controls expiry: false
heartbeat grants assignment authority: false
Master Records effect: STATE_TRANSITION_CUSTODY only
```

## Sovereign deployment boundary

The current user iPhone remains an allowed StegVerse physical carrier; no additional machine or third-party process host is a prerequisite. GitHub/GitHub Actions are source/validation/evidence surfaces only. Render, Vercel, Cloudflare hosted runtime, hosted inference, or another third-party scheduler/process host may not become production heartbeat authority.

Credential invariants:

```text
credential_authority: TV/TVC
credential_requirement: NONE
non_tv_tvc_secret_or_token_used: false
github_token_runtime_authority: NONE
render_production_runtime_used: false
wallet_signing_authority: USER_ONLY where applicable
broadcast_authority: USER_ONLY where applicable
```

## Authoritative files

```text
control/session-implementation-claim-2026-08-16-heartbeat-hb29-main-reconcile-197.json
docs/SOVEREIGN_HEARTBEAT_DEPLOYMENT_MIRROR_HANDOFF.md
docs/HB29_RECONCILIATION_VALIDATION.md
heartbeat_runtime/__init__.py
heartbeat_runtime/engine_v12.py
heartbeat_runtime/worker_runtime.py
schemas/heartbeat-carrier-runtime-state.schema.json
scripts/install_sovereign_heartbeat_service.py
scripts/run_worker_runtime.py
scripts/verify_sovereign_runtime_activation.py
tests/test_heartbeat_engine_v12_cutover.py
tests/test_worker_runtime_separation.py
tests/test_heartbeat_carrier_non_authority.py
tests/test_sovereign_heartbeat_service.py
tests/test_sovereign_runtime_activation_v12.py
tests/test_sovereign_runtime_activation_verifier.py
tests/test_sovereign_ephemeral_console.py
.github/workflows/heartbeat-worker-project.yml
.github/workflows/org-heartbeat.yml
.github/workflows/activate-sovereign-runtime-worker.yml
```

## Validation

Required source validation is the complete deterministic repository suite plus focused checks:

```text
python -m unittest tests.test_heartbeat_engine_v12_cutover
python -m unittest tests.test_worker_runtime_separation
python -m unittest tests.test_sovereign_heartbeat_service
python -m unittest tests.test_sovereign_runtime_activation_v12
python -m unittest tests.test_sovereign_runtime_activation_verifier
python -m unittest tests.test_sovereign_ephemeral_console
python -m unittest tests.test_heartbeat_carrier_non_authority
python -m unittest discover -v tests
python scripts/run_heartbeat_runtime.py --dry-run --cycles 1
python scripts/validate_handoff_execution_ownership.py
```

Positive validation evidence must be inspected directly. A workflow file, authored test, missing workflow run, or disposable source result is not live activation. Live activation remains node-local #122/#12 evidence.

## Cross-repository continuation

```text
local runtime/model: StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md -> COMPLETE_VALIDATED_RELEASED
formal coherent signal candidate: docs/COHERENT_SIGNAL_SPACE_TRANSITION_MANIFOLD_MIRROR_HANDOFF.md -> current-main preserved / worker-owned continuation
sovereign Base: tasks/TASK-2026-0005.json -> machine-owned real endpoint observation
StegFin phone: StegVerse-Labs/stegfin-governance#68/#60 -> current-phone exact evidence observer
Site phone evidence exporter: StegVerse-Labs/Site#289 / PR #290 -> source published; release bookkeeping separate
live heartbeat successor: StegVerse-Labs/.github#122/#12 -> resident StegVerse owner
```

MERGED INTO: `StegVerse-Labs/.github#197` for source reconciliation and `StegVerse-Labs/.github#122/#12` for live successor execution after this source lane releases.

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```yaml
task_id: HEARTBEAT-HB29-CURRENT-MAIN-RECONCILE-197
owner: claim/heartbeat-hb29-main-reconcile-197-current
state: CLAIMED_FOR_INTEGRATION
manual_execution_allowed: true
worker_registry_ref: NONE_BOUNDED_SOURCE_RECONCILIATION
collision_scope: bounded source/schema/deployment/verifier/validation files only
release_condition: deterministic PASS + merge + stale PR supersession
next_executable_action: validate current-main replacement PR and correct any failures
```

### WORKER-OWNED / DO NOT COMPETE

```yaml
task_id: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122-LIVE-MIGRATION
owner: StegVerse-Labs/.github#122/#12 resident StegVerse runtime
state: MACHINE_OWNED
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.json
collision_scope: live HB29 successor, resident carrier/worker processes, active claims/fences/leases
release_condition: directly inspectable node-local separated-runtime activation proof
next_executable_action: consume merged source reconciliation at the next admitted StegVerse execution opportunity
```

### ESCALATED / AUTHORITY-OWNED

```yaml
task_id: TV-TVC-CREDENTIAL-AUTHORITY
owner: TV/TVC
state: AUTHORITY_OWNED
manual_execution_allowed: false
worker_registry_ref: canonical TV/TVC authority surfaces
collision_scope: credential/secret/token material
release_condition: no non-TV/TVC credential path exists
next_executable_action: none unless a protected credential decision is actually required
```

### COMPLETED / SUPERSEDED

```yaml
task_id: LEGACY-HB29-RECONCILIATION-PR-LANES
state: SUPERSEDED_AFTER_REPLACEMENT_RELEASE
manual_execution_allowed: false
worker_registry_ref: NONE
collision_scope: PR #198 and divergent PR #199 only
release_condition: replacement PR #200 merges after deterministic validation
next_executable_action: close #198/#199 without merge after replacement release
```

## Current completion and archive condition

```text
developed_files: 18/18 source deliverables installed on current-main replacement branch
scaffolding_or_stubs: 0
missing_required_files: 0
validation: 2/5 required PR workflow groups PASS at this revision (Heartbeat Worker Project, Organization Heartbeat); remaining groups require rerun after validation-contract repairs
integration: 3/6 (current-main replay + coherent-signal convergence + source fixes complete; full PR validation/merge/supersession pending)
live_activation: MACHINE_OWNED / not claimed here
session_consolidation: original local-model goal and adjacent heartbeat/trade requirements all have durable owners; this source reconciliation remains unique until release
archive_dependency: replacement branch validation/merge and transfer of this session's source claim
```
