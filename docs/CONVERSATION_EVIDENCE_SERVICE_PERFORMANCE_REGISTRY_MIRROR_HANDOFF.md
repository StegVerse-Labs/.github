# Conversation Evidence / Service Performance Registry Mirror Handoff

Updated: 2026-09-19
Repository: `StegVerse-Labs/.github`
Canonical issue: `#2204`
Goal Task ID: `CONVERSATION-EVIDENCE-SERVICE-PERFORMANCE-REGISTRY-001`
COSV ID: `NOT YET ESTABLISHED`
Status: `RETIRED / CONTRACT DESIGNED+REGISTERED+MERGED / IMPLEMENTATION NOT STARTED`

## Purpose

Define the exact governed evidence contract for publishing service-performance disputes when the source conversation itself is material evidence.

The task is intentionally separate from the generic Site publication runtime task. Publication infrastructure may be reused later, but this task owns the evidence semantics, privacy/public-derivative boundary, provider response, corroboration, reconstruction, and enforcement-export contract.

## Canonical contract

`contracts/conversation-evidence-service-performance-publication-contract.v1.json`

The contract requires three distinct artifacts:

1. **Evidence Original** — complete preserved conversation/export bytes, ordered messages, attachments, capture provenance, participant assertions, and hashes. It is write-once.
2. **Governed Public Record** — a derivative of the Evidence Original with an explicit redaction manifest, transaction/service-performance binding, evidence state, provider-response state, corroboration summary, provenance, and non-adjudication notice.
3. **Authorized Enforcement Export** — the unabridged evidence package plus custody/reconstruction receipts and jurisdiction metadata. Export authorization does not create enforcement authority.

## Evidence semantics

- A complaint is an allegation, not a finding.
- A payment proves only the evidenced payment facts, not nonperformance.
- A compensation request does not establish predatory conduct.
- Recurrence can support a documented pattern of similar transactions but does not establish intent by itself.
- No response is recorded as no response, not an admission.
- Provider responses and counterevidence are preserved under the same provenance rules.
- Corroborating customer submissions require their own independently evidenced transaction/service relationship to count as transactional corroboration.
- Popularity signals and unsupported accusations are excluded from evidence-weighted corroboration.

## Original capture and attachment rules

The original conversation is immutable. Corrections and later evidence produce superseding records rather than rewriting the source.

Every message has a stable ordinal, source identifier when available, speaker assertion, timestamp assertion/precision, exact content representation, attachment references, and digest.

Every attachment preserves original bytes and digest. Any preview, OCR/transcript, thumbnail, or normalized version is a separately identified derivative.

## Redaction rules

Public projection never silently edits the source.

Every redaction records its location, original-fragment digest, reason code, replacement marker, policy version, and the resulting public-record digest. The unabridged original remains separately retained.

## Transaction / performance binding

The record can bind:

`service representation -> agreement/scope -> invoice/request -> payment evidence -> delivery/performance evidence -> refund/remediation -> dispute event`

Governed evidence states are intentionally narrow:

`NOT_EVALUATED`
`PERFORMANCE_SUPPORTED`
`PARTIAL_PERFORMANCE_SUPPORTED`
`NONPERFORMANCE_SUPPORTED`
`CONTESTED`
`INSUFFICIENT_EVIDENCE`

These are evidence states, not criminal/civil judgments.

## Provider response

A counterparty receives a governed path to submit a response and counterevidence. Response state is explicit: `NOT_REQUESTED`, `REQUESTED`, `RECEIVED`, `DECLINED`, or `NO_RESPONSE_BY_DISCLOSED_CUTOFF`.

## Jurisdiction-aware public projection

The contract records payer, provider, contract, payment-processor, performance-location, and publication-review jurisdiction facts when known. It records whether publication review is required, cleared for a defined derivative, restricted, or withheld.

The contract itself does not decide what publication is lawful.

## Master Records

Every governed publication, redaction supersession, provider-response admission, corroborating submission admission, and enforcement-export authorization must be separately reconstructable.

Progression requires:

`state=RECORDED`
`reconstruction_status=PASS`
`required_evidence_validation_status=PASS`
`receipt_sha256 == reconstructed_receipt_sha256`

## Authority boundary

Task Registry records work intent only.
WorkerCoordinator remains claim/fence authority.
Interlock/InTr remains governed transition authority.
Master Records remains observed-reality/reconstruction authority.
TV/TVC remains credential/scoped authority where applicable.

This task registration does not authenticate an existing conversation, identify a wrongdoer, establish legal liability, publish evidence, or authorize enforcement.

## Completion evidence

- Registration/design PR: `StegVerse-Labs/.github#2205`
- Exact validated PR head: `23992c7cab916581402b76e0a9e79f991d2455b3`
- Squash merge: `8f9f85d510deb47eec0e70492163c7beb365d03c`
- Canonical Task Registry registration generation: `85`
- Post-merge closure generation: `86`
- The contract-design goal is complete. No Site ingestion/UI, Master Records adapter, publication runtime, provider-response runtime, corroboration runtime, or enforcement-export implementation is claimed.

## Successor implementation boundary

Any implementation must use a new standalone canonical Goal Task that consumes this contract unchanged or explicitly versions it. The successor should implement evidence ingestion/capture first, then Master Records custody/reconstruction, then governed public projection, provider-response/corroboration paths, and finally authorized enforcement export. It must not infer legal guilt, fraud, predation, intent, or liability from publication, payment, recurrence, or nonresponse.

## Initial completion boundary

The first bounded milestone is complete only when:

- the standalone task is present in the canonical Task Registry;
- this mirror handoff exists;
- the v1 contract exists;
- README points to the task and contract;
- exact-source validation confirms the JSON artifacts parse and the task shard conforms to the canonical task-record schema.

Implementation of Site UI, ingestion, Master Records adapters, or enforcement export is a later transition and is not claimed by the contract milestone.
