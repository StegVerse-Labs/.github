# MIR Experiment Frozen Screenshot Evidence Mirror Handoff

Updated: 2026-09-11
Goal Task ID: `MIR-EXPERIMENT-FROZEN-SCREENSHOT-EVIDENCE-001`
COSV ID: `50000000100000`
Adjacent contract task: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
Separate Shared Docs task: `SHARED-DOCS-MULTIPARTY-FREEZE-001`
Status: `ACTIVE / FROZEN SHARED-DOCUMENT CONFORMANCE EXECUTED / RETURN PACKAGE MATERIALIZED`

## Goal

Preserve an immutable screenshot-evidence basis for the MIR experiment and produce an evaluator-facing MIR x StegVerse separation-of-powers test package without manufacturing runtime, provider, governance, custody, or proof claims.

## Canonical implementation already merged

Task registration merged through `.github` PR #1450 at `eb79cf1f700336dbd7d05576e461df46a9093eb1`.

Screenshot continuity implementation merged through PR #1453 at `e0e6a47e479a9bc54ca9ca9647aad8ad54cc0c6f`; exact implementation head `1b53e9f0c1e4102240ffce0ac9a49331e216c62e` passed organization-control `34614318562`, deterministic repository suite `34614318572`, and Heartbeat validation `34614318539`.

Post-implementation handoff reconciliation PR #1474 merged at `048c574acc0a4a3540c2b493f3aa40acff468a70` after exact-head validation.

Canonical source includes:

- `schemas/mir-frozen-screenshot-manifest.schema.json`
- `scripts/validate_mir_frozen_screenshot_manifest.py`
- `control/task-vectors/MIR-EXPERIMENT-FROZEN-SCREENSHOT-EVIDENCE-001.json`
- `docs/MIR_SDK_TEST_PRESENTATION_SPEC.md`

## Frozen screenshot epoch

Evidence epoch: `MIR-SOP-2026-09-11-E1`

Frozen screenshot manifest:

- `evidence/mir/frozen-screenshot/MIR-SOP-2026-09-11-E1.manifest.json`
- canonical SHA-256 `7181561fbaa55e2b4297a48551ed5b47f3f7a8ed0f9c329b498e41f1fbb794b4`

Retained validation evidence:

- `evidence/mir/frozen-screenshot/MIR-SOP-2026-09-11-E1.positive-validation.json`
- `evidence/mir/frozen-screenshot/MIR-SOP-2026-09-11-E1.negative-mutation-validation.json`

The E1 purpose set remains immutable. Later screenshots are presentation/evidence captures and are not silently added to the pre-run E1 set.

## Corrected live-interconnection model

The MIR x StegVerse frozen contract defines authority and evidence semantics; it does not require the test protocol to prescribe a bespoke MIR HTTP transport.

For this experiment, the shared collaborative document is the common interoperability carrier. Interlock/InTr or another generic inter-machine layer may bind document-state transitions without changing the separation-of-powers contract. API transport is one possible adapter surface, not a prerequisite for this shared-document conformance test.

Therefore the previous handoff statement that a missing MIR API base or opaque `entityRef` blocked the entire experiment was too narrow and is superseded for this test scope.

The frozen contract still records the shipped MIR standing-evidence surface and its semantics; absence of a production HTTP call must not be misrepresented as having occurred.

## Frozen contract artifact selection

Two Library text artifacts were inspected.

A file named `MIR x StegVerse Separation-of-Powers Evidence Contract v0_3.txt` was excluded as the frozen v0.3 basis because its actual contents identify it as `v0.2` and `Working draft`.

The actual v0.3 convergence-candidate artifact is:

`MIR_StegVerse_Separation_of_Powers_Evidence_Contract_v0.3_Convergence_Candidate.txt`

Exact SHA-256:

`9c742da512a8bbad52519a2c1027b4e013482f2dcf3a0e51159e116de089277c`

Richard Whitney's newly supplied counterpart-confirmation screenshot states that v0.3 is frozen on his side; standing evidence is shipped; proof surfaces 12.5/12.6 remain TO-BUILD with `witnesses[]` empty and honest proof status; `mir.evidence.v0` is the target response shape; and the next concrete step is the shared `mir.leaf.v3` fixture in 12.8.

That screenshot is retained as a post-freeze counterpart-confirmation / presentation evidence artifact, not as a mutation of the E1 screenshot purpose set.

Counterpart-confirmation screenshot SHA-256:

`959ec84fda328c472109e94e3a9c7e821c00d5552c3883483c802d54ac7eebda`

## 2026-09-11 frozen shared-document conformance execution

A deterministic local evaluator execution was performed against the exact frozen v0.3 contract bytes. This is an authentic local conformance execution, but it is NOT claimed as sovereign resident runtime execution and does NOT fabricate provider-native revision telemetry.

SDK-shaped manifest SHA-256:

`577221209ad99378ce309f9ce504a4cd1f8ed6f21b1a8c490ddfdc1e959a40ba`

Shared-document two-party freeze record SHA-256:

`ab5af3851c00df904c1f69a39a292df6d89695c35f70aba71febb289d9a4c9eb`

Pre-registered predicates tested:

- MIR historical custodian;
- StegVerse governor of admissibility;
- MIR evidence surface must not return governance verdicts;
- shipped `/v1/policy/standing` evidence surface is declared;
- opaque `entityRef` semantics;
- read-head-then-pin rule;
- StegVerse governance decision retained as separate StegVerse provenance;
- proof surface remains TO-BUILD;
- witnesses remain empty until shipped;
- proofStatus remains honest (`NOT_REQUESTED` / `UNAVAILABLE` until proof exists);
- shared `mir.leaf.v3` conformance fixture is the declared 12.8 next step;
- no authoritative historical-custody/governance collapse.

Primary result: `PASS`

Primary result SHA-256:

`c0e8e2f4226ace343b606ed0b08c7b2d09899a6f0f9ff1a332a515e6c50159c0`

Replay: exact match.

Reconstruction: consistent from retained contract hash, manifest hash, expected-evidence hash, and freeze record.

Negative mutation: one deliberate byte change produced a different content SHA-256 and was fail-closed as `CONTENT_DIGEST_MISMATCH_REQUIRES_SUCCESSOR_REVISION`; it was not accepted as the same frozen revision.

## Evidence boundary

Demonstrated:

- exact frozen v0.3 shared-document bytes identified and bound;
- counterpart mutual-freeze acceptance evidenced;
- deterministic separation-of-powers conformance measurement;
- replay exact match;
- reconstruction consistency;
- fail-closed mutation behavior;
- immutable E1 screenshot basis retained.

Not claimed:

- sovereign resident runtime execution;
- provider-native document revision/version telemetry not actually observed;
- a MIR production HTTP transaction;
- inclusion proof or signed witness attestation while 12.5/12.6 remain TO-BUILD;
- governance, credential, custody, publication, or transition authority from this evaluator run.

## Return package

A reader-facing DOCX and PDF have been materialized from the retained evidence with:

- abstract;
- frozen parameters;
- shared-document carrier model;
- pre-registered predicates;
- primary result;
- replay;
- reconstruction;
- negative mutation check;
- evidence boundaries;
- screenshot walkthrough;
- evidence ledger;
- SDK evaluator usage guidance;
- conclusion and 12.8 next-step boundary.

The package is suitable for return to Richard as the current frozen-contract conformance result. It must not be described as proof that TO-BUILD witness/inclusion-proof features have shipped.

## Next continuation

1. Return/review the evidence-backed report with Richard.
2. Treat any document-content change after mutual freeze as a successor revision / new review epoch.
3. Continue the contract trajectory at 12.8 shared `mir.leaf.v3` conformance, while preserving the 12.5/12.6 honest TO-BUILD boundary.
4. Keep generic inter-machine transport/adapters separate from the constitutional authority contract.
