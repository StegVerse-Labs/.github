# SV-DN-1 Sovereign Execution Chain Mirror Handoff

## Canonical scope

```text
goal_id: SV-DN1-SOVEREIGN-EXECUTION-CHAIN-001
repository: StegVerse-Labs/.github
branch: feature/sv-dn1-sovereign-execution-chain
canonical product owner: StegVerse-org/stegverse-demo-suite
canonical product handoff: docs/SV_DN1_DOUBLE_INTERLOCK_MIRROR_HANDOFF.md
credential_authority: TV/TVC
github_token_runtime_authority: NONE
heartbeat_authority: REFERENCE_ONLY
authority_effect: NONE_ORCHESTRATION_ONLY
```

## Goal

Turn the already-merged SV-DN-1 machine tasks into one executable, non-hosted sovereign first-round progression that can consume a single admitted resident execution opportunity without requiring a persistent third-party scheduler or a second user machine.

The chain owns orchestration only:

```text
SV-DN1-SOURCE-MATERIALIZATION-001
-> SV-DN1-RESIDENT-OBSERVER-001
-> SV-DN1-INTR-RUNTIME-001
-> SV-DN1-SDK-FIRST-ROUND-001
```

Each task retains its own canonical WorkerCoordinator claim/fence, authority ceiling, network boundary, receipts, and completion semantics. This chain grants none of those authorities.

## Source-of-truth order

1. `docs/SV_DN1_SOVEREIGN_EXECUTION_CHAIN_MIRROR_HANDOFF.md`
2. `docs/SV_DN1_SOURCE_MATERIALIZATION_MIRROR_HANDOFF.md`
3. `docs/SV_DN1_RESIDENT_OBSERVER_MIRROR_HANDOFF.md`
4. `docs/SV_DN1_INTR_RUNTIME_MIRROR_HANDOFF.md`
5. `docs/SV_DN1_SDK_FIRST_ROUND_MIRROR_HANDOFF.md`
6. `heartbeat_runtime/worker_runtime.py`
7. `scripts/run_worker_runtime.py`
8. `scripts/refresh_sovereign_worker_runtime_source.py`
9. live runtime registry, bound-state receipts, and source roots

Newer authentic runtime evidence overrides this document.

## Admission correction already merged

PR #343 merged the independent-task-control and dependency correction:

```text
merge_commit: 75fbb638a8003d42517620cc95b383070ea3b15e
organization control plane run 33137868295: PASS
heartbeat worker validation run 33137868303: PASS
```

Canonical dependency contract:

```text
SOURCE MATERIALIZATION
  dependencies: []

RESIDENT OBSERVER
  dependencies:
    - SV-DN1-SOURCE-MATERIALIZATION-001

ROUTE-SPECIFIC InTr
  dependencies:
    - SV-DN1-RESIDENT-OBSERVER-001

SDK FIRST ROUND
  dependencies:
    - SV-DN1-INTR-RUNTIME-001
```

All four registry fragments are admitted under:

```text
authority_domain: INDEPENDENT_TASK_CONTROL
claim_state: AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM
fresh_fence_required: true
minimum_fencing_token_exclusive: 22
carrier_trigger_required: false
heartbeat_grants_execution_authority: false
```

WorkerCoordinator's existing dependency gate only releases a child when every declared dependency is exactly `COMPLETED`.

## Runtime execution model

The chain MAY execute only on an actual StegVerse-owned/federated resident process surface that already has the separated carrier reference materialized.

It MUST reject:

- GitHub Actions;
- Render;
- Vercel;
- Cloudflare hosted workers/pages;
- arbitrary hosted CI;
- GitHub/provider credentials;
- fabricated sovereign-node declarations.

The chain does not require a continuous process. It uses targeted one-shot WorkerCoordinator cycles:

```text
python scripts/run_worker_runtime.py --task-id <task-id>
```

This preserves the current architecture:

- HeartBeat reference does not grant authority;
- WorkerCoordinator independently evaluates task admission;
- each task receives a fresh fence;
- unrelated task execution and carrier packets are suppressed in targeted mode;
- GitHub Actions remains validation-only.

## Local source refresh

A resident may refresh static WorkerCoordinator source from an already-local canonical checkout before execution:

```text
scripts/refresh_sovereign_worker_runtime_source.py
```

Refresh:

- performs no network fetch;
- acquires no credential;
- preserves mutable runtime state;
- does not overwrite claims/fences/receipts;
- copies registry and process-adapter fragments;
- does not itself execute a task.

## Step completion verification

The orchestrator must not rely only on process return code.

After each targeted cycle it must re-read the canonical mutable worker registry and require the task state to be `COMPLETED`.

It must also verify the task-specific durable receipt:

```text
SV-DN1-SOURCE-MATERIALIZATION-001
  ~/.stegverse/state/sv-dn1-source-materialization/receipts/latest.json
  transition_id = SV_DN1_EXACT_SOURCE_MATERIALIZATION_COMPLETE

SV-DN1-RESIDENT-OBSERVER-001
  ~/.stegverse/state/sv-dn1-resident-observer/receipts/latest.json
  transition_id = SV_DN1_RESIDENT_SOURCE_CAPTURE_COMPLETE

SV-DN1-INTR-RUNTIME-001
  ~/.stegverse/state/sv-dn1-intr-runtime/receipts/latest.json
  route_id = SV-DN-1-HF-PUBLIC
  state = COMPLETE
  destination_validation = PASS
  lineage_verified = true

SV-DN1-SDK-FIRST-ROUND-001
  ~/.stegverse/state/sv-dn1-sdk-first-round/receipts/latest.json
  transition_id = SV_DN1_FIRST_PRODUCTION_ROUND_ANALYZED
```

If a task returns to `HANDOFF_READY`, becomes `BLOCKED`, or lacks the required durable receipt, the chain stops. It never skips a predecessor or fabricates completion.

## Production source roots

The SDK first-round worker requires exact local canonical roots:

```text
STEGVERSE_SDK_SOURCE_ROOT
STEGVERSE_STEGCORE_SOURCE_ROOT
STEGVERSE_CORE_LITE_SOURCE_ROOT
STEGVERSE_MASTER_RECORDS_SOURCE_ROOT
```

The orchestrator may forward these non-secret locators but may not invent or remotely acquire private repository credentials.

Current public/private source posture:

```text
StegVerse-org/StegVerse-SDK: public
Data-Continuation/core-lite: public
StegVerse-Labs/StegCore: private
master-records/orchestration: private
```

Private source materialization remains within TV/TVC repository-broker authority or already-local sovereign source. The chain must stop at the exact missing source predicate rather than bypass TV/TVC.

## Resident request bridge

A canonical resident request is intent only, not authority.

The chain may be requested through an additional resident request file without replacing the existing Ecosystem Chat request. A resident request consumer may invoke this chain only after local source refresh and still relies on the four task handoffs for actual claim/fence/network/execution authority.

The request must state:

```text
request_granted_authority: false
heartbeat_grants_execution_authority: false
github_token_required: false
credential_authority: TV/TVC
second_machine_required: false
```

## Actual sovereign execution boundary

At this time repository evidence does not prove that a task-capable sovereign resident process is currently executing this chain.

The canonical repository retains:

```text
control/heartbeat-live-status.json:
  heartbeat protocol = ACTIVE_PROTOCOL_VERIFIED

control/worker-runtime-state.json:
  last durable mode = CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION
```

Heartbeat existence therefore must not be confused with worker execution.

Actual completion requires a resident process to emit fresh WorkerCoordinator claim/fence and task receipts. Source merge, hosted CI, or chat execution cannot substitute.

## Completion

Chain completion transition:

`SV_DN1_SOVEREIGN_FIRST_ROUND_CHAIN_COMPLETE`

It requires all four tasks `COMPLETED` with their exact durable receipts and the final first-round receipt proving:

```text
sdk_admission: SDK_ADMITTED
master_records_custody_status: RECORDED
replay_consequence_reexecuted: false
reconstruction_consequence_reexecuted: false
first_round_analysis: ANALYZED
dashboard_generated: true
dashboard_publicly_hosted: false
```

Public hosting remains a separate repository/Pages publication gate.

## Current state

```text
independent-task-control correction: MERGED / PASS
source worker: MERGED
resident worker: MERGED
InTr worker: MERGED
SDK first-round worker: MERGED
single-opportunity sovereign chain orchestrator: IMPLEMENTING
resident request bridge: IMPLEMENTING
authentic chain execution receipt: NOT OBSERVED
public live dashboard: NOT PUBLISHED
```

## Archive readiness

Once this chain source is merged, every machine-executable SV-DN-1 first-round step will have a durable non-hosted execution path. Product activation still depends on an authentic sovereign execution opportunity and exact private canonical source availability.
