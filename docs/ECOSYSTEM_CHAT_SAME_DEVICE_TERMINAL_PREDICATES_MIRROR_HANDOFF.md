# Ecosystem Chat Same-Device Terminal Predicates Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-Labs/.github`
Architecture owner: `.github#201`
Task: `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`
State: `STEGOS_SOURCE_PROJECTION_RELEASED_AUTHENTIC_DEVICE_EXECUTION_PENDING`

## Defect repaired upstream

The canonical parent terminalizer formerly accepted only the native/private-process runtime pair:

```text
real_model_process_observed=true
private_endpoint_only=true
```

The already-implemented current-iPhone sovereign runtime intentionally reports those two predicates false and instead proves:

```text
browser_service_worker_runtime_observed=true
device_local_intercepted_endpoint=true
network_egress_required=false
real_inference_response_observed=true
endpoint_transport=SERVICE_WORKER_LOCAL_INTERCEPT
endpoint=https://stegverse.org/stegos-bootstrap/local-model
service_worker_scope=https://stegverse.org/stegos-bootstrap/
```

The TVC, LLM-adapter, and Master Records web-runtime validators accept this exact device surface. `scripts/run_independent_ecosystem_chat_parent.py` therefore classifies the sovereign execution surface as either `PRIVATE_PROCESS` or `CURRENT_USER_IPHONE_SERVICE_WORKER`, and terminal activation requires the aggregate `sovereign_runtime_execution_surface_observed=true` rather than false process-only facts.

## StegOS source projection reconciliation

The downstream source-projection step previously listed as the next transition is now complete at the source layer:

```text
StegVerse-Labs/StegOS issue: #213
source pin PR: #214
bounded adapter PR: #215
material existing-service-worker integration PR: #216
validated source head: 1c56b0475e00c5be9b9e3e8a500c12c70a954eef
StegOS CI validation run: 34021150351 / SUCCESS
merged source commit: 4ef5e1e3e06969ed538cf0538d5657652abb26e1
claim-release PR: #217
claim-release commit: 7a34d282b0eba3ff7d51ed6fb316b4332eb09a51
```

The released StegOS source reuses the exact canonical portable WorkerCoordinator checkout, TV/TVC route authority, LLM-adapter browser runtime, Master Records browser reconstruction runtime, one existing service worker, one existing `stegos-web-bootstrap-v1` IndexedDB namespace, one portable WorkerCoordinator state key, the existing device-local model endpoint, and the existing hash-linked device journal.

The released same-origin interface is:

```text
POST /stegos-bootstrap/portable-workercoordinator/ecosystem-chat
```

This source release does not itself mint the parent claim/fence and does not alter the canonical `.github` package state.

## Unchanged terminal requirements

The runtime-surface repair and StegOS source release do not relax:
- exact TVC route verification;
- exact LLM-adapter execution verification;
- measured usage;
- Master Records reconstruction verification;
- provider-usage reconstruction PASS;
- transition reconstruction PASS;
- same-execution identity;
- persistent conversational runtime readiness;
- TV/TVC credential authority / `NONE` credential requirement;
- no GitHub token / no hosted production authority;
- bounded fresh parent claim/fence;
- fail-closed release on nonterminal or scope failure.

## Current runtime truth

```text
parent_package_state=HANDOFF_READY
parent_claim_id=null
parent_worker_id=null
minimum_fencing_token_exclusive=24
fresh_first_possible_fence=G25
StegOS_source_projection_released=true
current_iPhone_checkout_observed=false
current_iPhone_local_inference_observed=false
measured_usage_observed=false
Master_Records_same_execution_reconstruction_PASS=false
parent_terminal=false
Site_HIL_activation=false
```

The historical G20 carrier receipt remains nonterminal evidence and is not rewritten by this source reconciliation.

## README impact

README update is **not required for this reconciliation-only change**. The canonical parent runtime semantics and same-device service-worker acceptance were already documented when the terminalizer changed. This update records downstream source completion and changes no checkout algorithm, package semantics, runtime interface, authority boundary, prerequisite, failure behavior, or capability meaning.

## Non-inference boundary

Source, merge, CI, StegOS route availability, and this reconciliation do not prove that the current iPhone executed the task, that a fresh G25+ fence was issued, that measured usage or reconstruction occurred, or that Ecosystem Chat activated.

## Next transition

The next authentic transition is now:

```text
consume the released StegOS interface on CURRENT_USER_IPHONE
-> atomically mint the canonical fresh parent claim/fence through the exact portable WorkerCoordinator
-> require G25 or greater
-> obtain service-worker local-model runtime proof + exact TVC route
-> execute through exact LLM-adapter runtime with measured usage
-> reconstruct the same execution through Master Records
-> require provider-usage reconstruction PASS + transition reconstruction PASS + same_execution=true
-> preserve device-journal replay PASS
-> return that authentic device evidence to the canonical parent terminalizer
```

No second machine, second WorkerCoordinator, hosted inference provider, non-TV/TVC credential, or GitHub runtime authority is admissible as a substitute.

## Auri MyKV reusable peripheral source releases — 2026-09-25

Reconciled against canonical Registry main generation 248 and existing owner `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`, COSV `50000000100000`. This is **source-evidence reconciliation** under the same owner, not a new task/checkout, an execution admission, an assertion that the historical physical-iPhone fixture is a universal node requirement, or promotion of the parent runtime predicates recorded above. Global `data/task-registry-global-invariants.json` makes KV/SKAP Vault the sole user verifier and eligible StegOS nodes interchangeable; physical identity is not a verification or completion gate.

Released source evidence:

- Existing KV device-backed capability owner `StegVerse-Labs/continuity-vault-kit#53`, with typed transport owner #124: PR #223 merged `c6d4a9c29350b9b5fcb8b9a0ceee8b9a0a84f773`; exact-head `b43b44e643fe1ae223a432588e01f1eb216b7761` passed KV Guardrails, Security Baseline, Release Integrity, Runtime Import/Secret Field Policy and Repository Diagnostics. Seven non-authorizing profiles: visual display, touch/gesture, separate audio input/output, separate video input/output, and optional flexible-glass composition. Existing `auri-ecosystem-chat` and `stegwhisper` modules retain `INSTALLED_INACTIVE` and reference the shared source; 16 dedicated source-only tests passed.
- Existing StegOS Ecosystem Chat source owner #213: PR #413 merged `14fd948be9fc40613065df33b3a0a185cac04943`; exact-head `60607af2c2bbaa0857dcf8269cf5f67e1f3d1fcf` passed StegOS CI `36192724946` and GADI `36192724988`. The first CI failure was real frozen source-projection drift after modifying the service worker. Correct repair restored `mobile/web-bootstrap/service-worker.js` byte-identically to Git blob `3062112065bd49e96d5eeef87c71bbb5dc09a0fb`, importing the optional Auri module through the existing bridge; all prior projection tests and 22 added source-only Auri tests passed. Follow-up handoff correction PR #414 merged `49efc6b3d736dde7b995e4b64c8f92f26096c409` after CI SUCCESS `36192956978`.

The existing Ecosystem Chat route `POST /stegos-bootstrap/portable-workercoordinator/ecosystem-chat` now supports an optional `X-StegVerse-Auri-Preflight: source-only` diagnostic using `request_kind: AURI_LIVE_MODE_PREFLIGHT`. Three natural utterances resolve to `live_audio`, `live_video`, and `live_audio_video`, with mode-specific independent capture scopes, revocation and transport checks, stable `session_id`, and predecessor-linked, typed-transport-bound **manifest candidates** pinned to the merged KV profiles. `CANDIDATE_ALLOW_REQUIRES_REAL_RUNTIME_DISPOSITION` and `CANDIDATE_NON_ALLOW` are **not** actual runtime ALLOW/DENY or Master Records receipts. Actual direct mute, OS capture prompts, AV execution and physical peripheral exchange are not implemented by the preflight.

`AI_SESSION_GATE` does not presently exist as a usable implementation interface and is **not a source-development or source-merge prerequisite**. The existing `scripts/resolve_task_work_correlation.py` already separates canonical source correlation from real runtime admission. At the time of this source release, the Site task orchestrator published `admitted_tasks=[]` / `external_session_ownership_allowed=false`; Site#239 retains UI implementation ownership without a competing source checkout.

**Outstanding authentic execution**: an eligible interchangeably selected StegOS execution surface, actual SKAP relationship and separate audio/video capture consent, real mode-specific manifested requests admitted by existing SDK and Interlock/InTr at every actual boundary, TV/TVC operation if needed, authorized native capture/output, mid-session revocation and node replacement behavior, retained organization receipts, and exact same-execution predecessor-linked Master Records reconstruction. No real mode transition was attempted through an authenticated resident interface by these source-only PRs, so there is no genuine ALLOW, DENY or FAIL_CLOSED receipt to report from them. Preserve the historical runtime predicates in this handoff until original receipts support an authorized transition.
