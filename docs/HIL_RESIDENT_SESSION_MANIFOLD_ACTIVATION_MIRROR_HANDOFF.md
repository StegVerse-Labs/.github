# HIL Resident Session Manifold Activation Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Issue: `#1178`
Canonical goal task: `SHWP-HIL-SOVEREIGN-RECEIVER-001`
Manifold task: `HIL-RESIDENT-SESSION-MANIFOLD-ACTIVATION-001`
Current task COSV: `50000000103000`

## Source of truth

This file is the canonical continuation record for the HIL sovereign receiver lane as visited through the governed resident-session manifold.

Primary inherited sources:

- `docs/HIL_RESIDENT_SESSION_COHORT_MIRROR_HANDOFF.md`
- `docs/HIL_SOVEREIGN_RECEIVER_ACTIVATION_MIRROR_HANDOFF.md`
- `docs/GOVERNED_MULTILANE_MANIFOLD_ACTIVATION_MIRROR_HANDOFF.md`
- `docs/CROSS_TASK_COORDINATION_MIRROR_HANDOFF.md`
- `docs/HIL_G25_REQUEST_CONSUMPTION_RECONCILIATION_20260909.md`
- `docs/HIL_BROWSER_ESRL_EVIDENCE_INTAKE_MIRROR_HANDOFF.md`
- `docs/HIL_POST_ESRL_READINESS_MIRROR_HANDOFF.md`
- `docs/HIL_ESRL_ACCEPTANCE_RECONCILIATION_MIRROR_HANDOFF.md`
- `StegVerse-Labs/Site/docs/HIL_BROWSER_ESRL_LEASE_OPEN_MIRROR_HANDOFF.md`
- `scripts/intake_hil_browser_esrl_evidence.py`
- `scripts/evaluate_hil_post_esrl_readiness.py`
- `scripts/reconcile_hil_esrl_acceptance.py`
- `scripts/verify_hil_post_restart_reconstruction.py`

## Canonical current state

The parent task remains `ACTIVE / HANDOFF_READY`, non-archivable, with COSV `50000000103000` and exactly three independent evidence obligations:

1. `AUTHENTIC_ESRL_HIL_LEASE_OPEN_NOT_YET_OBSERVED`
2. `POST_RESTART_EXACT_BYTE_PROOF_NOT_YET_PRESERVED`
3. `TVC_HIL_LIFECYCLE_HANDOFF_NOT_YET_PROVEN`

Accepted upstream physical state is unchanged:

```text
request = RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002
runtime surface = CURRENT_USER_IPHONE_BROWSER
browser context = ctx_d151139d2db1eeecb6512f5844058246
node = stegnode-web-f24e3bfb7f5343cb37323187a88e51f3
claim = SHWP-SHWP-HIL-SOVEREIGN-RECEIVER-001-G25
fence = 25
request consumption = SATISFIED
journal replay = PASS
```

Canonical request-consumption evidence remains `receipts/sovereign-host/hil-resident-execution-request-consumption.latest.json`. G25 request consumption is complete; it does not imply broader HIL lifecycle completion.

## Completed ESRL source lineage

### ESRL successor and canonical intake

Site PR `#1159` merged the same-context current-iPhone browser ESRL successor while preserving the admitted v16 service-worker wrapper and existing G25 WorkerCoordinator checkout lineage. `.github` PR `#1248` merged the fail-closed `scripts/intake_hil_browser_esrl_evidence.py` path.

The first authentic ESRL attempt retained the exact G25 context/node/fence but failed closed with `canonical checkout receipt hash required`. Investigation established a source-envelope compatibility defect rather than checkout loss.

Site PR `#1165`, merged at `7a72c94b3e4fc246424975d97729c4f2220fbef0`, repaired the historical-envelope compatibility by deriving a missing checkout hash only from the exact retained checkout after full lineage validation, preserving the authentic raw execution-entry digest, and including the checkout hash in future activation results. No replacement checkout or claim/fence was introduced.

Site PR `#1169`, merged at `9751d100250c5a3905a363e08c9d9bed47d54ff7`, made the ESRL page automatically continue from exact retained G25 state and persist only an exact same-context `LEASE_OPEN` result. Manual retry/copy/download remain fallbacks.

### Stale standalone-Safari convergence defect

A later authentic current-iPhone observation showed standalone Safari still rendering the older **Open ESRL lease** / `No ESRL evidence yet.` page until the button was tapped, despite repository source already containing the automatic-resume page. The button was therefore acting as an accidental page/worker convergence trigger.

Site PR `#1173` repaired this and is **MERGED** at `61865d7649fc39669caa39008568764f8b7c45b4`.

The repair preserves `stegos-web-bootstrap-v16` and `HIL_BROWSER_EVIDENCE_V16`, adds `hil-esrl-activate.html` to the existing wrapper shell, preserves `skipWaiting()` / `clients.claim()`, and after worker activation re-navigates only an already-open same-origin ESRL page so refreshed auto-resume source is loaded. It does not clear IndexedDB/localStorage, portable WorkerCoordinator state, retained evidence, or G25 lineage.

Exact-head PR `#1173` validation all passed after two detected defects were repaired rather than bypassed:

- `Validate StegOS Persistent Card UX` run `34364465283` — SUCCESS;
- `No Required Third-Party Runtime` run `34364465495` — SUCCESS;
- `Site Handoff Orchestrator` run `34364465573` — SUCCESS;
- `Ecosystem Heartbeat Orchestration` run `34364465326` — SUCCESS;
- `Site Bootstrap Validate - No Non-TV/TVC Credential Authority` run `34364465667` — SUCCESS.

The repaired validation defects were:

1. the already-merged auto-resume claim was stale as `CLAIMED` and was terminalized to `RELEASED`, removing a dependency-surface collision;
2. the new service-worker Git blob `a27fb3d98f32924452da9b19921b9824d3d2a7c3` was explicitly registered in the StegOS projection successor allowlist.

Post-merge push validation on `61865d7649fc39669caa39008568764f8b7c45b4` also passed for persistent-card validation (`34364653678`) and no-required-third-party-runtime (`34364653358`).

Site PR `#1176`, merged at `c1b75e1a7ee095918db727a0da87688c544af5e4`, reconciled the canonical Site ESRL handoff to the #1173 merge/validation state. Its exact-head validation passed: Site Handoff Orchestrator `34365046902`, Ecosystem Heartbeat `34365046877`, and Site Bootstrap `34365046905`.

A separate terminalization-only Site claim-release PR `#1177` releases the post-merge handoff reconciliation claim; it does not release the still-active stale-navigation runtime observation claim.

## Current physical evidence boundary

Repository source, exact-head validation, merge, and post-merge handoff reconciliation are complete for the stale-navigation repair. Public propagation into the retained standalone-Safari context is still a physical observation requirement. A control-plane execution environment that cannot directly observe the retained Safari storage/service-worker state cannot substitute for that physical evidence.

The next successful physical path must be:

```text
same retained standalone-Safari G25 context
-> current /stegos-bootstrap/hil-esrl-activate.html bytes
-> current v16 wrapper/page convergence
-> automatic exact-state ESRL resume
-> existing retained G25 checkout
-> HIL_BROWSER_ESRL_V1
-> REQUESTED -> ADMITTED -> PROVISIONING -> LOCAL_READY -> LEASE_OPEN
-> exact stegverse.hil-browser-esrl-lease-open/v1 JSON
-> canonical .github ESRL intake
-> worker/task/COSV reconciliation
```

Expected current page behavior after propagation:

```text
Retry ESRL lease = fallback button
automatic lease attempt begins without tapping it
successful LEASE_OPEN => JSON appears
Copy evidence JSON / Download evidence JSON become enabled
```

iOS Safari can still require a user gesture for dependable file export. The lease-opening path itself must not depend on that gesture.

No site data should be cleared and no replacement G25 claim/fence should be minted.

## Fail-closed evidence semantics

The ESRL successor still requires exact task/request/context/node/claim/fence bindings, exact request hash, journal replay `PASS`, authentic execution-entry digest, exactly one retained checkout, checkout-tail parity, valid canonical checkout receipt hash, `CURRENT_USER_IPHONE`, TV/TVC, and GitHub runtime authority `NONE`.

The `.github` intake cross-checks the exported ESRL artifact against accepted G25 request-consumption evidence and rejects subject mismatch, transformed lineage, or downstream overclaim.

Source availability, CI, merge, service-worker installation, page availability, automatic retry, cache convergence, or deployment do not satisfy `AUTHENTIC_ESRL_HIL_LEASE_OPEN_NOT_YET_OBSERVED`. Only an exact physical component artifact accepted by canonical intake qualifies.

## Prewired post-ESRL continuation

PR `#1353`, merged at `8ce03ba2d7597f844cdf791d0201f2aaf1273a24`, installed the fail-closed read-only post-ESRL readiness classifier `scripts/evaluate_hil_post_esrl_readiness.py` plus `docs/HIL_POST_ESRL_READINESS_MIRROR_HANDOFF.md`. It consumes only accepted ESRL intake evidence and reports the first unsupported downstream stage: receiver READY/custody, post-restart exact-byte proof, TVC lifecycle handoff, or parent runtime-evidence completion. It cannot launch, restart, invoke TVC, mutate WorkerCoordinator/COSV, or promote source/CI into runtime evidence.

Issue `#1354` and `docs/HIL_ESRL_ACCEPTANCE_RECONCILIATION_MIRROR_HANDOFF.md` prewire the canonical bookkeeping bridge immediately after accepted ESRL evidence. `scripts/reconcile_hil_esrl_acceptance.py` requires the current exact task vector `50000000103000`, current three-blocker registry state, and an accepted exact ESRL intake receipt. Only then may it propose:

```text
50000000103000 -> 50000000102000
remove only AUTHENTIC_ESRL_HIL_LEASE_OPEN_NOT_YET_OBSERVED
retain POST_RESTART_EXACT_BYTE_PROOF_NOT_YET_PRESERVED
retain TVC_HIL_LIFECYCLE_HANDOFF_NOT_YET_PROVEN
next runtime stage = HIL_RECEIVER_READY_AND_CUSTODY
```

The proposal is deliberately non-mutating (`mutation_performed=false`). The actual task-vector/registry/COSV mutation remains a separate reviewed reconciliation after authentic intake.

## Subsequent predicates

After authentic ESRL `LEASE_OPEN`, preserve the independent obligations for:

- post-restart exact-byte reconstruction/proof; and
- TVC HIL lifecycle handoff.

Neither may be inferred from ESRL source or `LEASE_OPEN` alone.

## Declared manifold lineage

Machine-readable lineage remains `control/manifold-lineage.d/hil-resident-session-manifold-activation-001.json` and continues to include:

- `SHWP-HIL-SOVEREIGN-RECEIVER-001`
- `COSV-LIVE-PACKET-AUTOMATION-006`
- `SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001`
- `SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001`
- `SHWP-TV-TVC-RESIDENT-PROOF-001`
- `SHWP-DURABLE-RUNTIME-ACTIVATION`
- `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`

Each child keeps independent request identity, claim/fence, evidence, completion predicate, and retry semantics. HIL does not infer terminalization from another lane.

## README maintenance

README state was re-reviewed for the Site stale-navigation repair, post-ESRL readiness classifier, and ESRL acceptance reconciliation helper. These remain internal fail-closed continuation/control helpers and do not change the documented public runtime interface or the existing execution/governance architecture. No README prose change is required for accuracy at this stage.

## Downstream continuation

Downstream verification remains fail-closed and tracked separately by `.github` issue `#1238`. Pertinent destinations remain `StegVerse-Labs/Site`, `GCAT-BCAT-Engine/Publisher`, `StegVerse-Labs/admissibility-wiki`, `StegVerse-002/stegguardian-wiki`, and `StegVerse-Labs/Sit` only if an HIL-specific consumer/role is independently established.

No destination may treat G25 consumption, ESRL source merge, stale-page convergence, Site merge, readiness classification, or a reconciliation proposal as full HIL activation/release.

## Completion boundary

The HIL receiver lane remains `ACTIVE / HANDOFF_READY`, `archive_eligible=false`, broader activation false, and downstream propagation false until authentic evidence discharges all three remaining parent obligations.
