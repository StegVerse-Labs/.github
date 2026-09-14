# StegBrowser Runtime Materialization Remediation Mirror Handoff

Updated: 2026-09-14

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- Parent/remediates: `STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001`
- Shared runtime-evidence owner: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
- Issue: `StegVerse-Labs/.github#1866`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / RESIDENT CARRIER OUTPUT POINTER RUNTIME-BOUND BUT NOT GITHUB-VISIBLE`
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

That receipt embeds `execution_result` from the existing Healer scheduler invocation. The scheduler result already contains `resident_custody_root_observation_retention`, including the canonical retained packet path, packet SHA-256, retained root, retained-root source, and packet state. Therefore the retained packet pointer is not missing from source and does not require a second export mechanism.

The first exact remaining defect is:

```text
RESIDENT_CARRIER_OUTPUT_POINTER_NOT_GITHUB_VISIBLE_BUT_RUNTIME_BOUND
```

This is a runtime-observation boundary, not a new source-side repair requirement. No current authentic resident copy of the Healer carrier consumption receipt or its embedded packet pointer is visible through GitHub/source/CI evidence. GitHub/source/CI remains non-authoritative for resident execution.

## Device / node invariant correction

`data/task-registry-global-invariants.json` applies to this Goal. StegOS devices are interchangeable execution/transport nodes, physical-device identity gates are prohibited, and KV/SKAP Vault is the sole user-verification authority.

The prior handoff text incorrectly rebound this lane to a `current iPhone` / TestFlight prerequisite. That dependency is removed. Historical device-specific observations remain provenance only.

This Goal may advance from any eligible StegOS execution surface that authentically materializes the governed resident state and binds applicable KV/SKAP continuity, WorkerCoordinator claim/fence lineage, and Interlock/InTr admission. Lack of a connected assistant-side filesystem connector is an evidence-reachability observation only; it is not a task-state gate and does not require a second physical device.

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

## Current classification

```text
HEALER_CARRIER_OUTPUT_NOT_ACCESSIBLE_AFTER_HEALER83
RESIDENT_CARRIER_OUTPUT_POINTER_NOT_GITHUB_VISIBLE_BUT_RUNTIME_BOUND
POST_REPAIR_HEALER_CARRIER_PACKET_OBSERVED_FOR_RT_STEGBROWSER_RUNTIME_CONSUMPTION_001 = false
RESIDENT_CUSTODY_ROOT_AUTHENTICALLY_OBSERVED_FOR_STEGBROWSER = false
```

## Exact next required observation

Observe the authentic resident copy of `receipts/sovereign-host/healer-sovereign-scheduler-request-consumption.latest.json` through any already-authorized resident evidence surface associated with an eligible admitted StegOS node. From its embedded `execution_result.resident_custody_root_observation_retention`, bind the exact packet path/hash/root/root-source/state.

If and only if the embedded packet state proves `RESIDENT_CUSTODY_ROOT_OBSERVED` for one authentic governed resident root, run/read `scripts/check_stegbrowser_runtime_consumption_receipts.py --runtime-root <authentic-root>` only as a non-authorizing classifier.

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

`ACTIVE / CHECKED_OUT / RESIDENT_CARRIER_OUTPUT_POINTER_NOT_GITHUB_VISIBLE_BUT_RUNTIME_BOUND / RESIDENT_ROOT_NOT_AUTHENTICALLY_OBSERVED / RECEIPT_REACHABILITY_NOT_CLASSIFIED / RUNTIME_CONSUMPTION_NOT_CLAIMED / PHYSICAL_DEVICE_IDENTITY_GATE_PROHIBITED / NO_SECOND_USER_OPERATED_DEVICE`

## Manual work

None.
