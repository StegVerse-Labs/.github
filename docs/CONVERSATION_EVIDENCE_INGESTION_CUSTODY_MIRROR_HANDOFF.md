# Conversation Evidence Ingestion / Custody Mirror Handoff

Updated: 2026-09-19
Repository: `StegVerse-Labs/.github`
Canonical issue: `#2258`
Goal Task ID: `CONVERSATION-EVIDENCE-INGESTION-CUSTODY-001`
Parent design task: `CONVERSATION-EVIDENCE-SERVICE-PERFORMANCE-REGISTRY-001`
COSV ID: `20011000100000`
Status: `ACTIVE / FIRST BOUNDED IMPLEMENTATION PHASE`

## Contract boundary

Consumes `contracts/conversation-evidence-service-performance-publication-contract.v1.json` unchanged.

This phase implements only immutable evidence ingestion, authenticity-envelope construction, service/transaction/performance binding, required-evidence carriage, and canonical Master Records custody/reconstruction. It does not implement public Site projection, provider-response UI, corroboration UI, enforcement export, or legal/reputational adjudication.

## Implementation

- `workers/conversation_evidence_ingestion.py` builds deterministic ingestion packages, preserves ordered message content/digests and exact attachment bytes/digests, refuses overwrite on persisted record roots, and creates explicit authenticity and transaction bindings.
- `schemas/conversation-evidence-ingestion-package.schema.json` identifies the ingestion-package envelope.
- `tests/test_conversation_evidence_ingestion.py` covers deterministic packaging, write-once behavior, attachment hashing, unchanged v1 contract consumption, exact required-evidence carriage, successful Master Records closure, and fail-closed digest mismatch.
- Existing `workers/canonical_state_transition_custody.py` remains the sole Python custody client. No second Master Records service/store is introduced.

## Master Records transition

Transition: `CONVERSATION_EVIDENCE_INGESTED`.

Required evidence:
1. `CONVERSATION_EVIDENCE_ORIGINAL`
2. `CONVERSATION_AUTHENTICITY_ENVELOPE`
3. `SERVICE_TRANSACTION_BINDING`

Progression requires `RECORDED`, `reconstruction_status=PASS`, `required_evidence_validation_status=PASS`, and exact receipt/reconstruction digest equality.

Source tests may prove the consumer enforces this contract; only an authentic Master Records return can prove runtime custody/reconstruction.

## Privacy / authority

No source conversation is committed by this task. Test fixtures are synthetic.
The ingestion transition records evidence only. It performs no publication and no adjudication.
Interlock/InTr transition authority and Master Records custody/reconstruction authority remain unchanged.

## Next boundary

After exact-head source validation and merge, run an authentic synthetic ingestion through the existing Master Records custody surface. Only after that returns the full progression tuple may this phase claim authentic custody completion or derive a later public-projection implementation task.
