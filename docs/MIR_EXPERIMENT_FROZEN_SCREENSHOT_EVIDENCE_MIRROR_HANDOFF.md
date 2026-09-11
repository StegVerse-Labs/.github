# MIR Experiment Frozen Screenshot Evidence Mirror Handoff

Updated: 2026-09-11
Goal Task ID: `MIR-EXPERIMENT-FROZEN-SCREENSHOT-EVIDENCE-001`
COSV ID: `50000000100000`
Adjacent contract task: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
Separate Shared Docs task: `SHARED-DOCS-MULTIPARTY-FREEZE-001`
Status: `ACTIVE`

## Goal

Pre-freeze the MIR experiment screenshot evidence set so the exact same screenshot artifacts, bound to the exact same declared purposes, are used throughout the complete test.

## Core invariant

For a single experiment evidence epoch, each screenshot purpose is bound before execution to one exact screenshot artifact and digest. The binding is immutable for that run.

No mid-test screenshot replacement, re-cropping, alternate capture, purpose reassignment, selective substitution, or post-hoc favorable image selection is permitted.

If any screenshot artifact or purpose binding changes, the existing experiment evidence epoch is no longer continuous. A successor evidence epoch / new test run must be declared rather than presenting the changed evidence set as the same test.

## Canonical implementation

Task registration was merged through `.github` PR #1450 at merge commit `eb79cf1f700336dbd7d05576e461df46a9093eb1` after exact-head validation succeeded.

The screenshot-continuity implementation was merged through `.github` PR #1453 at squash commit `e0e6a47e479a9bc54ca9ca9647aad8ad54cc0c6f`. Exact implementation head `1b53e9f0c1e4102240ffce0ac9a49331e216c62e` passed all observed required validation lanes before merge:

- organization-control run `34614318562` — PASS;
- deterministic repository suite run `34614318572` — PASS;
- Heartbeat worker validation run `34614318539` — PASS.

Post-implementation handoff reconciliation PR #1474 exact head `b18c5a6daf2deda29ed248145544b12f49442353` passed organization-control run `34616424431`, Heartbeat run `34616424504`, and deterministic repository suite run `34616424418`, then merged at `048c574acc0a4a3540c2b493f3aa40acff468a70`.

Canonical source now includes:

- `schemas/mir-frozen-screenshot-manifest.schema.json`
- `scripts/validate_mir_frozen_screenshot_manifest.py`
- `control/task-vectors/MIR-EXPERIMENT-FROZEN-SCREENSHOT-EVIDENCE-001.json`
- `docs/MIR_SDK_TEST_PRESENTATION_SPEC.md`

The schema fixes the manifest vocabulary. The validator computes a deterministic SHA-256 over canonical JSON and compares a candidate manifest against the frozen baseline. Within one evidence epoch it fails closed if experiment identity changes, evidence epoch changes, the purpose set changes, any purpose maps to a different artifact reference/digest, or the complete manifest digest changes.

These validation failures remain experiment-evidence states. They grant no governance or execution authority.

## COSV binding

The task is assigned `task.v1` vector `50000000100000` (`L R U I V G O C M T B E A P`). This records an ACTIVE machine-owned task (`L=5`) with no unassigned/chat-owned work encoded at this coordination point, canonical owner installation known (`M=1`), no blocker encoded, evidence incomplete, and activation/propagation unclaimed.

The vector is coordination state only. It grants no execution, governance, credential, claim/fence, custody, publication, or experiment-evidence authority.

## Required manifest fields

The manifest binds:

- `schema`
- `experiment_id`
- `evidence_epoch`
- `frozen_at`
- `frozen_by`
- `entries[]`

Each screenshot entry binds at minimum:

- `purpose_id`
- `purpose_description`
- `artifact_ref`
- `artifact_sha256`
- `captured_at` when known

The validator derives the deterministic manifest digest; it is not accepted as an unverified self-asserted field.

## Test-wide continuity rule

Every test stage that consumes screenshot evidence must reference the same frozen manifest digest and the same purpose-to-artifact mappings. A stage may consume only the subset relevant to that stage, but it may not substitute a different artifact for an existing purpose.

A changed screenshot or changed purpose assignment cannot be repaired inside the same evidence epoch. The remediation is to declare a successor evidence epoch and restart the affected experiment run from its pre-execution evidence freeze.

## Failure semantics

- unknown/missing purpose -> `SCREENSHOT_PURPOSE_UNREGISTERED`
- duplicate purpose -> `SCREENSHOT_PURPOSE_DUPLICATE`
- invalid artifact digest -> `SCREENSHOT_ARTIFACT_DIGEST_INVALID`
- purpose remap -> `SCREENSHOT_PURPOSE_BINDING_CHANGED`
- purpose set replacement/removal/addition -> `SCREENSHOT_SET_MUTATED`
- complete canonical manifest drift -> `SCREENSHOT_MANIFEST_DIGEST_CHANGED`
- missing required screenshot -> `SCREENSHOT_EVIDENCE_UNAVAILABLE`
- experiment or epoch identity drift -> `SCREENSHOT_EXPERIMENT_CHANGED` / `SCREENSHOT_EVIDENCE_EPOCH_CHANGED`

These are experiment evidence states, not governance outcomes.

## Separation from Shared Docs

`SHARED-DOCS-MULTIPARTY-FREEZE-001` governs collaborative document revision freeze semantics.

This task governs the MIR experiment's fixed screenshot evidence basis. The two tasks may reuse generic digest/freeze primitives, but neither task subsumes the other.

## Frozen evidence epoch materialized

Evidence epoch `MIR-SOP-2026-09-11-E1` now has a retained purpose-indexed manifest at:

- `evidence/mir/frozen-screenshot/MIR-SOP-2026-09-11-E1.manifest.json`

Frozen manifest SHA-256:

- `7181561fbaa55e2b4297a48551ed5b47f3f7a8ed0f9c329b498e41f1fbb794b4`

Retained deterministic validation evidence:

- `evidence/mir/frozen-screenshot/MIR-SOP-2026-09-11-E1.positive-validation.json`
- `evidence/mir/frozen-screenshot/MIR-SOP-2026-09-11-E1.negative-mutation-validation.json`

The unchanged manifest validates successfully. An intentional artifact-digest mutation fails closed with `SCREENSHOT_PURPOSE_BINDING_CHANGED` and `SCREENSHOT_MANIFEST_DIGEST_CHANGED`.

The current frozen set contains three unique retained Library screenshots. A fourth discovered Library image was byte-identical to an existing screenshot and was not falsely represented as a fourth unique artifact.

## Canonical evaluator-facing PDF specification

`docs/MIR_SDK_TEST_PRESENTATION_SPEC.md` defines the agreed single-PDF structure for the completed evaluator presentation.

The final report is required to include:

1. abstract;
2. test objective and scope;
3. frozen parameters;
4. end-to-end flow overview;
5. primary execution and result;
6. replay and replay result;
7. reconstruction and reconstruction result;
8. conclusion;
9. screenshot walkthrough covering the evaluator-relevant path from Manifest Builder through final result, replay, reconstruction, and evidence export where available;
10. Appendix A — evidence ledger;
11. Appendix B — SDK overview and usage guide with a worked example; and
12. Appendix C — roadmap and future development, including browser-friendly access to all SDK functions that can be safely exposed with semantic parity to the programmatic SDK.

The PDF must remain two-layered: reader-facing narrative first, evidence rigor underneath. UI screenshots may explain the flow, but receipts, hashes, checkpoint pins, manifests, replay evidence, and reconstruction evidence remain the proof basis.

## Evidence still required

No complete MIR v0.3 integration-test continuity claim is made yet. The pre-run screenshot freeze and mutation/fail-closed validation now exist, but completion of the full evaluator test presentation still requires:

1. authentic live primary execution evidence;
2. every evidence-consuming stage to reference the same frozen manifest digest where applicable;
3. authentic replay input and result;
4. authentic reconstruction input and result;
5. evaluator-facing screenshots for the key SDK stages defined in the presentation spec;
6. post-run deterministic comparison proving no purpose/artifact binding changed; and
7. the final generated PDF populated from those authentic retained artifacts.

The live MIR `POST /v1/policy/standing` read-head-then-pin call has not yet been executed because no authentic MIR API base and no valid opaque test `entityRef` were recovered from the connected project sources searched so far. Neither value may be fabricated.

The per-task COSV shard and canonical task record bind vector `50000000100000`. Aggregate task-vector-index visibility remains subject to repository validation and will be reconciled if the deterministic suite requires explicit index insertion.

## Completion boundary

Completion requires the frozen screenshot manifest and exact artifact digests, authentic primary execution, replay, reconstruction, test-stage references to the same frozen basis where required, evaluator-relevant screenshots, post-run continuity validation, and the final evidence-backed PDF defined by `docs/MIR_SDK_TEST_PRESENTATION_SPEC.md`.

No completed integration-test or final-PDF claim is made until those authentic artifacts exist and the validation evidence passes.
