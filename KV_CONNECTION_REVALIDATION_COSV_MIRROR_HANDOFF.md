# KV Connection Revalidation COSV Mirror Handoff

Status: ACTIVE / DEVICE_LOCAL_KV_OWNER_OBSERVED_EXACT_READBACK / GOOGLE_DRIVE_EXISTING_PEER_RECOVERED / AUTHENTIC_KV2_REQUEST_RESIDENT_INGRESS_OBSERVED / PROVIDER_BINDING_MERGED / IDENTITY_PRESERVING_KV2_MATERIALIZER_MERGED / FOUR_LEG_SKAP_KV_DEVICE_SOURCE_GATE_MERGED / SOVEREIGN_QUERY_SECRET_SAFE_CALLBACK_DEPLOYMENT_PROOF_PENDING / GOOGLE_DRIVE_CONNECT_VERIFY_RUNTIME_PENDING / FULL_ROUNDTRIP_RUNTIME_PENDING
Repository: `StegVerse-Labs/.github`
Issue: #419
Updated: 2026-09-10
Authority effect: NONE

## Canonical task binding

```text
GOAL TASK ID: KV-CONNECTION-REVALIDATION-WORKER-001
COSV ID: 50000000102000
CANONICAL OWNER REPOSITORY: StegVerse-Labs/continuity-vault-kit
SITE CONSUMER REPOSITORY: StegVerse-Labs/Site
TRANSPORT OWNER: StegVerse-Labs/StegOS
CREDENTIAL AUTHORITY: TV/TVC
TRANSITION/POSTURE AUTHORITY: Interlock/InTr
```

## Current authentic resident basis

Current iPhone resident KV #1 remains owner-observed:

```text
instance_id: kvi_0d5d4cfd531db51bbcf7fdfc0311f5dc
kv_set_id: personal
storage: device-local-browser-indexeddb
relationship: NOT_CONNECTED
exact_readback: true
durability: BEST_EFFORT_BROWSER_ORIGIN
```

Existing Google Drive cloud KV remains exact-byte identified as:

```text
instance_id: kvi_a31335d2cc3745fa987b635432cfed2c
requested peer ordinal: KV #2
relationship: NOT_CONNECTED
```

Authentic current-device adoption request already reached resident ingress:

```text
request_id: SITE-CLOUD-KV-4347408852127319cbda574f02e03edb
resident_ingress_observed: true
governance: PENDING_INTERLOCK_INTR
instance_materialized: false
provider_operation_authorized: false
```

Do not infer provider execution, SKAP session use, cloud materialization, relationship mutation, or runtime activation from this ingress observation.

## Source closure completed in this continuation

### Four-leg SKAP <-> KV <-> Device proof gate

StegVerse-Labs/StegOS PR #327 merged at `84ddc96e38d6a5156becd91fb49da7dd14047bca` after exact-head StegOS CI run `34518469300` succeeded.

`stegos/skap_kv_device_roundtrip.py` now refuses a functional-completion claim unless one operation proves the exact adjacent sequence:

```text
DEVICE_SYSTEM -> KV -> SKAP_VAULT -> KV -> DEVICE_SYSTEM
```

Every leg must have a complete Universal InTr receipt chain; each leg must hash-chain to the previous terminal receipt; the KV->SKAP payload must be bound to an active task-scoped authoritative Interlock/InTr posture instance at HIGHEST; TV/TVC remains credential authority; the resulting roundtrip receipt is evidence-only.

### Identity-preserving recovered-cloud KV #2 materialization

StegVerse-Labs/continuity-vault-kit PR #210 merged at `559fea2fbc4c7a78ee674a546b5132327b103a83`. Exact-head checks all succeeded:

```text
KV Cloud Peer Adoption Provider Binding: 34518950052 SUCCESS
KV Existing Instance Adoption: 34518950039 SUCCESS
Repository validation diagnostics: 34518950093 SUCCESS
Security Baseline: 34518950167 SUCCESS
KV Guardrails: 34518950012 SUCCESS
```

`runtime/cloud_peer_set_membership_materialization.py` consumes only already-admitted CONNECT+VERIFY readiness and binds the recovered Google Drive identity into the personal set as KV #2 without generating a replacement `kvi_...`, rewriting cloud identity, rewriting private content, moving data, changing relationship tier, or acquiring credential/provider authority. It fails closed on premature readiness, ordinal collision, cross-set/cross-ordinal reuse, missing evidence references, credential material, or identity rewrite semantics.

## Google Drive / SKAP credential-session path

The prior Google-session implementation gap has materially narrowed. Current TVC source includes:

```text
#302 / PR #323 -> callback-contained protected refresh custody -> merged 7ccaac0792abc587b6d273489111183fc2d19538
#315 / PR #325 -> bounded Google Drive session installation into existing vault agent -> merged 90c935b1a8480d568fea2d8300b115a3ef9d72af
#327 / PR #329 -> protected Google client-secret use through canonical SKAP resolver -> merged 3e09a756ad969574e24fd963e6da0227753dba7a
```

TVC #317 owns the Google Personal-KV owner-consent callback. Its sole safety prerequisite is TVC #328 / StegVerse-org/LLM-adapter #271 query-secret-safe public ingress.

LLM-adapter #271 source hardening is merged via PR #328 at `05140d58613cffcfd08f164ff5459c36870a60ee`: built-in Uvicorn request-target access logging is disabled and the composed Gateway is wrapped with path-only query-secret-safe logging.

A historical/development branch `deployed-gateway-query-safe-271` is NOT admissible for the current closure because its own work-safety receipt states that it targets a Render production entrypoint. Current StegVerse requirements prohibit Render/hosted runtime authority for this lane. The required deployment observation must therefore be from the sovereign/non-Render `stegverse.org -> TVC` callback ingress.

TVC #328 has been reconciled with that distinction and remains open until authentic sovereign deployed-ingress evidence exists.

## Exact remaining runtime sequence

1. The existing Service Gateway owner proves the active sovereign/non-Render public ingress uses the merged query-secret-safe logging boundary; no OAuth code/query secret may persist in request-target/access logging.
2. TVC #328 may then close and TVC #317 may install/activate the exact `https://stegverse.org/tvc/google-drive/callback` owner-consent route through its existing authority lane.
3. One owner-authorized Google session must be acquired inside TV/TVC/SKAP without exporting client secret, authorization code, access token, refresh token, bearer material, or provider secret to Site, ordinary KV, repository state, logs, argv, or environment.
4. Existing request `SITE-CLOUD-KV-4347408852127319cbda574f02e03edb` must drive authentic Google Drive CONNECT and VERIFY through Interlock/InTr with provider-result evidence.
5. CVK must consume those admitted results and materialize the existing `kvi_a31335d2cc3745fa987b635432cfed2c` as `personal` KV #2 using the identity-preserving materializer.
6. The resulting response must traverse `SKAP_VAULT -> KV -> DEVICE_SYSTEM` and produce the four-leg StegOS roundtrip evidence.
7. The current StegOS device must independently exact-readback the returned bounded result.
8. Only then may `SKAP <-> KV <-> StegOS Device` be marked runtime-functional.

## Explicit non-completion conditions

```text
source merge != runtime execution
CI PASS != provider execution
resident ingress != Google CONNECT/VERIFY
SKAP source implementation != active owner session
Render deployment != sovereign deployment evidence
KV #2 readiness != KV #2 materialization
one-way KV->SKAP receipt != bidirectional roundtrip
roundtrip source verifier != authentic roundtrip receipt
```

## Manual work

None now. Do not repeat the Google Drive adoption request, clear Safari/stegverse.org state, reinstall KV, authorize Google Drive, or create KV #3 until the sovereign callback safety predicate and TVC #317 route are ready for the existing request.
