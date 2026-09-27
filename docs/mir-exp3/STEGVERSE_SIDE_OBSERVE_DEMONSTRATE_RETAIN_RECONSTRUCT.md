# StegVerse contribution — independent observation, demonstration, retention and reconstruction

**MIR/SV Experiment 3, source/evidence audit draft — 24 September 2026**

Method: Match Richard's four headings; give every capacity its limitation and independent check **in the same section**. Separate (a) source specification, (b) source-level/CI evidence reported in an earlier canonical handoff, (c) historical runtime evidence described in existing handoffs, and (d) current independently retrieved runtime receipts. No category silently inherits the authority of another. This document does **not** claim execution of a new MIR/SV experiment or access to private sovereign resident ledgers.

## 1. Observe

**Capability / bounded claim (SOURCE-CONTRACT):** The established StegVerse event-triggered path specifies browser event → registered Node/write-once `intr_outbox` → Universal InTr ingress/current Interlock/InTr → bounded EVENT_EPHEMERAL Web Worker → execution-time identity → governed consequence → canonical state receipt. WorkerCoordinator controls registered machine-owned tasks where needed but does not create browser events. This can produce evidence of **what the participating StegVerse instruments actually emitted** when they execute.

**Limit at equal weight:** Defining that path does not show an event was ever triggered, that every external or physical activity was observed, that sensors independently sampled an environment, or that a missing submission equals non-occurrence. The 2026-09-17 canonical MIR custody handoff explicitly reported **no observed current MIR outbox/INGRESS_ADMITTED/bounded execution/RTC-007–009/return receipt** after its write-through correction. Current resident org-ledger HEAD and immutable receipts were **not independently accessible through the connected GitHub source interface** for this audit. Therefore current Exp3 independent observations = `NOT_ESTABLISHED`. Missing GitHub source receipts are **not evidence of missing resident receipts**.

**Independent check:** Read `docs/CANONICAL_MASTER_RECORDS_STATE_TRANSITION_CUSTODY_MIRROR_HANDOFF.md`; inspect Site's `assets/mir-roundtrip-browser-activation.js`, `intr-mir-roundtrip-extension.js`, `assets/mir-roundtrip-sv002-browser-runtime.js`, registered Node `intr_outbox`, plus authentic organization ledger `HEAD.json` and immutable referenced entries *when authorized read is available*. Cross-check actual browser/outbox/ingress event hashes and immediate-predecessor linkage rather than counting source code as observations. Explicitly record external declared-coverage schedules and activity-side sampling; absent both, completeness is UNMEASURED.

## 2. Demonstrate

**Capability / bounded claim (SOURCE-CONTRACT + PRIOR SOURCE/CI REPORTED):** Canonical policy requires current Interlock/InTr decision, TV/TVC if required, an exact transition receipt, and canonical Master Records submission with `state=RECORDED`, `reconstruction_status=PASS`, `required_evidence_validation_status=PASS`, exact receipt/reconstructed digest equality, plus per-item required-evidence validation. The existing handoff reports Site source conformance at commit `91d12a55a602168a30472ba9ed4489b9066c4b91`, workflow `35193442678`; Master Records required-evidence source merge `32d89da201c4653413c85510bec629124b2e3a25`. Earlier frozen shared-document MIR v0.3 local conformance independently **within StegVerse local harness** is recorded separately, including exact replay and fail-closed single-byte mutation; it is not resident or MIR production evidence.

**Limit at equal weight:** Hash agreement and a self-issued report are not proof of physical truth, independent custody, complete observation or actual admitted transition. CI cannot establish resident execution. A valid `RECORDED/PASS` response must be tied to the **exact** authentic transition and immediate predecessor—not a fixture or an unrelated receipt. The user and Richard independently author their sides; neither may silently certify the other's measurement.

**Independent check:** Fetch the named GitHub commits/workflow by exact SHA/run; recompute the frozen v0.3 contract SHA `9c742da512a8bbad52519a2c1027b4e013482f2dcf3a0e51159e116de089277c` against original bytes, run existing deterministic frozen-manifest validator, and separately request authentic resident organization chain and corresponding Master Records actual response. Record *exact* provenance and independent-recomputability status for each demonstration.

## 3. Retain

**Capability / bounded claim (SOURCE-CONTRACT):** The canonical StegVerse schema `stegverse.canonical-state-transition-receipt/v1` and submission schema `stegverse.master-records.state-transition-submission/v1` bind transition and any required evidence to exact SHA-256 digests. The `/api/master-records/state-transitions` service is the specified authoritative custody endpoint. Each non-empty evidence manifest item must specify identity/type, exact content and encoding, content SHA-256 and matching origin-transition ID, which the existing Master Records source is reported to validate and retain. Browser IndexedDB is subordinate continuity/cache; it cannot issue canonical Master Records custody.

**Limit at equal weight:** Source's durable-write contract is not proof of deployed retention, global coverage, immutable organization receipts in an accessible resident, retention completeness, restoration after data loss or independently separated custody. A source path and a reported historical commit do not establish what evidence exists **now**. No claim is made that all required evidence from prior MIR transitions survives, that a third-party copy exists, or that absence of a receipt demonstrates no transition occurred.

**Independent check:** Authenticated read-only organization-ledger `HEAD.json` → each immutable `receipts/<sha256>.json` → compare exact digest and predecessor → corresponding authoritative Master Records `RECORDED` response + exact evidence manifests and reconstructed item digests. Determine retention policy and negative loss cases from actual service configuration and destructive test receipts, not this specification.

## 4. Reconstruct

**Capability / bounded claim (SOURCE-CONTRACT):** Under the canonical state-transition contract, every state-dependent successor should consume the immediate predecessor's verified Master Records closure; reconstruction of the state receipt and all required evidence, with digest equality, is the precondition for continued governed progression. Properly retained, ordered receipts can reconstruct the **recorded StegVerse transition lineage** and preserve separately attributable participant observations, denials, dissent and unknown classes where actually captured.

**Limit at equal weight:** The reconstructable unit is the **retained recorded state transition**, not every off-record action, physical consequence, undisclosed unknown or causal explanation. No verified current Exp3 end-to-end replay from resident organization custody through Master Records was obtained in this audit. A local frozen-document replay, prior successful StegVerse-002 fixture and source-level Test/Demo 3 or manifold evidence cannot be repackaged as Exp3's authentic run. Participants may share a blind spot, so the union of disclosed unknowns is not an exhaustive universal unknown set.

**Independent check:** From a genuine retained org-ledger HEAD, walk the complete immediate-predecessor chain for a chosen run; recompute exact per-receipt and evidence digests; resolve each corresponding Master Records response with `RECORDED/PASS/PASS`; independently compare reconstructed ordered state to recorded before/after states, and retain contradictory accounts as distinct evidence. Try a known omission derived from the **activity-side** sampling frame; an exclusively record-side sample cannot falsify completeness.

## Four-question cross-index for the joint manuscript

| Question | StegVerse source-supported answer | Actual Exp3 observation ceiling |
|---|---|---|
| What was claimed? | Exact manifest, proposed transition, authority and expected evidence can be source-bound. | No new Exp3 manifested run retrieved. |
| What was independently observed? | If run, separate Node event, InTr decision, runtime and Master Records receipts can be cross-checked. | Not established from accessible current resident evidence. |
| What physical work occurred? | Execution consequence must carry bounded machine receipts where applicable. | Physical external outcome is not independently established; software execution cannot alone prove physical work. |
| What remains unknown? | Per-observer unknowns, dissent and observational scope should remain separately attributable. | Shared blind spots, unavailable current runtime, undeclared coverage and activity-side omissions remain UNBOUNDED/UNKNOWN. |

## Disagreement ledger / negative controls

- MIR asserts partner reports but no direct environmental observation; StegVerse source specifies event/instrument observation **if executed**. These are different observation frames; do not infer superiority or erase either ceiling.
- MIR cryptographic chain can demonstrate committed assertion integrity; StegVerse Master Records source specifies transition/evidence reconstruction. Neither independently establishes physical truth or complete reporting.
- Independent authority: MIR historical accounting does not mint StegVerse transition authority; StegVerse governance does not rewrite MIR's historical corpus. Preserve independent disagreement when the resulting accounts differ.
- Counterexample 1: undeclared omitted physical event (structural observability limit) versus declared but unsubmitted activity event (reporting gap).
- Counterexample 2: replayable chain of incomplete/false assertions.
- Counterexample 3: two agreeing participants sharing a missing sensor.
- Counterexample 4: missing required evidence or mismatched predecessor causes fail-closed progression under the *specified* contract; actual runtime negative test remains UNVERIFIED for Exp3.

## Provenance and next independent checks

Sources: `docs/CANONICAL_MASTER_RECORDS_STATE_TRANSITION_CUSTODY_MIRROR_HANDOFF.md` (historical source/CI reports as of 2026-09-18); `docs/MIR_EXPERIMENT_FROZEN_SCREENSHOT_EVIDENCE_MIRROR_HANDOFF.md` (frozen v0.3 local test); `docs/MIR_STEGVERSE_SEPARATION_OF_POWERS_EVIDENCE_CONTRACT_MIRROR_HANDOFF.md` (parent reference contract); Richard's original PDF hash as in canonical Exp3 handoff. Current accessible evidence is **GitHub source and submitted counterpart PDF/screenshots**, not a live sovereign runtime or current third-party proof bundle. Upgrade classes only on independently retrieved exact artifacts and authentic custody readback.

## 2026-09-24 manifested SDK execution: first reproducible experiment artifact

This manuscript now has an actual **manifested** SDK source-scoped companion. [Read SDK manifest input](https://github.com/StegVerse-org/StegVerse-SDK/blob/main/inspection/examples/mir-sv-exp3/assessment-input.json); [read diagnostic request](https://github.com/StegVerse-org/StegVerse-SDK/blob/main/inspection/examples/mir-sv-exp3/diagnostic-request.json); [retrieve exact generated manifest and diagnostic result](https://github.com/StegVerse-org/StegVerse-SDK/actions/runs/36085026183/artifacts/10843328013). The existing installed SDK Manifest Builder canonicalizes the four dimension sections and four questions, with one capability/limit/check triple per section. The existing read-only `ecosystem_diagnostic` processor returns **4 source-contract declaration PASS checks and 8 NOT_OBSERVED authentic current resident/physical/coverage checks**, without inventing missing evidence. Six focused tests and all 12 applicable source workflows passed at exact SDK head `2508068f5475364ed4b47db6f6349e9b91fdb290`. The source manifest SHA-256 is `e1b05a082ce19d3d254e3cde1dced03019174a94287724959672c9e65510c8f3`; local diagnostic result SHA-256 `5acde471f793546a7a457ab11cbe142aeefa6637e747550390f1db213cfaeaea`.

The existing public SDK `run-manifest` dispatch correctly refused isolated source-only CI without configured authentic Universal InTr ingress (`UNIVERSAL_INTR_INGRESS_NOT_CONFIGURED`), so only the SDK's **non-authorizing local diagnostic** was invoked. **Do not infer** real current org-ledger readback, physical work, Publisher output, external communication or Master Records reconstruction from this successful SDK source-level experiment. An actual resident sample will be a separately hash-bound successor manifest rather than a retroactive modification of this exact source fixture.

## Reviewer-facing Publisher source implementation / current evidence ceiling

The existing Publisher generic review-asset support [PR #73](https://github.com/GCAT-BCAT-Engine/Publisher/pull/73) and SDK external-review-default and generic transfer [PR #318](https://github.com/StegVerse-org/StegVerse-SDK/pull/318) are merged with exact-head source tests passing. Ordinary runs may omit Publisher; review-intent successor manifests default to required Publisher, subject to explicit opt-out. The original frozen source-only Exp3 SDK manifest remains byte-identical and is **not retroactively a review-run terminal artifact**. Local user-original validation passed for the PDF and all ten screenshots; the current conversation's private evaluator intake archive retains the exact 11 originals and their hash-bound base64 assets. No authenticated current Exp3 InTr/canonical Master Records/Publisher destination or SDK return/far-side receipt has been observed. Exact original bytes do not independently establish the historical truth or completeness of the screenshots; the limits remain adjacent to each capability.
