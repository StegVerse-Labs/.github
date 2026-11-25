# FDB-CANON-001 — Task Registry Registration Mirror Handoff

Goal Task ID: FDB-CANON-001
Registration request: control/canonical-task-registration-requests/fdb-canon-001.json
Observed Registry generation at proposal: G326 (122 tasks; aggregate sha256 f384240f3da7c085c0c70555c38c5fbac5021dc272101291b69b88a51b2dc271)
STATUS: PROPOSED — registration requested. A manifest proposes; it is not
admission and grants no claim, fence, or execution authority.

## Why this registration exists

This work stood in the Ecosystem KV coordination queue only. On 2026-11-25
the principal directed that ALL work be visible ALL the time to ALL lanes,
whether or not a lane can take it — visibility is a property of the state,
not of eligibility and not of any transport. Entering lanes verify and read
the Canonical Task Registry at entry; work with no state row there is work
a lane cannot see. This registration places the state row. The operative
full text remains the queue item in the Ecosystem KV:

QUEUE__WORK__FREEDOM_SANDBOX_REVIEW_INGRESS__01.md — Ecosystem KV Drive 1SHehQIYwOuA-SLq6eQA0-zsMvfwdl4ur; handoff of record: StegVerse-Labs/FREE-DOM_Books/docs/handoff/FREE_DOM_BOOKS_MIRROR_HANDOFF.md

## Eligibility and discharge

Sandbox determinations per the ingress item; Item 3 must carry an explicit F-FD-1 public-repo disposition or admission fails closed. Production readiness does not authorize release; the author's publication approval remains in force.

Discharge is by the filed receipts the operative text names, or a six-field
non-ALLOW per item. The coordinator verifies each discharge on its record.

## Next admissible transition

INGRESS_ADMITTED, DEFERRED, or SUPERSEDED, under the canonical registration
transition (contracts/canonical-task-registration-transition.v1.json).
