# StegBrowser Runtime Materialization Remediation Mirror Handoff

Updated: 2026-09-14

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- Parent/remediates: `STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001`
- Shared runtime-evidence owner: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
- Issue: `StegVerse-Labs/.github#1866`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / DESCENDANT DEVICE-GATE PROPAGATION APPLIED / RESIDENT CARRIER OUTPUT POINTER RUNTIME-BOUND / ELIGIBLE EXECUTION SURFACE REACHABILITY PENDING`
- External/second user-operated device required: `false`

## Current truth

The source-side packet/retention repairs remain merged and validated, but source state does not prove runtime execution.

- `StegVerse-Healer#81` added the task-bound non-authorizing `resident_custody_root_observation` packet surface.
- `StegVerse-Healer#82` repaired resident-root bootstrap circularity through the existing local source-refresh path.
- `StegVerse-Healer#83` retained the canonical packet at `receipts/sovereign-host/stegbrowser-resident-custody-root-observation.latest.json` under the observed resident root or existing materialization target.
- `.github#1879` bound the missing retained-packet observation state.
- `.github#1884` merged as `301147aed13c9bd3fe637225db91f9ca2c378864` after exact-head validation, binding `HEALER_CARRIER_OUTPUT_NOT_ACCESSIBLE_AFTER_HEALER83` without a new code path.

`scripts/consume_healer_sovereign_scheduler_request.py` persists the resident Healer carrier consumption receipt at:

```text
receipts/sovereign-host/healer-sovereign-scheduler-request-consumption.latest.json
```

That receipt embeds `execution_result.resident_custody_root_observation_retention`, including packet path, SHA-256, retained root, retained-root source, and packet state. The retained packet pointer is therefore source-bound and does not require a second export mechanism.

## Canonical device / node invariant

`data/task-registry-global-invariants.json` applies. KV/SKAP Vault is the sole user-verification authority. Eligible StegOS devices are interchangeable execution/transport nodes. Physical-device identity, named-handset completion gates, device attestation as user verification, and connector inventory as task state are prohibited.

Historical device-specific observations remain provenance only.

## Descendant propagation completed in prompt 14

The interchangeable-device invariant was propagated through the normative descendant surfaces that still encoded a current-iPhone completion gate:

- `docs/GLOBAL_RUNTIME_EVIDENCE_CONVERGENCE_MATRIX.md` — shared predicate changed to `AUTHENTIC_RETAINED_STEGOS_STEGBROWSER_RUNTIME_OBSERVED`; StegBrowser lane no longer requires current-iPhone continuity.
- `data/canonical-task-records/GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001.json` — removed current-iPhone/TestFlight physical-runtime dependency, set physical-device gate to prohibited, human action to null, and admitted any eligible StegOS substrate.
- `docs/STEGOS_AI_PREEXECUTION_RUNTIME_PROOF_MIRROR_HANDOFF.md` and its canonical task record — replaced current-iPhone runtime gate with `AUTHENTIC_ADMITTED_STEGOS_RUNTIME_CONSUMES_AI_PREEXECUTION_TASK` while preserving historical same-device observations as provenance.
- `docs/KV_BOUND_EPHEMERAL_BROWSER_PROJECTION_MIRROR_HANDOFF.md` and its canonical task record — replaced `TESTFLIGHT_CURRENT_IPHONE_RUNTIME_OBSERVED` with `AUTHENTIC_RETAINED_STEGOS_STEGBROWSER_RUNTIME_OBSERVED`; retained the Site/TVC/TestFlight path as an eligible reusable implementation path rather than a named-device requirement.
- `tests/test_kv_bound_ephemeral_browser_projection_component_reconciliation.py` was reviewed and already asserts that `TESTFLIGHT_CURRENT_IPHONE_RUNTIME_OBSERVED` is absent from the goal predicates; no weakening was required.
- Root README reviewed: it already carries the registry-wide KV/SKAP verifier and interchangeable StegOS device model; no additional README mutation required.

Historical receipts, evidence files, source component names, and observations were not rewritten.

## Current exact defect

```text
RESIDENT_CARRIER_OUTPUT_POINTER_NOT_GITHUB_VISIBLE_BUT_RUNTIME_BOUND
ELIGIBLE_ADMITTED_STEGOS_EXECUTION_SURFACE_NOT_CURRENTLY_REACHABLE_THROUGH_ASSISTANT_EXECUTION_CONNECTOR
```

The second line is evidence reachability only. It is not a device requirement, authorization state, substrate-unsuitable conclusion, or new blocker class.

A direct execution-surface inventory check during prompt 14 returned zero connected execution devices. Therefore the global convergence runner was not executed: doing so in GitHub Actions or fabricating a resident result would violate the authority model. GitHub Actions remain validation/evidence transport only.

## Existing authorized output access path

```text
<resident-root>/receipts/sovereign-host/healer-sovereign-scheduler-request-consumption.latest.json
  -> execution_result
  -> resident_custody_root_observation_retention
  -> packet_ref / packet_relative_path / packet_sha256 / retained_under_root / retained_under_root_source / packet_state
```

Canonical retained packet:

```text
<resident-root>/receipts/sovereign-host/stegbrowser-resident-custody-root-observation.latest.json
```

## Exact next required execution

Use the first reachable eligible StegOS execution surface in canonical substrate order. Bind applicable KV/SKAP continuity, exact WorkerCoordinator claim/fence lineage, and Interlock/InTr admission. Then:

1. observe the authentic resident Healer carrier consumption receipt;
2. bind the retained packet pointer and authentic governed resident root;
3. run/read `scripts/check_stegbrowser_runtime_consumption_receipts.py --runtime-root <authentic-root>` only as a non-authorizing classifier;
4. enter `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001` through existing Canonical Work ingress;
5. freeze one measurement run ID;
6. execute `scripts/run_global_runtime_node_profile_convergence.py` exactly once in measurement-only mode;
7. retain `receipts/sovereign-host/global-runtime-node-profile-convergence.latest.json` and fan evidence to the 18 lanes only under exact subject/task binding.

Do not substitute source code, CI success, workflow artifacts, repository files, issue comments, connector reachability, or physical-device identity for resident-state evidence.

## Authority invariants

- Task Registry: coordination only.
- KV/SKAP Vault: sole user-verification authority.
- StegOS devices: interchangeable transport/execution nodes; physical-device identity gate prohibited.
- Healer carrier / neutral reusable scheduler: scheduling and invocation transport only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed transition authority.
- TV/TVC: credential/provider authority where applicable.
- Master Records: observed-reality/reconstruction authority.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.
- No second scheduler, dispatcher, credential path, GitHub runtime authority path, runtime plane, MIR-specific transport, provider authority, WorkerCoordinator bypass, or second user-operated device is authorized.

## Current state

`ACTIVE / CHECKED_OUT / DEVICE_INTERCHANGEABILITY_PROPAGATED / RESIDENT_CARRIER_OUTPUT_POINTER_NOT_GITHUB_VISIBLE_BUT_RUNTIME_BOUND / EXECUTION_SURFACE_REACHABILITY_PENDING / RESIDENT_ROOT_NOT_AUTHENTICALLY_OBSERVED / RECEIPT_REACHABILITY_NOT_CLASSIFIED / RUNTIME_CONSUMPTION_NOT_CLAIMED / PHYSICAL_DEVICE_IDENTITY_GATE_PROHIBITED / NO_SECOND_USER_OPERATED_DEVICE`

## Manual work

None.
