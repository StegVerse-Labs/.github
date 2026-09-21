# SDK Four-Stage Post-Lineage Evidence Package Mirror Handoff

Updated: 2026-09-20
Goal Task ID: `SDK-FOUR-STAGE-POST-LINEAGE-EVIDENCE-PACKAGE-001`
Parent Goal Task ID: `SDK-RUN-MANIFEST-RESULT-LINEAGE-BINDING-001`
COSV ID: `71000000111111`
Status: ACTIVE / CHECKED OUT

## Purpose

Create a successor evidence bundle proving the repaired shared public `run-manifest` result-lineage contract through the same four-stage manifest-only experiment. The prior authoritative rerun bundle remains immutable historical evidence and must not be overwritten or relabeled.

## Required evidence

- exact post-lineage-repair SDK source identity;
- one frozen source identity for all four stages;
- all four manifests built before stage execution;
- fresh Test 1, Test 2, Test 3, and Task 4 results through public `run-manifest`;
- intrinsic `canonical_manifest_sha256`, `request_sha256`, `processor_result_sha256`, and `manifest_lineage` verification in every result;
- neutral Test 3 scenario for the successor run;
- Task 4 overlap semantics limited to concurrent invocation lifetimes, not CPU-parallel instruction execution;
- raw manifests/results/source index/metadata/hash inventory;
- one pre-test interpretation PDF and four post-test evidence PDFs generated only from executed results;
- one new ZIP with its own SHA-256, without changing prior bundles.

## Source candidate

Post-lineage SDK merged main: `69921971106ffb4008bf5914c34b34bc51745ff0`.
Exact validated PR head: `18a5f30b61557bf557b563797fccb241628f4b2d`.
Tested and merged Git tree: `6431e9b19a43cfa7f112bafcf28fdb23d96dd1b6`.

The exact-head four-stage workflow run `35547155843` passed after the lineage repair. Its artifact may be used as the fresh successor execution evidence only if its retained raw manifests/results prove all required intrinsic lineage fields and exact source binding.
