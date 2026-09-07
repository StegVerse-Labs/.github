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
transition/governance admission: canonical Interlock/InTr + StegCore three-layer evaluation
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
```

This lane MUST NOT create a second heartbeat, oscillator, scheduler, WorkerCoordinator, governance evaluator, InTr backbone, credential authority, vault, or Master Records authority.

## Goal

Produce one authentic governed Kimi round trip on the existing StegVerse resident runtime:

```text
existing WorkerCoordinator claim/fence
-> exact Kimi candidate/request binding
-> canonical Universal InTr provider-operation request transport
-> canonical hosted-LLM Governance profile
-> canonical StegCore ALLOW/DENY/FAIL-CLOSED decision
-> separate valid TVC single-use Kimi lease
-> TVC non-exportable provider operation
-> authentic Moonshot/Kimi response
-> LLM-adapter sanitized response/usage evidence
-> Master Records custody/reconstruction
-> canonical Universal InTr response transport
-> exact resident receipt bundle
```

No source merge, CI result, transport completion, Governance ALLOW, TVC lease, provider response, or Master Records record substitutes for the others.

## Canonical source dependencies

- `StegVerse-org/LLM-adapter` Kimi transport/runtime integration merged through PRs #293 and #295.
- `StegVerse-org/LLM-adapter` exact request-preservation fix PR #298 merged as `9fb66fbf59b4797857f1747b3796956d0c6cc405`.
- `StegVerse-Labs/StegOS` issue #222 / PR #223 owns `external-provider-operation`; merge + CI required before resident execution.
- `StegVerse-Labs/Governance` issue #38 / PR #39 owns `hosted-llm-provider-operation.v1`; merge + CI required before resident execution.
- `StegVerse-Labs/TVC` existing Kimi operation profile uses `vault://tvc/providers/kimi/api-key`, `chat_completion_with_usage`, and `kimi-k3`; key bytes must remain broker-local.
- Existing `.github` Test Lanes direct-run support for Kimi is reusable source evidence but does not itself establish the required InTr/Governance/Master Records round trip.

## Exact request constraint

Kimi TVC runtime v1 currently admits exactly one `user` message and sends its content unchanged to TVC. Multi-message or non-user-role requests fail closed until TVC exposes a message-preserving chat operation contract.

The resident activation probe will therefore use one deterministic non-secret user message only.

## Runtime truth requirements

The worker may derive governance facts only from current resident evidence. It may not hard-code truthy `resolved_facts` merely to obtain ALLOW. At minimum it must verify:

1. current WorkerCoordinator invocation/claim/fence supplied by the existing worker runtime;
2. exact merged source/profile identities for StegOS, Governance, LLM-adapter, TVC, and Master Records;
3. exact canonical InTr request completion and receipt binding;
4. current policy/profile/authority references;
5. current TVC lease validity and exact Kimi/model/operation binding;
6. no provider/GitHub secret-bearing environment passed to the worker;
7. TVC result reports single-use consumption and no secret return/log/retention;
8. LLM-adapter response remains non-authoritative and requires egress InTr;
9. Master Records custody/reconstruction succeeds before terminal completion;
10. exact response transport completes after provider result.

Missing evidence maps to `BLOCKED` / `DENY` / `FAIL_CLOSED`; the worker must not synthesize proof.

## README impact preflight

This work materially adds a resident task but does not change the organization-level architecture, authority boundaries, HB semantics, WorkerCoordinator semantics, credential model, or generic runtime contract already documented by `docs/ORG_MIRROR_HANDOFF.md`, `HB_MACHINE_CONTINUATION_MIRROR_HANDOFF.md`, and existing resident-worker documentation. A root README update is not required unless implementation introduces a new public interface or changes generic resident-runtime behavior.

## Planned resident surfaces

```text
handoffs/KIMI-INTR-RESIDENT-ACTIVATION-001.json
control/worker-registry.d/kimi-intr-resident-activation-001.json
control/process-worker-adapters.d/kimi-intr-resident-activation-001.json
control/resident-execution-request.d/kimi-intr-resident-activation-001.json
workers/kimi_intr_resident_activation_worker.py
tests/test_kimi_intr_resident_activation.py
docs/KIMI_INTR_RESIDENT_ACTIVATION_MIRROR_HANDOFF.md
```

Any dispatcher change must reuse the existing resident request dispatcher and selector mechanism. No new listener or scheduler is allowed.

## Completion predicates

1. Scoped mirror handoff exists. **COMPLETE**
2. LLM-adapter exact Kimi TVC binding merged/validated. **COMPLETE**
3. Canonical StegOS provider-operation InTr profile merged/validated. **PENDING**
4. Canonical Governance hosted-LLM profile merged/validated. **PENDING**
5. Resident task/worker/adapter/request source installed and repository validation passes. **PENDING**
6. Existing resident WorkerCoordinator consumes the request under a fresh valid claim/fence. **RUNTIME PENDING**
7. Authentic InTr ingress + StegCore decision + TVC Kimi operation + Master Records custody + InTr egress observed in one execution. **RUNTIME PENDING**
8. Exact runtime evidence retained and reconciled; only then may activation be claimed or propagated. **RUNTIME PENDING**

## Propagation after authentic activation

After predicate 8, verify/update as applicable:

- `StegVerse-Labs/StegIndex`
- `StegVerse-Labs/Site`
- `GCAT-BCAT-Engine/Publisher`
- `admissibility-wiki`
- `stegguardian-wiki`

No downstream surface may claim Kimi activation from source/CI alone.

## Current status

`SOURCE_BUILD_IN_PROGRESS / AUTHENTIC_RUNTIME_ROUND_TRIP_NOT_YET_OBSERVED`.
