# Kimi InTr Resident Activation Mirror Handoff

Updated: 2026-09-07
Repository: `StegVerse-Labs/.github`
Task: `KIMI-INTR-RESIDENT-ACTIVATION-001`
COSV: `50000000101000`
Peer task in Group 6: `SHWP-DEEPSEEK-INTR-RUNTIME-001`

## Authority and source-of-truth chain

This handoff is the resident-execution projection for the Kimi/Moonshot lane. It is subordinate to and must reuse the canonical provider/runtime boundaries defined by:

- `StegVerse-org/LLM-adapter/docs/KIMI_INTR_TRANSPORT_MIRROR_HANDOFF.md`
- `StegVerse-org/LLM-adapter/tasks/LLMA-KIMI-INTR-RUNTIME-292.json`
- `StegVerse-Labs/TVC` Kimi provider capsule / lease / non-exportable provider-operation semantics
- canonical Universal InTr transport semantics
- canonical Governance / StegCore ALLOW | DENY | FAIL-CLOSED decision semantics
- canonical Master Records provider-usage custody/reconstruction
- the existing `StegVerse-Labs/.github` WorkerCoordinator resident lane

No source in this task may create a second scheduler, worker authority system, credential store, provider-secret path, governance authority, heartbeat authority, or Master Records authority.

## Exact execution objective

Complete one authentic same-execution Kimi resident cycle using the already-installed components:

```text
exact TVC/Moonshot provider payload bytes/hash
-> Universal InTr ingress TRANSPORT_COMPLETE
-> Governance / StegCore ALLOW
-> TVC single-use Kimi capability lease
-> TVC non-exportable provider operation
-> authentic Moonshot/Kimi response
-> TVC use receipt
-> Master Records provider-usage custody + reconstruction PASS
-> Universal InTr egress TRANSPORT_COMPLETE bound to exact response bytes
-> retained resident WorkerCoordinator completion receipt
```

Transport completion is not governance approval. Governance ALLOW is not provider execution or credential authority. TV/TVC remains the sole provider consequence / credential authority.

## Required reuse

The resident implementation must consume the exact canonical Kimi provider-wire identity from `StegVerse-org/LLM-adapter`, including the production composition exposed by:

- `llm_adapter/kimi_tvc_provider_wire.py`
- `llm_adapter/kimi_governed_admission.py`
- `llm_adapter/kimi_tvc_runtime_executor.py`
- `llm_adapter/kimi_canonical_runtime.py`

The current TVC Kimi contract accepts exactly one user prompt and materializes it as one user message. Until TVC exposes a message-preserving chat contract, multi-message or non-user-role resident requests must fail closed.

The resident Kimi task should reuse the structure of the existing DeepSeek lane where semantics are shared, especially:

- WorkerCoordinator claim/fence validation
- hosted-runtime prohibition
- secret-environment prohibition
- local-source-root requirements
- separate ingress and egress governance/transport evidence
- TVC broker use without credential export
- Master Records custody before egress completion
- secret-free receipt persistence

Provider-specific request construction, provider-wire hashing, lease semantics, endpoint/model binding, and Kimi canonical admission must remain Kimi-specific and must not be copied from DeepSeek where the canonical Kimi contract differs.

## Activation predicates

`KIMI-INTR-RESIDENT-ACTIVATION-001` remains incomplete until one authentic same-execution chain proves all of:

1. fresh existing WorkerCoordinator claim and positive fencing token;
2. exact Kimi provider-wire payload/hash resolved from canonical LLM-adapter production code;
3. authentic Universal InTr ingress `TRANSPORT_COMPLETE` receipt bound to that exact provider-wire identity;
4. authentic Governance / StegCore decision receipt with `decision=ALLOW`;
5. authentic TV/TVC Kimi capability lease and non-exportable provider operation;
6. authentic Moonshot/Kimi provider response for the bound request;
7. authentic TVC use receipt proving no credential export/log/retention;
8. Master Records `custody_recorded=true` and `reconstructability=PASS`;
9. authentic Universal InTr egress completion bound to the exact response bytes/hash;
10. a resident WorkerCoordinator completion receipt carrying common task/session/transition/request identity across the retained chain.

Mocks, fixtures, CI success, source merge, handoff creation, runtime-profile presence, transport completion alone, Governance ALLOW alone, TVC readiness alone, or provider output alone do not satisfy activation.

## Machine preflight and README invariant

Before any functional mutation for this resident lane, run the repository's applicable machine preflight and declare README impact. Because adding a resident Kimi execution surface materially changes runtime behavior and integration semantics, the implementation change set must update `README.md` in the same change set unless a later canonical preflight produces an evidence-supported non-material determination.

This handoff file is coordination/documentation only and grants no execution, claim/fence, transition, credential, provider-use, custody, publication, or runtime-truth authority.

## Current state

```text
task: KIMI-INTR-RESIDENT-ACTIVATION-001
cosv: 50000000101000
coordination_state: HANDOFF_READY
source implementation in LLM-adapter: IMPLEMENTED_PENDING_RUNTIME_PROOF
resident WorkerCoordinator Kimi consumer in StegVerse-Labs/.github: NOT_YET_INSTALLED_BY_THIS_TASK
credential architecture duplication: PROHIBITED
provider credential plaintext in .github or LLM-adapter: PROHIBITED
canonical sovereign local route replaced: false
heartbeat grants authority: false
transport grants execution authority: false
governance grants execution authority: false
governance grants credential authority: false
live Kimi connector: NOT_YET_PROVEN
release/tag authority: NOT_INFERRED
```

## Next admissible work

1. Resolve the current `StegVerse-Labs/.github` machine preflight entrypoint and run it for this material resident-runtime mutation with README impact required.
2. Reuse the existing DeepSeek resident lane as the structural reference, not as a provider-semantic template.
3. Install a bounded Kimi worker, resident request consumer, worker-registry fragment, process-adapter fragment, task vector/registry projection, validation-only workflow, and README documentation.
4. Bind the worker to canonical Kimi exact-provider-wire construction and separate InTr + Governance evidence before TVC execution.
5. Execute only on the existing sovereign resident surface and retain authentic same-execution receipts.
6. After authentic activation proof, evaluate release/tag readiness and project pertinent updates to `StegVerse-Labs/Site`, `GCAT-BCAT-Engine/Publisher`, `admissibility-wiki`, and `stegguardian-wiki` as separate governed tasks.

## Known remaining installation destinations

```text
StegVerse-Labs/.github:
  workers/kimi_intr_resident_activation_worker.py
  control/resident-execution-request.d/kimi-intr-resident-activation-001.json
  control/resident-execution-request.d/consume-kimi-intr-resident-activation.py
  control/worker-registry.d/kimi-intr-resident-activation-001.json
  control/process-worker-adapters.d/kimi-intr-resident-activation-001.json
  control/task-vectors/KIMI-INTR-RESIDENT-ACTIVATION-001.json
  handoffs/KIMI-INTR-RESIDENT-ACTIVATION-001.json
  validation-only workflow entry
  README.md resident Kimi section

StegVerse-Labs/TVC:
  REUSE existing Kimi capsule / lease / non-exportable provider operation; no new credential semantics

StegVerse-org/LLM-adapter:
  REUSE existing exact-provider-wire and canonical Kimi runtime composition; no duplicate runtime architecture

master-records/orchestration:
  REUSE canonical provider-usage custody/reconstruction
```
