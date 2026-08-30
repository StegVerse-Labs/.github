# SV-DN-1 Sovereign Execution Chain Mirror Handoff

## Canonical scope

```text
goal_id: SV-DN1-SOVEREIGN-EXECUTION-CHAIN-001
repository: StegVerse-Labs/.github
branch: main
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
-> SV-DN1-PRODUCTION-SOURCE-PREP-001
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

PRODUCTION SOURCE PREP
  dependencies:
    - SV-DN1-INTR-RUNTIME-001

SDK FIRST ROUND
  dependencies:
    - SV-DN1-INTR-RUNTIME-001
    - SV-DN1-PRODUCTION-SOURCE-PREP-001
```

All five SV-DN-1 registry fragments are admitted under:

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

SV-DN1-PRODUCTION-SOURCE-PREP-001
  ~/.stegverse/state/sv-dn1-production-source-prep/receipts/latest.json
  schema = stegverse.sv-dn1.production-source-prep-receipt/v2
  transition_id = SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE
  source_identity_scheme = sha256-content-manifest
  exactly four canonical source_identities are present
  exactly four canonical source_roots are present
  source_root_env agrees with source_roots component-by-component
  migration_anchors_verified = true
  network_source_fetch_performed = false
  github_platform_required = false
  credential_used = false
  github_token_used = false
  repository_writeback_performed = false
  sdk_admitted = false

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

Source preparation is platform-neutral. Any of the four canonical components may be satisfied by an already-local verified root supplied through its non-secret `STEGVERSE_*_SOURCE_ROOT` locator, by a root already present under the canonical materialization tree, or by a local content-addressed StegVerse source package. The source-preparation worker performs no network acquisition and does not require GitHub or the repository broker merely to recognize already-local source. If a component is genuinely absent from all admitted local surfaces, it stops `HANDOFF_READY` and names the required local package location.

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

It requires all five tasks `COMPLETED` with their exact durable receipts and the final first-round receipt proving:

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
production source prep worker: MERGED / VALIDATED
SDK first-round worker: MERGED
single-opportunity sovereign chain orchestrator: MERGED
resident request bridge: MERGED
authentic chain execution receipt: NOT OBSERVED
public live dashboard: NOT PUBLISHED
```

## Merge and validation evidence

```text
PR #348: MERGED
merge_commit: a45095d2c2099b9318915410e78a4615b4dc68e6
validated_head: 34234237264e96c7da8226d19ff4a7c43e18de09
heartbeat worker validation run 33138330575 / job 98743294611: PASS
organization control plane run 33138330592 / job 98743294652: PASS
complete deterministic repository suite: PASS
hosted-environment rejection: PASS
credential scrubbing: PASS
existing-claim no-steal behavior: PASS
sequential dependency progression: PASS
durable receipt validation: PASS
resident request non-authority/retry behavior: PASS
```

The first-round chain now includes explicit canonical production-source preparation before SDK execution. Missing private roots are a machine-owned TVC spool dependency rather than an implicit local-path prerequisite. No authentic chain execution receipt has been observed yet.

## Production source preparation integration evidence

```text
PR #371: MERGED
merge_commit: f488e70fca67e80fa6b674ee7380b0e04c5000f7
heartbeat worker validation run 33228272533: PASS
organization control plane run 33228272505: PASS
```

The one-shot resident chain now advances through five independently fenced tasks. The SDK step cannot execute until the production-source-preparation task is COMPLETED and has exposed exact non-secret local roots for SDK, StegCore, Core-Lite, and Master Records.

## TVC private-source prerequisite execution path

The source-preparation stage now has a current-head machine validation carrier for its upstream TVC broker:

```text
TVC broker PR #92 expected head: ce1d4a31f5cfc65ee59af52f821336e0859c0fbd
.github validation carrier PR #384: MERGED
independent validation request: ISSUED
authentic governed PASS: NOT OBSERVED
broker admission: NOT COMPLETE
private source materialization: NOT OBSERVED
```

This means the remaining private-source gate is now an execution/evidence boundary rather than missing control-plane wiring.

## Archive readiness

Once this chain source is merged, every machine-executable SV-DN-1 first-round step will have a durable non-hosted execution path. Product activation still depends on an authentic sovereign execution opportunity and exact private canonical source availability.


## v2 production-source receipt correction — 2026-08-30

The sovereign chain previously retained the obsolete pre-v2 durable-receipt predicates `public_source_roots_verified`, `private_source_roots_verified`, and `runtime_anchor_blobs_verified`. Those predicates diverged from the already-merged platform-neutral production-source worker and would have rejected an otherwise valid v2 receipt.

The chain now validates the canonical v2 source identity/root contract directly and forwards the four verified non-secret locators to the SDK first-round worker only after that validation succeeds. This is a validation-shape correction only; it grants no source acquisition, credential, repository, SDK, governance, or publication authority.
