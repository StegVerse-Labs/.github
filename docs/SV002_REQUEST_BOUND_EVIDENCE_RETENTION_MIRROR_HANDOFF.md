# SV002 REQUEST_BOUND Evidence Retention Mirror Handoff

Goal Task ID: `SV002-REQUEST-BOUND-EVIDENCE-RETENTION-001`
Parent Goal Task ID: `STEGVERSE-002-EXPERIMENT-RERUN-001`
Root experiment: `STEGVERSE-002-SELF-CHARACTERIZATION-001`
COSV: `50000000107000`
Status: `IN_PROGRESS / SOURCE REPAIR MERGED / AUTHENTIC RESIDENT EVIDENCE PENDING`

## Bounded goal

Close only the isolated first-receipt evidence-loss seam for the frozen v0.3 rerun. Determine from authentic existing resident outputs whether the canonical callable was never invoked or whether it wrote `RERUN_REQUEST_BOUND.json` and then failed later, without adding another request, runtime, scheduler, dispatcher, listener, bridge, Site path, device prerequisite, workflow runtime, or authority plane.

## Parent evidence tail

Direct Master Records review established that the parent rerun has not entered Master Records. The first unproven runtime transition is `REQUEST_BOUND`.

The current resident callable writes:

```text
~/.stegverse/self-characterization-001/RERUN_REQUEST_BOUND.json
~/.stegverse/self-characterization-001/RERUN_REQUEST_SUBMISSION.json
```

and the existing resident executor writes:

```text
resident-runtime/state/resident-executor.latest.json
```

## Isolated defect and repair

Source review found an evidence-loss defect inside the existing callable/executor path:

1. `invoke_sv002_experiment_rerun.py` writes `RERUN_REQUEST_BOUND.json` before federation submission.
2. If federation publication then fails, the prior exception result reported `request_bound_claimed=false` regardless of the already-written bound receipt.
3. `resident_executor.py` then raised on the nonzero child return code and discarded the structured child result before writing its existing heartbeat.

This made “callable invoked + request bound + later publication failure” indistinguishable in the executor heartbeat from a pre-binding failure.

StegVerse-002/.github PR #39 repairs only that evidence loss and merged at:

`3a0033742b1ff311bde6c210681ab47df6b734cd`

The repair preserves validated Goal/COSV/experiment/operation/invocation_count/packet/frame identity in the existing blocked callable result and existing resident executor heartbeat. No new evidence path or execution path is created.

## Runtime nonclaim

The merged source repair does not prove a resident process executed after the repair.

```text
authentic resident executor heartbeat after repair: NOT OBSERVED
authentic RERUN_REQUEST_BOUND.json bytes after repair: NOT OBSERVED
REQUEST_BOUND parent predicate: NOT PROMOTED
downstream parent rerun predicates: NOT ADVANCED
```

## Decision rule

When authentic resident evidence becomes available:

- `sv002_callable_attempted=false` or no callable attempt evidence -> classify invocation-side failure;
- `sv002_callable_attempted=true` plus validated `request_bound_claimed=true` / `sv002_request_bound_observed=true` -> classify binding as successful and failure downstream of REQUEST_BOUND;
- malformed or mismatched Goal/COSV/experiment/operation/invocation_count/packet/frame -> fail closed at the mismatch;
- no authentic resident heartbeat -> outcome remains unresolved.

Only exact authentic bytes may promote the parent `REQUEST_BOUND` predicate.

## Authority

WorkerCoordinator remains execution claim/fence authority. Interlock/InTr remains transition authority. TV/TVC remains credential authority. Master Records remains observed-reality/custody/reconstruction authority. GitHub/CI/source grants no runtime authority.

## Manual work

None.
