# Sovereign Heartbeat Deployment Mirror Handoff

Updated: 2026-08-16T16:33:00-05:00

## Active goal

```text
goal_id: HEARTBEAT-HB29-CURRENT-MAIN-RECONCILE-197
parent_goal: SHWP-SOVEREIGN-DEPLOYMENT-NO-THIRD-PARTY-001
originating_goal: close retained legacy HB29 under the released carrier/control-plane separation, activate the current canonical carrier schema when an allowed StegVerse execution opportunity exists, and never reintroduce combined heartbeat worker authority
repository: StegVerse-Labs/.github
branch: claim/heartbeat-hb29-main-reconcile-197
canonical_issue: StegVerse-Labs/.github#197
parent_issue: StegVerse-Labs/.github#122
canonical_live_owner: StegVerse-Labs/.github#122/#12 resident StegVerse control plane
implementation_claim: CLAIMED_FOR_INTEGRATION_RECONCILIATION
validation_claim: SAME_BOUNDED_SOURCE_LANE
claim_created_at: 2026-08-16T16:33:00-05:00
claim_release_condition: stale v11 deployment binding is removed, installer/materialization selects current carrier v12 and separately materializes worker runtime without combining authority, deterministic validation passes, PR merges, and live migration remains explicitly assigned to the canonical resident owner
credential_authority: TV/TVC
non_tv_tvc_secret_or_token_allowed: false
github_token_runtime_authority: NONE
render_production_runtime_allowed: false
```

This is a distinct integration/reconciliation role. It does **not** claim the live heartbeat producer, `control/heartbeat-state.json`, current worker registry state, active claims/fences/leases, or resident process authority. Those remain worker-owned under #122/#12. It corrects source/deployment drift on current `main` so the released installer cannot reactivate the obsolete combined v11 runtime after `main` already separated carrier and worker coordination.

## Physical carrier constraint

The current user's iPhone is the sole permitted user physical carrier for this workstream.

```text
sole_permitted_user_physical_carrier: CURRENT_USER_IPHONE
additional_physical_machine_required: false
additional_physical_machine_allowed: false
third_party_machine_required: false
third_party_process_host_required: false
wait_for_other_machine: prohibited
search_for_other_machine: prohibited
```

A missing desktop, server, VM, Raspberry Pi, Render service, GitHub runner, Vercel host, Cloudflare worker, or other third-party process host is never a heartbeat activation blocker.

## Canonical runtime split on current main

Current `main` is authoritative over older deployment prose:

```text
heartbeat_runtime.engine_v12.HeartbeatRuntime = non-authorizing carrier
heartbeat_runtime.CarrierHeartbeatRuntime = canonical carrier export
heartbeat_runtime.worker_runtime.WorkerCoordinator = separate worker lifecycle coordinator
scripts/run_heartbeat_runtime.py = carrier-only runner
scripts/run_worker_runtime.py = worker/control-plane runner
heartbeat_runtime.HeartbeatRuntime = temporary v11 compatibility alias only; not production deployment target
```

The prior deployment handoff and `scripts/install_sovereign_heartbeat_service.py` still named `heartbeat_runtime.engine_v11.HeartbeatRuntime` as the canonical deployed runtime. That is source/deployment drift and is the precise defect owned by this reconciliation lane.

## HB29 continuity model

Heartbeat continuity is continuity of retained canonical state transitions, not an always-running wall-clock process.

```text
historical retained state: HB29 / generation 29
historical state is retained provenance: true
wall-clock continuity required: false
wall-clock worker expiry authority: false
next valid carrier successor derives from retained state: true
another physical node required before successor: false
heartbeat grants execution authority: false
worker lifecycle authority is separate: true
```

The current-main source reconciliation may validate disposable HB29 successor behavior, but it may not mutate the repository/live HB29 snapshot. Actual HB30 or later durable successor evidence is emitted only by the canonical resident StegVerse execution owner when an allowed execution opportunity exists.

## Authority invariants

```text
heartbeat carrier authority effect: NONE
worker/control-plane authority source: independent admitted worker task state
Master Records role: custody/reconstruction only
credential authority: TV/TVC
non-TV/TVC runtime secret/token: PROHIBITED
GitHub production runtime authority: NONE
Render production runtime: PROHIBITED
Vercel production runtime: PROHIBITED
Cloudflare production runtime: PROHIBITED
third-party scheduler/process host: PROHIBITED AS PRODUCTION AUTHORITY
```

## Authoritative files for this reconciliation

```text
docs/SOVEREIGN_HEARTBEAT_DEPLOYMENT_MIRROR_HANDOFF.md
scripts/install_sovereign_heartbeat_service.py
tests/test_sovereign_heartbeat_service.py
control/session-implementation-claim-2026-08-16-heartbeat-hb29-main-reconcile-197.json
```

Potential validation-only additions must remain bounded to this source integration role. `control/heartbeat-state.json`, `control/worker-registry.json`, `control/heartbeat-subsignals.json`, `authorizations/**`, `workers/**`, and live activation receipts are prohibited mutation surfaces for this claim.

## Superseded/merged work

PR #198 (`feat/heartbeat-hb29-cutover-197`) was created against an older base and attempted its own competing v12 cutover implementation. Current `main` subsequently acquired the canonical carrier-only v12 and separate worker coordinator. The unique requirement from #198 that remains valid is preserved here: retained HB29 must not be silently treated as worker authority, and the next live carrier successor must be directly evidenced by the canonical owner. The competing source implementation is to be closed/superseded after this current-main reconciliation is merged.

MERGED INTO: `StegVerse-Labs/.github#122`, `StegVerse-Labs/.github#197`, this handoff, and the current-main carrier/worker split.

## Validation commands

```text
python -m unittest tests.test_sovereign_heartbeat_service
python -m unittest tests.test_heartbeat_carrier_non_authority
python scripts/run_heartbeat_runtime.py --dry-run --cycles 1
python scripts/run_worker_runtime.py --dry-run --cycles 1
```

Validation must prove that deployment materialization names carrier v12 as the heartbeat carrier, includes the separate worker runner, does not bind v11 as production carrier authority, carries no non-TV/TVC credential requirement, and does not claim CI/disposable execution as live activation.

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```yaml
- task_id: HEARTBEAT-HB29-CURRENT-MAIN-RECONCILE-197
  execution_owner: claim/heartbeat-hb29-main-reconcile-197
  claim_state: CLAIMED_FOR_INTEGRATION_RECONCILIATION
  worker_registry_ref: NONE_BOUNDED_SOURCE_RECONCILIATION
  manual_execution_allowed: true
  collision_scope: installer/materialization/tests/handoff only; live heartbeat state and worker authority excluded
  release_condition: deterministic source validation PASS + PR merge + obsolete PR #198 superseded
  next_executable_action: replace stale v11 deployment binding with carrier-v12 plus separate worker materialization and validate
```

### WORKER-OWNED / DO NOT COMPETE

```yaml
- task_id: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122-LIVE-MIGRATION
  execution_owner: StegVerse-Labs/.github#122/#12 resident StegVerse runtime
  claim_state: MACHINE_OWNED
  worker_registry_ref: control/worker-registry.json
  manual_execution_allowed: false
  collision_scope: live HB29 successor, active claims/fences/leases, resident processes, production carrier operation
  release_condition: node/current-carrier observable successor receipt under current separated schema
  next_executable_action: consume merged deployment reconciliation at next admitted StegVerse execution opportunity
```

### ESCALATED / AUTHORITY-OWNED

```yaml
- task_id: TV-TVC-CREDENTIAL-AUTHORITY
  execution_owner: TV/TVC
  claim_state: AUTHORITY_OWNED
  worker_registry_ref: canonical TV/TVC authority surfaces
  manual_execution_allowed: false
  collision_scope: protected credential/secret/token material only
  release_condition: no non-TV/TVC runtime credential path exists
  next_executable_action: none unless a protected credential decision is actually required
```

### COMPLETED / SUPERSEDED

```yaml
- task_id: LEGACY-ENGINE-V11-COMBINED-PRODUCTION-BINDING
  execution_owner: NONE_AFTER_RECONCILIATION
  claim_state: SUPERSEDED_BY_CURRENT_MAIN_CARRIER_WORKER_SPLIT
  worker_registry_ref: NONE
  manual_execution_allowed: false
  collision_scope: old installer canonical-runtime declaration only
  release_condition: installer/tests no longer describe engine_v11 as production heartbeat carrier
  next_executable_action: NONE
```

## Incomplete work and archive condition

This source reconciliation remains active until the stale installer binding is corrected, validated and merged and PR #198 is superseded. Live HB29→successor observation remains separately machine-owned and is not fabricated by this lane. The complete session is not archive-ready while this unique reconciliation and the active Site phone-evidence publication lane remain unfinished.

```text
developed files: 1/4 at claim creation
validation: 0/4
integration: 0/3
live activation: canonical resident owner only
session consolidation: current-main convergence recorded; execution transfer incomplete until merge
```
