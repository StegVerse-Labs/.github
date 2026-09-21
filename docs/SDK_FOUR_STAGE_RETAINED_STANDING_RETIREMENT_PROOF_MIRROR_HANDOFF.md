# SDK Four-Stage Retained Standing / Retirement Proof Mirror Handoff

Updated: 2026-09-21
Goal Task ID: `SDK-FOUR-STAGE-RETAINED-STANDING-RETIREMENT-PROOF-001`
Parent Goal Task ID: `SDK-FOUR-STAGE-EVIDENCE-REMEDIATION-001`
COSV ID: `71000000111111`
Status: ACTIVE / HANDOFF_READY

## Proven predecessor

Option-A evidence remediation is complete on SDK PR #304.

- exact validated head: `0bc31804750c224257409e2774fe918e3c797c10`
- exact validated tree: `f42bb1017aa6f7bb185ba410d8ddca369524b77a`
- merged main: `e1116e9cb5f5043c9198505d64560b710c517e88`
- merged tree: `f42bb1017aa6f7bb185ba410d8ddca369524b77a`
- tree equality: PASS
- exact-head four-stage validation run: `35648276053`
- retained artifact: `10661081336`
- artifact SHA-256: `82fd8e824fe5fb175ae17fc57ea34a729996dd37b02878b11969f10abcd93ba5`
- all 13 triggered SDK exact-head workflows: PASS

The predecessor proved a falsifiable local-semantic measurement contract, genuine disjoint partition/reconstruction, recomputed group commitment, local-semantic/governed-runtime boundary enforcement, and Test-2/Test-3 differential invariance. It deliberately did not claim authentic prior standing or retirement.

## Goal

Close the remaining Richard-scenario evidence distinction with retained runtime evidence rather than derivation.

The proof must reuse existing StegVerse authority planes:

```text
SDK manifested request
  -> WorkerCoordinator authentic claim/fence
  -> TV/TVC warrant
  -> Interlock/InTr admission
  -> retained ACTIVATE/standing receipt in canonical Master Records
  -> invocation admitted only because retained standing exists
  -> task completion
  -> CLOSE/RETIRE retained in canonical Master Records
  -> post-close invocation using stale fence
  -> DENY
  -> denial retained + reconstructable in canonical Master Records
```

## Standing predicate

A manifest-supplied claim/fence is not standing proof.

Before any invocation may count:

1. an authentic external WorkerCoordinator claim/fence must exist;
2. `WORKERCOORDINATOR_CLAIM_FENCE_BOUND` must be `RECORDED` in canonical Master Records;
3. reconstruction must be `PASS`;
4. required-evidence validation must be `PASS`;
5. receipt SHA-256 must exactly equal reconstructed receipt SHA-256;
6. the activation/standing custody record must predate and be a required input to invocation admission.

## Retirement predicate

Retirement is not established by a literal `worker_live_after_close=false`.

After retained close/retire:

1. submit one invocation against the retired worker using the now-stale fence;
2. Interlock/InTr must deny it because current retained standing no longer admits invocation;
3. the denial must be retained in canonical Master Records;
4. denial reconstruction and required-evidence validation must both PASS;
5. exact receipt/reconstruction digest equality is required.

This authentic refusal is the retirement observation.

## HB chronology

HB stamping may bind `hb_epoch_at_recording`, `hb_generation_at_recording`, receipt SHA-256, transition ID, and transition sequence to Master Records receipts where the existing receipt schema supports it.

HB remains strictly non-authorizing. Admission depends on retained standing/custody plus governing transition policy, never on the HB value.

## No-new-plane constraint

Do not add another runtime, scheduler, dispatcher, WorkerCoordinator, credential source, Interlock/InTr substitute, Master Records substitute, custody store, endpoint, or device dependency.

Trace and repair only the first concrete defect in the already-existing SDK -> WorkerCoordinator -> TV/TVC -> Interlock/InTr -> Master Records path.

## Completion

Do not close from source tests or GitHub Actions alone. Completion requires authentic runtime evidence for both prior standing and post-retirement refusal, each with canonical Master Records RECORDED + reconstruction PASS + required-evidence PASS + exact digest equality.

## Generation fence

This successor was derived after Option-A merge and canonical generation 178. Registration advances the proposed coordination branch to generation 179.
