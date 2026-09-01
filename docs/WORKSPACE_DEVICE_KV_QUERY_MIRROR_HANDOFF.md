# Workspace DEVICE_KV Query Mirror Handoff

Updated: 2026-08-31
Repository: StegVerse-Labs/.github
State: SOURCE_INTEGRATED_REFRESH_INSTALL_BOUND_RUNTIME_OBSERVATION_PENDING
Authority effect: NONE
Credential authority: TV/TVC

## Goal
Extend the existing admitted DEVICE_KV endpoint handler with one bounded Personal-KV Workspace projection record class. This is endpoint handling, not WorkerCoordinator task execution and not a new authority path.

## Record class
`WORKSPACE_PERSONAL_PROJECTION`
Requester: `Site / Workspace`
Scope: `workspace_identity`, `principals`, `relationships`, `organizations`, `memberships`, `feed`, `assistant`
Selector: `{ "workspace_type": "PERSONAL" }`

The request remains exact Node-bound `kv.interlock.request.v1`, `BOUNDED_CONTEXT`, and `authority_effect=NONE`. The extension loads CVK `runtime/workspace_projection.py` from the current `STEGVERSE_KV_SOURCE_ROOT` and reads the current `STEGVERSE_KV_ROOT`.

## Organizational boundary
No Org-KV or Org-Emp-KV request is accepted by this extension. Those require their own organization-resident runtime and employee+machine conjunctive admission.

## Integrated source
- `scripts/workspace_device_kv_query_extension.py` validates/executes the bounded record class.
- `scripts/consume_device_kv_intr_materialization_request_base.py` preserves the exact pre-extension consumer.
- `scripts/consume_device_kv_intr_materialization_request.py` delegates all pre-existing requests unchanged and handles only Workspace through the extension, returning through the existing persisted HB-derived DEVICE_KV query-response carrier.
- wrapper re-exports the base module API for compatibility.
- `scripts/refresh_sovereign_worker_runtime_source_base.py` preserves the prior source refresh implementation; `refresh_sovereign_worker_runtime_source.py` now adds the Workspace extension/base files to `STATIC_FILES`.
- `scripts/bootstrap_sovereign_runtime_base.py` preserves prior bootstrap; `bootstrap_sovereign_runtime.py` now requires the Workspace extension/base files.
- `scripts/install_sovereign_heartbeat_service_base.py` preserves prior installer; `install_sovereign_heartbeat_service.py` now copies the Workspace extension/base files into the resident source tree.
- `tests/test_workspace_device_kv_query_extension.py` covers exact request, node binding, and organizational-selector rejection.
- `.github/workflows/workspace-device-kv-validation.yml` is validation-only and passed on exact source head containing the integrated consumer + refresh/bootstrap/install wrappers.

## Current evidence
Source integration: COMPLETE.
Validation-only compile/predicate run: PASS.
Resident source refresh execution: NOT YET OBSERVED.
Current-node Workspace request/response: NOT YET OBSERVED.

## Remaining evidence gates
Run sovereign resident source refresh on the eligible node, confirm current CVK source root includes `runtime/workspace_projection.py`, then issue the first current-node `WORKSPACE_PERSONAL_PROJECTION` and retain persisted response + HB exact-byte recovery + Site consumption evidence.

## Non-claims
GitHub validation grants no runtime authority and does not prove resident Personal KV access or request consumption.

## 2026-09-01 workflow-surface registry reconciliation

The standalone validation workflow is now registered in the organization workflow-surface registry. This closes the unrelated organization-control-plane hygiene failure that had been visible during SV002 review. It does not advance resident Workspace DEVICE_KV runtime evidence.
