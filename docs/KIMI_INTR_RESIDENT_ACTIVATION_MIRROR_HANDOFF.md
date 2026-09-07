# Kimi InTr Resident Activation Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-Labs/.github`
Issue: `#1120`
Branch: `feat/kimi-intr-resident-activation-1120`
Goal: `KIMI-INTR-RESIDENT-ACTIVATION-001`

## Authority

```text
canonical resident carrier: existing HB32 / oscillator substrate
claim/fence authority: existing WorkerCoordinator
exact-packet transport evidence: canonical Universal InTr / TRANSPORT_COMPLETE
governance disposition: canonical Governance/StegCore ALLOW | DENY | FAIL-CLOSED
credential/provider-operation authority: TV/TVC
provider transport/evidence owner: StegVerse-org/LLM-adapter
Universal InTr profile owner: StegVerse-Labs/StegOS
Governance profile owner: StegVerse-Labs/Governance
observed-reality/custody owner: master-records/orchestration
GitHub Actions runtime authority: NONE
heartbeat grants execution authority: false
request grants execution authority: false
second user-operated machine required: false
provider credential material in .github: PROHIBITED
Master Records credential material in .github: PROHIBITED
```

This lane MUST NOT create a second heartbeat, oscillator, scheduler, WorkerCoordinator, governance evaluator, InTr backbone, credential authority, vault, or Master Records authority.

## Goal

Produce one authentic governed Kimi round trip on the existing StegVerse resident runtime:

```text
existing WorkerCoordinator fresh claim/fence
-> exact TVC/Moonshot provider JSON bytes
-> canonical Universal InTr external-provider-operation transport
-> TRANSPORT_COMPLETE bound to exact provider bytes
-> canonical hosted-LLM Governance profile
-> canonical StegCore ALLOW/DENY/FAIL-CLOSED decision
-> separate valid TVC single-use Kimi lease
-> TVC non-exportable provider operation
-> authentic Moonshot/Kimi response
-> LLM-adapter sanitized response/usage evidence
-> Master Records local non-exportable custody + reconstruction PASS
-> exact response bytes through Universal InTr
-> exact resident receipt bundle
```

No source merge, CI result, transport completion, Governance ALLOW, TVC lease, provider response, or Master Records record substitutes for the others.

## Canonical source dependencies

Completed upstream source dependencies:

- `StegVerse-org/LLM-adapter` Kimi runtime integration and exact-message preservation are merged.
- `StegVerse-org/LLM-adapter#303` separates Universal InTr `TRANSPORT_COMPLETE` from Governance `ALLOW` and requires Master Records custody before canonical egress.
- `StegVerse-org/LLM-adapter#311` merged as `5aad95bd202809d82d4d19a7cbcf1224eeb81724`; canonical production admission hashes the exact non-secret TVC/Moonshot provider payload `{model,messages,max_tokens,stream[,response_format]}` and preserves that admitted envelope through TVC execution.
- `StegVerse-Labs/StegOS#223` merged and validated; owns `external-provider-operation` Universal InTr profile.
- `StegVerse-Labs/Governance#39` merged and validated; owns `hosted-llm-provider-operation.v1`.
- `master-records/orchestration#83` merged and validated; owns the local non-exportable provider-usage custody broker.
- `StegVerse-Labs/TVC` existing Kimi operation profile continues to own `vault://tvc/providers/kimi/api-key`, `chat_completion_with_usage`, and `kimi-k3`; key bytes remain broker-local.

No new credential, transport-authority, Governance-authority, custody-authority, HB, or scheduler semantics were introduced.

## Exact request constraint

Kimi TVC runtime v1 currently admits exactly one `user` message and sends its content unchanged to TVC. Multi-message or non-user-role requests fail closed until TVC exposes a message-preserving chat operation contract.

The resident probe uses one deterministic non-secret user message derived from the already-pinned SV-RECON-001 task. The active v2 worker uses the canonical LLM-adapter `kimi_tvc_provider_wire` functions with `max_output_tokens=4096` and `response_format=json`; those exact parameters are hash-bound before InTr admission and checked again before the TVC broker call.

## Current resident surfaces

```text
handoffs/KIMI-INTR-RESIDENT-ACTIVATION-001.json
control/worker-registry.d/kimi-intr-resident-activation-001.json
control/process-worker-adapters.d/kimi-intr-resident-activation-001.json
control/resident-execution-request.d/kimi-intr-resident-activation-001.json
workers/kimi_intr_resident_activation_worker.py       legacy branch implementation, not active adapter
workers/kimi_intr_resident_activation_worker_v2.py    active exact-wire implementation
scripts/refresh_and_execute_kimi_intr_resident_task.py
scripts/consume_kimi_intr_resident_activation_request.py
tests/test_kimi_intr_resident_activation.py
docs/KIMI_INTR_RESIDENT_ACTIVATION_MIRROR_HANDOFF.md
```

The process adapter selects only `kimi_intr_resident_activation_worker_v2.py`. No new listener or scheduler exists.

## Runtime truth requirements

The v2 worker derives Governance inputs from current runtime evidence rather than hard-coding a favorable result. It verifies:

1. current WorkerCoordinator invocation/claim/fence supplied by the existing worker runtime;
2. current admitted capability scope;
3. canonical local source/profile presence for LLM-adapter, StegOS, Governance, StegCore, TVC, Test Lanes, and Master Records;
4. TVC broker and Master Records local custody Unix sockets are actual local sockets before any provider consequence;
5. no provider/GitHub/Master Records secret-bearing environment reaches the worker;
6. exact TVC/Moonshot provider bytes hash to the value transported by Universal InTr;
7. Universal InTr returns `TRANSPORT_COMPLETE` for that exact payload;
8. Governance receives the same exact candidate hash and current claim/fence/profile/transport facts;
9. only a canonical StegCore `ALLOW` continues;
10. TVC produces a valid Kimi single-use capability lease;
11. the TVC operation submitted to the vault broker still has the admitted provider/model/prompt/max-output/response-format/request-hash tuple;
12. LLM-adapter preserves the admitted exact envelope through provider execution;
13. Master Records custody is recorded and reconstruction reports PASS;
14. Universal InTr egress payload hash matches the exact canonical response bytes;
15. terminal completion requires every same-execution predicate to be true.

Missing evidence maps to `BLOCKED` / `DENY` / `FAIL_CLOSED`; the worker must not synthesize proof.

## README impact preflight

This work adds one bounded resident task and a task-specific worker revision. It does not change the organization-level architecture, HB semantics, WorkerCoordinator semantics, credential model, generic process-adapter contract, or public interface already documented by the existing organization/runtime handoffs. Root README change is not required for this change set.

## Completion predicates

1. Scoped mirror handoff exists. **COMPLETE**
2. LLM-adapter exact TVC/Moonshot provider-byte binding merged/validated. **COMPLETE**
3. Canonical StegOS provider-operation InTr profile merged/validated. **COMPLETE**
4. Canonical Governance hosted-LLM profile merged/validated. **COMPLETE**
5. Master Records local non-exportable custody broker merged/validated. **COMPLETE**
6. Resident task/worker/adapter/request source installed. **COMPLETE ON BRANCH**
7. Resident repository validation passes and branch is merged. **PENDING CI / MERGE**
8. Existing resident WorkerCoordinator consumes the task under a fresh valid claim/fence. **RUNTIME PENDING**
9. Authentic exact-byte InTr ingress + StegCore decision + TVC Kimi operation + Master Records custody + exact-byte InTr egress observed in one execution. **RUNTIME PENDING**
10. Exact runtime evidence retained and reconciled; only then may activation be claimed or propagated. **RUNTIME PENDING**

## Propagation after authentic activation

After predicate 10, verify/update as applicable:

- `StegVerse-Labs/StegIndex`
- `StegVerse-Labs/Site`
- `GCAT-BCAT-Engine/Publisher`
- `StegVerse-Labs/admissibility-wiki`
- `StegVerse-002/stegguardian-wiki`

No downstream surface may claim Kimi activation from source/CI alone.

## Current status

`SOURCE_BUILD_COMPLETE_PENDING_CI_MERGE / AUTHENTIC_RUNTIME_ROUND_TRIP_NOT_YET_OBSERVED`.
