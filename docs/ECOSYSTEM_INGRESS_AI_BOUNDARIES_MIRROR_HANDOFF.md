# Ecosystem Ingress + AI Boundaries — Mirror Handoff

Updated: 2026-09-12
Goal Task ID: `ECOSYSTEM-INGRESS-AI-BOUNDARIES-001`
Issue: `StegVerse-Labs/.github#1620`
Status: `ACTIVE / ARCHITECTURAL VALIDATION + ENFORCEMENT`

## Goal

Define, validate, and enforce the StegVerse ecosystem ingress topology and AI-access boundaries independently from generic manifest-processing semantics.

## Registration closure

Registration PR `StegVerse-Labs/.github#1621` passed exact-head validation on `96ce02fbdc1b2edfb735b07324a8cb5583a4956f`:

- organization-control run `34715605044` — PASS;
- Heartbeat validation run `34715605065` — PASS;
- deterministic repository suite run `34715605059` — PASS.

PR #1621 was squash-merged as `42a4f9aa78c86608a90c328b1429e234024c1bd6`.

## Target topology under validation

1. ChatGPT/session coordination enters the Task Registry coordination area only and has no downstream execution authority by virtue of session presence.
2. ChatGPT is the only AI permitted to enter the Task Registry area.
3. Future non-ChatGPT AI support coalesces into a common AI decision-processing region protected by sandbox enforcement and cannot enter Task Registry coordination surfaces.
4. External frameworks/models enter through the LLM Adapter and then canonical SDK manifest ingress only.
5. External evaluators/testers enter the SDK directly and submit manifested data packets only.
6. Direct evaluator injection into Core-Lite, StegCore, StegGate, internal processors, or custody surfaces is forbidden.
7. Downstream of canonical SDK ingress, processing semantics remain controlled by the separate manifest-processing invariant task `SDK-GENERIC-MANIFEST-ECOSYSTEM-INVARIANT-005`.

## Source evidence added after registration merge

The first source-enforcement slice materializes:

- `data/task-registry-ai-ingress-policy.json` — exact actor-kind policy for session-bearing Task Registry AI/interactive ingress;
- `scripts/evaluate_task_registry_ai_session_checkin.py` — fail-closed wrapper that rejects missing actor identity, explicit non-ChatGPT AI kinds, and unknown actor kinds before delegating to the canonical Task Registry collision/check-in evaluator;
- `tests/test_task_registry_ai_session_ingress.py` — tests missing-identity denial, non-ChatGPT AI denial, unknown-kind denial, ChatGPT pass-through, authority ceiling, and runtime-attestation nonclaim;
- `data/task-registry-ai-entry-surface-inventory.json` — first explicit entry-surface inventory and bypass classification.

The source policy allows `CHATGPT_SESSION`, `HUMAN_OPERATOR`, and `NON_AI_SYSTEM_COORDINATOR`; among AI actor kinds, only `CHATGPT_SESSION` is admitted. This is a declaration gate, not cryptographic/provider identity attestation. No runtime identity proof is claimed.

## Entry-surface inventory — current classification

### `scripts/evaluate_task_registry_ai_session_checkin.py`

`PARTIAL / PASS_SOURCE_LEVEL_FOR_DECLARED_ACTOR_KIND`

The wrapper fails closed for missing actor identity and denies explicit non-ChatGPT AI actor kinds before canonical check-in. It does not prove that a caller declaring `CHATGPT_SESSION` is authentically ChatGPT.

### `scripts/evaluate_task_registry_collision_checkin.py`

`NOT_PROVEN / POTENTIAL_BYPASS_IF_AI_REACHABLE`

This remains the canonical general Task Registry check-in evaluator and currently has no observed actor-identity gate. It is legitimate for internal/non-AI coordination use, but ChatGPT-only AI exclusivity is not proven until all callers are classified and external AI reachability to this general entrypoint is closed or constrained.

### `scripts/record_task_registry_session_return.py`

`NOT_PROVEN`

This session-return entrypoint has not yet been shown to apply equivalent AI actor policy.

### `scripts/materialize_task_session_close.py`

`NOT_PROVEN`

Detailed caller/actor-path inventory remains required.

### `scripts/install_and_run_canonical_work_event_bootstrap.py`

`INTERNAL PATH / AI REACHABILITY NOT PROVEN`

This consumes the canonical collision evaluator as internal Canonical Work preflight. It is not classified as AI ingress merely because it touches Task Registry state.

## Evidence already observed outside Task Registry source gate

### Evaluator boundary — strong source evidence

The SDK evaluator handoff explicitly requires:

```text
external evaluator
-> StegVerse SDK manifested submission / normalization / binding
-> Core-Lite manifested route carrier
-> StegCore / canonical StegGate
-> Master Records custody
-> governed result returned through the manifested route
```

It explicitly treats direct evaluator submission/injection to Core-Lite, StegCore, or StegGate as unauthorized and an SDK-bypass path as a boundary violation.

### External framework boundary — partial

SDK generic manifested ingress exists, but LLM Adapter -> canonical SDK generic route delegation remains only partial evidence for this goal. The adjacent manifest-invariant goal owns processor-selection remediation after canonical SDK ingress.

### Common AI decision-processing region / sandbox — not yet materialized as a proven enforcement region

No repository evidence observed yet is sufficient to claim the future non-ChatGPT AI convergence/sandbox boundary exists as an enforced runtime architecture.

## Current classification

- Task Registry AI entry-surface inventory: `PARTIAL_SOURCE_INVENTORY_RUNTIME_REACHABILITY_NOT_PROVEN`.
- ChatGPT-only Task Registry exclusivity: `PARTIAL_SOURCE_DECLARATION_GATE_WRAPPER_ONLY_RUNTIME_IDENTITY_NOT_PROVEN`.
- Non-ChatGPT AI Task Registry denial: `PARTIAL_SOURCE_DECLARATION_GATE_WRAPPER_ONLY`.
- Common AI decision-processing/sandbox region: `NOT_PROVEN`.
- External framework/model -> LLM Adapter -> SDK exclusivity: `PARTIAL`.
- External evaluator/tester -> SDK manifested ingress exclusivity: `PASS_SOURCE_LEVEL_RUNTIME_NOT_PROVEN`.

## Completion predicates

- exact Task Registry AI ingress policy defined;
- every AI/session-capable Task Registry entry surface inventoried;
- all AI session callers routed through the fail-closed AI session gate;
- direct AI reachability to the general Task Registry check-in evaluator prevented or proven impossible;
- ChatGPT-only Task Registry entry backed by authentic origin/identity evidence, not declaration alone;
- non-ChatGPT AI denial/fail-closed behavior proven at runtime;
- common AI decision-processing region defined and sandboxed before additional AI support is activated;
- LLM Adapter is the exclusive framework/model ingress before SDK;
- LLM Adapter delegates into canonical SDK manifest ingress rather than direct processor selection;
- evaluator-facing SDK is the exclusive external evaluator ingress;
- direct evaluator/internal bypass paths rejected;
- coordination ingress, processing ingress, and execution authority remain distinct;
- representative runtime evidence exists for each enforced boundary;
- no completion claim from documentation/source construction alone.

## Authority boundaries

- Task Registry: coordination/work-control surface, not general data-processing ingress.
- ChatGPT/session: coordination client only at Task Registry boundary.
- Future non-ChatGPT AI: AI decision-processing region only; Task Registry access forbidden.
- LLM Adapter: external framework/model protocol ingress only; downstream processing via SDK.
- SDK: external evaluator manifested-data ingress and canonical processing ingress.
- Interlock/InTr: transition transport/admission, not ingress-policy authority.
- TV/TVC: credential authority.
- GitHub Actions: validation/evidence transport only; runtime authority NONE.
- Heartbeat: observability only.

## README completeness review

The root README already documents Canonical Work Task Registry ingress, the Task Registry/WorkerCoordinator/TV-TVC/Interlock-InTr/Master Records authority split, and that session presence does not grant execution authority. This slice adds a scoped source declaration gate and inventory without changing those public authority semantics. No root README text change is required for this source-only slice; any future externally reachable AI ingress surface or runtime identity mechanism is MATERIAL and must update the README in the same change set.

## Separation from adjacent goal

`SDK-GENERIC-MANIFEST-ECOSYSTEM-INVARIANT-005` owns what determines processing after SDK manifest admission.

`ECOSYSTEM-INGRESS-AI-BOUNDARIES-001` owns who may enter through which ecosystem boundary and which alternate/bypass paths must be impossible.

## Next continuation

1. Validate the source-gate branch and merge only on exact-head green evidence.
2. Enumerate every caller of `evaluate_task_registry_collision_checkin.py`, `record_task_registry_session_return.py`, and `materialize_task_session_close.py` and classify each as ChatGPT AI session, human, or non-AI internal coordinator.
3. Route every AI-capable caller through `evaluate_task_registry_ai_session_checkin.py` or enforce equivalent policy at the shared boundary.
4. Define authentic origin/identity evidence required before `CHATGPT_SESSION` can be trusted at runtime.
5. Define the common non-ChatGPT AI decision-processing/sandbox region before enabling additional AI support.
6. Continue LLM Adapter -> SDK exclusivity and evaluator bypass validation without conflating that work with downstream processor-selection invariants.
