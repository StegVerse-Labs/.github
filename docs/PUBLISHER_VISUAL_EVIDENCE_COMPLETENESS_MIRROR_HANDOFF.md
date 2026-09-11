# Publisher Visual Evidence Completeness Mirror Handoff

Updated: 2026-09-11
Goal Task ID: `PUBLISHER-VISUAL-EVIDENCE-COMPLETENESS-001`
COSV ID: `50000000100010`
Status: `ACTIVE / RULE + ELAN RUN 2 VISUAL REPAIR IN PROGRESS`

## Goal

Every published experimental/evaluator-facing Publisher document must include the pertinent end-to-end screenshots needed to both substantiate the evidence flow and help evaluators understand how to experiment with the SDK or applicable interface.

This task applies that rule immediately to the completed predecessor `ELAN-CUMULATIVE-PUBLICATION-001` by adding a Run 2 visual sequence parallel to Run 1 and issuing a revised cumulative package without deleting or rewriting the prior render receipt.

## Evidence boundary

The authentic Run 2 workflow already completed in `StegVerse-org/StegVerse-SDK` run `34565152578`. No contemporaneous Run 2 screenshots were retained in that artifact.

Therefore the Run 2 images produced here must be labeled **post-run evidence views reconstructed from exact retained Run 2 artifacts**. They may display exact artifact values and the evaluator flow, but they may not be described as screenshots captured during the historical execution.

## Required Run 2 visual sequence

1. Source-native input: Events 1, 2, 3; Event 3 explicit observed non-emission.
2. Evaluation declaration: observed evidence, no inferred intent/semantics.
3. Governance request.
4. Completed manifest.
5. Exact transition request.
6. InTr posture binding.
7. SDK-to-governance handoff.
8. Governance decision: `ALLOW / ok`.
9. Route receipts / transition chain.
10. Exact-run custody: `RECORDED`.
11. Replay: deterministic match.
12. Reconstruction: chain verified.
13. Returned result.
14. Controlled comparison: baseline missing Event 3 vs observed-silence Event 3.

## Publisher-wide visual rule

For experimental/evaluator-facing publications, the canonical source must declare either:

- `visual_evidence_required: true` with an ordered visual-evidence manifest covering all material stages; or
- `visual_evidence_required: false` with an explicit reason explaining why screenshots are not pertinent.

A publication must not silently omit screenshots. When historical execution did not retain contemporaneous screenshots, Publisher may generate post-run evidence views from hash-bound retained artifacts, provided the views are labeled reconstructed/post-run and never represented as historical captures.

## ELAN predecessor

Predecessor task: `ELAN-CUMULATIVE-PUBLICATION-001`

Terminal predecessor COSV: `71000000100100`

Original cumulative render receipt remains evidence of the prior package and must not be overwritten. This task must create a successor revision receipt and new artifact hashes.

## Completion predicates

- Publisher visual-evidence rule is documented and machine-checkable.
- Run 2 gets all 14 pertinent end-to-end evidence views from authentic retained artifacts.
- Each Run 2 image clearly says it is a post-run reconstructed evidence view.
- Revised cumulative source embeds Run 1 and Run 2 visuals.
- PDF and DOCX are regenerated and visually inspected page-by-page.
- HTML, Markdown, JSON, DOCX, and PDF hashes are rebound in a successor render receipt.
- Prior source/render receipts remain preserved.
- No public-release claim is inferred from rendering.

## Next work

1. Materialize the 14 Run 2 post-run evidence views from the retained Run 2 artifact ZIP.
2. Add the universal visual-evidence contract and validator to Publisher.
3. Revise the ELAN cumulative source and generated package.
4. Validate PDF/DOCX visually.
5. Record successor receipt and merge only from exact-head green validation.
