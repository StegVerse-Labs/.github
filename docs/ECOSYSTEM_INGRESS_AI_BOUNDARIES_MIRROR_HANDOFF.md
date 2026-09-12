# Ecosystem Ingress + AI Boundaries — Mirror Handoff

Updated: 2026-09-12
Goal Task ID: `ECOSYSTEM-INGRESS-AI-BOUNDARIES-001`
Issue: `StegVerse-Labs/.github#1620`
Status: `ACTIVE / ARCHITECTURAL VALIDATION + ENFORCEMENT`

## Goal

Define, validate, and enforce the StegVerse ecosystem ingress topology and AI-access boundaries independently from generic manifest-processing semantics.

## Target topology under validation

1. ChatGPT/session coordination enters the Task Registry coordination area only and has no downstream execution authority by virtue of session presence.
2. ChatGPT is the only AI permitted to enter the Task Registry area.
3. Future non-ChatGPT AI support coalesces into a common AI decision-processing region protected by sandbox enforcement and cannot enter Task Registry coordination surfaces.
4. External frameworks/models enter through the LLM Adapter and then canonical SDK manifest ingress only.
5. External evaluators/testers enter the SDK directly and submit manifested data packets only.
6. Direct evaluator injection into Core-Lite, StegCore, StegGate, internal processors, or custody surfaces is forbidden.
7. Downstream of canonical SDK ingress, processing semantics remain controlled by the separate manifest-processing invariant task `SDK-GENERIC-MANIFEST-ECOSYSTEM-INVARIANT-005`.

## Evidence already observed

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

SDK generic manifested ingress exists, but current LLM Adapter governed ingress still contains direct injected `governance_handler` behavior. Therefore LLM Adapter -> canonical SDK generic route delegation is not yet proven end-to-end.

### ChatGPT / Task Registry exclusivity — not proven

Current Task Registry/session handoffs separate ChatGPT coordination state from execution and state that ChatGPT is not part of downstream execution chains. That does not yet prove technical exclusivity preventing every other AI/model from reaching Task Registry entry surfaces.

### Common AI decision-processing region / sandbox — not yet materialized as a proven enforcement region

No repository evidence observed yet is sufficient to claim the future non-ChatGPT AI convergence/sandbox boundary exists as an enforced runtime architecture.

## Required validation inventory

Classify as `PASS`, `PARTIAL`, `VIOLATION`, or `NOT_PROVEN`:

1. ChatGPT -> Task Registry coordination entry surfaces.
2. Non-ChatGPT AI -> Task Registry denial surfaces.
3. Common AI decision-processing region and sandbox enforcement.
4. External framework/model -> LLM Adapter -> SDK exclusivity.
5. External evaluator/tester -> SDK manifested ingress exclusivity.
6. Direct bypass attempts to Core-Lite / StegCore / StegGate / internal processors.
7. Session coordination vs execution-authority separation.
8. Adapter and provider paths that could accidentally expose Task Registry or internal processing surfaces.

## Completion predicates

- exact Task Registry AI ingress policy defined;
- ChatGPT-only Task Registry entry enforcement proven;
- non-ChatGPT AI denial/fail-closed behavior proven;
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

## Separation from adjacent goal

`SDK-GENERIC-MANIFEST-ECOSYSTEM-INVARIANT-005` owns what determines processing after SDK manifest admission.

`ECOSYSTEM-INGRESS-AI-BOUNDARIES-001` owns who may enter through which ecosystem boundary and which alternate/bypass paths must be impossible.

## Next continuation

1. Inventory Task Registry entry surfaces and identify every AI/model-accessible path.
2. Prove or remediate ChatGPT-only Task Registry exclusivity.
3. Define the common AI decision-processing/sandbox region before enabling additional AI support.
4. Patch LLM Adapter external-framework ingress to canonical SDK-only delegation.
5. Validate evaluator SDK-only ingress and add explicit bypass rejection tests.
6. Record source + runtime evidence separately and fail closed on unproven exclusivity claims.
