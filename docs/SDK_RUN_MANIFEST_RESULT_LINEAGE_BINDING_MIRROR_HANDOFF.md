# SDK run-manifest result lineage binding mirror handoff

Updated: 2026-09-20
Goal Task ID: `SDK-RUN-MANIFEST-RESULT-LINEAGE-BINDING-001`
Parent Goal Task ID: `SDK-FOUR-STAGE-MANIFEST-EXPERIMENT-RERUN-001`
COSV ID: `71000000111111`
Status: RETIRED / COMPLETED / VALIDATED

## Purpose

Repair the shared public `run-manifest` boundary so every successful result is independently bound to the canonical complete ingress manifest and to a deterministic generic run-manifest execution request. The repair must apply to every installed processing capability through the shared dispatcher rather than by modifying Tests 1-4 individually.

## Required repairs

1. Add a deterministic `canonical_manifest_sha256` binding to every returned public run-manifest result.
2. Add a deterministic generic `request_sha256` for the run-manifest execution request and retain the exact request object/schema in result lineage.
3. Bind the unmodified processor result bytes/semantics through a `processor_result_sha256` commitment so nested receipts and closures are transitively committed by the returned result.
4. Fail closed if a processor attempts to return conflicting reserved lineage fields.
5. Add regression coverage proving the shared dispatcher guarantee across manifested worker routes.
6. Preserve the completed four-stage experiment as historical evidence; do not rewrite its retained PDFs or raw results.
7. Replace future-facing Test 3 person-specific scenario naming with a neutral identifier while accepting the historical identifier as a deprecated compatibility alias.
8. Describe SDK 1.3.0 as a release candidate until tag/release publication evidence exists.

## Source baseline

StegVerse-org/StegVerse-SDK main observed at task registration: `310c9fe7988a659c22764f4e16e2086f7cb22b12`.

The current shared dispatcher validates the manifest but returns the processor mapping unchanged, so top-level lineage binding is optional per processor. That is the first deterministic defect to repair.

## Final closure - 2026-09-20

SDK PR #299 merged as `69921971106ffb4008bf5914c34b34bc51745ff0` after all 12 applicable exact-head workflows passed on tested head `18a5f30b61557bf557b563797fccb241628f4b2d`, including four-stage validation run `35547155843`. The tested head and merged main commit share exact Git tree `6431e9b19a43cfa7f112bafcf28fdb23d96dd1b6`.

The shared public `run-manifest` dispatcher now returns `canonical_manifest_sha256`, deterministic generic `request_sha256`, `processor_result_sha256`, and `manifest_lineage` containing the exact run-manifest request object. The processor result is hashed before dispatcher enrichment, so all nested lifecycle receipts/closures are transitively committed by the public result without test-specific logic.

Future Test 3 manifests use `TEST_3_INVARIANCE_SHORT_LIVED_ACTOR_SEAM`. The historical `TEST_3_RICHARD_SHORT_LIVED_ACTOR_SEAM` remains accepted only as a compatibility alias. Historical four-stage artifacts were not rewritten. SDK 1.3.0 remains explicitly a release candidate; no tag/release publication is claimed.

No remaining repair predicate is open.
