# SV002 Frozen Corpus Materialization Dependency Update — 2026-09-17

Goal Task ID: `SHWP-SV002-FROZEN-CORPUS-MATERIALIZATION-001`
COSV: `50000000107001`
Tracking issue: `#2064`

## Verified materialization attempts

- local shell/raw GitHub: failed DNS resolution;
- connected GitHub recursive tree inspection: PASS;
- connected GitHub exact single-blob retrieval: PASS;
- connected GitHub archive/tarball endpoint: rejected by connector allowlist;
- public web/archive route: unavailable because the formal repositories are not publicly viewable from the public web path;
- container downloader cannot use the private archive without a publicly viewable URL;
- no new workflow-dispatch capability is exposed in the connected GitHub surface;
- no complete `stegverse.source-package/v1` or equivalent retained frozen package was found in TT/RTG/GTG/AE at the required source state.

## Existing source-transport dependency discovered

The canonical existing implementation is `StegVerse-Labs/TVC:TVC-PRIVATE-SOURCE-READ-001`, not a new materializer. TVC provides a bounded TV/TVC-authorized private-source-read capability and a portable source-package path after authentic resident materialization.

Current canonical TVC state remains:

`SOURCE_COMPLETE_PR146_ONLY_RESIDENT_ADMISSION_PENDING`

Current task evidence states that the private-source service installation, credential presence/grant, and exact resident materialization are not observed. Therefore the SV002 child cannot truthfully use TVC private-source materialization yet.

## Current blocker

`SV002-FROZEN-CORPUS-BULK-MATERIALIZATION` is now narrowed to:

`DEPENDENCY_TVC_PRIVATE_SOURCE_READ_RESIDENT_ADMISSION_NOT_OBSERVED`

Do not create a second credential path, use generic GitHub credentials, substitute public/current-branch source, or downgrade the byte-complete source-index requirement.

## Reuse after dependency admission

Once the existing TVC private-source-read lane can materialize exact immutable commits, request the four already-pinned TT/RTG/GTG/AE commits, build the complete source indexes and `source_sha256` values with the existing SV002 builder semantics, then reuse the previously proven sandbox native adapter, v0.3 exporter, corrected post-response `EGRESS_EMITTED`, Master Records reconstruction/custody/readback, and origin-delivery chain without reimplementation.

Authority effect: `NONE_COORDINATION_AND_SOURCE_TRANSPORT_ONLY`.
