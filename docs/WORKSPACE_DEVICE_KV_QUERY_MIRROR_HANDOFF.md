# Workspace DEVICE_KV Query Mirror Handoff

Updated: 2026-08-31
Repository: StegVerse-Labs/.github
State: ACTIVE_IMPLEMENTATION
Authority effect: NONE
Credential authority: TV/TVC

## Goal
Extend the existing admitted DEVICE_KV endpoint handler with one bounded Personal-KV Workspace projection record class. This is endpoint handling, not WorkerCoordinator task execution and not a new authority path.

## Record class
`WORKSPACE_PERSONAL_PROJECTION`

Requester: `Site / Workspace`
Scope: `workspace_identity`, `principals`, `relationships`, `organizations`, `memberships`, `feed`, `assistant`
Selector: `{ "workspace_type": "PERSONAL" }`

The request remains exact Node-bound `kv.interlock.request.v1`, `BOUNDED_CONTEXT`, and `authority_effect=NONE`. The extension loads `runtime/workspace_projection.py` from the current CVK source root and reads the current `STEGVERSE_KV_ROOT`.

## Organizational boundary
No Org-KV or Org-Emp-KV request is accepted by this extension. Those require their own organizational runtime and employee+machine conjunctive admission.

## Implemented source
- `scripts/workspace_device_kv_query_extension.py` validates and executes the bounded Personal Workspace record class.
- `tests/test_workspace_device_kv_query_extension.py` covers exact request, node binding, and rejection of organizational selector substitution.
- CVK source `runtime/workspace_projection.py` owns the Personal KV projection.
- Site source `assets/workspace-kv-bridge.js` generates the exact request and requires the existing HB-derived DEVICE_KV response path.

## Remaining integration seam
The current `scripts/consume_device_kv_intr_materialization_request.py` still recognizes only the pre-existing My-KV directory/health/installation record classes. It must dispatch `WORKSPACE_PERSONAL_PROJECTION` to `workspace_device_kv_query_extension.execute_workspace_query` before the first authentic Workspace request can complete. Until that exact seam is installed, Site fails closed rather than substituting browser state or fabricated data.

## Claimed delta
- `scripts/workspace_device_kv_query_extension.py`
- `tests/test_workspace_device_kv_query_extension.py`
- pending narrow integration in `scripts/consume_device_kv_intr_materialization_request.py`
- this handoff

## Non-claims
Source implementation does not prove a resident Personal KV, Workspace registry, current node request, HB return, or Site consumption.