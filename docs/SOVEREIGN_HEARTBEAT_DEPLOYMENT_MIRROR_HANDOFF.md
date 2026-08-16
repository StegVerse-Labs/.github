# Sovereign Heartbeat Deployment Mirror Handoff

## Active goal

```text
goal_id: SHWP-SOVEREIGN-DEPLOYMENT-NO-THIRD-PARTY-001
repository: StegVerse-Labs/.github
canonical_branch: main
canonical_owner: StegVerse-Labs/.github#12
implementation_claim: COMPLETE_RELEASED
validation_claim: COMPLETE_RELEASED
completion_state: COMPLETE_VALIDATED_TRANSFERRED
```

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

A missing desktop, server, VM, Raspberry Pi, Render service, GitHub runner, Vercel host, Cloudflare worker, or any other physical/process host is never a heartbeat activation or release blocker.

## Canonical runtime authority

```text
production_selector: scripts/run_heartbeat_runtime.py::select_runtime
legacy_compatibility_runtime: heartbeat_runtime.engine_v11.HeartbeatRuntime
HB29_successor_runtime: heartbeat_runtime.engine_v12.HeartbeatRuntime
legacy_retained_state: control/heartbeat-state.json @ HB29
separated_carrier_state: control/heartbeat-carrier-runtime-state.json from HB30 onward
worker_control_plane: control/worker-control-plane-coordination.json + control/worker-registry.json
```

The production selector uses v12 only when canonical retained state is exactly legacy HB29 or a separated carrier state already exists. Library/test compatibility remains v11 for unrelated fixtures. GitHub and GitHub Actions may remain source/validation/evidence surfaces only. They do not own production heartbeat cadence, worker leasing, or runtime authority.

## Corrected continuity model

Heartbeat continuity is continuity of retained canonical state transitions, not a requirement that some separate machine execute a 10 ms process forever.

```text
historical retained state: HB29 / generation 29
historical state is immutable: true
wall-clock continuity required: false
wall-clock worker expiry authority: false
next valid heartbeat successor derives from retained state: true
another physical node required before successor: false
HB29 remaining the latest durable observation blocks release: false
```

When an allowed StegVerse execution opportunity associated with the current iPhone/control plane occurs, the runtime derives the successor from the retained state and emits HB30 or a later valid successor. A gap in wall-clock execution does not manufacture missing epochs and does not invalidate retained continuity.

From HB30 onward, the heartbeat carrier and worker control plane are separate: the carrier is a zero-authority regulatory reference frame, while claims, fences, leases, scheduling, and worker lifecycle remain in the control plane. HB29 remains immutable provenance instead of being rewritten into the new schema.

This aligns the heartbeat model with the project state-transition primitive: continuity is observed through related state transitions; temporal persistence is not a prerequisite for the transition primitive itself.

## Superseded blocker language

The following are no longer valid release conditions or blockers:

```text
SOVEREIGN_NODE_RUNTIME_NOT_YET_OBSERVED
DEPLOYMENT_HOST_CONTROL_PLANE_REACHABILITY
WAIT_FOR_ADDITIONAL_STEGVERSE_OWNED_OR_FEDERATED_MACHINE
continuous external process host required
advance beyond HB29 before release merely to prove another machine exists
```

Canonical blocker record:

```text
management/SHWP_RUNTIME_ACTIVATION_BLOCKER.json
schema: stegverse.runtime-activation-constraint/v1.0
current_blocker: null
release_blocked_by_physical_node_availability: false
release_blocked_by_heartbeat_epoch_remaining_at_29: false
```

## Worker ownership

Workers must not derive a task whose remedy is to acquire, activate, or wait for another physical machine. Any such task is inadmissible under this handoff.

Allowed continuation is bounded to:

```text
retain/reconstruct canonical heartbeat state
advance from the retained epoch when an allowed execution opportunity exists
preserve claim/fence uniqueness
preserve worker coordination state
emit custody evidence
fail closed on actual state-integrity defects
```

## Master Records role

Master Records remains custody and reconstruction only. It does not require an external always-on heartbeat host and does not gain execution authority from heartbeat receipts.

## Completed implementation

```text
no-third-party deployment correction: COMPLETE
additional-machine requirement: REMOVED
current iPhone physical-carrier constraint: CANONICAL
historical HB29 state: RETAINED
HB29 as release blocker: REMOVED
wall-clock continuous-process requirement: REMOVED
TV/TVC credential boundary: PRESERVED
GitHub runtime authority: NONE
```

## Release posture

There is no physical-node availability blocker remaining for the heartbeat workstream. Any future release gate must identify an actual state-integrity, code-validation, custody, or governance defect; it may not be expressed as absence of another machine or absence of a continuously running third-party process.

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```yaml
- task_id: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122-LIVE-MIGRATION-SOURCE
  execution_owner: hb29-separated-producer-source-lane
  claim_state: CLAIMED_FOR_IMPLEMENTATION
  worker_registry_ref: NONE_BOUNDED_SOURCE_CLAIM_issue_197
  manual_execution_allowed: true
  collision_scope: engine_v12 + HB29-aware production selector + materialization/validation source; live HB29 state, worker registry, claims/fences and node-local runtime state excluded
  release_condition: PR #198 merges after deterministic no-token validation and issue #197 records source release
  next_executable_action: finish source validation, merge, release bounded source claim, then hand runtime execution back to resident G18
```

### WORKER-OWNED / DO NOT COMPETE

```yaml
- task_id: SHWP-DURABLE-RUNTIME-ACTIVATION
  execution_owner: resident sovereign heartbeat / G18 fencing token 18
  claim_state: MACHINE_OWNED
  worker_registry_ref: control/worker-registry.json#SHWP-DURABLE-RUNTIME-ACTIVATION
  manual_execution_allowed: false
  collision_scope: node-local live heartbeat process, current worker claims/fences/leases, live activation receipts and post-cutover HB30+ operation
  release_condition: resident execution produces node-local separated HB30+ state plus applicable sovereign activation proof or exact fail-closed evidence
  next_executable_action: after source release, G18 runs the released selector on the sovereign execution opportunity and retains HB29 cutover evidence
```

### ESCALATED / AUTHORITY-OWNED

```yaml
- task_id: TV-TVC-CREDENTIAL-AUTHORITY
  execution_owner: StegVerse-Labs/TV + StegVerse-Labs/TVC
  claim_state: AUTHORITY_OWNED
  worker_registry_ref: canonical TV/TVC authority surfaces
  manual_execution_allowed: false
  collision_scope: protected credential admission/publication only; heartbeat carrier and control-plane source do not gain protected credential authority
  release_condition: TV/TVC remains the only credential authority and no NON-TV/TVC secret/token is introduced
  next_executable_action: evaluate only a separately admitted credential-bearing boundary if one ever arises; otherwise no action
```

### COMPLETED / SUPERSEDED

```yaml
- task_id: LEGACY-COMBINED-HEARTBEAT-PRODUCER-HB29
  execution_owner: none_after_cutover
  claim_state: SUPERSEDED_AFTER_NODE_LOCAL_HB30_CUTOVER
  worker_registry_ref: control/heartbeat-state.json#HB29_IMMUTABLE_PROVENANCE
  manual_execution_allowed: false
  collision_scope: historical combined heartbeat schema/state only
  release_condition: exact HB29 hash is bound by receipts/heartbeat-schema-cutover/HB29.json and first separated carrier state is HB30
  next_executable_action: NONE_AFTER_CUTOVER; retain HB29 as immutable provenance
```
