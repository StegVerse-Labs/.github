# Kimi InTr Resident Activation Mirror Handoff

Task: `KIMI-INTR-RESIDENT-ACTIVATION-001`
COSV ID: `50000000101000`
State: `ACTIVE`
Repository: `StegVerse-Labs/.github`
Upstream transport/runtime source: `StegVerse-org/LLM-adapter`
Upstream mirror: `StegVerse-org/LLM-adapter/docs/KIMI_INTR_TRANSPORT_MIRROR_HANDOFF.md`

## Source of truth

This file is the current continuation source of truth for the resident Kimi activation lane in `StegVerse-Labs/.github`. It does not supersede the upstream Kimi transport handoff and grants no credential, deployment, publication, or autonomous transition authority.

## Already materialized upstream capability

The Kimi transport/runtime source is not a blank scaffold. `StegVerse-org/LLM-adapter` already contains:

- `llm_adapter/kimi_intr_transport.py`
- `llm_adapter/kimi_governed_admission.py`
- `llm_adapter/kimi_tvc_provider_wire.py`
- `llm_adapter/kimi_tvc_broker.py`
- `llm_adapter/kimi_tvc_runtime_executor.py`
- `llm_adapter/kimi_canonical_runtime.py`
- Kimi TVC/runtime tests
- capability registration and task metadata

The production path preserves TVC non-exportable provider use; direct credential-resolver transport remains compatibility/test-only.

## Missing resident binding in StegVerse-Labs/.github

Unlike DeepSeek, no task-specific resident WorkerCoordinator implementation for `KIMI-INTR-RESIDENT-ACTIVATION-001` is currently materialized in `StegVerse-Labs/.github`.

Required destination surfaces are:

- `workers/kimi_intr_runtime_worker.py`
- `control/worker-registry.d/kimi-intr-runtime-001.json`
- `control/process-worker-adapters.d/kimi-intr-runtime-001.json`
- `control/resident-execution-request.d/kimi-intr-runtime-001.json`
- `control/resident-execution-request.d/consume-kimi-intr-runtime.py`
- `handoffs/KIMI-INTR-RESIDENT-ACTIVATION-001.json`
- Kimi validation-only workflow entry if required by the workflow-surface registry
- secret-free runtime receipts under `receipts/kimi-intr-runtime/**`

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

The upstream Kimi transport/runtime capability is materialized, but the `.github` resident consumer/registry/adapter/request/handoff set has not yet been built for this task identity. TVC-side exact lease/profile compatibility must be confirmed before copying DeepSeek resident semantics; do not invent a Kimi lease issuer name or profile.

## Next authorized build sequence

1. confirm the exact Kimi TVC runtime profile / provider-operation binding already exposed by `StegVerse-Labs/TVC` and the LLM-adapter Kimi runtime executor;
2. materialize the bounded Kimi resident WorkerCoordinator worker and adapter set in `StegVerse-Labs/.github`;
3. create a standing resident request with no credential material and no hosted-runtime authority;
4. wire dispatcher consumption through the existing independent task-control path;
5. validate source/preflight only in GitHub Actions;
6. run the actual cycle only on the existing sovereign resident surface;
7. admit activation only from the same-execution Kimi receipt.

## Completion accounting

Upstream Kimi transport/runtime implementation: `90%+` materialized.
Resident `.github` binding for this task: `35%` (authoritative handoff now exists; implementation surfaces remain to be installed).
Goal activation: `20%` until resident binding exists and a same-execution sovereign receipt is observed.

## Release/tag gate

No release/tag is authorized from this handoff alone. When the resident implementation and same-execution receipt make the lane release-ready, perform the release/tag step and create the follow-up verification task to project pertinent state to:

- `StegVerse-Labs/Site`
- `GCAT-BCAT-Engine/Publisher`
- `StegVerse-Labs/admissibility-wiki`
- `StegVerse-Labs/stegguardian-wiki`
