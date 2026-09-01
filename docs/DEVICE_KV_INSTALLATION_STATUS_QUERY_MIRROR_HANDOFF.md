# DEVICE_KV KnowledgeVault Installation Status Query Mirror Handoff

Repository: `StegVerse-Labs/.github`
Branch: `feat/device-kv-installation-status-query-20260831`
Updated: 2026-08-31T21:14:00-05:00
State: MERGED_VALIDATED / AUTHENTIC_NODE_QUERY_OBSERVATION_PENDING
Credential authority: TV/TVC
Authority effect: NONE

## Goal

Extend the existing read-only DEVICE_KV query/return endpoint so My KV onboarding can ask the current resident KnowledgeVault whether its canonical installation receipt is present and validated.

This is an extension of the existing endpoint handler:

```text
Site current registered Node
 -> DEVICE_KV kv_request
 -> shared profiled InTr ingress
 -> admitted endpoint query handler
 -> current local CVK projection source
 -> STEGVERSE_KV_ROOT/_System/installation.receipt.json
 -> bounded installation-status projection
 -> exact DEVICE_KV response
 -> HB-derived KV -> DEVICE return carrier
 -> existing result lookup
```

No new runtime owner, task, claim, fence, scheduler, route, or credential authority is introduced.

## Query contract

```text
schema_version=kv.interlock.request.v1
operation=REQUEST
requester={module: Site, component: MyKVOnboarding}
record_class=MY_KV_INSTALLATION_STATUS
requested_scope=[installation_status]
disclosure_mode=BOUNDED_CONTEXT
selector={receipt_path: _System/installation.receipt.json}
authority_ref=stegos-node://<exact ingress node_id>
```

The outer materialization payload hash remains the canonical hash of `kv_request`.

## Projection contract

The endpoint may return only the CVK bounded installation projection. It may not return the raw installation receipt, provider identifiers, provider credentials, private KV contents, or a full provider destination.

A verified projection proves current observation of the resident KV root and its canonical installation receipt. It does not prove fresh cloud-provider/session observation; Step 5 remains separate.

## Claimed surfaces

- `scripts/consume_device_kv_intr_materialization_request.py`
- `tests/test_device_kv_intr_event_materialization.py`
- `docs/DEVICE_KV_QUERY_RESPONSE_MIRROR_HANDOFF.md`
- this handoff

## Completion boundary

Source implementation, repository validation, merge. Runtime observation remains separate and requires an authentic node-origin query against current resident `STEGVERSE_KV_ROOT`.


## Merge evidence

```text
PR #725
merge 0ffe6a5ea61b2a0c24a28b702545ffbd8f6c0ec7
Validate organization control plane - No GitHub Token Authority: SUCCESS
Heartbeat Worker Project - Validation Only / No GitHub Token Authority: SUCCESS
```

Upstream CVK projection is merged at `b62387bb5ddb13dcca6ff5c7c24e5a14a2a10d23`.
Downstream Site live-first Step 2 integration is merged at `8e5540917531dd34219ada22a568024817c3e956`.

Lifecycle:

```text
source implementation=true
source validation=true
merge=true
authentic node-origin MY_KV_INSTALLATION_STATUS query observed=false
authentic resident KV installation projection returned=false
public iPhone Step 2 observation=false
```

No source/CI/merge evidence is promoted into runtime observation.
