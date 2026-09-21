# SDK run-manifest result lineage binding mirror handoff

Updated: 2026-09-20
Goal Task ID: `SDK-RUN-MANIFEST-RESULT-LINEAGE-BINDING-001`
Parent Goal Task ID: `SDK-FOUR-STAGE-MANIFEST-EXPERIMENT-RERUN-001`
COSV ID: `71000000111111`
Status: RETIRED / COMPLETED / VALIDATED

## Purpose

Repair the shared public `run-manifest` boundary so every successful result is independently bound to the canonical complete ingress manifest and to a deterministic generic run-manifest execution request. The repair applies through the shared dispatcher rather than through test-specific result logic.

## Final closure — 2026-09-20

SDK PR #299 merged as `69921971106ffb4008bf5914c34b34bc51745ff0` from exact tested head `18a5f30b61557bf557b563797fccb241628f4b2d`. The tested head and merged commit share Git tree `6431e9b19a43cfa7f112bafcf28fdb23d96dd1b6`.

All 12 applicable exact-head SDK workflows passed. The exact-head four-stage validation run was `35547155843`.

Completed repairs:
- every successful public `run-manifest` result now carries `canonical_manifest_sha256`;
- the dispatcher derives and retains a deterministic generic `request_sha256` and exact `stegverse.sdk.run-manifest-request/v1` object;
- `processor_result_sha256` commits the complete pre-enrichment processor result, transitively binding nested receipts/closures;
- reserved lineage-field collisions fail closed, while an existing processor-level `request_sha256` is preserved as `processor_request_sha256`;
- regression coverage validates the shared contract through the manifested worker routes;
- future Test 3 manifests use `TEST_3_INVARIANCE_SHORT_LIVED_ACTOR_SEAM`;
- historical `TEST_3_RICHARD_SHORT_LIVED_ACTOR_SEAM` remains a deprecated compatibility alias for retained evidence;
- the prior four-stage evidence package remains immutable and was not rewritten;
- SDK 1.3.0 remains explicitly a release candidate pending canonical tag/release publication.

No remaining repair predicate is open.
