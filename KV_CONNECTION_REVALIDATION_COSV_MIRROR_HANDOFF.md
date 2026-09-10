# KV Connection Revalidation COSV Mirror Handoff

Status: SOURCE_PROJECTION_MERGED_VALIDATED / PHYSICAL_KV1_ADOPTION_VERIFIED / DEVICE_LOCAL_KV_INSTALL_OWNER_OBSERVED_EXACT_READBACK / DEVICE_LOCAL_DURABILITY_BEST_EFFORT_BROWSER_ORIGIN / GOOGLE_DRIVE_EXISTING_PEER_EXACT_EVIDENCE_RECOVERED / GOOGLE_DRIVE_KV2_ADOPTION_INPUT_PREPARED / LEGACY_NODE_COMPATIBILITY_REPAIR_MERGED_DEPLOYED / AUTHENTIC_GOVERNED_ADOPTION_REQUEST_EMITTED / RESIDENT_INGRESS_OBSERVED / GOOGLE_DRIVE_KV2_NOT_MATERIALIZED / CLOUD_PROVIDER_EXECUTION_PENDING / DEVICE_KV_SKAP_ROUNDTRIP_CHILD_ACTIVE
Repository: `StegVerse-Labs/.github`
Issue: #419
Canonical COSV merge: #423 at `538885a85d1267f3080bde09b5375d6e8b99c577`
Updated: 2026-09-10
Authority effect: NONE

## Purpose

Project and track `KV-CONNECTION-REVALIDATION-WORKER-001` under canonical task.v1 COSV control while preserving the distinction between source state, owner-observed runtime state, physical owner-controlled KnowledgeVault evidence, browser durability, resident ingress, and authentic governed provider execution.

## Canonical task binding

```text
GOAL TASK ID: KV-CONNECTION-REVALIDATION-WORKER-001
COSV ID: 50000000102000
CANONICAL OWNER REPOSITORY: StegVerse-Labs/continuity-vault-kit
SITE CONSUMER REPOSITORY: StegVerse-Labs/Site
```

Canonical vector remains `50000000102000`.

## Source and resident basis

Multi-instance / provider-neutral KV source is merged through `StegVerse-Labs/continuity-vault-kit` PRs #196-#201. Existing-KV adoption source merged through PR #203 at `4f2f47120ab162273abba6eae3e2155a46db2c16` and physical-adoption evidence reconciliation through PR #204 at `2d6dd80e806557f23d2d22fa0b29b9c20577c54e`.

The current iPhone resident KV remains owner-observed as:

```text
State: INSTALLED
Instance: KV #1 · kvi_0d5d4cfd531db51bbcf7fdfc0311f5dc
Set: personal
Storage: device-local-browser-indexeddb
Relationship: NOT_CONNECTED
Persistence: requested; granted=false
Durability: BEST_EFFORT_BROWSER_ORIGIN
Exact readback: true
```

Resident KV and DEVICE_KV transport/cache remain distinct.

## Authentic physical Google Drive KV evidence

The existing Google Drive vault remains exact-byte identified as:

```text
existing cloud instance_id: kvi_a31335d2cc3745fa987b635432cfed2c
current ordinal: KV #1
requested peer ordinal: KV #2
relationship: NOT_CONNECTED
adoption.receipt.json: sha256:64a3af27be0bd6ae36b05b35e52894581413fff048cea237d370d0ec6248b552
my-kv-set-projection.json: sha256:187ab43f0bb09d88da154af26d57e1bfe7199fd90affd2dd81af5532f0e34cf4
```

Because the current iPhone resident KV is now KV #1, the existing Google Drive vault requires an explicit governed ordinal reassignment/adoption event. No silent rewrite is permitted.

## Prepared and deployed Google Drive KV #2 adoption transport

Site PR #1122 merged the bounded adoption transport at `b5c3939878bafc7f3aeb40a52458c7a4528c6628`.

The first authentic owner attempt exposed a legacy current-device Node IndexedDB shape lacking the newer `intr_outbox` store. Site PR #1124 repaired only that exact compatibility case and merged at `297301230b0e17ffc6d6050d708847ab75b8ce7e` after all required gates passed and Pages deployment succeeded.

The repair preserves the normal persisted-outbox path and adds a bounded event-ephemeral compatibility path only for the exact missing-object-store condition. It does not claim durable outbox persistence, provider execution, relationship mutation, or KV materialization.

## Authentic owner retry — resident ingress observed

After #1124 deployment, the owner retried the prepared Google Drive KV #2 adoption action once on the current iPhone. The owner-visible Site result showed:

```text
request_id=SITE-CLOUD-KV-4347408852127319cbda574f02e03edb
governance=PENDING_INTERLOCK_INTR
resident_ingress_observed=true
requested=KV #2
instance_materialized=false
provider_operation_authorized=false
```

Site PR #1127 reconciled this bounded owner-observed result into Site at merge commit `769cfa4e6c479fef26950889e8a1ea20d0502887` after Cloud KV Peer Manager, My KV Multi-Instance Provider Manager, Device Local KV Install, Site Handoff Orchestrator, Ecosystem Heartbeat Orchestration, and Site Bootstrap all passed.

The owner-visible result did not display `resident_transport_origin`, `provider_execution_attempted`, `relationship_mutation_attempted`, or `resident_materialization_observed`; canonical COSV therefore does not infer those values from source/deployment alone.

This evidence proves request emission and resident ingress only. It does not prove Google Drive provider execution, ordinal rewrite, KV #2 materialization, relationship mutation, data movement, replication, AI-corpus exposure, credential use, authority grant, or activation.

## Device <-> KV <-> SKAP roundtrip child

The end-to-end transport objective is now a separate child rather than widening this revalidation worker's semantics:

```text
child_goal: STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001
child_handoff: docs/DEVICE_KV_SKAP_ROUNDTRIP_MIRROR_HANDOFF.md
COSV: 50000000102000
state: ACTIVE
```

StegOS PR #326 merged at `2339f2f2fc8c28eb4d63077387013154dac9b75c` after exact-head CI `34517908014` succeeded. It composes the existing `device-kv` and `kv-skap` / `kv-skap-custody` connectors into one four-leg receipt chain and re-hashes current packet bytes at completion.

The child additionally owns the resident evidence verifier requiring one authentic:

```text
DEVICE_SYSTEM -> KV -> SKAP_VAULT -> KV -> DEVICE_SYSTEM
```

lineage with four canonical adjacent-hop receipts plus receipt-bound exact SKAP and KV readback. Source/CI success does not satisfy the runtime predicate.

This child is related to Google Drive KV #2 but not equivalent to provider execution. A bounded already-authorized non-destructive SKAP reference/ciphertext roundtrip can prove the transport chain without fabricating Google Drive CONNECT/VERIFY completion.

## Canonical vector state

The installed parent vector remains intentionally fail-closed at this checkpoint:

- lifecycle: `MACHINE_OWNED`;
- archive_ready: false;
- evidence_complete: false;
- activated: false;
- propagated: false.

Resident ingress retires the prior “request not emitted” gap, but provider execution/materialization predicates remain open. The child roundtrip also remains runtime-unproven until authentic terminal receipts/readback exist.

## Remaining sequence

1. Complete child `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001`: bind authentic resident Device/KV/SKAP evidence, execute the machine-governed non-destructive roundtrip, and retain four-hop/readback proof.
2. Bind `SITE-CLOUD-KV-4347408852127319cbda574f02e03edb` to authentic downstream Interlock/InTr governance/provider execution.
3. Observe explicit provider-result evidence; do not substitute source, CI, deployment, or resident ingress for provider execution.
4. Materialize the existing Google Drive vault as KV #2 only after authentic provider/governance evidence exists and provenance/private-content constraints remain preserved.
5. Resolve provider credentials through SKAP without copying credentials into ordinary KV, DEVICE_KV, Site, or repository state.
6. Prove provider CONNECT/VERIFY/READ/WRITE/SYNC/DISCONNECT and relationship-tier progression/downgrade/recovery with authentic admitted evidence.
7. Add iCloud or another cloud-hosted KV as KV #3/#n only after the current Google Drive request is resolved.
8. Use cloud recovery/replication to mitigate `BEST_EFFORT_BROWSER_ORIGIN` durability where persistent browser storage is not granted.
9. Mark evidence_complete/activated/propagated only when their exact predicates are observed.

## Manual work

None required during canonical reconciliation. Do not emit the Google Drive adoption request again, clear Safari/stegverse.org data, reinstall the resident KV, rebuild the Node, authorize Google Drive, or create another cloud peer until request `SITE-CLOUD-KV-4347408852127319cbda574f02e03edb` is bound to downstream provider/governance execution. Machine-owned resident/service-worker transitions remain separately governed and are not authorized by this handoff.
