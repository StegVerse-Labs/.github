# KV AI Memory Resident Execution Mirror Handoff

Status: ACTIVE / SOURCE-BINDING-IN-PROGRESS / LIVE-RUNTIME-PROOF-OPEN
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

This handoff does not authorize execution. Repository source, CI, request files, dispatcher registration, or successful local validation cannot substitute for an authentic claim/fence or Interlock/InTr receipt.

## Bounded resident composition target

```text
resident-local Personal-KV context packet
+ exact memory-packet InTr ALLOW receipt
+ resident-local user/model request material
-> validate exact packet + admission
-> materialize canonical ProviderRequest with KV provenance
-> preserve exact ProviderRequest hash
-> hand the request to the existing provider ingress path
-> preserve provider ingress / TVC operation / response / egress evidence
-> optional memory write proposal
-> target-KV admission and exact readback
```

Private KV contents and user prompts must remain resident-local. No private memory payload, prompt, credential, token, or provider secret belongs in the GitHub resident request object.

## Source implementation plan

1. Add an LLM-adapter materializer that consumes resident-local packet/admission/message files and emits one exact canonical `ProviderRequest` plus hash.
2. Add a non-authorizing `.github` resident request consumer that resolves already-local KV/LLM roots and invokes that materializer.
3. Register that consumer with the existing generic resident dispatcher.
4. Preserve exactly-once request-consumption semantics and reject hosted execution.
5. Stop at `PROVIDER_REQUEST_MATERIALIZED` unless an already-admitted existing provider executor is available in the same resident runtime. Do not fabricate ingress, TVC, provider, egress, custody, writeback, or activation evidence.

## Completion evidence

Source completion for this resident binding requires deterministic tests and hosted validation of the request consumer/materializer. Live goal completion additionally requires authentic same-execution evidence for:

- exact memory packet admission;
- exact ProviderRequest materialization;
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
resident memory binding: SOURCE IMPLEMENTATION IN PROGRESS
live memory packet admission: NOT OBSERVED
live model consumption: NOT OBSERVED
live KV writeback/readback: NOT OBSERVED
activated: false
authority_effect: NONE_SOURCE_ONLY
```
