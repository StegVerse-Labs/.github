# HIL Browser ESRL Evidence Intake Mirror Handoff

Updated: 2026-09-09
Repository: `StegVerse-Labs/.github`
Issue: `#1247`
Parent goal: `SHWP-HIL-SOVEREIGN-RECEIVER-001`
Parent handoff: `docs/HIL_RESIDENT_SESSION_MANIFOLD_ACTIVATION_MIRROR_HANDOFF.md`
Current parent COSV: `50000000103000`
Site source: `StegVerse-Labs/Site#1156` / PR `#1159`

## Purpose

Provide the canonical fail-closed intake for exact physical `stegverse.hil-browser-esrl-lease-open/v1` artifacts emitted by the same-context current-iPhone browser ESRL successor.

This source does not itself prove ESRL runtime execution and does not alter the parent blocker count.

## Intake contract

`scripts/intake_hil_browser_esrl_evidence.py` requires the exact exported artifact and cross-checks it against the already-canonical G25 request-consumption receipt:

`receipts/sovereign-host/hil-resident-execution-request-consumption.latest.json`

Required parity includes:

- canonical task and resident request ID/SHA256;
- accepted browser context and node identity;
- canonical G25 claim/fence;
- source execution-entry hash and journal replay PASS;
- `HIL_BROWSER_EVIDENCE_V16` source protocol;
- `HIL_BROWSER_ESRL_V1` lease protocol;
- deterministic lease ID / binding-hash relationship;
- explicit ESRL state progression `REQUESTED -> ADMITTED -> PROVISIONING -> LOCAL_READY -> LEASE_OPEN`;
- runtime materialization and local identity verification;
- same-device current-iPhone execution;
- public HTTPS observation remaining downstream optional;
- TV/TVC credential authority and GitHub runtime authority `NONE`.

The intake rejects any artifact that also claims custody, post-restart exact-byte proof, TVC lifecycle receipt, broader HIL completion, a second claim, or request-consumption authority.

## Output

A valid physical artifact may produce a non-authorizing intake receipt:

`stegverse.hil-browser-esrl-evidence-intake/v1`

with `state=ACCEPTED` and `esrl_lease_open_observed=true`. The exact source artifact SHA256 is preserved.

Acceptance by this script is evidence intake only. Parent worker/task/COSV state must be reconciled in a separate canonical change after an authentic artifact actually exists.

## Tests

`tests/test_hil_browser_esrl_evidence_intake.py` covers valid exact subject binding, context mismatch rejection, downstream-claim rejection, and exact source artifact hashing.

## README maintenance

`README.md` was reviewed. The repository already documents cross-task evidence, fail-closed runtime observation, WorkerCoordinator, and canonical handoff semantics; adding this task-specific intake script does not make the repository interface description inaccurate. No README prose change is required for this source-only intake.

## Completion boundary

Source completion requires merge and deterministic validation. Runtime completion still requires a same-context physical current-iPhone artifact from the Site successor, followed by this intake and a separate canonical worker/task/COSV reconciliation.

Until then the parent remains at exactly three blockers:

1. `AUTHENTIC_ESRL_HIL_LEASE_OPEN_NOT_YET_OBSERVED`
2. `POST_RESTART_EXACT_BYTE_PROOF_NOT_YET_PRESERVED`
3. `TVC_HIL_LIFECYCLE_HANDOFF_NOT_YET_PROVEN`
