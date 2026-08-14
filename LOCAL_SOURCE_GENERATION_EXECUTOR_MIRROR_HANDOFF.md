# Local Source-Generation Executor Mirror Handoff

## Source of truth

```text
organization: StegVerse-Labs
repository: .github
branch: feat/local-source-generation-executor-144
goal_id: LOCAL-SOURCE-GENERATION-EXECUTOR-001
issue: #144
parent_goal: ADMISSIBLE-SOURCE-GENERATION-CAPABILITY-ACTIVATION-001 / #137
canonical_source_generation_capability: stegverse:capability:formalism-source-generation:v1
canonical_local_model_capability: stegverse:capability:sovereign-local-model:v1
local_model_owner: StegVerse-002/micro-node-runtime
formal_model_development_dependency: StegVerse-002/micro-node-runtime#32
credential_authority: TV/TVC
github_token_runtime_authority: NONE
non_TV_TVC_secret_or_token_allowed: false
archive_ready: false
```

This lane installs the missing executable step between an admitted owner-work manifest and the existing `admissible_source_generation_capability_worker.py` binder. It does not create source-generation authority, repository authority, credential authority, merge authority, StegGate authority, or model-output authority.

## Originating session goal

Replace the remaining descriptive local model-selection step with an actual local discovery/launch/inference/proof path and formally develop the local model so the recursive formalism/manifold build can proceed without another chat session.

Canonical sequence:

```text
owner work admitted
-> exact activation evidence observed
-> canonical local runtime discovered
-> loopback-only least-stable process launched/reused
-> exact owner source + hashes bound into request
-> bounded structured local inference
-> strict result validation
-> process teardown + receipt
-> stegverse.local-source-generation-result/v0.1
-> existing AE source-generation binder
-> exact owner source packet
-> TV/TVC repository operation
```

## Authority and activation rule

The executor MUST fail closed unless both of the following are independently evidenced as `ACTIVATED`:

```text
stegverse:capability:formalism-source-generation:v1
stegverse:capability:sovereign-local-model:v1
```

Activation evidence must include existence hash, activation proof, integration evidence, runtime proof for the local model, TV/TVC credential authority, and `github_token_runtime_authority=false`. Worker availability, heartbeat, model availability, successful source tests, a loopback process, reconciliation output, coherence, gradients, or issue/PR state never substitute for activation.

The worker itself has no secrets. It accepts only nonsecret runtime/source locators:

```text
STEGVERSE_MICRO_NODE_RUNTIME_ROOT
STEGVERSE_FORMALISM_ROOTS_JSON
```

No GitHub/provider/wallet/TVC credential value may enter its child process. Repository operations remain downstream TV/TVC-only.

## Execution posture

The default is the least-stable sufficient shape:

```text
lifetime_class: ONE_SHOT_OPERATION
persistent_execution_used: false
endpoint: loopback only
launch owner: this bounded worker after activation evidence passes
teardown: mandatory after generation attempt
state externalization: receipts/local-source-generation-executor/**
```

Persistent model residency requires separate authorization and is not provided by this lane.

## Model contract

Preferred structured endpoint, when the canonical model owner implements it:

```text
POST /v1/source-generation
request schema: stegverse.local-source-generation-request/v0.1
response schema: stegverse.local-source-generation-response/v0.1
```

Until `StegVerse-002/micro-node-runtime#32` installs that profile, the executor may attempt the current OpenAI-compatible loopback chat endpoint with a strict JSON-only prompt, but invalid/unstructured output is a machine-observable BLOCKED result and is never converted into source.

The reference model remains a small sovereign bootstrap model and must not be represented as a production LLM.

## Required implementation surfaces

```text
LOCAL_SOURCE_GENERATION_EXECUTOR_MIRROR_HANDOFF.md
control/local-source-generation-executor.json
control/session-implementation-claim-2026-08-14-local-source-generation-executor.json
handoffs/SHWP-LOCAL-SOURCE-GENERATION-EXECUTOR-001.json
control/worker-registry.d/local-source-generation-executor-001.json
control/process-worker-adapters.d/local-source-generation-executor-001.json
workers/local_source_generation_executor_worker.py
tests/test_local_source_generation_executor_worker.py
data/local-source-generation-executor/task-state.json
```

## Validation contract

1. No generation occurs below explicit dual ACTIVATED evidence.
2. Owner source must be locally materialized and exact base SHA must be observed locally.
3. Every proposed path is safe and source hashes are bound into the request.
4. Only admitted paths may appear in model output.
5. Mirror handoff must be first in generated file ordering.
6. Replacement hashes are computed locally, never trusted from model output.
7. Endpoint is loopback-only.
8. Child environment contains no GitHub/provider/wallet/non-TV/TVC secret/token variables.
9. Process teardown is attempted after every launched-process execution.
10. Invalid JSON/schema/path/hash/size output fails closed and emits no generation result.
11. Runtime/model proof and measured usage are persisted.
12. The worker performs no GitHub mutation and emits no owner source packet directly.

## Execution ownership and collision partition

```text
MANUAL / SESSION-STARTABLE
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.d/local-source-generation-executor-001.json
collision_scope: workers/local_source_generation_executor_worker.py + control/local-source-generation-executor.json + task-specific handoff/registry/adapter/tests/state/receipts only
release_condition: source implementation merged/validated and continuation transferred to the registered worker; live completion requires dual ACTIVATED evidence plus a valid structured local-model response
next_executable_action: implement and validate the bounded local executor, then transfer live continuation to the registered worker

WORKER-OWNED / DO NOT COMPETE
SHWP-LOCAL-SOURCE-GENERATION-EXECUTOR-001 owns local source-generation execution after registration.
SHWP-ADMISSIBLE-SOURCE-GENERATION-CAPABILITY-001 owns validation/binding of the resulting generation record.
SHWP-FORMALISM-OWNER-MUTATION-EXECUTOR-001 owns downstream nonsecret TVC mutation-warrant preparation.

ESCALATED / AUTHORITY-OWNED
StegCore owns AE lifecycle/StegGate semantics.
StegVerse-002/micro-node-runtime owns model/runtime semantics and structured generation profile #32.
TV/TVC owns credential-bearing repository transport.
USER_ONLY remains signing/broadcast authority for StegFin.

COMPLETED / SUPERSEDED
The old descriptive `select a local model/runtime` step is superseded by the released sovereign runtime discovery/launch/proof implementation. This lane consumes it; it does not recreate it.
```

## Current blockers

```text
FORMALISM_SOURCE_GENERATION_CAPABILITY_NOT_ACTIVATED
SOVEREIGN_LOCAL_MODEL_CAPABILITY_NOT_ACTIVATED
STRUCTURED_SOURCE_GENERATION_PROFILE_NOT_YET_MERGED: StegVerse-002/micro-node-runtime#32
RESIDENT_END_TO_END_SOURCE_PACKET_NOT_YET_OBSERVED
```

Machine-observable release conditions are explicit activation evidence in the local executor activation envelope plus a structured loopback response satisfying the task schema.

## Integration / propagation

No Site, Publisher, admissibility-wiki, stegguardian-wiki, release, or tag propagation is authorized by this implementation. Propagation can occur only after the owning source is canonicalized through its normal release authority.

## Completion inventory

```text
required developed surfaces: 9
source implementation: IN_PROGRESS
hosted validation: PENDING
live activation: BLOCKED_ON_CANONICAL_EVIDENCE
resident structured generation: NOT_OBSERVED
owner source packet: NOT_OBSERVED
recursive owner mutation/re-observation: NOT_OBSERVED
```

## Archive condition

The scoped source implementation can release after merge and validation. This session remains non-archive-ready until its unique local-executor implementation is merged or durably transferred to a proven active executor. Wider #137 remains open until a real source packet is accepted by the owner-mutation executor and a recursive owner mutation/re-observation cycle is observed.