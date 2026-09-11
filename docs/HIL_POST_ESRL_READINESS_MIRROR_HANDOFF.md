# HIL Post-ESRL Readiness Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Parent goal: `SHWP-HIL-SOVEREIGN-RECEIVER-001`
Parent canonical handoff: `docs/HIL_RESIDENT_SESSION_MANIFOLD_ACTIVATION_MIRROR_HANDOFF.md`
Issue: `#1348`
Implementation tracker: `#1350`
Current parent COSV: `50000000103000`

## Purpose

Prewire the already-defined downstream HIL continuation so an accepted physical browser ESRL `LEASE_OPEN` can advance immediately to the first genuinely unresolved downstream evidence stage without rerunning completed G25 request-consumption work.

This handoff does not change the parent blocker count and does not claim runtime success.

## Reused source surfaces

- `scripts/intake_hil_browser_esrl_evidence.py`
- `workers/hil_sovereign_receiver_bridge.py`
- `workers/hil_sovereign_receiver_worker.py`
- `scripts/verify_hil_post_restart_reconstruction.py`
- `scripts/consume_hil_tvc_lifecycle_outbox.py`
- `StegVerse-Labs/TVC/tools/hil_intr_lifecycle_intake.py`

New read-only classifier:

- `scripts/evaluate_hil_post_esrl_readiness.py`
- `tests/test_evaluate_hil_post_esrl_readiness.py`

## Classification contract

The evaluator accepts an ESRL intake receipt only when it is `stegverse.hil-browser-esrl-evidence-intake/v1`, state `ACCEPTED`, task-bound to `SHWP-HIL-SOVEREIGN-RECEIVER-001`, and explicitly records `LEASE_OPEN` observation.

It then reports exactly one first unresolved stage:

```text
ESRL_LEASE_OPEN
HIL_RECEIVER_READY_AND_CUSTODY
POST_RESTART_EXACT_BYTE_PROOF
TVC_HIL_LIFECYCLE_HANDOFF
PARENT_RUNTIME_EVIDENCE_COMPLETE
```

The evaluator reads existing evidence only. It does not launch a receiver, restart a process, invoke TVC, mutate WorkerCoordinator state, change COSV, or infer runtime evidence from source/CI.

## Parent blockers

The parent remains at exactly three independent blockers until direct evidence changes canonical state:

1. `AUTHENTIC_ESRL_HIL_LEASE_OPEN_NOT_YET_OBSERVED`
2. `POST_RESTART_EXACT_BYTE_PROOF_NOT_YET_PRESERVED`
3. `TVC_HIL_LIFECYCLE_HANDOFF_NOT_YET_PROVEN`

An accepted ESRL receipt removes only the first blocker after separate canonical reconciliation. Receiver READY is a required downstream execution condition inside the continuation toward post-restart proof; it is not synthesized as a fourth parent blocker.

## Global-runtime relationship

`GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001` explicitly resumes HIL at `ESRL_LEASE_OPEN` and permits reuse of the HIL G25 browser evidence discipline, browser-origin Universal InTr pattern, and post-terminal downstream continuation pattern. It does not supersede the HIL parent task or authorize cross-task evidence substitution.

## README maintenance

`README.md` was re-reviewed. This change adds a repository-internal read-only readiness classifier and does not alter an externally meaningful runtime interface, authority boundary, credential path, or user-facing contract. No README prose change is required.

## Next execution boundary

The next authentic event is still the exact retained current-iPhone Safari ESRL attempt. If canonical `.github` intake accepts that artifact, run the readiness evaluator against the accepted receipt to determine whether the existing receiver is already directly READY/custody-capable or whether that is the next missing subject-bound observation. Continue only from the reported first unresolved stage.
