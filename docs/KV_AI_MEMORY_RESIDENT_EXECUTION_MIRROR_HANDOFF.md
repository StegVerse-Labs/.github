# KV AI Memory Resident Execution Mirror Handoff

Status: ACTIVE / EVENT-TRIGGERED-SHARED-INTR-BOOTSTRAP-VALIDATED / PORTABLE-TARGETED-DISPATCH-VALIDATED / RESIDENT-SOURCE-CARRIAGE-VALIDATED / RESIDENT-PROVIDERREQUEST-BINDING-VALIDATED / LIVE-INTR-PROOF-OPEN  
Goal Task ID: `SV-KV-AI-PERSISTENCE-001`  
COSV task.v1: `20111110110000`  
Repository: `StegVerse-Labs/.github`  
Canonical task record: `data/canonical-task-records/SV-KV-AI-PERSISTENCE-001.json`  
Executable handoff: `handoffs/SV-KV-AI-PERSISTENCE-001.json`  
Parent KV handoff: `StegVerse-Labs/continuity-vault-kit/KV_AI_PERSISTENCE_CLASSES_MIRROR_HANDOFF.md`  
LLM bridge handoff: `StegVerse-org/LLM-adapter/docs/KV_AI_MEMORY_CONTEXT_BRIDGE_MIRROR_HANDOFF.md`

## Goal

Bind Personal-KV continuity memory into the existing sovereign resident/WorkerCoordinator execution family without creating another scheduler, runtime owner, credential path, admission authority, model authority, private-content repository path, or device-discovery prerequisite.

## Authority boundary

```text
private continuity source: continuity-vault-kit
memory-packet admission: existing shared Universal InTr implementation
resident work ownership: existing WorkerCoordinator claim/fence
provider request/response admission: existing external LLM InTr path
credential/provider operation: TV/TVC only
provider-neutral model boundary: LLM-adapter
custody/reconstruction: Master Records
heartbeat: carrier/reference/observation only
```

Repository state, source preparation, CI, fixtures, route installation, source carriage, event-bootstrap source, or targeted-dispatch registration never substitute for an authentic InTr receipt, WorkerCoordinator claim/fence, provider operation, model response, or KV write receipt.

## Resident runtime-surface invariant

`CURRENT_USER_IPHONE` and equivalent device labels are informational only. This task must not discover, enumerate, poll for, confirm, authorize, identify, wait for, or require a physical iPhone, Remote Desktop Commander device, remotely connected device, or second user-operated machine.

```text
device confirmation required: false
device discovery required: false
device presence probe required: false
remote connected-device requirement: NOT_APPLICABLE
Remote Desktop Commander requirement: NOT_APPLICABLE
second user-operated device required: false
absence of connected-device result is blocker: false
device/runtime-surface identity mints authority: false
```

Runtime verification comes from authentic InTr admission/transition evidence, WorkerCoordinator claim/fence evidence where applicable, exact provider-request/result lineage, exact KV readback, and Master Records custody/reconstruction.

## Canonical private bound state

```text
~/.stegverse/state/kv-ai-memory-resident/
  inputs/context-packet.json
  inputs/memory-packet-admission.json
  inputs/provider-request-input.json
  materialized/provider-request.json
  receipts/provider-request-materialization.json
```

Private packet, prompt, and provider-request bytes remain outside GitHub.

## Source carriage

The generic resident dispatcher already registers selector `kv_ai_memory`. The resident runtime materializer and local WorkerCoordinator source refresher now also carry the required task-specific scripts:

- `scripts/consume_kv_ai_memory_resident_request.py`;
- `scripts/prepare_kv_ai_memory_intr_runtime_source.py`;
- `scripts/install_kv_ai_memory_universal_intr_route.py`;
- `scripts/submit_kv_ai_memory_packet_local.py`.

The resident-native event bootstrap implementation is `workers/kv_ai_memory_intr_event_bootstrap.py`. Because `workers/` is copied wholesale by both canonical resident materialization and static-source refresh, the preferred bootstrap itself is resident-carried without adding another script allow-list dependency. `scripts/run_kv_ai_memory_intr_event_bootstrap.py` is a thin CLI wrapper.

## Event-triggered shared Universal InTr bootstrap

The shared ingress implementation uses loopback and defaults to an ephemeral port. A static listener URL is therefore not a canonical runtime identity and is no longer required by the preferred KV-memory path.

The validated bootstrap reuses the same pattern already established by CanonicalWork:

```text
real fenced context-packet.json + provider-request-input.json
-> normalize already-local shared Universal InTr source
-> instantiate workers.universal_intr_profiled_ingress.Server((127.0.0.1, 0), runtime, 1)
-> receive OS-selected loopback port
-> pass exact one-request /intr/materialization URL only to existing KV-memory consumer
-> existing submitter sends exact packet bytes
-> shared listener returns ALLOW or reject
-> listener closes after one request
-> ALLOW only: memory-packet-admission.json exists
-> existing WorkerCoordinator claim/fence
-> fenced ProviderRequest materialization
```

The bootstrap:

- creates no second listener implementation;
- creates no scheduler or WorkerCoordinator;
- does not read private packet/prompt bytes itself;
- rejects hosted execution;
- does not mint InTr decisions, claims/fences, credentials, provider authority, KV-write authority, or activation authority;
- does not require a preconfigured `STEGVERSE_UNIVERSAL_INTR_INGRESS_URL`.

Preferred command:

```text
python scripts/run_kv_ai_memory_intr_event_bootstrap.py \
  --source-root <canonical-local-source-root> \
  --runtime-root <resident-runtime-root>
```

When private packet/provider inputs are absent, the bootstrap returns `BOUND_STATE_INPUT_NOT_READY` without starting the listener. That is a non-authorizing wait state, not a device or human blocker.

## Alternate exact-target resident bridge

The existing portable bridge remains valid:

```text
python scripts/refresh_and_dispatch_resident_requests.py \
  --source-root <canonical-local-source-root> \
  --runtime-root <resident-runtime-root> \
  --only-consumer kv_ai_memory
```

It now admits `kv_ai_memory` and forwards an explicitly supplied non-secret `STEGVERSE_UNIVERSAL_INTR_INGRESS_URL`. The native worker-service environment also preserves that non-secret binding. This is an alternate path when a shared listener URL already exists; it is not required by the preferred event-triggered path.

## Packet admission contract

The resident-local submission remains:

```text
HTTP loopback only
path = /intr/materialization
X-StegVerse-Transport = InTr
X-StegVerse-Transport-Origin = STEGOS_RESIDENT_LOCAL
X-StegVerse-Payload-SHA256 = exact raw-body SHA-256
X-StegVerse-Authorization-Id = absent
```

The shared listener admission must bind the exact `packet_id`, canonical `packet_sha256`, exact packet validation, and self-consistent `sha256:` receipt hash. The submitter rejects returned evidence that prematurely claims ProviderRequest materialization, provider ingress/execution, KV writeback, credentials, claim/fence creation, HeartBeat execution authority, or request execution authority.

Only a successfully validated listener receipt may populate `inputs/memory-packet-admission.json`.

## ProviderRequest boundary

Canonical surfaces remain:

- `handoffs/SV-KV-AI-PERSISTENCE-001.json`;
- `control/worker-registry.d/kv-ai-memory-resident-001.json`;
- `control/process-worker-adapters.d/kv-ai-memory-resident-001.json`;
- `control/resident-execution-request.d/kv-ai-memory-resident-001.json`;
- `workers/kv_ai_memory_resident_worker.py`;
- LLM-adapter `scripts/materialize_kv_memory_provider_request.py`.

The worker stops at `KV_AI_MEMORY_PROVIDER_REQUEST_MATERIALIZED`. It does not claim provider ingress ALLOW, provider execution, model response, egress ALLOW, or KV writeback.

## Hosted source validation

Relevant successful runs:

- `34803228613`, `34803228620` — LLM bridge/materializer;
- `34803483965` — original resident binding;
- `34804928451` — initial shared packet-admission source;
- `34805361433` — exact admission receipt hash and anti-authority hardening;
- `34805426026` — local route preparation;
- `34805510953` — resident admission orchestration;
- `34812254218`, `34812316750` — no-device/RDC runtime invariant;
- `34812755561` — dispatcher non-starvation regression repair;
- `34812879650` — resident source carriage;
- `34813405596` — portable `kv_ai_memory` selection and endpoint carriage;
- `34813739207` — first event-triggered shared-listener bootstrap validation;
- `34813923637` — resident-native bootstrap/carriage validation;
- `34814058310` — canonical Task Registry reconciliation validation.

Hosted validation proves source behavior only. It does not prove a current sovereign resident has private inputs or that a live packet/provider/KV round trip occurred.

README impact: the existing top-level README already identifies the fenced KV-memory resident state and canonical consumer/WorkerCoordinator lane. This refinement changes how the existing shared listener is instantiated for one event, not the public authority model, so no broad README rewrite is required.

## Next authentic evidence boundary

```text
real fenced Personal-KV packet + provider input
-> resident-native event bootstrap
-> authentic shared-listener exact-packet ALLOW
-> memory-packet-admission.json
-> fresh WorkerCoordinator claim/fence
-> authentic ProviderRequest materialization
```

No receipt may be synthesized from CI, source, fixtures, device identity, or connected-device presence.

## Current truth

```text
canonical task: IN_PROGRESS
KV memory source: VALIDATED
resident KV-memory source carriage: VALIDATED
resident-native event-triggered shared InTr bootstrap: VALIDATED
portable targeted kv_ai_memory dispatch: VALIDATED
Universal InTr endpoint environment carriage: VALIDATED
packet admission profile/transport: VALIDATED
canonical local route preparation: VALIDATED
canonical local packet submitter: VALIDATED
resident WorkerCoordinator binding: VALIDATED
LLM ProviderRequest bridge/materializer: VALIDATED
device discovery/presence/RDC gate: PROHIBITED
real private resident packet/input state: NOT OBSERVED
live shared-listener packet ALLOW: NOT OBSERVED
live WorkerCoordinator ProviderRequest materialization: NOT OBSERVED
live provider/model chain: NOT OBSERVED
live target-KV writeback/readback: NOT OBSERVED
activated: false
authority_effect: NONE_SOURCE_ONLY
```
