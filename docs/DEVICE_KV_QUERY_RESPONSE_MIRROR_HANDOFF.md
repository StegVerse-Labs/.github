# DEVICE_KV Query/Response Mirror Handoff

Repository: `StegVerse-Labs/.github`
Issue: `#676`
Branch: `feat/device-kv-query-response-670`
State: ACTIVE_IMPLEMENTATION
Updated: 2026-08-31T13:18:00-05:00
Credential authority: TV/TVC
Authority effect: NONE

## Goal

Complete the read side of the My KV owner-controlled vertical slice using the canonical DEVICE_KV materialization lane and the merged StegOS `kv_request` extension.

## Upstream

- StegOS #145 / PR #146 / merge `ba1e43dbadaef367c32c7a354fe2857746f6f1cd`
- CVK #164 / PR #165 / merge `f91e465bbf7196557005a8112a6c70c8712f9aaf`
- existing profiled DEVICE_KV ingress + resident consumer
- existing local HB-derived InTr carrier runtime

## Query contract

Only node-origin requests are eligible.

```text
kv_request.schema_version = kv.interlock.request.v1
operation = REQUEST
record_class =
  MY_KV_DIRECTORY_PROJECTION | MY_KV_CONNECTION_HEALTH
requester = Site / MyKVDirectory
authority_ref = stegos-node://<exact ingress node_id>
disclosure_mode = BOUNDED_CONTEXT
```

Allowed scopes:
- directory: `entries`, `connection_health`
- health: `connection_health`

The outer materialization `payload_hash` must equal the canonical SHA-256 of `kv_request`. A request may not carry both `portable_payload` and `kv_request`.

## Resident execution

```text
INGRESS_ADMITTED
 -> validate query binding + same node
 -> load current local CVK projection source
 -> require STEGVERSE_KV_ROOT
 -> execute list_admitted_directory/get_directory_health
 -> canonical response object
 -> response receipt hash
 -> exact response bytes
 -> canonical HB-derived carrier signal
 -> persist signal under shared heartbeat runtime
 -> durable query-result receipt
```

## Retrieval

The shared profiled ingress exposes a bounded result lookup surface. Result lookup requires exact materialization ID + request hash + node ID and returns only the already-persisted response carrier/result record. It does not execute or re-read KV state.

## Claimed surfaces

- `scripts/consume_device_kv_intr_materialization_request.py`
- `workers/universal_intr_profiled_ingress.py`
- `tests/test_device_kv_intr_event_materialization.py`
- `docs/DEVICE_KV_QUERY_RESPONSE_MIRROR_HANDOFF.md`

## Completion boundary

Source validation + merge. Runtime activation still requires a conforming HTTPS ingress, current resident source, a real private `STEGVERSE_KV_ROOT`, and an authentic node-origin query.

## KV Interlock selector dependency

CVK #166 / PR #167 adds the bounded `selector.directory_id` + `selector.canonical_path` fields to canonical `kv.interlock.request.v1`. This consumer treats that selector as query coordinates only; node-origin admission plus exact `stegos-node://<node_id>` binding remains separately required.
