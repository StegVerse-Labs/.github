# StegOS Sovereign Relay Materialization Mirror Handoff

Updated: 2026-08-26

```text
goal_id: SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001
repository: StegVerse-Labs/.github
branch: dev/stegos-sovereign-relay-materialization
pull_request: #275
parent_goal: SHWP-DURABLE-RUNTIME-ACTIVATION
upstream_goal: STEGOS-SOVEREIGN-NETWORK-CAPACITY-001
state: SOURCE_IMPLEMENTED_SUCCESSOR_VALIDATION_PENDING
credential_authority: TV/TVC
github_token_runtime_authority: NONE
heartbeat_grants_execution_authority: false
physical_additional_machine_required: false
third_party_runtime_required: false
runtime_activation: false
```

## Authority and nonduplication

This lane binds the merged `StegVerse-Labs/StegOS` sovereign relay adapter to the existing `.github` WorkerCoordinator/G18 execution plane. It does not create a second HeartBeat, worker scheduler, compute authority, route authority, credential path, canonical-state authority, or transport broker.

Canonical upstream StegOS source is merge `a91838bf1c20eaacbbdada7e391aa462a862d72e` and includes `stegos/ephemeral_relay_service.py`, `stegos/sovereign_ephemeral_node_adapter.py`, and the provider-neutral ESRL runtime-dispatch controller.

Live HeartBeat/runtime authority remains `SHWP-DURABLE-RUNTIME-ACTIVATION` / G18 until its canonical owner releases or supersedes that fence. This task is independently admitted task-control work only; HeartBeat is a reference frame and grants no execution authority.

## Implemented `.github` surfaces

```text
docs/STEGOS_SOVEREIGN_RELAY_MATERIALIZATION_MIRROR_HANDOFF.md
handoffs/SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001.json
workers/stegos_sovereign_relay_bridge.py
workers/stegos_sovereign_relay_materialization_worker.py
control/worker-registry.d/stegos-sovereign-relay-materialization-001.json
control/process-worker-adapters.d/stegos-sovereign-relay-materialization-001.json
cost-basis/worker-runtime/stegos-sovereign-relay-materialization.json
control/admissible-existence-retrospective-conformance.d/stegos-sovereign-relay-materialization-001.json
control/worker-capability-profiles.json generation 15 sovereign_relay_materialization admission
tests/test_stegos_sovereign_relay_materialization_worker.py
```

The executable handoff is `HANDOFF_READY` under `INDEPENDENT_TASK_CONTROL`, requires a fresh fence greater than 21, and carries a controlled activation request. The request is explicitly **not** represented as an authentic production capacity deficit (`production_capacity_deficit_claimed: false`). Its purpose is to obtain deployment-local runtime proof of the already-admitted relay capability without broadening authority.

## Intended runtime transition

```text
HANDOFF_READY relay-materialization task
-> independent WorkerCoordinator admission
-> fresh fence > 21
-> resolve already-materialized StegOS source root
-> verify exact pinned relay adapter surface
-> consume controlled admitted relay activation request
-> invoke merged StegOS ESRL controller + SovereignEphemeralNodeAdapter
-> existing .github sovereign materializer/supervisor
-> isolated sovereign runtime root
-> bounded opaque relay process
-> local identity verification
-> bounded rendezvous probe
-> ESRL LEASE_OPEN evidence
-> durable .github receipt
```

No network credential checkout is permitted. If the pinned StegOS source is not already materialized on the sovereign carrier, the worker remains active with a machine-resolvable source-materialization requirement rather than inventing another host or credential path.

## Validation progress

PR #275 initially exposed and repaired three source-integration defects rather than hiding them:

```text
run 33011119581: executable handoff rejected because policy_version and terminal_when were absent -> REPAIRED
run 33011207117: new tests used pytest while repository CI uses unittest; AE retrospective classification absent -> BOTH REPAIRED
```

At source head `e2c45f896931ea74ff654334e9e6b842b60ac102`:

```text
Validate organization control plane run 33011459601: SUCCESS
Sovereign Runtime Worker validation run 33011459565: SUCCESS
MCP Activation Binding validation run 33011459669: SUCCESS
Heartbeat Worker Project run 33011459574: new relay tests PASS; executable handoffs PASS; AE retrospective PASS; one unrelated concurrent heartbeat-identifier test failed on the then-current PR merge base
```

The concurrent heartbeat-identifier expectation has since been corrected on `main` to preserve the legacy machine `reference_frame` while adding the Base36 display alias. This handoff-only successor commit intentionally triggers validation against the current main merge base before merge. No success is claimed until current-head repository-owned validation passes.

## Completion predicates

Source completion requires the worker, source resolver, process-adapter registration, worker-registry fragment, executable handoff, capability profile, cost basis, AE classification, and tests to be merged with repository-owned validation.

Runtime completion requires a deployment-local execution under an admitted fresh fence that observes all of:

```text
stegos source root resolved and exact required source surfaces present
runtime request admitted
credential_authority = TV/TVC
credential material absent
third-party runtime absent
sovereign runtime materialized
relay process started
local identity verified
bounded rendezvous verified
ESRL lease_state = LEASE_OPEN
route_admitted = false
outbound_egress_executed = false
canonical_transition_committed = false
```

A hosted CI pass, fake process/socket test, source merge, or controlled activation request does not satisfy runtime completion.

## Downstream

After authentic `LEASE_OPEN`, prove durable Node-KV identity continuity across teardown/recreation. Route admission, outbound ESRL EGRESS, TV/TVC mandate/broker execution, far-side transport evidence, durable return carrier, Interlock ingestion, verified-work compensation, and settlement remain separate downstream governed transitions.

## Completion accounting

```text
source files/modules required by this lane: 10/10 installed
known scaffolding/stubs in this lane: 0
source integration validation: successor validation pending
runtime LEASE_OPEN: pending deployment-local machine execution
Node-KV teardown/recreation continuity: pending after LEASE_OPEN
```
