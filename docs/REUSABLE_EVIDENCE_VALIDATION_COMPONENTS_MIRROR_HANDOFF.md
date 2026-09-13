# Reusable Evidence Validation Components Mirror Handoff

Updated: 2026-09-12
Parent model: `data/reusable-task-component-model.json`
Component contract: `data/reusable-evidence-validation-component-contract.json`
Discovered by Goal Task: `TVC-RECIPIENT-ADMISSION-OPAQUE-SIGNER-BACKEND-001`
COSV: `50000000102000`
Status: `ACTIVE / SOURCE CONTRACT PROPOSED / RUNTIME SOURCE OF CURRENT BINDING UNPROVEN`

## Discovery

Reusable Task Component reconciliation of the recipient-admission signer found one genuinely reusable missing capability: deterministic selection of the current applicable already-verified KV/SKAP record from a candidate set.

The capability is not signer-specific. Any Goal Task that consumes already-verified KV/SKAP evidence can require the same operation, so the selection rule belongs in a reusable evidence-validation component rather than repeated task-specific code.

## Component

`RTC-EVIDENCE-CURRENT-SELECTOR-010` — Current Applicable Verification Record Selector.

Inputs:

- a non-secret authoritative current-verification binding;
- candidate already-admitted owner-authorization/admission-receipt pairs evaluated internally;
- the current operation context.

The selector identifies exactly one matching pair internally. Its output is limited to the existing non-secret KV/SKAP verification provenance projection, an opaque selected-record reference derived from source digests, and non-secret selection evidence. Source records are not returned.

The selector does not perform user verification, does not create verification state, and does not select the newest record by timestamp.

## Authority separation

KV/SKAP Vault remains the sole user-verification authority. TV/TVC remains credential/provider/release authority and owns admitted credential-transition receipt semantics. The selector has `NONE_EVIDENCE_SELECTION_ONLY` authority effect and cannot make a stale, historical, latest-only, device-bound, or transport-bound record current.

A current-binding input proves only the authoritative KV/SKAP current-state pointer represented by that input. The selector still validates exact candidate bindings and context, and its output does not authorize downstream execution.

## Current binding boundary

The selector does not synthesize a current binding. A consuming Goal Task must supply an authentic source using schema:

```text
stegverse.kv-skap.current-verification-binding/v1
```

The binding identifies the exact owner-authorization digest and admission-receipt digest and may bind task/COSV/purpose and freshness. If no authentic current binding is available, the component stops at `CURRENT_BINDING_MISSING` rather than choosing a candidate heuristically.

## Reentry

For identical inputs, selection is deterministic. Retry is appropriate only when an authoritative current binding or candidate set changes. Latest-by-time fallback is not admissible.

## Runtime evidence boundary

This source contract does not prove that KV/SKAP Vault has emitted a current-verification binding for an active Goal Task. Source merge and CI do not satisfy user-verification or runtime-completion predicates.

## README review

The root README already describes evidence validation as an independent Reusable Task Component family and the authority invariants remain unchanged. This first concrete evidence-validation contract does not require a new root README architecture section.

## Manual work

None.
