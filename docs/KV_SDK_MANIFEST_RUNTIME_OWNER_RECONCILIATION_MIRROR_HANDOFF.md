# KV / SDK Manifest Runtime and Custody Owner Reconciliation

Date: 2026-09-24
Original Goal Task ID: KV-CONNECTION-REVALIDATION-WORKER-001
Original COSV: 50000000102000 (unchanged)
Canonical coordination: StegVerse-Labs/.github
KV proof and connection-domain owner: StegVerse-Labs/continuity-vault-kit#119
Existing KV resident consumer: StegVerse-Labs/.github#366 and issue #424
SDK generic manifest/route/result-lineage owner: StegVerse-org/StegVerse-SDK
Service Gateway deployed query-secret-safe ingress: StegVerse-org/LLM-adapter#271
Google callback/provider credential owner: StegVerse-Labs/TVC#317/#328
Device/KV/SKAP four-leg proof: STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001
Authority effect: NONE; source and coordination only

## Current canonical registry and prompt-budget reconciliation

The latest accessible main canonical Task Registry generation at review was **221**, with no active registry entry for the original KV Goal. The original executable handoff remains at `handoffs/KV-CONNECTION-REVALIDATION-WORKER-001.json` and retains `successor_policy=INHERIT_OR_NARROW` / `max_successor_depth=2`. Its task vector remains `50000000102000`, MACHINE_OWNED, and evidence_complete=false. Exhaustion of 20/20 conversation prompts is a handoff budget limit only: it grants no state transition, claim, activation, or permission to mint another Goal. Preserve that original task identity and existing native owner; reuse the existing separately registered proof-intake and Device/KV/SKAP task identities where their narrower scopes apply. Check the authentic current registry generation and AI_SESSION_GATE/claim-fence only when performing an authorized implementation transition. This reconciliation is not a new registered Goal or a substitute for authentic admission.

## Source inspection / actual installed capabilities

Current SDK main VERSION.json declares 1.3.0 RELEASE_CANDIDATE plus 1.4.0.dev0 development. `stegverse/route_resolution.py` publishes governance, ecosystem_diagnostic, purpose_bound_worker and atomic_task_worker; **no kv_connection_revalidation route is installed**. The local purpose/atomic worker entries are SDK semantic demonstrations, not a substitute for resident provider execution. `stegverse/manifest_builder.py` validates processing.capability, processing.route_id and the published route tuple; it does not have a KV-specific processor_request binding. `stegverse/manifest_state_transition_runtime.py` has a reusable Universal InTr request contract, exact manifest/route/graph binding and strict ordered Master Records closures and replay/reconstruction validation. `stegverse/manifest_execution.py` binds canonical_manifest_sha256, request_sha256, processor_result_sha256 and manifest_lineage. Source construction, route resolution or local semantic demonstrations grant no runtime authority.

KV `runtime/connection_revalidation.py` already validates exact assembly, existing provider/session conformance proof and separate exact private-KV readback proof, rejects credentials/provider operation authority and stale proof timing, and exclusively calls canonical `verify_connection`. The .github existing resident worker `workers/kv_connection_revalidation_worker.py` consumes those proofs and persists private-KV state; do not replace it with an SDK-local executor. The CVK identity-preserving materializer in `runtime/cloud_peer_set_membership_materialization.py` already requires separately admitted CONNECT/VERIFY and readiness true before ordinal-2 binding. Do not call it from proof revalidation merely because a manifest was validated.

KV `runtime/intr_lifecycle_closure.py` is a derivation and local verification helper for a specific outbox -> ingress -> materialization-attempt chain. It currently builds a proposed custody record with `custody.status=ACCEPTED_FOR_CUSTODY`, then self-constructs a `MASTER_RECORDS_CUSTODY_RECORDED` closure and `state=COMPLETE` terminal-looking receipt **without consuming an independently authoritative Master Records acceptance result**. Its source tests validate the locally constructed receipts. This is a deterministic source-evidence authority/conformance gap, not authentic proof that runtime custody failed. In the current contract `MATERIALIZATION_EXECUTION_ATTEMPTED` is not successful KV CONNECT/VERIFY or provider proof, and proposed locally reconstructed digests are not independently accepted Master Records receipts. Never promote this proposed terminal receipt to canonical custody, SDK COMPLETED result, or deployed KV state.

## Required reuse and owner-specific missing compatibility

1. Canonical ingress retains the existing KV owner request, original Google Drive identity and COSV. A source-native KV proof-intake envelope may be mapped to the existing generic SDK manifest contract only under the existing SDK manifest owner and admitted canonical KV processing route. Do not bypass existing proof-intake worker or generate an independent KV request, session, scheduler or token.
2. Publish a KV processing route in the SDK **only after owner convergence and authentic Task Registry admission** establish that the generic SDK route is the necessary integration seam rather than merely a consumer of the existing canonical InTr transport. A KV adapter derives a graph only (`adapter_executes_lifecycle=false`), names the canonical task and requires WorkerCoordinator claim/fence for bounded worker execution. It must never perform provider auth, grant a KV relationship, construct authority from provider/session identifiers, or execute the canonical CVK verifier itself.
3. Reuse existing Universal InTr ingress, WorkerCoordinator claim/fence, TV/TVC provider credential custody and Master Records acceptance. The SDK validator's `RECORDED`, `reconstruction_status=PASS`, `required_evidence_validation_status=PASS`, exact reconstructed hash, immediate predecessor hash, replay and terminal records-only requirements remain intact. Inspect the existing Master Records native acceptance interface before modifying CVK closure. The CVK owner must split local custody preparation from authoritative closure or consume and verify the exact accepted Master Records receipt; only the actual native Master Records return may unlock `MASTER_RECORDS_CUSTODY_RECORDED`.
4. Result lineage binds the original manifest/request/canonical CVK assembly and persisted private-KV health receipt to the exact runtime evidence. A projection to MyKV cannot imply provider CONNECT, materialization, native installation, relationship mutation, or device roundtrip when those separate owners have not closed.
5. Healer's scheduler/checkpoint is an optional triggering and diagnostic carrier. Its receipts are **not** KV completion predicates. Do not introduce or require idle connected-device checks, another resident runtime, second worker, dispatcher, scheduler, ledger, credential ingress, or a second user-operated device.

## Preserved exact Google Drive and KV identities

Original request = SITE-CLOUD-KV-4347408852127319cbda574f02e03edb
Existing cloud instance = kvi_a31335d2cc3745fa987b635432cfed2c
Current local KV #1 identity = kvi_0d5d4cfd531db51bbcf7fdfc0311f5dc
Requested ordinal = KV #2; do not mint/rewrite a different cloud identity or alter private bytes.
Existing exact reusable invocation = KV-CONNECTION-REVALIDATION-WORKER-001:TVC-CAPABILITY-RUNTIME-002:QUERY-SECRET-SAFE-INGRESS-001 (do not reissue).

## Independent production execution gates

A. Service Gateway must provide authentic active public ingress log evidence on a harmless synthetic noncredential query-bearing request: canonical method/path/status retained; raw request target, query and synthetic value absent. Source and CI are not deployment proof.
B. Only after A: TVC callback preflight at the existing exact https://stegverse.org/tvc/google-drive/callback route. No credential in repositories, argv, environment, receipts, ordinary KV, Site or logs. TVC/SKAP is sole provider credential authority.
C. Only after B and separately authorized owner-present ceremony: provider consent; then authentic Interlock/InTr CONNECT/VERIFY with TVC provider-result evidence and applicable Master Records closure.
D. Only after C and materialization_ready=true: existing identity-preserving CVK KV #2 materializer; then separately owned single-device four-leg Device -> KV -> SKAP -> KV -> Device proof, exact readback and applicable Master Records evidence.

No authentic A-D runtime closure was established by this source review. Do not infer it from SDK 1.3 source validations, merged Healer schedule, local KV closure fixtures, CVK source merges or simulated SDK/KV journal integration.

## Narrow successor handoff / next admissible actions

Retain original Goal as parent correlation without minting or duplicating it. Use existing CVK #119 / .github #366 + #424 for nonsecret revalidation proof intake and existing `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` for its distinct runtime proof. Canonical Task Registry admission must explicitly resolve any missing SDK-to-KV integration ownership before a code change to SDK or CVK. Under that approved native owner, (i) repair CVK proposed-vs-accepted custody distinction, (ii) add a purpose-limited SDK manifest route/adapter only if not already supplied by existing Universal InTr integration, (iii) add positive, negative, stale-proof, wrong-manifest, wrong-owner and independent reconstruction tests, and (iv) validate exact-head checks before authorized merge. Runtime remains UNKNOWN_NOT_AUTHENTICALLY_OBSERVED until genuinely retained native closure. Do not issue another resident invocation or Google Drive request from this handoff.
