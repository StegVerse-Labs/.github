# DEVICE_KV Query/Response Mirror Handoff

Repository: `StegVerse-Labs/.github`
Issue: `#676`
Branch: `feat/device-kv-query-response-670`
State: SOURCE_MERGED_VALIDATED / AUTHENTIC_RUNTIME_QUERY_OBSERVATION_PENDING
Updated: 2026-09-02T10:18:00-05:00
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
  MY_KV_DIRECTORY_PROJECTION | MY_KV_CONNECTION_HEALTH | MY_KV_INSTALLATION_STATUS
requester = Site / MyKVDirectory
authority_ref = stegos-node://<exact ingress node_id>
disclosure_mode = BOUNDED_CONTEXT
```

Allowed scopes:
- directory: `entries`, `connection_health`
- health: `connection_health`\n- installation: `installation_status` with exact selector `_System/installation.receipt.json` and requester `Site / MyKVOnboarding`

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

## Upstream selector closure

CVK #166 merged through PR #167 at `70b19663305e63ac6016af9b56848e91aa89b77c`. The resident query consumer may now require canonical `kv.interlock.request.v1.selector` semantics from current local CVK source.

## Receiver-execution boundary

A bounded `kv_request` is handled directly by the already-running admitted DEVICE_KV receiver after exact ingress validation; it does **not** invoke WorkerCoordinator or mint a task claim/fence. This is endpoint handling, not delegated task execution. Portable-write and generic observation paths continue using their existing targeted executor. The query request grants no execution authority; the receiver's installed capability and exact request/Node predicates determine whether the read handler runs.


## 2026-08-31 installation-status extension

The existing endpoint handler now admits `MY_KV_INSTALLATION_STATUS` without adding a task or runtime owner.

```text
Site / MyKVOnboarding
-> exact Node-bound DEVICE_KV request
-> selector _System/installation.receipt.json
-> current local CVK get_installation_status()
-> bounded projection only
-> canonical DEVICE_KV query response
-> same HB-derived KV -> DEVICE carrier
-> same persisted result lookup
```

Directory/health requests retain `Site / MyKVDirectory`. Installation status uses the separate `Site / MyKVOnboarding` requester and cannot provide directory selectors.

The projection may establish current resident KV-root observation and canonical installation-receipt validity. It explicitly does not establish fresh cloud-provider observation or Step 5 verification.


## 2026-09-02 source release reconciliation

The source completion boundary for issue #676 has been satisfied.

```text
implementation PR: #677
implementation merge: 677ee5b65f6c8a7d4ced85e66e34850400675282
installation-status extension PR: #725
installation-status extension merge: 0ffe6a5ea61b2a0c24a28b702545ffbd8f6c0ec7
source implementation: COMPLETE
source validation: COMPLETE
merge: COMPLETE
runtime query observation: PENDING
```

The downstream current-iPhone Site path has also been repaired through the same exact three read classes:

```text
MY_KV_DIRECTORY_PROJECTION
MY_KV_CONNECTION_HEALTH
MY_KV_INSTALLATION_STATUS
```

Site PR #901 routes installation status through the device-local target; PR #902 accepts authentic device-local ingress evidence; PR #903 performs a bounded service-worker refresh/controller handoff before profile evaluation. Those Site repairs do not create a second DEVICE_KV authority and do not satisfy this repository's separate resident runtime-observation predicate.

Issue #676 may therefore close as source-complete while authentic resident/private-KV query execution remains an explicit downstream runtime evidence gate.
