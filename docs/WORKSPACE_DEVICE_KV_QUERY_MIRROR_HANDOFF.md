# Workspace DEVICE_KV Query Mirror Handoff

Updated: 2026-08-31
Repository: StegVerse-Labs/.github
State: SOURCE_INTEGRATED_RUNTIME_OBSERVATION_PENDING
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

## Integrated source
- `scripts/workspace_device_kv_query_extension.py` validates and executes the bounded Personal Workspace record class.
- `scripts/consume_device_kv_intr_materialization_request_base.py` is the exact pre-extension DEVICE_KV consumer blob preserved for regression-safe delegation.
- `scripts/consume_device_kv_intr_materialization_request.py` is now the entrypoint wrapper: all pre-existing requests delegate unchanged; `WORKSPACE_PERSONAL_PROJECTION` executes the bounded extension and returns through the same persisted HB-derived DEVICE_KV query-response carrier.
- the wrapper re-exports the base module API so existing imports/tests retain their prior surface.
- `tests/test_workspace_device_kv_query_extension.py` covers exact request, node binding, and rejection of organizational selector substitution.
- CVK `runtime/workspace_projection.py` owns Personal KV projection semantics.
- Site `assets/workspace-kv-bridge.js` generates the exact request and validates exact HB return recovery.

Source commits:
- extension: `9edcaa950bd4a52ae32650cf8bcd602623681c44`
- extension tests: `cd3de8467e39c77993c64fdc0a27ad0bc3023ac4`
- preserved base consumer: `44703b54f4e1d0819b778a5807b50901e8132311`
- integrated wrapper: `259d47fc3f0386a027e948a53ca814ef4bfe55fa`
- API compatibility fix: `757841dcbbbfd5938e2b013659f25bf8a2ebe3e1`

## Remaining evidence gates
- deterministic repository validation on the integrated exact head;
- resident source refresh containing the wrapper + extension + current CVK source;
- authentic current-node `WORKSPACE_PERSONAL_PROJECTION` ingress;
- persisted response receipt + HB-derived exact response recovery;
- Site consumption of that authentic projection.

## Non-claims
Source integration does not prove a resident Personal KV, Workspace registry, current node request, HB return, or Site consumption.