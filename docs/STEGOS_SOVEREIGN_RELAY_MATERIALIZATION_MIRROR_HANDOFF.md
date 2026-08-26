# StegOS Sovereign Relay Materialization Mirror Handoff

Updated: 2026-08-26

```text
goal_id: SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001
repository: StegVerse-Labs/.github
branch: main
pull_request: #275
merge_commit: 3c1462b603817a41dcac5ac5360b4e3b31cb3015
validated_premerge_head: 031cd9bff97b1aea56fed681e2d150f300e9dcb7
parent_goal: SHWP-DURABLE-RUNTIME-ACTIVATION
upstream_goal: STEGOS-SOVEREIGN-NETWORK-CAPACITY-001
state: SOURCE_COMPLETE_VALIDATED_MERGED_RUNTIME_HANDOFF_READY
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

## Released `.github` surfaces

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

## Released runtime transition

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

## Validation and merge evidence

PR #275 final source head `031cd9bff97b1aea56fed681e2d150f300e9dcb7` passed all repository-owned PR validations against the then-current merge base:

```text
Heartbeat Worker Project - Validation Only / No GitHub Token Authority
  run: 33011631973
  result: SUCCESS

Validate organization control plane - No GitHub Token Authority
  run: 33011631944
  result: SUCCESS

Sovereign Runtime Worker - Validation Only / No GitHub Token Authority
  run: 33011631878
  result: SUCCESS

MCP Activation Binding Validation - Non-Authorizing
  run: 33011632034
  result: SUCCESS
```

Earlier CI failures were consumed and repaired: executable-handoff policy/terminal fields, unittest compatibility, AE retrospective classification, finite cost basis, and runtime capability-profile admission. No open source defect from those failures remains in this lane.

PR #275 merged successfully as `3c1462b603817a41dcac5ac5360b4e3b31cb3015`.

## Runtime completion predicates

Source implementation, validation and merge are complete. Product/runtime completion remains a distinct deployment-local observation and requires a WorkerCoordinator execution under an admitted fresh fence that observes all of:

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

Terminal runtime evidence is:

```text
receipts/stegos-sovereign-relay/SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001.json
state: COMPLETED
transition_id: SOVEREIGN_RELAY_LEASE_OPEN
```

A hosted CI pass, source merge, fake process/socket test, or controlled activation request does not satisfy runtime completion.

## Downstream

After authentic `LEASE_OPEN`, prove durable Node-KV identity continuity across teardown/recreation. Route admission, outbound ESRL EGRESS, TV/TVC mandate/broker execution, far-side transport evidence, durable return carrier, Interlock ingestion, verified-work compensation, and settlement remain separate downstream governed transitions.

## Completion accounting

```text
source files/modules required by this lane: 10/10 installed
known scaffolding/stubs in this lane: 0
source implementation: COMPLETE
source validation: COMPLETE
merge/release integration: COMPLETE
runtime LEASE_OPEN: PENDING MACHINE-OWNED DEPLOYMENT-LOCAL EXECUTION
Node-KV teardown/recreation continuity: PENDING AFTER LEASE_OPEN
```

## Archive condition

This source/integration lane no longer requires session-local state. Continuation is fully durable in this handoff, the executable handoff, worker registry, process adapter, and merged source. Runtime activation remains machine-owned and must not be replaced by a chat-hosted or GitHub-hosted proof.
