# KV AI Memory Resident Execution Mirror Handoff

Status: ACTIVE / MEMORY-PACKET-INTR-SOURCE-PATH-VALIDATED / RESIDENT-PROVIDERREQUEST-BINDING-VALIDATED / LIVE-INTR-PROOF-OPEN
Goal Task ID: `SV-KV-AI-PERSISTENCE-001`
COSV task.v1: `20111110110000`
Repository: `StegVerse-Labs/.github`
Canonical task record: `data/canonical-task-records/SV-KV-AI-PERSISTENCE-001.json`
Parent KV handoff: `StegVerse-Labs/continuity-vault-kit/KV_AI_PERSISTENCE_CLASSES_MIRROR_HANDOFF.md`
LLM bridge handoff: `StegVerse-org/LLM-adapter/docs/KV_AI_MEMORY_CONTEXT_BRIDGE_MIRROR_HANDOFF.md`

## Goal

Bind Personal-KV continuity memory into the existing sovereign resident/WorkerCoordinator execution family without creating another scheduler, runtime owner, credential path, admission authority, model authority, or private-content repository path.

## Authority reuse

```text
private continuity source: continuity-vault-kit
memory-packet transport/admission: existing shared Universal InTr listener
resident work ownership: existing WorkerCoordinator claim/fence
provider request/response admission: existing external LLM InTr path
credential/provider operation: TV/TVC only
provider-neutral model boundary: LLM-adapter
custody/reconstruction: Master Records
heartbeat: carrier/reference/observation only
```

Repository state, source preparation, CI, fixtures, or route installation never substitute for an authentic InTr receipt, WorkerCoordinator claim/fence, provider operation, model response, or KV write receipt.

## Canonical private bound state

```text
~/.stegverse/state/kv-ai-memory-resident/
  inputs/context-packet.json
  inputs/memory-packet-admission.json
  inputs/provider-request-input.json
  materialized/provider-request.json
  receipts/provider-request-materialization.json
```

Private packet, prompt, and provider-request bytes remain outside GitHub. The resident request consumer tests readiness and invokes bounded subprocesses; it does not read the private packet itself.

## Shared Universal InTr packet admission

Canonical source surfaces:

- `workers/kv_ai_memory_intr_profile.py` — exact Personal-KV memory packet validation and non-authorizing admission receipt;
- `workers/kv_ai_memory_intr_transport.py` — resident-local transport header/hash validation;
- `scripts/install_kv_ai_memory_universal_intr_route.py` — idempotent transform for the existing shared listener;
- `scripts/prepare_kv_ai_memory_intr_runtime_source.py` — canonical runtime-source preparation wrapper;
- `scripts/submit_kv_ai_memory_packet_local.py` — private staged-packet submitter and exact returned-receipt validator;
- `scripts/consume_kv_ai_memory_resident_request.py` — autonomous wait/admit/continue orchestration;
- `tests/test_kv_ai_memory_intr_admission.py`;
- `tests/test_prepare_kv_ai_memory_intr_runtime_source.py`;
- `tests/test_kv_ai_memory_resident_binding.py`.

The resident-local submission contract is:

```text
HTTP loopback only
path = /intr/materialization
X-StegVerse-Transport = InTr
X-StegVerse-Transport-Origin = STEGOS_RESIDENT_LOCAL
X-StegVerse-Payload-SHA256 = exact raw-body SHA-256
X-StegVerse-Authorization-Id = absent
```

The shared listener admission must bind the exact `packet_id`, canonical `packet_sha256`, exact packet validation, and a self-consistent `sha256:` receipt hash. The canonical submitter additionally rejects any returned receipt that claims provider request materialization, provider ingress, provider execution, KV writeback, credential material, claim/fence creation, HeartBeat execution authority, or request execution authority at this boundary.

Only a successfully validated listener receipt may populate `inputs/memory-packet-admission.json`. Missing listener configuration, an unreachable/rejecting listener, malformed evidence, tampered receipt hash, or promoted authority claims remain fail-closed/wait states.

## Canonical resident progression

When `context-packet.json` and `provider-request-input.json` exist while `memory-packet-admission.json` is absent, the consumer may:

1. require an explicit `STEGVERSE_UNIVERSAL_INTR_INGRESS_URL`;
2. run `prepare_kv_ai_memory_intr_runtime_source.py` against already-local resident source;
3. require a valid preparation result (`ROUTE_INSTALLED_LOCAL_SOURCE` or `ROUTE_ALREADY_INSTALLED`);
4. invoke `submit_kv_ai_memory_packet_local.py` against the private bound-state root;
5. recheck bound-state readiness;
6. continue to existing WorkerCoordinator execution only if the authentic admission artifact now exists.

The preparation wrapper only normalizes local source. It does not start a listener, create a transport event, admit a packet, mint a claim/fence, execute a provider, or mutate KV.

```text
real Personal-KV readable state
-> private context packet + provider request input
-> local source normalization for existing shared Universal InTr listener
-> exact resident-local packet submission
-> authentic shared-listener ALLOW
-> private admission artifact
-> existing WorkerCoordinator fresh claim/fence
-> fenced LLM ProviderRequest materialization
-> existing provider ingress / TVC / response / egress chain
-> optional non-authorizing memory write proposal
-> authentic target-KV admission
-> exact-byte KV readback receipt
```

## Resident ProviderRequest binding

Existing resident execution surfaces remain canonical:

- `handoffs/SV-KV-AI-PERSISTENCE-001.json`;
- `control/worker-registry.d/kv-ai-memory-resident-001.json`;
- `control/process-worker-adapters.d/kv-ai-memory-resident-001.json`;
- `control/resident-execution-request.d/kv-ai-memory-resident-001.json`;
- `workers/kv_ai_memory_resident_worker.py`;
- dispatcher selector `kv_ai_memory`;
- LLM-adapter `scripts/materialize_kv_memory_provider_request.py`.

The worker stops at `KV_AI_MEMORY_PROVIDER_REQUEST_MATERIALIZED`. It does not claim provider ingress ALLOW, provider execution, model response, egress ALLOW, or KV writeback.

## Hosted validation

Previously validated:

- LLM bridge/materializer: runs `34803228613`, `34803228620` — SUCCESS;
- original resident binding: run `34803483965` — SUCCESS;
- initial shared memory-packet admission source: run `34804928451` — SUCCESS.

Hardening and source-preparation validation:

- run `34805361433` / job `103856079710` — SUCCESS; exact returned receipt hash validation, anti-authority checks, packet admission tests, resident binding tests, and compilation passed;
- run `34805426026` / job `103856264389` — SUCCESS; canonical runtime-source preparation tests and compilation passed;
- run `34805510953` / job `103856506912` — SUCCESS; resident consumer convergence on the canonical source-preparation wrapper, fail-closed preparation-result checks, packet-admission tests, resident binding tests, and compilation passed.

Hosted validation proves source behavior only. It does not prove that the current sovereign resident has private staged inputs, that the shared listener is bound, that a live packet ALLOW occurred, or that WorkerCoordinator/provider/model/writeback execution happened.

## Next authentic evidence boundary

The first unresolved predicate is now operational rather than architectural:

```text
real staged Personal-KV packet
+ real provider-request input
+ current shared loopback Universal InTr listener
-> returned exact packet ALLOW
-> memory-packet-admission.json
```

After that, the already-validated resident lane can attempt WorkerCoordinator ProviderRequest materialization. No receipt may be synthesized from CI, source, fixtures, or model output.

## Current truth

```text
canonical task: IN_PROGRESS
KV memory source: VALIDATED
packet admission profile/transport: VALIDATED
canonical local route preparation: VALIDATED
canonical local packet submitter: VALIDATED
resident autonomous admission orchestration: VALIDATED
resident WorkerCoordinator binding: VALIDATED
LLM ProviderRequest bridge/materializer: VALIDATED
real private resident packet/input state: NOT OBSERVED
live shared-listener packet ALLOW: NOT OBSERVED
live WorkerCoordinator ProviderRequest materialization: NOT OBSERVED
live provider/model chain: NOT OBSERVED
live target-KV writeback/readback: NOT OBSERVED
activated: false
authority_effect: NONE_SOURCE_ONLY
```
