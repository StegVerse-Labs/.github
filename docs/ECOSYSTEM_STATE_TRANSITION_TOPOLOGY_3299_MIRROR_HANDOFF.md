# Ecosystem state-transition topology and sovereign receipt conformance

Status: coordination proposal; not Registry admission or runtime certification. Canonical issue: https://github.com/StegVerse-Labs/.github/issues/3299

## Invariants
- A transition produces resulting state. The admissibility matrix evaluates that state against its manifest, evidence and predicates and returns ALLOW, DENY or FAIL_CLOSED. A transition **never grants, confers or transfers authority**.
- Authority is a state variable. A datum classified SECRET carries a manifest minimum authority threshold for ALLOW; satisfying it alone is not sufficient when other predicates fail.
- Previous resulting state and evidence are inputs to subsequent evaluation; do not substitute disconnected gates or automatic authority inheritance.
- **EXCEED** the strictest applicable legal, contractual, classification and security requirements and apply the StegVerse overlay where stronger. Baseline compliance is insufficient; certification/accreditation is never inferred.
- Each applicable transition requires evidence, a sovereign **Organization Ledger receipt**, authenticated readback and continuity/reconstruction verification. Local receipts, CI, transport and merges do not replace sovereign proof.
- ACTIONS BY MANIFEST; no mandatory external machines, second operated device, new frameworks, alternate authority or AI_SESSION_GATE.

## Coordinated owners
Registry/COSV (.github), SDK/StegCore/InTr, StegOS/StegNode/StegApp/StegBrowser/HCB, TV/TVC/SKAP, KV/MyKV/StegMemory, Publisher/Organization Ledger/Master Records, PAT-003 research. Each owner reconciles its existing ISSUE and handoff before edits; authenticate claim/fence and use exact-head protections. Confidential patent detail remains private.

## Acceptance
Prove source-to-KV, KV-to-memory, KV-to-disclosure, and interrupted-transfer recovery with positive/negative manifests, classification thresholds, revocation, replay and continuity tests. Each flow needs actual resulting states, dispositions, receipts, authentic sovereign ledger recording/readback and consistency verification; distinguish simulated/local evidence from authenticated runtime observations. Obtain independent review and protected merge only with required evidence.

## Ordering
First converge repo contracts, then wire reusable flows, then evaluate Fieldy or other device as an optional source. No Fieldy-specific dependency in the common infrastructure.

## Existing coordination
- https://github.com/StegVerse-Labs/.github/issues/1620
- https://github.com/StegVerse-Labs/.github/issues/3291
- https://github.com/StegVerse-Labs/.github/issues/3204
- https://github.com/StegVerse-Labs/Patents/issues/16
