# KV AI Memory Resident Execution Mirror Handoff

Status: ACTIVE / RESIDENT-PROVIDERREQUEST-BINDING-VALIDATED / BOUND-STATE-INPUT-PENDING / LIVE-INTR-PROOF-OPEN
Goal Task ID: `SV-KV-AI-PERSISTENCE-001`
COSV task.v1: `20111110110000`
Repository: `StegVerse-Labs/.github`
Canonical task record: `data/canonical-task-records/SV-KV-AI-PERSISTENCE-001.json`
Parent KV handoff: `StegVerse-Labs/continuity-vault-kit/KV_AI_PERSISTENCE_CLASSES_MIRROR_HANDOFF.md`
LLM bridge handoff: `StegVerse-org/LLM-adapter/docs/KV_AI_MEMORY_CONTEXT_BRIDGE_MIRROR_HANDOFF.md`

## Goal

Bind the already-implemented Personal-KV AI memory packet and LLM ProviderRequest bridge into the existing sovereign resident/WorkerCoordinator execution family without creating another runtime owner, scheduler, admission authority, credential path, or model authority.

## Runtime authority reuse

```text
resident dispatch: existing StegVerse-Labs/.github dispatcher
work ownership: existing WorkerCoordinator claim/fence semantics
KV transport/admission: existing Universal InTr / Interlock
provider request/response admission: existing external LLM InTr path
credential/provider operation: TV/TVC only
provider-neutral model boundary: StegVerse-org/LLM-adapter
private continuity source: StegVerse-Labs/continuity-vault-kit
custody/reconstruction: Master Records
heartbeat: carrier/reference only
```

This handoff does not authorize execution. Repository source, CI, request files, dispatcher registration, or successful validation cannot substitute for an authentic claim/fence or Interlock/InTr receipt.

## Implemented resident binding

The source binding is now materialized:

- executable handoff: `handoffs/SV-KV-AI-PERSISTENCE-001.json`;
- WorkerCoordinator registry: `control/worker-registry.d/kv-ai-memory-resident-001.json`;
- fenced ProcessWorkerAdapter: `control/process-worker-adapters.d/kv-ai-memory-resident-001.json`;
- resident request: `control/resident-execution-request.d/kv-ai-memory-resident-001.json`;
- request consumer: `scripts/consume_kv_ai_memory_resident_request.py`;
- worker: `workers/kv_ai_memory_resident_worker.py`;
- generic dispatcher selector: `kv_ai_memory` in `scripts/dispatch_resident_execution_requests.py`;
- deterministic validation: `tests/test_kv_ai_memory_resident_binding.py`;
- hosted validation: `.github/workflows/validate-kv-ai-memory-resident.yml`.

The LLM-adapter now also supplies `scripts/materialize_kv_memory_provider_request.py`, which consumes only resident-local packet/admission/request-input files and emits one deterministic provider-neutral `ProviderRequest` plus hash. It does not perform provider execution or decide admission.

## Fenced private-state contract

Private state is outside repository content at:

```text
~/.stegverse/state/kv-ai-memory-resident/
  inputs/context-packet.json
  inputs/memory-packet-admission.json
  inputs/provider-request-input.json
  materialized/provider-request.json
  receipts/provider-request-materialization.json
```

`ProcessWorkerAdapter` exposes only a sandbox mirror of that bound-state root to the fenced worker. The consumer checks only whether the three input paths exist; it deliberately does not read their bytes. Therefore a missing packet/admission/request input returns `BOUND_STATE_INPUT_NOT_READY` without consuming the request or attempting WorkerCoordinator execution.

Repository state receives no private memory packet, prompt, materialized ProviderRequest, token, API key, or provider credential.

## Bounded resident composition

```text
resident-local Personal-KV context packet
+ exact memory-packet InTr ALLOW receipt
+ resident-local user/model request material
-> non-authorizing resident request consumer
-> existing WorkerCoordinator fresh claim/fence
-> fenced ProcessWorkerAdapter bound-state mirror
-> LLM-adapter exact ProviderRequest materializer
-> provider-request hash + bound-state receipt
-> HANDOFF_READY for existing provider ingress continuation
```

The current worker intentionally stops at `KV_AI_MEMORY_PROVIDER_REQUEST_MATERIALIZED`. Its receipt fixes all of the following false until independently observed:

```text
provider_ingress_admission_observed=false
provider_execution_observed=false
provider_egress_admission_observed=false
kv_writeback_observed=false
credential_material_present=false
worker_claim_or_fence_minted=false
```

That prevents source materialization from being misrepresented as live AI consumption or KV mutation.

## Hosted validation

LLM-adapter materializer head `920fedd13a182636c80a30fc10d9482ee21de57a`:

- run `34803228613` / job `103849905207` — SUCCESS;
- run `34803228620` / job `103849906564` — SUCCESS.

The dedicated `.github` resident-binding workflow run `34803483965` / job `103850649371` completed SUCCESS. It passed:

- `pytest -q tests/test_kv_ai_memory_resident_binding.py`;
- Python compilation for the resident worker, request consumer, and generic dispatcher.

The tests prove bounded source behavior only: clean waiting with absent private inputs, bound-state-only materialization, non-authorizing runtime flags, dispatcher registration, and registry/handoff/adapter authority invariants.

## Next executable boundary

The source binding no longer needs another runtime owner or another request transport. The next authentic transition is:

```text
resident-local exact Personal-KV packet exists
+ authentic memory-packet InTr ALLOW artifact exists
+ resident-local provider request input exists
-> existing `kv_ai_memory` dispatcher consumer
-> current WorkerCoordinator fenced execution
-> exact ProviderRequest materialized in bound state
-> existing provider ingress InTr / TVC / response / egress path
```

After provider response evidence exists, the already-built KV memory write proposal must traverse target-KV admission and exact-byte readback before persistent memory writeback is claimed.

No runtime receipt may be synthesized from repository source, CI, a fixture, or a model response.

## Completion evidence

Live goal completion still requires authentic same-execution evidence for:

- exact memory packet admission;
- exact ProviderRequest materialization under current WorkerCoordinator claim/fence;
- provider request ingress ALLOW;
- TV/TVC provider execution where applicable;
- provider response and egress ALLOW;
- Master Records custody/reconstruction;
- memory write proposal admission and exact KV readback.

## Current truth

```text
canonical task: IN_PROGRESS
KV memory source: VALIDATED
LLM memory bridge: VALIDATED
LLM resident materializer: VALIDATED
resident WorkerCoordinator binding: VALIDATED
resident private-input state: NOT OBSERVED
live memory packet admission: NOT OBSERVED
live ProviderRequest materialization: NOT OBSERVED
live model consumption: NOT OBSERVED
live KV writeback/readback: NOT OBSERVED
activated: false
authority_effect: NONE_SOURCE_ONLY
```
