# Ecosystem Ingress + AI Boundaries — Mirror Handoff

Updated: 2026-09-12
Goal Task ID: `ECOSYSTEM-INGRESS-AI-BOUNDARIES-001`
Issue: `StegVerse-Labs/.github#1620`
Status: `ACTIVE / ARCHITECTURAL VALIDATION + ENFORCEMENT`

## Goal

Define, validate, and enforce StegVerse ecosystem ingress topology and AI-access boundaries independently from generic manifest-processing semantics.

## Completed source slices

Registration PR `#1621` passed exact-head validation and squash-merged as `42a4f9aa78c86608a90c328b1429e234024c1bd6`.

Task Registry AI/session source-gate PR `#1623` passed exact-head organization-control `34715826621`, deterministic repository suite `34715826818`, and Heartbeat validation `34715826744`, then squash-merged as `0b4be7f07ed57cb72055aa6e2264813e16159d53`.

The merged source policy establishes that among AI actor kinds only `CHATGPT_SESSION` is admitted to the session-bearing Task Registry coordination gate. `HUMAN_OPERATOR` and `NON_AI_SYSTEM_COORDINATOR` remain legitimate non-AI actor kinds. The declaration gate is not authentic origin attestation and does not prove runtime ChatGPT identity.

## Current continuation — session return / close source gate

The active continuation extends `data/task-registry-ai-ingress-policy.json` from check-in only to the full session-bearing Task Registry coordination lifecycle.

Source changes under validation:

- `scripts/record_task_registry_session_return.py` now requires `--actor-kind`, fails closed for missing/unknown/non-ChatGPT AI actor kinds, preserves actor kind in the hash-linked event and receipt, and requires a matching gated check-in disposition before a `CHATGPT_SESSION` return is accepted.
- `scripts/materialize_task_session_close.py` now requires and propagates actor kind, verifies the return receipt actor matches the close request, and preserves the source/runtime-attestation nonclaim.
- `data/task-session-close-orchestration-contract.json` now requires `actor_kind`, binds the AI ingress policy, and explicitly requires non-ChatGPT AI denial plus gated ChatGPT check-in continuity before close/handoff emission.
- `tests/test_task_registry_session_return_recorder.py` and `tests/test_task_registry_session_close_orchestration.py` cover missing actor denial, non-ChatGPT AI denial, ChatGPT gated-check-in continuity, non-AI coordinator preservation, authority ceiling, and runtime-attestation nonclaim.
- `data/task-registry-ai-entry-surface-inventory.json` now classifies return/close as source-level gated and leaves the general collision/check-in evaluator as the principal unresolved bypass surface.

This source slice does not claim runtime identity attestation, runtime non-ChatGPT AI denial, or proof that every external AI-capable caller is forced through the gated surface.

## Current classification

- Task Registry AI entry-surface inventory: `PARTIAL_SOURCE_INVENTORY_RUNTIME_REACHABILITY_NOT_PROVEN`.
- ChatGPT-only Task Registry exclusivity: `PARTIAL_SOURCE_SESSION_LIFECYCLE_GATE_RUNTIME_IDENTITY_NOT_PROVEN`.
- Non-ChatGPT AI Task Registry denial: `PARTIAL_SOURCE_SESSION_LIFECYCLE_GATE`.
- Task Registry session return/close AI policy: `PASS_SOURCE_LEVEL_RUNTIME_IDENTITY_NOT_PROVEN` once this continuation validates and merges.
- General `evaluate_task_registry_collision_checkin.py` external-AI bypass closure: `NOT_PROVEN`.
- Common non-ChatGPT AI decision-processing/sandbox region: `NOT_PROVEN`.
- External framework/model -> LLM Adapter -> SDK exclusivity: `PARTIAL`.
- External evaluator/tester -> SDK manifested ingress exclusivity: `PASS_SOURCE_LEVEL_RUNTIME_NOT_PROVEN`.

## Target topology

1. ChatGPT/session coordination enters Task Registry coordination surfaces only and has no downstream execution authority from session presence.
2. ChatGPT is the only AI permitted to enter Task Registry coordination surfaces.
3. Future non-ChatGPT AI converges into a common sandbox-enforced AI decision-processing region with Task Registry access denied.
4. External frameworks/models enter through LLM Adapter -> canonical SDK manifest ingress only.
5. External evaluators/testers enter SDK directly through manifested data submission only.
6. Direct evaluator injection into Core-Lite, StegCore, StegGate, internal processors, or custody surfaces is forbidden.
7. Downstream processor-selection semantics remain owned by `SDK-GENERIC-MANIFEST-ECOSYSTEM-INVARIANT-005`.

## Authority model

- Task Registry: coordination/work-control truth only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: transition/admission authority.
- TV/TVC: credential authority.
- Master Records: observed-reality/reconstruction authority.
- ChatGPT/session: coordination client only; no downstream execution authority.
- GitHub Actions: validation/evidence transport only; runtime authority NONE.
- Heartbeat: observability only.

## Completion predicates

- every AI/session-capable Task Registry entry surface inventoried;
- all AI session callers routed through fail-closed Task Registry AI policy;
- direct AI reachability to the general Task Registry check-in evaluator prevented or proven impossible;
- ChatGPT-only entry backed by authentic origin/identity evidence, not declaration alone;
- non-ChatGPT AI denial proven at runtime;
- common AI decision-processing region defined and sandboxed before additional AI support is activated;
- LLM Adapter is exclusive framework/model ingress before SDK;
- LLM Adapter delegates into canonical SDK manifest ingress;
- evaluator-facing SDK is exclusive external evaluator ingress;
- direct evaluator/internal bypass paths rejected;
- coordination ingress, processing ingress, and execution authority remain distinct;
- representative runtime evidence exists for each enforced boundary;
- no completion claim from source/documentation alone.

## README review

The root README already documents Canonical Work Task Registry ingress, the Task Registry/WorkerCoordinator/TV-TVC/Interlock-InTr/Master Records authority split, and that session presence does not grant execution authority. This continuation tightens internal session lifecycle source validation without changing those public authority semantics, so no root README text rewrite is required for this slice. Any externally reachable AI ingress or authentic runtime identity mechanism is MATERIAL and must update the README in the same change set.

## Next continuation

1. Validate and merge the session return/close source gate only on exact-head green evidence.
2. Enumerate every caller of `scripts/evaluate_task_registry_collision_checkin.py` and classify each as ChatGPT session, human, or non-AI internal coordinator.
3. Route any AI-capable caller through `scripts/evaluate_task_registry_ai_session_checkin.py` or enforce the same policy at the shared external boundary.
4. Prevent direct external AI reachability to the general collision/check-in evaluator or prove that reachability impossible.
5. Define authentic ChatGPT-origin evidence before promoting declaration-level source gating to runtime exclusivity.
6. Define the common non-ChatGPT AI decision-processing/sandbox region before enabling additional AI support.
7. Continue LLM Adapter -> SDK exclusivity and evaluator-bypass validation without conflating that work with downstream processor-selection invariants.
