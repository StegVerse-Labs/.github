# Stale Heartbeat Reclamation Mirror Handoff

## Canonical scope

```text
goal_id: SHWP-STALE-HEARTBEAT-RECLAMATION-20260814
repository: StegVerse-Labs/.github
branch: main
originating_goal: a stopped heartbeat must not leave workers or claims as indefinite collision blockers; stale lifecycle history must be retained by Master Records while bounded StegFin continuity remains eligible
canonical_trade_task: StegVerse-Labs/stegfin-governance/task-state/STEGFIN-CONTINUITY-CARRIER-007.json
credential_authority: TV/TVC
github_token_runtime_authority: NONE
wallet_signing_authority: USER_ONLY
broadcast_authority: USER_ONLY
```

This handoff is scoped to stuck-carrier reclamation and does not replace `docs/ORG_MIRROR_HANDOFF.md`, the canonical heartbeat lifecycle, StegFin trade authority, TV/TVC credential authority, or Master Records custody authority.

## Finding

The ordinary worker-expiry implementation is not missing. `heartbeat_runtime/engine_v2.py::_invoke` calls `_expire` when the **next heartbeat cycle** reaches a task's `expiry_epoch`; `_expire` emits expiry history, releases the worker claim, and admits recovery when the required Master Records final report is missing.

The uncovered defect is carrier liveness: when the heartbeat process itself stops, no later epoch exists to evaluate heartbeat-relative expiry. A stale last projection can therefore remain visible indefinitely even though it must not retain perpetual collision authority over a separate continuity carrier.

## Correction — COMPLETE / VALIDATED

Canonical implementation:

```text
scripts/acquire_stegfin_continuity_claim.py
implementation commit: eb1f4fc8ba443180d27bd8d6e15d4a2737dee53f
tests/test_stegfin_continuity_claim.py
focused test commit: 835bc0703a3793eba762381163b47c37f877fbfd
```

The continuity claimant now distinguishes carrier freshness from lease history:

```text
fresh resident StegFin collision -> BLOCK
stale resident StegFin collision -> retain history, remove collision effect only
unknown heartbeat liveness timestamp -> no stale override; preserve fail-closed collision semantics
new continuity fence -> strictly greater than every observed resident fence
stale reclamation grants execution authority -> FALSE
```

The default stale threshold for this bounded continuity claim is 60 seconds. This threshold is a collision-liveness rule for the independent continuity claim; it does not rewrite the canonical heartbeat's cycle-bound task expiry model.

A stale observation creates a local continuity receipt under:

```text
~/.stegverse/continuity/receipts/stale-heartbeat/STEGFIN-CONTINUITY-CARRIER-007-HB<epoch>.json
```

The receipt preserves the projected lease history, last observed fence, heartbeat epoch, last cycle timestamp, TV/TVC authority boundary and a Master Records notification requirement before the higher-fenced continuity claim proceeds.

## Validation

```text
Heartbeat Worker Project run: 31840751012 SUCCESS
job: 94896860324 SUCCESS
anonymous checkout: PASS
GitHub credential token absent from validation process: PASS
compile: PASS
canonical JSON parse: PASS
executable handoffs: PASS
complete deterministic repository suite: PASS
heartbeat dry-run non-persistence: PASS
projection rebuild: PASS
workflow non-authorizing boundary: PASS

Organization control-plane validation run: 31840751015 SUCCESS
```

The predecessor run `31840596350` failed because older continuity-claim fixtures omitted `last_cycle_at`. That diagnostic exposed a compatibility requirement: missing liveness metadata must not create permission to override a resident collision. Commit `eb1f4fc8ba443180d27bd8d6e15d4a2737dee53f` implemented that fail-closed compatibility and the successor full-suite run passed.

## Master Records custody — COMPLETE

The directly observed HB29 history is now retained in:

```text
master-records/orchestration/custody/heartbeat-stale-reclamation/HB29-STEGFIN-CONTINUITY-20260814.json
Master Records commit: b04e0519da4687ffdc417fb2986fa15accc16a3e
Master Records lifecycle handoff update: 4eec024303f0224c15a64b07aa195e600e84f05a
```

Observed source state:

```text
heartbeat epoch: 29
last_cycle_at: 2026-08-10T20:51:11Z
max observed active-lease fence: 18
resident StegFin LIVE-ENTRY/PRETRADE lease observed in HB29 projection: FALSE
```

Therefore the HB29 snapshot itself is not a valid StegFin collision block. Master Records retains its history; it does not grant execution authority or fabricate an `AUTHORIZATION_EXPIRED` event that never occurred on a live heartbeat cycle.

## StegFin consequence

The canonical StegFin continuity task already states:

```text
hard_dependencies: []
preferred_carrier: resident sovereign heartbeat
preferred_carrier_required: false
resident_heartbeat_required: false
manual_execution_allowed: false
claim_state: MACHINE_CLAIM_ON_EXECUTION
```

Accordingly, waiting for HB29 or a resident worker completion notification is **not** a lawful universal prerequisite for `STEGFIN-CONTINUITY-CARRIER-007`.

The machine continuity worker may proceed when an authorized continuity executor exists and one of its canonical TV/TVC transports is usable:

```text
A. actual same-host TV/TVC Unix broker socket
OR
B. governed HTTPS TVC provider-operation runtime after TVC-CAPABILITY-RUNTIME-002 READY evidence
```

The continuity worker then acquires the higher-fenced claim, obtains fresh Inventory N, performs bounded pretrade preparation and stops at `WALLET_HANDOFF_READY`. Signing and broadcast remain USER_ONLY.

## Current live transport observation

Render is fallback-only and does not define production authority. Direct inspection of the existing Render TVC service shows the newest 2026-08-14 deployments as `build_failed`; therefore the HTTPS TVC route is not currently proven READY by that surface. No current tool access proves an actual same-host `/run/stegverse/vault-broker.sock` exists on an authorized continuity host.

This means HB29 is no longer the trade blocker, but a live authorized continuity carrier plus usable canonical TV/TVC transport still has to be observed before a real `WALLET_HANDOFF_READY` result can be claimed.

## Collision partition

Do not:

- create a second heartbeat or fake HB30;
- restore stale resident authority;
- use GitHub/Render credentials as TV/TVC authority;
- export provider secrets;
- sign or broadcast for the user;
- claim a trade, quote, Inventory N or wallet handoff without live receipts.

## Claim state

```text
implementation claim: control/session-implementation-claim-2026-08-14-stale-heartbeat-reclamation.json
source correction: COMPLETE_VALIDATED
Master Records notification/custody: COMPLETE
StegFin stale-HB collision dependency: REMOVED
remaining trade execution: MACHINE_OWNED / LIVE TRANSPORT + EXECUTOR OBSERVATION REQUIRED
release condition for this scoped implementation claim: update durable claim state to released after canonical StegFin continuation surfaces consume this handoff reference
```

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```yaml
- task_id: STALE-HEARTBEAT-RECLAMATION-VALIDATION
  execution_owner: explicitly claimed validation/reconciliation session only
  manual_execution_allowed: true
  worker_registry_ref: NONE
  collision_scope: read-only/source validation of already-released reclamation semantics; no live continuity claim or wallet/provider operation
  release_condition: validation evidence is recorded and claim released
  next_executable_action: no implementation action; validate only when a consumer change requires it
```

### WORKER-OWNED / DO NOT COMPETE

```yaml
- task_id: STEGFIN-CONTINUITY-CARRIER-007
  execution_owner: canonical StegFin continuity worker + TV/TVC runtime authority
  manual_execution_allowed: false
  worker_registry_ref: control/worker-registry.d/stegfin-continuity-carrier-007.json
  collision_scope: live claim acquisition, TV/TVC transport selection, Inventory N, quote/pretrade preparation and WALLET_HANDOFF_READY emission
  release_condition: machine-owned continuity run reaches terminal receipt or fail-closed owner state
  next_executable_action: machine worker executes when an authorized carrier and canonical TV/TVC transport are observable
```

### ESCALATED / AUTHORITY-OWNED

```yaml
- task_id: STALE-HEARTBEAT-AUTHORITY-COLLISION
  execution_owner: TV/TVC + Master Records + canonical runtime owner
  manual_execution_allowed: false
  worker_registry_ref: applicable owner records
  collision_scope: credential/route authority, stale-history custody and live collision disputes
  release_condition: exact canonical owner resolves or supersedes the conflict
  next_executable_action: fail closed and escalate to the exact owner
```

### COMPLETED / SUPERSEDED

```yaml
- task_id: SHWP-STALE-HEARTBEAT-RECLAMATION-20260814
  execution_owner: NONE
  manual_execution_allowed: false
  worker_registry_ref: NONE
  collision_scope: released source correction only
  release_condition: COMPLETE_VALIDATED source correction already recorded
  next_executable_action: NONE
```
