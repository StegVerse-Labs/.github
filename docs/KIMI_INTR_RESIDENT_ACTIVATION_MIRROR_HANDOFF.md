# Kimi InTr Resident Activation Mirror Handoff

Task: `KIMI-INTR-RESIDENT-ACTIVATION-001`
COSV ID: `50000000101000`
State: `ACTIVE`
Repository: `StegVerse-Labs/.github`
Upstream transport/runtime source: `StegVerse-org/LLM-adapter`
Upstream mirror: `StegVerse-org/LLM-adapter/docs/KIMI_INTR_TRANSPORT_MIRROR_HANDOFF.md`

## Source of truth

This file is the current continuation source of truth for the resident Kimi activation lane in `StegVerse-Labs/.github`. It does not supersede the upstream Kimi transport handoff and grants no credential, deployment, publication, or autonomous transition authority.

## Verified upstream runtime/provider binding

The exact Kimi runtime/provider contract is now confirmed from current source:

- runtime profile: `stegverse:runtime-profile:llm-adapter-kimi:v1`
- base resident profile: `stegverse:runtime-profile:hb-intr-resident:v1`
- protocol: `stegverse.intr.kimi.transport.v1`
- TVC provider: `kimi`
- TVC capability: `llm.measure.kimi`
- provider operation: `chat_completion_with_usage`
- TVC vault ref: `vault://tvc/providers/kimi/api-key`
- production model currently bound by the LLM-adapter runtime/request surface: `kimi-k3`
- provider endpoint: `https://api.moonshot.ai/v1/chat/completions`
- credential authority: `TV/TVC`
- provider API-key export: prohibited

The upstream Kimi transport/runtime source remains materially implemented in `StegVerse-org/LLM-adapter`, including the Kimi InTr transport, governed admission, TVC provider wire/broker, TVC runtime executor, canonical runtime, tests, capability registration, and task metadata.

## Current resident binding state in StegVerse-Labs/.github

The resident binding is no longer an empty scaffold. The repository currently contains:

- `control/worker-registry.d/kimi-intr-runtime-001.json`
- `control/process-worker-adapters.d/kimi-intr-runtime-001.json`
- `control/resident-execution-request.d/kimi-intr-runtime-001.json`
- `handoffs/KIMI-INTR-RESIDENT-ACTIVATION-001.json`
- `control/task-vectors/KIMI-INTR-RESIDENT-ACTIVATION-001.json`

The standing request is `REQUESTED`, uses `stegverse:runtime-profile:llm-adapter-kimi:v1`, protocol `stegverse.intr.kimi.transport.v1`, provider `kimi`, model `kimi-k3`, and preserves TV/TVC-only credential authority with hosted runtime and provider credential material prohibited.

## Remaining implementation surfaces

The following task-specific resident surfaces are still not presently observed as materialized:

- `workers/kimi_intr_runtime_worker.py`
- `control/resident-execution-request.d/consume-kimi-intr-runtime.py`
- Kimi validation-only workflow entry if required by `control/workflow-surface-registry.json`
- secret-free runtime receipts under `receipts/kimi-intr-runtime/**`
- sovereign same-execution terminal activation receipt

## Required predicates before implementation may claim activation

1. reuse the existing sovereign WorkerCoordinator; do not create another scheduler/runtime;
2. bind canonical StegGate ingress and egress decisions;
3. use only TV/TVC provider credential authority;
4. require Kimi TVC non-exportable provider operation;
5. retain Master Records provider-usage custody/reconstruction before egress admission;
6. prohibit hosted runtime markers and provider credential environment material;
7. require one same-execution terminal receipt;
8. require no second physical machine.

## Immediate blocker

`KIMI_INTR_RESIDENT_WORKER_AND_CONSUMER_NOT_YET_MATERIALIZED`

The exact runtime/profile/provider binding has been confirmed, and the registry/adapter/request/handoff surfaces exist. The remaining source blocker is the bounded Kimi WorkerCoordinator worker plus request consumer. Activation remains separately blocked until a same-execution sovereign receipt is observed.

## Next authorized build sequence

1. materialize `workers/kimi_intr_runtime_worker.py` against the confirmed Kimi runtime/profile/provider contract;
2. materialize `control/resident-execution-request.d/consume-kimi-intr-runtime.py` using the existing independent task-control dispatcher path;
3. add or register a validation-only Kimi workflow only if required by the workflow-surface registry;
4. validate source/preflight only in GitHub Actions;
5. run the actual cycle only on the existing sovereign resident surface;
6. persist only authorized secret-free receipts;
7. admit activation only from the same-execution Kimi receipt.

## Completion accounting

Upstream Kimi transport/runtime implementation: `90%+` materialized.
Resident `.github` binding for this task: `60%` materialized (task vector, executable handoff, worker registry, process adapter, and resident request exist; worker/consumer/runtime evidence remain).
Goal activation: `35%` until the resident worker/consumer exist and a same-execution sovereign receipt is observed.

## Release/tag gate

No release/tag is authorized from this handoff alone. When the resident implementation and same-execution receipt make the lane release-ready, perform the release/tag step and create the follow-up verification task to project pertinent state to:

- `StegVerse-Labs/Site`
- `GCAT-BCAT-Engine/Publisher`
- `StegVerse-Labs/admissibility-wiki`
- `StegVerse-Labs/stegguardian-wiki`
