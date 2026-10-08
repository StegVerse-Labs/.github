# SDK-MANIFEST-ECOSYSTEM-TRANSITION-DISPOSITION-001 — Mirror Handoff

Updated: 2026-10-07
Goal Task ID: `SDK-MANIFEST-ECOSYSTEM-TRANSITION-DISPOSITION-001`
Parent Task ID: `SDK-GENERIC-MANIFEST-ECOSYSTEM-INVARIANT-005`
COSV ID: `71000000100126`
Status: `ACTIVE / CHECKED_OUT`

## Goal

After source-conformance repairs, exercise representative governance and non-governance ACTIONS as manifest-bound state transitions and retain terminal ALLOW/DENY/FAIL_CLOSED dispositions, and applicable Organization ledger receipts; also retain Master Records reconstruction evidence taken after the Organization record. That reconstruction is non-gating.

## Inherited invariants

- Every ACTION is a manifest-bound state transition.
- Processing semantics are selected only by admitted `processing.capability` + `processing.route_id` and installed route resolution.
- Terminal attempted-boundary disposition is `ALLOW | DENY | FAIL_CLOSED`.
- Organization ledger append is runtime reality when Organization state changes.
- Master Records is limited to organization records and reconstruction evidence; Organization runtime reality does not depend on it.
- No external machine, listener, session, receiver liveness, hosted service, scheduler, or later observer may be awaited as a transition/completion predicate.
- Receiver unavailability follows `DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION`.

## Remaining predicates

- `MANIFEST_BOUND_INTR_ADMISSION_ATTEMPT_TERMINAL_DISPOSITION_RETAINED`
- `GOVERNANCE_MANIFEST_ROUTE_ATTEMPT_TERMINAL_DISPOSITION_RETAINED`
- `NON_GOVERNANCE_MANIFEST_ROUTE_ATTEMPT_TERMINAL_DISPOSITION_RETAINED`
- `APPLICABLE_ORGANIZATION_STATE_TRANSITION_RECEIPT_RETAINED`
- `APPLICABLE_POST_ORGANIZATION_RECORD_RECONSTRUCTION_EVIDENCE_RETAINED`
- `ALL_ACTIONABLE_SURFACES_CLASSIFIED_CONFORMING_OR_REGISTERED_EXEMPTION`

## Completion discipline

Close only from exact source/runtime evidence appropriate to each predicate. Source/CI/merge evidence must not be promoted to runtime execution. Preserve historical evidence and use registered exemptions only for genuine nonconformance that cannot be repaired; reachability is not an exemption justification.

## 2026-10-07 cross-organization roundtrip source assessment

Source inspection (not execution) identified `StegVerse-org/.github:resident-runtime/run_sv002_self_characterization_roundtrip.py` as a legacy host-coupled specimen: it resolves local checkouts, calls subprocess federation cycles, and rejects hosted environments. It must not become a normative dependency for SV-LLM. `StegVerse-org/.github:org-boundary/registry/federation.json` has 15 entries and no SV-LLM peer at inspected default head. `SV-LLM/.github:org-runtime/crossing.py` already models manifested ingress/egress, no receiver liveness prerequisite, durable queue, and organization ledger append. SDK `stegverse/review_publisher_transfer.py` only prepares Publisher evidence envelopes; Publisher `publisher/intr_artifact_transfer.py` is the existing InTr destination adapter. These are source observations, not live dispositions.

Required repair at existing owners: reconcile federation membership under its registry rules; implement manifest-directed egress/ingress/return with `processing.capability` and `processing.route_id`, independently disposition each attempted boundary, preserve TV/TVC custody and organization-ledger append, use `DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION` rather than host/spool liveness as a prerequisite, and invoke the existing Publisher route only if the admitted manifest requests presentation. No new machine, framework, scheduler, authority, or runtime gate. CI may validate source but cannot attest actual crossing. Non-ALLOW must name the failed predicate and retry edge at the actually invoked boundary; do not fabricate downstream results.

Remaining: owner-specific source repairs, exact-head tests, CI evidence, Organization readback and applicable Master Records reconstruction; that reconstruction is non-gating. No ALLOW, live crossing, Publisher PDF, or runtime validation is claimed by this assessment.
