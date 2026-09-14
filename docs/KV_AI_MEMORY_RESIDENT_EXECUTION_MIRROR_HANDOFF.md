# KV AI Memory Resident Execution Mirror Handoff

Status: ACTIVE / MEMORY-PACKET-INTR-SUBMISSION-VALIDATED / RESIDENT-PROVIDERREQUEST-BINDING-VALIDATED / LIVE-INTR-PROOF-OPEN
Goal Task ID: `SV-KV-AI-PERSISTENCE-001`
COSV task.v1: `20111110110000`
Repository: `StegVerse-Labs/.github`
Canonical task record: `data/canonical-task-records/SV-KV-AI-PERSISTENCE-001.json`
Parent KV handoff: `StegVerse-Labs/continuity-vault-kit/KV_AI_PERSISTENCE_CLASSES_MIRROR_HANDOFF.md`
LLM bridge handoff: `StegVerse-org/LLM-adapter/docs/KV_AI_MEMORY_CONTEXT_BRIDGE_MIRROR_HANDOFF.md`

## Goal

Bind the implemented Personal-KV AI memory packet and LLM ProviderRequest bridge into the existing sovereign resident/WorkerCoordinator execution family without creating another runtime owner, scheduler, admission authority, credential path, or model authority.

## Runtime authority reuse

```text
resident dispatch: existing StegVerse-Labs/.github dispatcher
work ownership: existing WorkerCoordinator claim/fence semantics
memory-packet admission: existing shared Universal InTr listener
provider request/response admission: existing external LLM InTr path
credential/provider operation: TV/TVC only
provider-neutral model boundary: StegVerse-org/LLM-adapter
private continuity source: StegVerse-Labs/continuity-vault-kit
custody/reconstruction: Master Records
heartbeat: carrier/reference only
```

Repository source, CI, request files, dispatcher registration, route installation, or successful validation cannot substitute for an authentic shared-listener admission, WorkerCoordinator claim/fence, provider operation, or KV receipt.

## Implemented resident binding

Existing source binding:

- executable handoff: `handoffs/SV-KV-AI-PERSISTENCE-001.json`;
- WorkerCoordinator registry: `control/worker-registry.d/kv-ai-memory-resident-001.json`;
- fenced ProcessWorkerAdapter: `control/process-worker-adapters.d/kv-ai-memory-resident-001.json`;
- resident request: `control/resident-execution-request.d/kv-ai-memory-resident-001.json`;
- request consumer: `scripts/consume_kv_ai_memory_resident_request.py`;
- worker: `workers/kv_ai_memory_resident_worker.py`;
- dispatcher selector: `kv_ai_memory`;
- deterministic validation: `tests/test_kv_ai_memory_resident_binding.py`.

The resident worker still stops at `KV_AI_MEMORY_PROVIDER_REQUEST_MATERIALIZED` and cannot claim provider ingress, provider execution, egress, model consumption, or KV writeback.

## Private bound-state contract

```text
~/.stegverse/state/kv-ai-memory-resident/
  inputs/context-packet.json
  inputs/memory-packet-admission.json
  inputs/provider-request-input.json
  materialized/provider-request.json
  receipts/provider-request-materialization.json
```

Private packet/prompt/provider-request bytes remain outside repository content. The consumer checks path readiness only; private packet bytes are read by the bounded local submitter/worker subprocesses, not by the consumer itself.

## Shared Universal InTr memory-packet admission

The former manual gap between `context-packet.json` and `memory-packet-admission.json` is now source-implemented using the existing shared Universal InTr listener:

- `workers/kv_ai_memory_intr_profile.py` — exact Personal-KV packet validator and non-authorizing admission receipt producer;
- `workers/kv_ai_memory_intr_transport.py` — resident-local InTr transport validator;
- `scripts/install_kv_ai_memory_universal_intr_route.py` — idempotent shared-listener route/profile installer;
- `scripts/submit_kv_ai_memory_packet_local.py` — private bound-state packet submitter and returned-receipt validator;
- `tests/test_kv_ai_memory_intr_admission.py` — exact-hash, tamper, transport, submitter, and route-idempotence coverage.

The resident-local hop requires:

```text
HTTP loopback only
path = /intr/materialization
X-StegVerse-Transport = InTr
X-StegVerse-Transport-Origin = STEGOS_RESIDENT_LOCAL
exact raw-body SHA-256
no X-StegVerse-Authorization-Id
```

No TVC relay credential is needed for this local carriage. TV/TVC remains credential authority for downstream provider operations that require credentials.

The authentic listener response must bind `packet_id` and canonical `packet_sha256` and return a `sha256:` receipt hash. Only then may the submitter write `inputs/memory-packet-admission.json`. Missing ingress or rejected packets remain a wait/fail-closed state; the submitter never fabricates ALLOW.

## Autonomous resident progression

When the private packet and provider-request input exist but admission does not, `consume_kv_ai_memory_resident_request.py` now:

1. requires an explicit `STEGVERSE_UNIVERSAL_INTR_INGRESS_URL`;
2. idempotently prepares the shared-listener route from already-local source;
3. invokes the private local submitter;
4. rechecks bound-state readiness;
5. proceeds to the existing WorkerCoordinator path only if the authentic admission file now exists.

If the URL is absent, listener is unavailable, admission is rejected, or the returned receipt does not exactly bind the packet, the consumer does not attempt the WorkerCoordinator step.

The consumer itself still does not read packet bytes and does not mint a claim/fence or admission.

## Bounded resident composition

```text
private Personal-KV packet
+ private provider-request input
-> shared loopback Universal InTr exact-packet submission
-> authentic packet ALLOW written back to private bound state
-> existing resident request consumer
-> existing WorkerCoordinator fresh claim/fence
-> fenced ProcessWorkerAdapter
-> LLM-adapter exact ProviderRequest materializer
-> HANDOFF_READY for existing provider ingress continuation
```

## Hosted validation

Existing LLM materializer validation:

- `34803228613` / `103849905207` — SUCCESS;
- `34803228620` / `103849906564` — SUCCESS.

Original resident-binding validation:

- `34803483965` / `103850649371` — SUCCESS.

Shared memory-packet admission source head `7e95e58c0f6ebfa839dbaa6a475b8df7ca06ab01`:

- run `34804928451` / job `103854827156` — SUCCESS;
- prior resident-binding tests and new packet-admission tests passed together;
- compilation passed for the profile, transport validator, route installer, local submitter, consumer, worker, and dispatcher.

This proves source behavior only. It does not establish that a private packet currently exists, that the shared listener is currently bound, that an authentic packet ALLOW has occurred, or that WorkerCoordinator/provider/model/writeback execution occurred.

## Next executable evidence sequence

```text
real Personal-KV readable entries
-> private packet + provider-input staging
-> explicit existing shared loopback ingress URL
-> authentic shared-listener packet ALLOW
-> private memory-packet-admission.json
-> current WorkerCoordinator claim/fence
-> exact ProviderRequest materialization
-> existing provider ingress InTr / TVC / response / egress
-> non-authorizing write proposal
-> authentic target-KV admission
-> exact-byte KV readback
```

No runtime receipt may be synthesized from repository source, CI, a fixture, or a model response.

## Current truth

```text
canonical task: IN_PROGRESS
KV memory source: VALIDATED
shared packet-admission source: VALIDATED
shared packet-admission live event: NOT OBSERVED
LLM memory bridge/materializer: VALIDATED
resident WorkerCoordinator binding: VALIDATED
resident private-input state: NOT OBSERVED
live ProviderRequest materialization: NOT OBSERVED
live model consumption: NOT OBSERVED
live KV writeback/readback: NOT OBSERVED
activated: false
authority_effect: NONE_SOURCE_ONLY
```
