# KV Connection Revalidation COSV Mirror Handoff

Status: SOURCE_PROJECTION_MERGED_VALIDATED / STORAGE_ENDPOINT_V2_MERGED_VALIDATED / PHYSICAL_KV1_ADOPTION_VERIFIED / DEVICE_LOCAL_KV_INSTALL_OWNER_OBSERVED_EXACT_READBACK / DEVICE_LOCAL_DURABILITY_BEST_EFFORT_BROWSER_ORIGIN / GOOGLE_DRIVE_EXISTING_PEER_EXACT_EVIDENCE_RECOVERED / GOOGLE_DRIVE_KV2_ADOPTION_INPUT_PREPARED / LEGACY_NODE_COMPATIBILITY_REPAIR_MERGED_DEPLOYED / AUTHENTIC_GOVERNED_ADOPTION_REQUEST_EMITTED / RESIDENT_INGRESS_OBSERVED / QUERY_SECRET_SAFE_GATEWAY_SOURCE_MERGED / DEPLOYED_QUERY_SECRET_SAFE_INGRESS_EVIDENCE_PENDING / GOOGLE_DRIVE_KV2_NOT_MATERIALIZED / CLOUD_PROVIDER_EXECUTION_PENDING / DEVICE_KV_SKAP_ROUNDTRIP_CHILD_ACTIVE
Repository: `StegVerse-Labs/.github`
Issue: #419
Canonical COSV merge: #423 at `538885a85d1267f3080bde09b5375d6e8b99c577`
Updated: 2026-09-15
Authority effect: NONE

## Purpose

Project and track `KV-CONNECTION-REVALIDATION-WORKER-001` under canonical task.v1 COSV control while preserving the distinction between source state, owner-observed runtime state, physical owner-controlled KnowledgeVault evidence, browser durability, resident ingress, provider-access prerequisites, and authentic governed provider execution.

## Canonical task binding

```text
GOAL TASK ID: KV-CONNECTION-REVALIDATION-WORKER-001
COSV ID: 50000000102000
CANONICAL OWNER REPOSITORY: StegVerse-Labs/continuity-vault-kit
SITE CONSUMER REPOSITORY: StegVerse-Labs/Site
```

Canonical vector remains `50000000102000`.

## Provider-neutral storage endpoint v2 reconciliation

The canonical owner and Site consumer now both contain the compatibility-preserving storage-endpoint v2 model requested under this Goal:

- `StegVerse-Labs/continuity-vault-kit` PR #214 merged at `e1617b4d6b14383f1a72d60c8a1bd997ce7a149f` after exact-head hosted validation passed;
- `StegVerse-Labs/Site` PR #1347 merged at `c57486ab24f5b20781ce9736435ec8b801e45c48` after exact-head hosted validation passed;
- canonical storage model is `KV instance -> storage endpoint -> access adapter -> location`;
- endpoint classes cover DEVICE, CLOUD, NETWORK/NAS, and REMOVABLE storage;
- credential/session requirements are adapter-specific;
- legacy v1 provider-operation requests remain compatible;
- the existing Google Drive KV #2 request lineage is not regenerated, rehashed, renamed, or replaced;
- KV identity, provenance, relationship tiers, Interlock/InTr authority, credential authority, and runtime evidence boundaries are unchanged.

Source/CI/merge of storage-endpoint v2 grants no provider access, no provider operation authority, no relationship mutation, no data movement, no KV materialization, no AI-corpus exposure, and no activation.

Canonical evidence refs:

- `StegVerse-Labs/continuity-vault-kit:KV_STORAGE_ENDPOINT_V2_MIRROR_HANDOFF.md`;
- `StegVerse-Labs/Site:docs/KV_STORAGE_ENDPOINT_V2_MIRROR_HANDOFF.md`.

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

## Prepared Google Drive KV #2 request and resident ingress

The existing request remains exactly:

```text
request_id=SITE-CLOUD-KV-4347408852127319cbda574f02e03edb
governance=PENDING_INTERLOCK_INTR
resident_ingress_observed=true
requested=KV #2
instance_materialized=false
provider_operation_authorized=false
```

Site PR #1127 reconciled the bounded owner-observed resident-ingress result at merge commit `769cfa4e6c479fef26950889e8a1ea20d0502887`.

This proves request emission and resident ingress only. It does not prove Google Drive provider execution, ordinal rewrite, KV #2 materialization, relationship mutation, data movement, replication, AI-corpus exposure, credential use, authority grant, or activation.

## Existing provider binding and identity-preserving materializer

`StegVerse-Labs/continuity-vault-kit` already contains the canonical provider-binding source for CONNECT/VERIFY and `runtime/cloud_peer_set_membership_materialization.py` for identity-preserving post-verification set membership.

The materializer requires admitted evidence with `materialization_ready=true` and `provider_connect_verified=true` before it can bind existing cloud identity `kvi_a31335d2cc3745fa987b635432cfed2c` into `personal` as KV #2. It preserves the existing cloud identity, leaves relationship tier `NOT_CONNECTED`, forbids private-content rewrite, requires CONNECT/VERIFY receipt refs, and grants no provider, relationship, transport, credential, or activation authority.

Therefore the recovered Google Drive vault MUST NOT be passed through the generic new-identity adoption materializer.

## Query-secret-safe owner-consent prerequisite

The Google Drive owner-consent/provider-execution lane is currently fail-closed on the public callback ingress safety predicate.

The existing Service Gateway owner `StegVerse-org/LLM-adapter#271` has merged the source hardening through PR #328:

- Uvicorn built-in request-target access logging is disabled;
- `QuerySecretSafeAccessLogMiddleware` logs only HTTP method, canonical path, and status;
- the middleware intentionally does not read or serialize ASGI `query_string`, raw request target, headers, cookies, body, OAuth authorization code, state, or provider credential material.

This closes the source implementation gap only. It does **not** satisfy the deployed-ingress predicate.

Canonical TVC handoff `docs/GOOGLE_DRIVE_PERSONAL_KV_OWNER_CONSENT_CALLBACK_INGRESS_MIRROR_HANDOFF.md` still requires authentic observation that the active `stegverse.org -> TVC` path is running the query-secret-safe boundary and cannot persist synthetic callback query material before `/tvc/google-drive/callback` may be installed/activated for owner consent.

No authentic deployed-ingress log observation is recorded in the canonical sources reviewed on 2026-09-15. Therefore Google consent, provider auth-code exchange, CONNECT, VERIFY, and KV #2 materialization remain inadmissible at this checkpoint.

## Device <-> KV <-> SKAP roundtrip child

The end-to-end transport objective remains a separate child:

```text
child_goal: STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001
child_handoff: docs/DEVICE_KV_SKAP_ROUNDTRIP_MIRROR_HANDOFF.md
COSV: 50000000102000
state: ACTIVE
```

The child requires one authentic:

```text
DEVICE_SYSTEM -> KV -> SKAP_VAULT -> KV -> DEVICE_SYSTEM
```

lineage with four canonical adjacent-hop receipts plus receipt-bound exact SKAP and KV readback. Source/CI success does not satisfy the runtime predicate.

## Canonical vector state

The installed parent vector remains intentionally fail-closed:

- lifecycle: `MACHINE_OWNED`;
- archive_ready: false;
- evidence_complete: false;
- activated: false;
- propagated: false.

Storage-endpoint v2 is merged source capability. It does not retire the provider-execution or authentic roundtrip evidence predicates.

## Remaining sequence

1. Produce authentic deployed-ingress evidence for the existing query-secret-safe Service Gateway using a harmless synthetic query value; prove the active public gateway logs only method + canonical path + status and does not persist the synthetic query value or raw request target.
2. Reconcile `StegVerse-org/LLM-adapter#271` and `StegVerse-Labs/TVC#328/#317` only from that authentic deployed observation.
3. Implement/activate the exact TVC callback route only after the ingress-safety predicate passes, reusing the existing owner-consent controller, canonical SKAP client-secret protected-use adapter, protected refresh store, vault-session consumer, Interlock/InTr boundaries, and canonical carrier.
4. Execute authentic owner-present Google consent inside TV/TVC/SKAP; do not expose provider credential plaintext to Site, ordinary KV, repositories, logs, argv, environment, or browser response.
5. Bind existing request `SITE-CLOUD-KV-4347408852127319cbda574f02e03edb` to canonical CONNECT and VERIFY operations through Interlock/InTr and retain exact provider-result and admission receipt evidence.
6. Only after CONNECT+VERIFY evidence yields `materialization_ready=true`, bind existing cloud identity `kvi_a31335d2cc3745fa987b635432cfed2c` into `personal` as KV #2 with identity/private-content preservation.
7. Return the result through SKAP -> KV -> current StegOS Device and require the canonical four-leg roundtrip proof plus exact terminal readback.
8. Prove later READ/WRITE/SYNC/DISCONNECT and relationship-tier progression/downgrade/recovery only through authentic admitted evidence; do not infer them from CONNECT/VERIFY or materialization.
9. Add KV #3/#n only after the current Google Drive request is resolved.
10. Mark evidence_complete/activated/propagated only when their exact predicates are observed.

## Manual work

None at this checkpoint. Do not re-emit or replace `SITE-CLOUD-KV-4347408852127319cbda574f02e03edb`, do not initiate Google consent, do not authorize Google Drive, do not clear Safari/stegverse.org data, do not reinstall KV, and do not create KV #3 until authentic deployed query-secret-safe ingress evidence is retained and the TVC callback preflight is reopened.
