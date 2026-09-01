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

The request remains exact Node-bound `kv.interlock.request.v1`, `BOUNDED_CONTEXT`, and `authority_effect=NONE`. The consumer loads `runtime/workspace_projection.py` from the current CVK source root and reads the current `STEGVERSE_KV_ROOT`.

## Organizational boundary
No Org-KV or Org-Emp-KV request is accepted by this extension. Those require their own organizational runtime and employee+machine conjunctive admission.

## Claimed delta
- extension of `scripts/consume_device_kv_intr_materialization_request.py`
- tests added to existing DEVICE_KV materialization test surface
- this handoff

## Non-claims
Source merge does not prove a resident Personal KV, Workspace registry, current node request, HB return, or Site consumption.