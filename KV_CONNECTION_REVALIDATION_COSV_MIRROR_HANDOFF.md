# KV Connection Revalidation COSV Mirror Handoff

Status: SOURCE_PROJECTION_MERGED_VALIDATED / PHYSICAL_KV1_ADOPTION_VERIFIED / DEVICE_LOCAL_KV_INSTALL_OWNER_OBSERVED_EXACT_READBACK / DEVICE_LOCAL_DURABILITY_BEST_EFFORT_BROWSER_ORIGIN / GOOGLE_DRIVE_EXISTING_PEER_EXACT_EVIDENCE_RECOVERED / GOOGLE_DRIVE_KV2_ADOPTION_INPUT_PREPARED / AUTHENTIC_GOVERNED_ADOPTION_EXECUTION_PENDING
Repository: `StegVerse-Labs/.github`
Issue: #419
Canonical COSV merge: #423 at `538885a85d1267f3080bde09b5375d6e8b99c577`
Updated: 2026-09-08
Authority effect: NONE

## Purpose

Project and track `KV-CONNECTION-REVALIDATION-WORKER-001` under canonical task.v1 COSV control while preserving the distinction between source state, owner-observed runtime state, physical owner-controlled KnowledgeVault evidence, browser durability, and authentic governed provider execution.

## Canonical task binding

```text
GOAL TASK ID: KV-CONNECTION-REVALIDATION-WORKER-001
COSV ID: 50000000102000
CANONICAL OWNER REPOSITORY: StegVerse-Labs/continuity-vault-kit
SITE CONSUMER REPOSITORY: StegVerse-Labs/Site
```

Canonical vector remains `50000000102000`.

## Source state

Worker source is merged through PR #417 at `6db36604bb1c2dfbecd6311807e3385d6193b3ec`. The original COSV projection merged through PR #423 at `538885a85d1267f3080bde09b5375d6e8b99c577` after exact-head organization-control and Heartbeat Worker validation.

Multi-instance / provider-neutral KV source is merged through `StegVerse-Labs/continuity-vault-kit` PRs #196-#201. Existing-KV adoption source merged through PR #203 at `4f2f47120ab162273abba6eae3e2155a46db2c16`. Physical-adoption evidence reconciliation merged through PR #204 at `2d6dd80e806557f23d2d22fa0b29b9c20577c54e`.

Site consumer/runtime-source state is merged through:

- PR #1109 — bounded registered-Node / generated-InTr / HB-derived-carrier resident DEVICE_KV transport;
- PR #1110 — prepublication MyKV #1/#2/#n UI candidate;
- PR #1113 — canonical plural provider projection alignment;
- PR #1114 — exact-byte owner-mediated KV-set projection admission into resident DEVICE_KV;
- PR #1115 — first-class resident device-local KnowledgeVault installer, separated from DEVICE_KV transport/cache;
- PR #1116 — provider-neutral cloud-peer create/adopt request source;
- PR #1120 — resident runtime reconciliation, durability classification, and exact existing Google Drive adoption evidence, merged at `aaa8a8d253534bd53afbec075b376d73401ad18c` after Device Local KV Install, Cloud KV Peer Manager, My KV Multi-Instance Provider Manager, Site Handoff Orchestrator, Ecosystem Heartbeat Orchestration, and Site Bootstrap all passed.

## Authentic current-device resident KV evidence observed

The owner executed the deployed resident installer on the current iPhone. The deployed Site reported:

```text
State: INSTALLED
Instance: KV #1 · kvi_0d5d4cfd531db51bbcf7fdfc0311f5dc
Set: personal
Storage: device-local-browser-indexeddb
Relationship: NOT_CONNECTED
Persistence: requested; granted=false
Exact readback: true
```

This is authentic owner-observed runtime evidence from the deployed Site surface. It is not represented as independent machine observation.

The resident KnowledgeVault is distinct from DEVICE_KV transport/cache:

```text
resident KV database: stegverse-device-local-kv-v1
DEVICE_KV transport/cache: stegverse-device-local-intr-v1
```

Because persistent browser storage was not granted, the resident installer now classifies current durability as:

```text
BEST_EFFORT_BROWSER_ORIGIN
cloud_recovery_recommended=true
```

Exact readback is therefore observed, but survival under browser-origin eviction is not overclaimed. Cloud peer recovery/replication is the intended durability path after authentic provider connection.

## Authentic physical Google Drive KV evidence

The owner-controlled Google Drive KnowledgeVault remains intact with its original installation receipt and adopted multi-instance records. The original installation receipt is exact-byte bound at:

```text
sha256:f00378cd1f68e08a39c837f2a80e7e105e822a321c0eea17a91318b4b6e5ea19
```

Raw bytes from the physical cloud vault were fetched and hashed exactly:

```text
existing cloud instance_id:
kvi_a31335d2cc3745fa987b635432cfed2c

_System/Instances/instance.json
1106 bytes
sha256:8bf5ba7d911a52506a582f064315c9831a84c0c5fbb6ec7a031c325a79af090a

_System/Instances/adoption.receipt.json
1023 bytes
sha256:64a3af27be0bd6ae36b05b35e52894581413fff048cea237d370d0ec6248b552

_System/my-kv-set-projection.json
1631 bytes
sha256:187ab43f0bb09d88da154af26d57e1bfe7199fd90affd2dd81af5532f0e34cf4
```

The historical Google Drive cloud vault is still internally recorded as KV #1, `personal`, `NOT_CONNECTED`. Because the current iPhone resident KV is now authentically KV #1, attaching the existing Google Drive vault requires an explicit ordinal reassignment/adoption event rather than a silent rewrite.

## Prepared Google Drive KV #2 adoption input

Site PR #1120 records the exact bounded input for `ADOPT_EXISTING_CLOUD_KV_PEER`:

```text
storage_medium: google-drive
current_instance_number: 1
requested_instance_number: 2
existing_instance_id: kvi_a31335d2cc3745fa987b635432cfed2c
existing_receipt_sha256: sha256:64a3af27be0bd6ae36b05b35e52894581413fff048cea237d370d0ec6248b552
existing_projection_sha256: sha256:187ab43f0bb09d88da154af26d57e1bfe7199fd90affd2dd81af5532f0e34cf4
private_content_rewrite_authorized: false
existing_identity_rewrite_authorized: false
provenance_preservation_required: true
```

This is preparation only. No provider operation, cloud materialization, ordinal rewrite, relationship transition, data movement, replication, AI-corpus exposure, execution authority, or activation is claimed.

## Canonical vector state

The installed vector file remains intentionally unchanged at this checkpoint:

- lifecycle: `MACHINE_OWNED`;
- archive_ready: false;
- blocker_count: 2;
- evidence_complete: false;
- activated: false;
- propagated: false.

The runtime blockers are not retired merely because source, physical evidence, or owner-observed browser readback now exist. The next closure predicate is authentic governed adoption execution from the resident device through the intended Interlock/InTr/provider path.

## Installed canonical files

- `control/task-vectors/KV-CONNECTION-REVALIDATION-WORKER-001.json`
- `control/task-vector-index.json`
- `control/cosv-global-registry-coverage.json`
- `control/worker-registry.d/kv-connection-revalidation-worker-001.json`
- `tests/test_kv_connection_revalidation_cosv.py`
- `scripts/check_kv_connection_revalidation_cosv.py`
- `docs/KV_CONNECTION_REVALIDATION_COSV_VALIDATION.md`

## Remaining sequence

1. Emit the prepared existing-Google-Drive `ADOPT_EXISTING_CLOUD_KV_PEER` request from the installed resident KV on the current iPhone so it receives a real request ID and current resident binding.
2. Pass that request through authentic Interlock/InTr admission; do not substitute source/CI evidence for execution.
3. Materialize Google Drive as KV #2 only after authentic provider-result evidence exists and preserve private content/provenance.
4. Add a new iCloud or other cloud-hosted KV as KV #3/#n.
5. Resolve provider credentials through SKAP without copying credentials into ordinary KV or Site state.
6. Prove provider CONNECT/VERIFY/READ/WRITE/SYNC/DISCONNECT and relationship-tier progression/downgrade/recovery with authentic admitted evidence.
7. Use cloud recovery/replication to mitigate `BEST_EFFORT_BROWSER_ORIGIN` durability on devices where persistent storage is not granted.
8. Publish ordinary My KV navigation/README when the live resident/cloud workflow is established.
9. Mark evidence_complete/activated/propagated only when their exact predicates are observed.

## Manual work

None required right now. Do not reinstall the resident KV, clear Safari/stegverse.org website data, or authorize a cloud provider yet. The next owner action should only be needed after the prepared Google Drive adoption input is exposed on the deployed resident surface so it can be emitted without re-entering the recovered evidence manually.
