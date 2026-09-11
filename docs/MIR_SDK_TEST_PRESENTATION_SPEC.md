# MIR SDK Test Presentation Specification

Updated: 2026-09-11
Goal Task ID: `MIR-EXPERIMENT-FROZEN-SCREENSHOT-EVIDENCE-001`
COSV ID: `50000000100000`
Status: `ACTIVE`

## Purpose

Define the canonical structure for a single evaluator-facing PDF that presents the MIR × StegVerse SDK test as both a persuasive walkthrough and a reproducible evidence package.

The PDF must distinguish presentation narrative from evidentiary claims. Screenshots illustrate observed steps; hashes, manifest references, pinned checkpoints, receipts, replay results, and reconstruction results provide the proof trail.

## Required report structure

1. Title page
   - Test name
   - Date
   - SDK/test version
   - Evidence epoch
   - One-sentence objective

2. Abstract
   - What was tested
   - Why the test matters
   - Primary result
   - Why an evaluator or prospective SDK user should care

3. Test objective and scope
   - Exact test question
   - Included SDK capabilities
   - Explicit exclusions and unsupported surfaces
   - Separation-of-powers constraints

4. Frozen test parameters
   - Experiment ID
   - Evidence epoch
   - Frozen screenshot manifest digest
   - Purpose-to-screenshot bindings
   - Fixed input manifest and processing path
   - Pre-registered expected evidence fields
   - Endpoint/runtime target where applicable
   - Replay basis
   - Reconstruction basis

5. End-to-end flow overview
   - Manifest Builder
   - Expected evidence-field registration
   - Request submission
   - MIR evidence retrieval
   - StegVerse evaluation/result
   - Replay
   - Reconstruction

6. Primary test execution and result
   - Submission summary
   - Returned evidence/result artifact
   - Pinned checkpoint/evidence reference
   - StegVerse-side result
   - Exact result state; no stronger claim than retained evidence supports

7. Replay and result
   - Replay input and selected state
   - Original result
   - Replay result
   - Delta or exact-match result
   - Replay evidence references

8. Reconstruction and result
   - Reconstruction inputs
   - Retained references/receipts used
   - Reconstruction outcome
   - Consistency/inconsistency result
   - Reconstruction evidence references

9. Conclusion
   - What the test demonstrated
   - What the test did not demonstrate
   - Why the result is relevant to SDK adoption
   - Remaining technical work, if any

10. Screenshot walkthrough
    - One subsection per key step
    - Screenshot title
    - Purpose ID
    - What the evaluator should notice
    - Artifact reference and SHA-256 digest
    - Related request/result/receipt reference

## Required screenshot sequence

The final presentation should capture, at minimum, evaluator-relevant screens for:

1. Manifest Builder / manifested-data creation
2. Processing-path selection
3. Pre-registration of expected evidence fields
4. Final pre-submission frozen manifest summary
5. Request submission
6. MIR evidence/standing response or equivalent source-evidence view
7. StegVerse evaluation/result view
8. Final result/receipt view
9. Replay request
10. Replay result
11. Reconstruction request
12. Reconstruction result
13. Evidence export / retained package summary when available

The screenshot set must be frozen before the evaluated run when the test design requires those images as test evidence. Presentation-only screenshots captured after execution must be labeled as presentation captures and must not be represented as pre-run frozen evidence.

## Appendix A - Evidence Ledger

Include:

- frozen manifest digest;
- evidence epoch;
- screenshot purpose bindings and SHA-256 values;
- fixed input-manifest digest;
- pre-registered expected evidence fields;
- runtime/source references;
- MIR checkpoint pin(s);
- decision/result references;
- replay references;
- reconstruction references;
- mutation/fail-closed evidence;
- exact software/contract versions used.

## Appendix B - SDK Overview and Usage Guide

Explain the SDK in plain technical language and provide evaluator-usable instructions.

### What the SDK does

The SDK allows an external framework or evaluator to submit manifested data of a supported class, identify the intended processing path, and receive bounded outputs that may range from a governance/evidence artifact to the applicable state-transition information represented by that artifact.

The SDK does not convert evidence into authority. MIR remains historical custodian for MIR-held history; StegVerse governance evaluates admissibility; Interlock/InTr governs transitions where applicable; TV/TVC retains credential authority; Master Records retains observed-reality/reconstruction responsibilities where applicable.

### Canonical usage flow

1. Create or load the input manifest.
2. Select the desired processing path.
3. Pre-register expected evidence fields before execution.
4. Freeze the manifested input and evidence expectations when the test requires a frozen basis.
5. Submit the request through the SDK.
6. Inspect the returned evidence/governance/result artifact.
7. Retain exact references, receipts, hashes, and checkpoint pins needed for reproducibility.
8. Replay against the selected retained or current state when replay is supported.
9. Reconstruct the original result from retained evidence when reconstruction is supported.
10. Export or retain the evidence package for independent review.

### Evaluator guidance

The guide must include at least one concrete worked example using the exact test presented in the report. It should show the manifest shape, expected evidence fields, submission path, returned artifact class, replay invocation or equivalent UI path, and reconstruction invocation or equivalent UI path.

## Appendix C - Roadmap and Future Development

Roadmap statements must distinguish implemented capabilities from planned work.

### Browser-friendly SDK access

Target: every SDK operation that can be safely exposed should have a browser-accessible equivalent with semantic parity to the programmatic SDK.

Planned browser-facing capabilities include:

- guided Manifest Builder;
- data-class and processing-path selection;
- expected evidence-field registration;
- frozen-manifest preview and digest display;
- authenticated request submission;
- result and receipt inspection;
- MIR/other evidence-reference inspection without transferring source-system authority;
- visual replay;
- visual reconstruction;
- downloadable evidence packs and receipts;
- provenance/lineage visualization;
- provider-neutral adapter configuration;
- authenticated collaborative workspaces where applicable;
- browser-visible validation/error states;
- examples, templates, and developer documentation;
- parity checks proving browser operations emit the same canonical SDK artifacts as equivalent programmatic operations.

### Development principles

- Browser UX must not become a second SDK with different semantics.
- No browser convenience layer may silently bypass manifest freezing, evidence-field preregistration, authority separation, or receipt requirements.
- UI state is not execution proof.
- Presentation screenshots are not substitutes for receipts, checkpoint pins, hashes, or reconstruction evidence.
- New provider/framework adapters should reuse the same manifested-data and evidence contracts rather than introduce provider-specific authority semantics.

## Publication criterion

The final PDF may be labeled a completed test presentation only when the primary execution, replay, reconstruction, screenshot walkthrough, and evidence ledger are populated from authentic retained artifacts. Missing live-runtime portions must remain explicitly marked as unexecuted or unavailable rather than represented with placeholders as completed results.
