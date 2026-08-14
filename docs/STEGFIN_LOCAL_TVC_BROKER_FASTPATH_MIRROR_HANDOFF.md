# StegFin Local TVC Broker Fast-Path Mirror Handoff

## Authority

This scoped handoff is subordinate to `handoffs/STEGFIN-CONTINUITY-CARRIER-007.json` and `StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md`. It changes transport readiness only; it grants no credential, trade, signing, broadcast, provider-secret, or settlement authority.

```text
goal_id: STEGFIN-LOCAL-TVC-BROKER-FASTPATH-009
parent_goal: STEGFIN-BASE-ROUNDTRIP-001
repository: StegVerse-Labs/.github
branch: fix/stegfin-local-tvc-broker-fastpath
canonical_worker: workers/stegfin_continuity_carrier_worker_v3.py
adapter: process:stegfin-continuity-carrier-v1
credential_authority: TV/TVC
wallet_signing_authority: USER_ONLY
broadcast_authority: USER_ONLY
github_token_required: false
```

## Defect

The canonical continuity runner already accepts either an HTTPS TV/TVC broker endpoint or an absolute same-host Unix broker socket, but the registered worker required `TVC-CAPABILITY-RUNTIME-002` HTTPS primary-runtime readiness before it would even inspect the same-host socket. That made the HTTPS exposure path a universal hard dependency even when the canonical private TV/TVC broker was already locally available.

## Fix

`workers/stegfin_continuity_carrier_worker_v3.py` now selects a live absolute Unix socket only when it is an actual Unix socket. On that path it preserves the old worker's exact TVC source validation, bypasses only the HTTPS runtime-observer gate, and then executes the existing `run_continuity_pretrade.py` against the real socket. The continuity runner therefore performs the actual provider-operation attempt; a dead, invalid, or denying socket fails closed.

If no local Unix socket is available, v3 delegates unchanged to the existing v2 -> primary-runtime-observer path.

## Security boundary

```text
non-TV/TVC secret/token accepted: false
GitHub token allowlisted: false
provider API key exported: false
wallet key accepted: false
signing: USER_ONLY
broadcast: USER_ONLY
carrier grants execution authority: false
```

No synthetic HTTP probe receipt is persisted and no claim is made that `tvc.stegverse.org` is observable when the Unix fast path is used. The local transport readiness record is explicitly `READY_LOCAL_TV_TVC_UNIX_BROKER_BOUND` and has authority effect `TRANSPORT_READINESS_ONLY`.

## Validation

Required validation:

```text
python -m unittest -v tests.test_stegfin_continuity_local_broker_fastpath
complete deterministic repository suite
executable handoff validation
no-token workflow proof
```

## Collision state

At implementation start the registered continuity task was `HANDOFF_READY`, `claim_id=null`, and its worker was `AVAILABLE`; there was no active continuity execution claim. The implementation changes adapter/source behavior only and does not acquire the trade collision scope.

## Release condition

Merge only after repository validation passes. After merge, machine execution may use either:

```text
A) same-host canonical TV/TVC Unix broker socket
OR
B) existing HTTPS primary runtime + TVC-CAPABILITY-RUNTIME-002 READY receipt
```

Both paths converge on the same terminal predicate:

```text
WALLET_HANDOFF_READY
credential_authority=TV/TVC
non_tv_tvc_secret_or_token_used=false
provider_secret_exported=false
signed=false
broadcast=false
```

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```yaml
- task_id: STEGFIN-LOCAL-TVC-BROKER-FASTPATH-009-SOURCE
  execution_owner: explicitly claimed nonconflicting repository implementation/validation lane
  manual_execution_allowed: true
  worker_registry_ref: control/worker-registry.d/stegfin-continuity-carrier-007.json
  collision_scope: source-only adapter/worker/test/handoff changes while no continuity execution claim is active
  release_condition: PR validation passes and source is merged, or the source claim is released/superseded
  next_executable_action: validate and merge the source-only fast-path implementation without acquiring the trade collision scope
```

### WORKER-OWNED / DO NOT COMPETE

```yaml
- task_id: STEGFIN-CONTINUITY-CARRIER-007
  execution_owner: stegfin-continuity-carrier-worker
  manual_execution_allowed: false
  worker_registry_ref: control/worker-registry.d/stegfin-continuity-carrier-007.json
  collision_scope: collision-safe trade claim, Inventory N, TV/TVC provider operation, quote/allowance/simulation, and WALLET_HANDOFF_READY production receipt
  release_condition: WALLET_HANDOFF_READY or fail-closed terminal worker receipt; yield if a resident equivalent trade lineage owns the scope first
  next_executable_action: after source merge, machine scheduler selects the local Unix broker path when present or the existing HTTPS observer path otherwise
```

### ESCALATED / AUTHORITY-OWNED

```yaml
- task_id: TV-TVC-PROVIDER-OPERATION-AUTHORITY
  execution_owner: TV/TVC runtime/vault authority
  manual_execution_allowed: false
  worker_registry_ref: StegVerse-Labs/TVC/tasks/TVC-CAPABILITY-RUNTIME-002.json
  collision_scope: provider credential semantics, vault socket authority, provider operation execution, and HTTPS primary-runtime authority
  release_condition: TV/TVC exposes an authorized local Unix broker or the canonical governed HTTPS runtime and retains provider secrets inside the vault boundary
  next_executable_action: TV/TVC services the selected canonical transport; no consumer/session credential substitutes
```

### COMPLETED / SUPERSEDED

```yaml
- task_id: STEGFIN-HTTPS-PRIMARY-RUNTIME-AS-UNIVERSAL-HARD-DEPENDENCY
  execution_owner: NONE
  manual_execution_allowed: false
  worker_registry_ref: control/worker-registry.d/stegfin-continuity-carrier-007.json
  collision_scope: historical orchestration assumption only
  release_condition: superseded when the validated v3 fast path is merged
  next_executable_action: NONE_AFTER_MERGE
```
