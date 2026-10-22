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

## Reconciliation of already-completed SDK-MR-A lifecycle (2026-10-22)

The existing canonical record `data/canonical-task-records/SDK-MR-A-VALIDATION-CUSTODY-001.json` is `COMPLETED_VALIDATED / RETIRED`, COSV `71000000100110`, `end_to_end_complete=true`. The recorded receiving-organization governance disposition for request `SDK-MR-A-ORGANIZATION-LEDGER-RECEIPT-004`, packet `pkt-c64077b3c2b188aabf176050`, is **DENY / signal.inputs_incomplete**, not ALLOW. Decision receipt: `sha256:273ffa70d766e003d7c649d4b7b5fd83c95a532f58c0c79fd13bf5617ca094da`; sender closure receipt: `sha256:f3156e28ee4aa4fdcd4af475dbd21aaea56d5f0c1d151187583f5ca97ba85c4b`. Historical independently verified ledger tips were Labs `9f0a53e5029a2587d2b4ac24e93f557c99238099` and Org `ab3cbc14058d296d9e9e4dbed8bbebfda81cf3c9`. Owner closure: https://github.com/StegVerse-Labs/.github/issues/3099#issuecomment-6119932050 and https://github.com/StegVerse-org/StegVerse-SDK/issues/452#issuecomment-6119934544 .

**No replay:** These historical receipts establish that SDK-MR-A's decision return and closure occurred, not that topology PR #3300's newly written verifier has executed against those records. PR #3300 is source integration plus negative tests, with its own exact-head CI/review obligations. A separate, newly authorized manifest would be required for any new runtime transition; do not reactivate retired SDK-MR-A simply to exercise this verifier.

**Semantics:** A governance DENY is an authentic resulting-state decision; successful delivery/receipt/return is not a grant of the requested custody change. Organization ledger readback ALLOW refers to recording/readback integrity, not admissibility of the denied operation.

## Reusable-task capability inventory and ownership (2026-10-22)

This inventory is source-backed, not a request for a new Goal or an alternate execution framework.

| Capability | Existing implementation | Disposition |
|---|---|---|
| Organization chain walk, body digest, predecessor links, source-retention verification | `resident-runtime/organization_ledger_readback.py::readback` | REUSE, no duplicate |
| Transition-ID/predecessor-specific native receipt binding | `workers/canonical_state_transition_custody.py::organization_receipt_gate` | REUSE, no duplicate |
| Existing designated ref writer, fast-forward CAS and fresh fetch | `.github/workflows/organization-ledger-transition.yml` | REUSE; do not invoke for a read-only check |
| Read-only fresh-fetch conformance proof with expected receipt membership | `.github/workflows/topology-sovereign-readback.yml` + `scripts/ecosystem_transition_topology.py::verify_published_organization_chain` | IMPLEMENTED here, no new runtime |
| Reusable cross-Goal parameter contract and native Task Library registration | Not established by this bounded inventory | Candidate only; inventory the canonical library and register via existing owner if no equivalent |

Actual exact-head proof: `477593c43bf4fe3fc58a95f57f40a40031fc2082`, https://github.com/StegVerse-Labs/.github/actions/runs/39734902386 SUCCESS; published 56-receipt chain, expected receipt `sha256:273ffa70d766e003d7c649d4b7b5fd83c95a532f58c0c79fd13bf5617ca094da`. Readback ALLOW is recording integrity only, not governance admission. Existing library registration is not inferred from this proof.

Exact-head ratchet https://github.com/StegVerse-Labs/.github/actions/runs/39734902382 FAILED with six tests unrelated by filename to the four PR-changed files (three component-010, Ecosystem Chat, Lane D fixture, Registry check-in). Filename disjointness does not prove causality or absence of a regression. Do not skip these tests or silently add them to the baseline. Reconcile against current main and route source repairs through existing owners. Independent review and protected merge remain outstanding.
