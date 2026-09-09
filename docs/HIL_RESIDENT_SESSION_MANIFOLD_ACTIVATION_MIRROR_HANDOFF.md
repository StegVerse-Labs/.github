# HIL Resident Session Manifold Activation Mirror Handoff

Updated: 2026-09-09
Repository: `StegVerse-Labs/.github`
Issue: `#1178`
Canonical goal task: `SHWP-HIL-SOVEREIGN-RECEIVER-001`
Manifold task: `HIL-RESIDENT-SESSION-MANIFOLD-ACTIVATION-001`
Current task COSV: `50000000103000`

## Source of truth

This file is the canonical continuation record for the HIL sovereign receiver lane as visited through the governed resident-session manifold.

Inherited canonical sources:

- `docs/HIL_RESIDENT_SESSION_COHORT_MIRROR_HANDOFF.md`
- `docs/HIL_SOVEREIGN_RECEIVER_ACTIVATION_MIRROR_HANDOFF.md`
- `docs/GOVERNED_MULTILANE_MANIFOLD_ACTIVATION_MIRROR_HANDOFF.md`
- `docs/CROSS_TASK_COORDINATION_MIRROR_HANDOFF.md`
- `docs/HIL_G25_REQUEST_CONSUMPTION_RECONCILIATION_20260909.md`
- `docs/HIL_BROWSER_ESRL_EVIDENCE_INTAKE_MIRROR_HANDOFF.md`
- `scripts/dispatch_resident_execution_requests.py`
- `scripts/run_worker_runtime.py`
- `scripts/intake_hil_browser_esrl_evidence.py`

## Current continuation state

- PR `#1179` is MERGED at `929efd22e7347e339be580fd74fc2da879bb6e59`; HIL resident-session manifold source materialization and deterministic source-refresh parity are complete.
- PR `#1213` is MERGED at `858670d709dc4855b583449e489ba74f5f37e798`; fail-closed exact physical browser-evidence intake is present.
- Site PRs `#1132`, `#1133`, and `#1134` repaired standalone-Safari service-worker/controller generation convergence without clearing browser state or minting a replacement claim/fence.
- Exact current-iPhone standalone-Safari G25 evidence was accepted through the canonical intake in `.github` PR `#1237`, merged at `b23dde76cd1a411afcd8460c847ae37a03c01a31`.
- `PRED-RESIDENT-REQUEST-CONSUMED-HIL-SOVEREIGN-RECEIVER-002` is `SATISFIED` by `receipts/sovereign-host/hil-resident-execution-request-consumption.latest.json`.
- Accepted evidence is bound to `RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002`, runtime surface `CURRENT_USER_IPHONE_BROWSER`, claim `SHWP-SHWP-HIL-SOVEREIGN-RECEIVER-001-G25`, fencing token `25`, and an observed terminal HIL transition. The broader HIL lifecycle remains incomplete.
- PR `#1240` reconciled the canonical worker registry, per-task COSV, aggregate COSV index, and focused regression coverage to the accepted G25 state and MERGED at `6d5be30e71f824fc5cc0fc9ba27e2ecbcdc28c0f`.
- Canonical task COSV is `50000000103000`, consistent with exactly three remaining blockers.
- Site PR `#1159` is MERGED at `72c3620348019996cd6731e3b59b770c734f7477`. It adds the same-context current-iPhone browser ESRL successor while preserving the exact admitted v16 service-worker wrapper and existing G25 WorkerCoordinator checkout lineage. Exact-head Site Bootstrap, persistent-card, Site handoff, and Ecosystem Heartbeat validation all passed before merge.
- `.github` PR `#1248` is MERGED at `f56f1e734e458706119023c8c226e80db46adb70`. It adds `scripts/intake_hil_browser_esrl_evidence.py`, focused standard-library tests, and the ESRL intake handoff. Exact-head organization-control, deterministic repository suite, and Heartbeat validation all passed before merge.
- The first authentic physical ESRL attempt was observed from the same standalone-Safari G25 context. It retained browser context `ctx_d151139d2db1eeecb6512f5844058246`, node `stegnode-web-f24e3bfb7f5343cb37323187a88e51f3`, and fence `G25`, then failed closed with `canonical checkout receipt hash required`; no ESRL artifact was produced or accepted.
- Investigation found a compatibility defect in the Site source envelope rather than lost checkout state: the accepted G25 activation-result envelope omitted `canonical_checkout_receipt_sha256`, and its authentic execution-entry digest is raw 64-hex while the first ESRL successor expected a prefixed digest form.
- Site PR `#1165` is MERGED at `7a72c94b3e4fc246424975d97729c4f2220fbef0`. The repair derives a missing checkout hash only from the exact retained portable WorkerCoordinator receipt after task/claim/fence/checkout-count/tail validation, preserves raw execution-entry digest parity with the canonical `.github` intake, and includes the checkout hash directly in future HIL activation results. It does not clear site data or mint another claim/fence. Exact-head Site Bootstrap, persistent-card, Site handoff, and Ecosystem Heartbeat validation passed, and post-merge Site Bootstrap and persistent-card validation also passed.
- Site PR `#1169` is MERGED at `9751d100250c5a3905a363e08c9d9bed47d54ff7`. The ESRL page now automatically resumes the repaired lease attempt when the exact retained G25 Safari state is present, persists only an exact same-context `LEASE_OPEN` result, rejects stale/mismatched retained ESRL evidence, and keeps a manual retry/export fallback. Exact-head Site Bootstrap, persistent-card, Site handoff, and Ecosystem Heartbeat validation all passed before merge.
- Source capability now exists on both sides of the ESRL evidence boundary, the observed envelope defect has been repaired, and avoidable manual lease initiation has been removed. Runtime observation is still not satisfied because no exact `LEASE_OPEN` artifact has yet been accepted by `.github`.
- `archive_eligible=false`; broader activation and downstream propagation remain false/fail-closed.

## Remaining HIL receiver blockers

Exactly three independent evidence obligations remain:

1. `AUTHENTIC_ESRL_HIL_LEASE_OPEN_NOT_YET_OBSERVED`
2. `POST_RESTART_EXACT_BYTE_PROOF_NOT_YET_PRESERVED`
3. `TVC_HIL_LIFECYCLE_HANDOFF_NOT_YET_PROVEN`

These blockers must be discharged by their own authentic evidence. G25 request consumption, ESRL source merge, physical page reachability, automatic page retry, or a fail-closed ESRL attempt do not imply them.

## Governing objective

Visit the existing HIL resident-session cohort in one bounded manifold execution while preserving each task's independent request identity, claim/fence, evidence, completion predicate, and retry semantics.

```text
one manifold visit
!= one shared claim/fence
!= one shared completion predicate
```

No second runtime, dispatcher, WorkerCoordinator, scheduler, heartbeat, oscillator, credential route, transition plane, or second user-operated machine is introduced by this handoff.

## Declared lineage

Machine-readable lineage:

`control/manifold-lineage.d/hil-resident-session-manifold-activation-001.json`

Declared nodes:

- `SHWP-HIL-SOVEREIGN-RECEIVER-001` — existing resident request consumer selector `hil`.
- `COSV-LIVE-PACKET-AUTOMATION-006` — existing WorkerCoordinator task.
- `SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001` — existing WorkerCoordinator task.
- `SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001` — existing WorkerCoordinator task.
- `SHWP-TV-TVC-RESIDENT-PROOF-001` — existing WorkerCoordinator task.
- `SHWP-DURABLE-RUNTIME-ACTIVATION` — existing resident request consumer selector `g18`; HIL does not depend on G18 terminalization.
- `SHWP-ECOSYSTEM-CHAT-INFERENCE-001` — existing resident request consumer selector `ecosystem_chat`.

## G25 request-consumption disposition

The formerly first actionable HIL predicate:

`PRED-RESIDENT-REQUEST-CONSUMED-HIL-SOVEREIGN-RECEIVER-002`

is no longer pending. It is satisfied by the accepted exact component artifact. The canonical request-consumption receipt is:

`receipts/sovereign-host/hil-resident-execution-request-consumption.latest.json`

The G25 reconciliation details are preserved in:

`docs/HIL_G25_REQUEST_CONSUMPTION_RECONCILIATION_20260909.md`

## Next actionable predicate: authentic ESRL LEASE_OPEN

The same-device source path, current-iPhone successor, fail-closed canonical intake, physical compatibility repair, and automatic same-context continuation are now implemented and merged. The remaining obligation is a successful authentic runtime observation in the same retained Safari context.

Canonical producer/intake path:

```text
same standalone-Safari context holding accepted G25 local-ready state
-> Site /stegos-bootstrap/hil-esrl-activate.html
-> automatic exact-state resume
-> existing portable WorkerCoordinator state / exact retained G25 checkout
-> HIL_BROWSER_ESRL_V1
-> explicit REQUESTED -> ADMITTED -> PROVISIONING -> LOCAL_READY -> LEASE_OPEN
-> exact retained/exported stegverse.hil-browser-esrl-lease-open/v1 JSON
-> scripts/intake_hil_browser_esrl_evidence.py
-> accepted non-authorizing ESRL evidence receipt
-> separate worker/task/COSV reconciliation
```

The repaired Site successor requires the exact G25 task/request/context/node/claim/fence, exact retained checkout receipt, source execution-entry digest, and journal replay `PASS`. For the already-authentic G25 envelope that predates direct checkout-hash export, the missing checkout hash may be recovered only from the exact retained WorkerCoordinator receipt after full lineage validation. A present source hash still must match exactly. No second checkout or replacement claim/fence is permitted.

The page now self-initiates this route when the exact retained source state is present and no valid same-context ESRL result is already stored. A successful exact result is retained under `stegos-hil-esrl-last-success-v1`; stale or mismatched retained evidence is deleted. iOS Safari still requires user interaction for dependable file export, so exact JSON download remains a physical export step after `LEASE_OPEN` is visible.

The `.github` intake cross-checks the exported artifact against the canonical G25 request-consumption receipt and fails closed on subject mismatch or downstream overclaim. Public HTTPS observation remains a distinct downstream interoperability condition and is not a prerequisite for routine same-device lease opening.

Source, CI, merge, page availability, service-worker installation, deployment, automatic retry, or the prior fail-closed physical attempt do not satisfy this predicate. Only an exact physical component artifact accepted by the canonical intake can qualify.

## Subsequent predicates

After authentic ESRL `LEASE_OPEN`, preserve the existing independent evidence obligations for:

- post-restart exact-byte reconstruction/proof; and
- TVC HIL lifecycle handoff.

Neither is inferred from source validation, GitHub Actions, G25 browser evidence, ESRL source availability, ESRL source merge, automatic lease initiation, or ESRL lease opening alone.

## Resident source-refresh parity

The umbrella manifold consumer requires static coordination inputs under:

- `control/manifold-lineage.d/`
- `control/task-vector-index.d/`
- `data/canonical-task-records/`

The canonical local-only WorkerCoordinator source refresh carries these static inputs while excluding mutable runtime state, network credential acquisition, or repository mutation.

## README completeness determination

README was re-reviewed for the Site ESRL successor, checkout-hash compatibility repair, automatic same-context continuation, and `.github` intake. Site retains the exact admitted v16 service-worker wrapper and loads the ESRL successor through the existing HIL portable-state bridge; the accepted `HIL_BROWSER_EVIDENCE_V16` path remains unchanged. `.github` already documents cross-task evidence, WorkerCoordinator, and fail-closed runtime observation semantics. No README prose change is required for either repository at this stage.

## Downstream continuation

Downstream verification remains fail-closed and is tracked separately by `.github` issue `#1238`.

Pertinent destinations are:

- `StegVerse-Labs/Site`
- `GCAT-BCAT-Engine/Publisher`
- `StegVerse-Labs/admissibility-wiki`
- `StegVerse-002/stegguardian-wiki`
- `StegVerse-Labs/Sit` only if an HIL-specific consumer/role is independently established.

No downstream destination may treat G25 request consumption, ESRL source merge, automatic page continuation, or the repaired fail-closed attempt as equivalent to full HIL activation or release.

## Completion boundary

The HIL receiver lane remains ACTIVE / HANDOFF_READY and non-archivable. Completion requires authentic evidence discharging all three remaining blockers. Until then, activation, release, propagation, and archive eligibility remain fail-closed.
