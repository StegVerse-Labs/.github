# Ecosystem State-Transition Disposition Invariant

Owner: `STEGVERSE-CANONICAL-WORK-COORDINATION-001` (COSV `10100000100000`); source-only proposal for existing issue #1766, not a new goal or a canonical transition.
Date: 2026-09-25. Companion routing owner: issue #1615; external framework publication owners: admissibility-wiki #50 and #66. This document is a proposed reusable contract and does not claim runtime deployment.

## Invariant

Every requested operation is represented as a specific attempted state transition with an explicit predecessor, proposed successor, manifested processing capability and route where applicable, governing constraints, evidence and resulting admissibility disposition. The task advances to the next *actual* actionable non-ALLOW disposition or a proven ALLOW result; it never terminates with an unlabeled "blocker", silent unknown or passive observation request.

`ALLOW` is the only disposition that permits the requested consequence to commit. Every other disposition, including `DENY`, `FAIL_CLOSED` and named STOP/DEFER classes, must preserve non-commit, identify the precise unsatisfied transition condition and provide the next lawful correction/retry edge. A missing datum is a value in the attempted transition's evidence/input state, not an independent completion state or proof of non-occurrence. If the established execution interface cannot be invoked, the *interface-attachment or admission attempt itself* must be evaluated at its actual boundary; do not fabricate a downstream runtime disposition.

A receipt is not self-authorizing: its producer, exact predecessor linkage, constraint result, custody and Master Records reconstruction must be verified before it justifies a successor transition. Receipt existence, source merge, CI success, report publication, or runtime-profile compatibility alone never imply ALLOW.

## Minimal proposed transition-disposition receipt

- Exact task/correlation ID, manifest ID/digest, processing.capability + processing.route_id, producer/boundary, requested action, predecessor state and hash.
- Proposed successor state, evaluated constraint IDs and versions, supplied evidence hashes, missing or conflicting evidence and exact evaluation stage.
- `disposition`: `ALLOW`, `DENY`, `FAIL_CLOSED` or another defined *non-ALLOW* class, with `consequence_committed` true only for an evidenced ALLOW execution.
- `failure_code`, `failed_predicate`, `required_evidence_or_repair`, `retry_entrypoint`, `owning_existing_goal`, and `next_attempt` on non-ALLOW. No vague `BLOCKED`, `UNKNOWN` or `NOT_OBSERVED` may stand alone as a final finding.
- Immediate predecessor receipt reference, receipt digest, organization custody reference where applicable, Master Records reconstruction/validation reference where applicable, and an explicit evidence-class distinction between source validation, synthetic test, attempted ingress, actual execution and public publication.
- Non-ALLOW results must not mutate the denied consequential state; retained failure receipts themselves may validly advance diagnostic/correction state under their own governed transition.

## Execution loop

1. Construct an exact attempted transition from the current canonical predecessor and admitted manifest; resolve route from manifest capability+route only, never model/provider/framework/adapter/source identity.
2. Invoke the existing Interlock/InTr transition path when applicable and obtain the actual disposition. If a call cannot enter, evaluate the failed ingress/attachment transition at the preceding established boundary with its own concrete non-ALLOW disposition; never impersonate an uncalled downstream service.
3. For non-ALLOW, retain the exact failed predicate and remediation receipt, bind it to its predecessor and existing owner, and re-attempt the earliest correctable edge using existing WorkerCoordinator and TV/TVC paths as applicable.
4. For ALLOW, execute only the admitted consequence and retain its organization receipt where applicable, Master Records custody/reconstruction and digest/evidence validation. Continue to the declared next state and terminal closure. A separate post-transition "authentic observer" gate is not allowed after verified canonical closure.
5. If source access, an external permission, or a physical input is genuinely unavailable, record an actionable non-ALLOW disposition for the *actual request to obtain or use it*. State precisely what requires a human or external participant. No simulated outcome is promoted to authentic runtime truth.

## External framework evaluation and visible findings

Use public-source extraction and topology tools such as DeepWiki, gitingest and gitdiagram as optional, interchangeable evidence-acquisition adapters; none determines governance or processor selection. Preserve exact sources, dates, versions, licensing/access limits, and claim-vs-implementation distinctions. Generate a neutral manifest describing the framework, chosen evaluation capability/route, reproducible test inputs and expected evidence. The SDK submits the manifest to the existing evaluator/InTr path, not to a bespoke framework-specific authority.

Publish each finding as a traceable attempted transition: claim and supporting source; exact tested source/version/manifest; proposed S0→S1; governing predicate; actual ALLOW or non-ALLOW disposition and failure code; reproducible receipt/reconstruction links; exact untested boundary, if any, converted into a separately identified next admission/attachment attempt. Separate source-only comparisons, synthetic tests, live execution and unperformed tests. Do not state that a framework failed when the evaluator never ran. Do not award an untested framework a PASS because its documentation claims compatibility.

## Language normalization

Replace misleading phrases implying that an AI or subsystem accumulates, possesses or grants final governance authority with concrete state-transition dependencies, governing constraints, claim/fence scope, custody roles, and admitted consequences. Existing labels containing "authority" may remain machine identifiers until safely migrated; their descriptions must state which exact predicate, boundary and transition they represent. This is a semantic source-audit requirement, not permission to rename external APIs without compatibility work.

## Adoption and evidence

Source-owner review belongs to existing coordination issue #1766, processing-selection issue #1615, SDK existing manifest/evaluator owners, and external evaluation wiki owners #50/#66. Implement bounded validation at each owner's source without cross-owner edits or a new scheduler, runtime, ledger, credentials or device. This documentation branch does not mutate the canonical Registry, imply authenticated AI_SESSION_GATE admission, attest runtime invocation, or close any goal. Only exact-head validation, approved owner transition, retained receipt readback, and Master Records reconstruction can substantiate those claims.
