# Cross-Framework Current-Basis v0.4 Resident Run Mirror Handoff

Updated: 2026-08-29
Repository: `StegVerse-Labs/.github`
Issue: #468
Branch: `feat/current-basis-v04-resident-run-465`
Parent handoff: `docs/ORG_MIRROR_HANDOFF.md`

## Goal

Execute the exact frozen cross-framework current-basis v0.4 StegVerse side on the existing sovereign resident WorkerCoordinator using already-local canonical sources. Do not create a second evaluator, runtime, scheduler, heartbeat, credential authority, or source-fetch path.

```text
test_id: cross-framework-current-basis-001
vector_schema: stegverse.cross-framework-current-basis-vector.v0.4
frozen_manifest_sha256: 07a08496c21b31f70f6f45ef731aa5f6b2522a6fc8f67f2d0a4c2b6fceda7a3f
frozen_manifest_git_blob_sha1: 59d818a15fc7be732c97dae7d2174d8cfe9a7bab
SDK freeze/review provenance: StegVerse-org/StegVerse-SDK#94
SDK execution integration: StegVerse-org/StegVerse-SDK#99
StegCore native derivation: StegVerse-Labs/StegCore#161 / PR #162
```

## Test semantics

Absent explicitly supplied prior-state data, S0 is the declared initial testing state and requires no historical receipt. Material policy-basis change is not itself proof of invalidation or architecture-native non-currentness. The common v0.4 vector stays frozen and neutral. Canonical StegCore independently derives its native request.

The S0->S1 receipt is post-observation evidence. The resident task may terminalize only after the SDK harness records S1 observation, the post-observation transition receipt, Master Records exact-run custody, replay custody, and reconstruction custody in `RUN_COMPLETE.json`.

## Authority boundary

```text
execution owner: existing sovereign WorkerCoordinator
heartbeat grants execution authority: false
credential authority: TV/TVC
GitHub token runtime authority: NONE
network source fetch: PROHIBITED
source mutation: PROHIBITED
second user machine required: false
GitHub Actions runtime authority: NONE
publication authority: NONE
external consequence: false
```

## Planned machine surfaces

```text
handoffs/SHWP-CROSS-FRAMEWORK-CURRENT-BASIS-V04-001.json
control/worker-registry.d/cross-framework-current-basis-v04-001.json
control/process-worker-adapters.d/cross-framework-current-basis-v04-001.json
control/task-vectors/SHWP-CROSS-FRAMEWORK-CURRENT-BASIS-V04-001.json
workers/cross_framework_current_basis_v04_worker.py
control/resident-execution-request.d/cross-framework-current-basis-v04-001.json
scripts/consume_cross_framework_current_basis_v04_request.py
tests/test_cross_framework_current_basis_v04_worker.py
tests/test_cross_framework_current_basis_v04_resident_request.py
```

## Required local source inputs

The worker must locate already-local clean repositories through non-secret path hints or canonical local-source locations:

```text
StegVerse-org/StegVerse-SDK
StegVerse-Labs/StegCore
Data-Continuation/core-lite
master-records/orchestration
```

It must fail closed unless the exact required SDK execution source and StegCore native-derivation source are present. It must not clone, fetch, pull, or acquire repository credentials.

## Completion gates

```text
specialized handoff: CREATED
worker/handoff/registry/adapter: IMPLEMENTED_ON_BRANCH
resident request/consumer/dispatcher wiring: IMPLEMENTED_ON_BRANCH
source refresh materialization wiring: IMPLEMENTED_ON_BRANCH
focused tests: IMPLEMENTED_ON_BRANCH
hosted source validation: PENDING
merge: PENDING
authentic resident request consumption: NOT OBSERVED
authentic StegVerse independent run: NOT OBSERVED
RUN_COMPLETE.json: NOT OBSERVED
result packet publication: NOT YET ELIGIBLE
```


## Implemented branch state

```text
worker: workers/cross_framework_current_basis_v04_worker.py
executable handoff: handoffs/SHWP-CROSS-FRAMEWORK-CURRENT-BASIS-V04-001.json
registry: control/worker-registry.d/cross-framework-current-basis-v04-001.json
adapter: control/process-worker-adapters.d/cross-framework-current-basis-v04-001.json
task vector: control/task-vectors/SHWP-CROSS-FRAMEWORK-CURRENT-BASIS-V04-001.json
resident request: control/resident-execution-request.d/cross-framework-current-basis-v04-001.json
consumer: scripts/consume_cross_framework_current_basis_v04_request.py
dispatcher registration: scripts/dispatch_resident_execution_requests.py
fresh materialization: scripts/install_sovereign_heartbeat_service.py
native bootstrap required-source registration: scripts/bootstrap_sovereign_runtime.py
local source refresh carriage: scripts/refresh_sovereign_worker_runtime_source.py
focused tests:
  tests/test_cross_framework_current_basis_v04_worker.py
  tests/test_cross_framework_current_basis_v04_resident_request.py
```

The worker writes the exact run only beneath resident runtime `receipts/cross-framework-current-basis-v04/`; the canonical source repositories remain read-only. Nonterminal attempts remain retryable. Only a WorkerCoordinator result of `COMPLETED` backed by the exact `RUN_COMPLETE.json` makes the resident request exactly-once terminal.
