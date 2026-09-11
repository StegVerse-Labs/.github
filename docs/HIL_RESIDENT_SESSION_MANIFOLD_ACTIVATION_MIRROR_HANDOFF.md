# HIL Resident Session Manifold Activation Mirror Handoff

Updated: 2026-09-11
Repository: `StegVerse-Labs/.github`
Primary issue: `#1178`
Atomic ESRL reconciliation issue: `#1458`
Canonical goal task: `SHWP-HIL-SOVEREIGN-RECEIVER-001`
Manifold task: `HIL-RESIDENT-SESSION-MANIFOLD-ACTIVATION-001`
Current task COSV: `50000000102000`

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
- `docs/HIL_ESRL_EXACT_INTAKE_RECONCILIATION_20260911.md`
- `docs/HIL_ESRL_EXACT_BYTE_ACCEPTANCE_MIRROR_HANDOFF.md`
- `StegVerse-Labs/Site/docs/HIL_BROWSER_ESRL_LEASE_OPEN_MIRROR_HANDOFF.md`
- `scripts/intake_hil_browser_esrl_evidence.py`
- `scripts/evaluate_hil_post_esrl_readiness.py`
- `scripts/reconcile_hil_esrl_acceptance.py`
- `scripts/verify_hil_post_restart_reconstruction.py`

## Canonical current state

The parent task remains `ACTIVE / HANDOFF_READY`, non-archivable, with COSV `50000000102000` and exactly two independent evidence obligations:

1. `POST_RESTART_EXACT_BYTE_PROOF_NOT_YET_PRESERVED`
2. `TVC_HIL_LIFECYCLE_HANDOFF_NOT_YET_PROVEN`

`AUTHENTIC_ESRL_HIL_LEASE_OPEN_NOT_YET_OBSERVED` is discharged by the exact accepted current-iPhone ESRL artifact and must not reappear unless that evidence is later invalidated by canonical evidence.

Accepted physical/runtime lineage is:

```text
request = RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002
runtime surface = CURRENT_USER_IPHONE_BROWSER
browser context = ctx_d151139d2db1eeecb6512f5844058246
node = stegnode-web-f24e3bfb7f5343cb37323187a88e51f3
claim = SHWP-SHWP-HIL-SOVEREIGN-RECEIVER-001-G25
fence = 25
request consumption = SATISFIED
journal replay = PASS
ESRL state = LEASE_OPEN
lease = HIL-BROWSER-ESRL-7bafde4a280e847758da157e
exact source SHA256 = a6756c54da15f09cd6a3dbb201375891803f6589fd644db4c545be39ebe41b92
ESRL intake = ACCEPTED
next runtime stage = HIL_RECEIVER_READY_AND_CUSTODY
```

Canonical request-consumption evidence remains `receipts/sovereign-host/hil-resident-execution-request-consumption.latest.json`. Canonical ESRL intake evidence is `receipts/sovereign-host/hil-browser-esrl-evidence-intake.latest.json`. G25 request consumption and ESRL `LEASE_OPEN` are complete; neither implies the remaining post-restart exact-byte proof or TVC lifecycle handoff.

## Exact ESRL acceptance and atomic COSV reconciliation

The exact current-iPhone ESRL `LEASE_OPEN` artifact was preserved byte-for-byte as `evidence/physical/hil-esrl-lease-open-a6756c54da15f09cd6a3dbb201375891803f6589fd644db4c545be39ebe41b92.json`. `.github` PR `#1454` merged the accepted exact artifact at `658f8c710a3af1726565904d372050d6e1948013` after organization-control, deterministic repository-suite, and Heartbeat validation passed.

PR `#1454` intentionally left canonical COSV fail-closed because initial local task-vector/worker-registry mutation exposed aggregate parity requirements. Issue `#1458` owns the coordinated transition across all four canonical projection surfaces:

- `control/task-vectors/SHWP-HIL-SOVEREIGN-RECEIVER-001.json`
- `control/worker-registry.d/hil-sovereign-receiver-001.json`
- `control/task-vector-index.json`
- `control/cosv-global-registry-coverage.json`

The only admissible transition is:

```text
50000000103000 -> 50000000102000
remove only AUTHENTIC_ESRL_HIL_LEASE_OPEN_NOT_YET_OBSERVED
retain POST_RESTART_EXACT_BYTE_PROOF_NOT_YET_PRESERVED
retain TVC_HIL_LIFECYCLE_HANDOFF_NOT_YET_PROVEN
preserve G25 / fence 25 / retained checkout lineage
preserve accepted ESRL exact bytes and accepted intake
next runtime stage = HIL_RECEIVER_READY_AND_CUSTODY
```

The four surfaces now express that transition together on the `#1458` reconciliation branch. This is bookkeeping reconciliation only: `archive_eligible=false`, broader activation remains false, propagation remains false, TV/TVC remains credential authority, and GitHub runtime authority remains `NONE`.

## Completed ESRL source lineage

Site PR `#1159` merged the same-context current-iPhone browser ESRL successor while preserving the admitted v16 service-worker wrapper and existing G25 WorkerCoordinator checkout lineage. `.github` PR `#1248` merged the fail-closed `scripts/intake_hil_browser_esrl_evidence.py` path.

The first authentic ESRL attempt retained the exact G25 context/node/fence but failed closed with `canonical checkout receipt hash required`. Site PR `#1165`, merged at `7a72c94b3e4fc246424975d97729c4f2220fbef0`, repaired historical-envelope compatibility without replacing the checkout, claim, or fence. Site PR `#1169`, merged at `9751d100250c5a3905a363e08c9d9bed47d54ff7`, made the ESRL page automatically continue from retained G25 state and persist only exact same-context `LEASE_OPEN` results.

A later current-iPhone observation exposed stale standalone-Safari page/worker convergence. Site PR `#1173`, merged at `61865d7649fc39669caa39008568764f8b7c45b4`, repaired that path while preserving `stegos-web-bootstrap-v16`, `HIL_BROWSER_EVIDENCE_V16`, retained storage, WorkerCoordinator state, and G25 lineage. Its exact-head validation passed, and Site PR `#1176`, merged at `c1b75e1a7ee095918db727a0da87688c544af5e4`, reconciled the Site ESRL handoff.

The resulting exact physical artifact is now accepted. Public propagation, cache convergence, source merge, or CI were never treated as substitutes for the physical artifact; the ESRL predicate was discharged only when the exact component artifact passed canonical intake.

## Current runtime evidence boundary

The ESRL physical-observation boundary is complete. The current boundary is receiver READY/custody followed by the two still-independent parent predicates.

The continuation order is fail-closed:

```text
accepted exact ESRL LEASE_OPEN
-> HIL_RECEIVER_READY_AND_CUSTODY
-> preserve authentic receiver/custody evidence
-> controlled restart / same-execution reconstruction
-> preserve post-restart exact-byte proof
-> TVC HIL lifecycle handoff
-> parent completion evaluation
```

No source merge, CI result, task-vector edit, or handoff prose may substitute for authentic runtime/custody/restart/TVC evidence.

## Fail-closed evidence semantics

The ESRL lineage remains bound to exact task/request/context/node/claim/fence, request hash, journal replay `PASS`, authentic execution-entry digest, exactly one retained checkout, checkout-tail parity, canonical checkout receipt hash, `CURRENT_USER_IPHONE`, TV/TVC, and GitHub runtime authority `NONE`.

The accepted `.github` intake cross-checks the exact artifact against accepted G25 request-consumption evidence. Subject mismatch, transformed lineage, or downstream overclaim remains inadmissible.

The accepted ESRL artifact proves only the ESRL predicate. It does not prove receiver custody, restart reconstruction, TVC lifecycle handoff, release, propagation, or full HIL activation.

## Post-ESRL continuation

PR `#1353`, merged at `8ce03ba2d7597f844cdf791d0201f2aaf1273a24`, installed the fail-closed read-only classifier `scripts/evaluate_hil_post_esrl_readiness.py` plus `docs/HIL_POST_ESRL_READINESS_MIRROR_HANDOFF.md`. It consumes accepted ESRL intake evidence and identifies the first unsupported downstream stage. It cannot launch, restart, invoke TVC, mutate WorkerCoordinator/COSV, or promote source/CI into runtime evidence.

Issue `#1354` and `scripts/reconcile_hil_esrl_acceptance.py` prewired the exact `50000000103000 -> 50000000102000` proposal. That helper remains deliberately non-mutating. Issue `#1458` is the reviewed canonical realization of that proposal across task-local and aggregate projection surfaces.

The next stage is `HIL_RECEIVER_READY_AND_CUSTODY`. The continuation must reuse the admitted G25/ESRL identity and may not mint replacement evidence merely to obtain a favorable result.

## Remaining predicates

The two independent obligations after accepted ESRL `LEASE_OPEN` are:

- post-restart exact-byte reconstruction/proof; and
- TVC HIL lifecycle handoff.

Neither may be inferred from ESRL `LEASE_OPEN`, receiver source state, repository validation, or the COSV reconciliation.

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

README state was re-reviewed for the exact ESRL acceptance and the atomic COSV reconciliation. These changes reconcile internal evidence/control state and do not change the documented public runtime interface or governance architecture. No README prose change is required for accuracy at this stage.

## Downstream continuation

Downstream verification remains fail-closed and tracked separately by `.github` issue `#1238`. Pertinent destinations remain `StegVerse-Labs/Site`, `GCAT-BCAT-Engine/Publisher`, `StegVerse-Labs/admissibility-wiki`, `StegVerse-002/stegguardian-wiki`, and `StegVerse-Labs/Sit` only if an HIL-specific consumer/role is independently established.

No destination may treat G25 consumption, ESRL acceptance, readiness classification, COSV reconciliation, or repository validation as full HIL activation/release.

## Completion boundary

The HIL receiver lane remains `ACTIVE / HANDOFF_READY`, `archive_eligible=false`, broader activation false, and downstream propagation false until authentic evidence discharges both remaining parent obligations. Current continuation begins at `HIL_RECEIVER_READY_AND_CUSTODY`.
