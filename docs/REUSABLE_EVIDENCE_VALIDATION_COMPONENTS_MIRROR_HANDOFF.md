# Reusable Evidence Validation Components Mirror Handoff

Updated: 2026-09-12
Parent model: `data/reusable-task-component-model.json`
Component contract: `data/reusable-evidence-validation-component-contract.json`
Discovered by Goal Task: `TVC-RECIPIENT-ADMISSION-OPAQUE-SIGNER-BACKEND-001`
COSV: `50000000102000`
Status: `ACTIVE / SOURCE CONTRACT PROPOSED / RUNTIME SOURCE OF CURRENT BINDING UNPROVEN`

## Discovery

Reusable Task Component reconciliation of the recipient-admission signer found one genuinely reusable missing capability: deterministic selection of the **current applicable already-verified KV/SKAP record** from a candidate set.

The capability is not signer-specific. Any Goal Task that consumes already-verified KV/SKAP evidence can need the same operation, and embedding “choose the current record” independently in each task would duplicate evidence-selection semantics.

## Component

`RTC-EVIDENCE-CURRENT-SELECTOR-010` — Current Applicable Verification Record Selector.

The selector accepts:

- a non-secret authoritative current-verification binding;
- candidate already-admitted owner-authorization/admission-receipt pairs;
- the current operation context.

It returns exactly one selected pair plus non-secret selection evidence, or fails closed.

The selector does not perform WebAuthn, does not create verification, does not mint user identity, does not decrypt credentials, and does not select the newest record by timestamp.

## Authority separation

KV/SKAP Vault remains the sole user-verification authority. TV/TVC remains credential/provider/release authority and owns the semantics of an admitted credential transition receipt. The selector itself is `NONE_EVIDENCE_SELECTION_ONLY` and cannot make a stale, historical, merely latest, device-bound, transport-bound, or unauthenticated record current.

A current-binding input proves only the authoritative KV/SKAP current-state pointer represented by that input. The selector still validates exact candidate bindings and context; its output does not authorize downstream execution.

## Current binding boundary

The reusable selector deliberately does not synthesize a current binding. A consuming Goal Task must supply an authentic current-binding source with schema:

```text
stegverse.kv-skap.current-verification-binding/v1
```

The binding must identify the exact owner-authorization digest and admission-receipt digest and may bind task/COSV/purpose and freshness. If no authentic current binding is available, the component stops at `CURRENT_BINDING_MISSING` rather than choosing a candidate heuristically.

## Reentry

For identical inputs, selection is deterministic. A failed selection may be retried only when an authoritative current binding or candidate set changes. “Try the latest candidate” is not an admissible remediation.

## Runtime evidence boundary

This source contract does not prove that KV/SKAP Vault has emitted a current-verification binding for any active Goal Task. Source merge and CI therefore do not satisfy any task’s user-verification or runtime-completion predicate.

## README review

The root README already describes evidence validation as an independent Reusable Task Component family and the authority invariants remain unchanged. Materializing this first concrete evidence-validation contract does not change the repository-wide model semantics enough to require a new root README architecture section.

## Manual work

None.
