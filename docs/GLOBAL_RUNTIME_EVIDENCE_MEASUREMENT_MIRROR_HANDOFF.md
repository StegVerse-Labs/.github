# Global Runtime Evidence Measurement Mirror Handoff

Goal Task ID: `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001`
Parent Goal: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
COSV: `50000010100000`
Canonical issue: `StegVerse-Labs/.github#1294`
Status: `ACTIVE / PRE-LOOP INGRESS DEFECTS REPAIRED IN SOURCE / AUTHENTIC RERUN PENDING`

## Purpose

Execute exactly one authentic sovereign-resident measurement-only global runtime profile convergence cycle after the merged failure-boundary and pre-run hardening work.

## Measurement invariants

- Use `scripts/run_global_runtime_node_profile_convergence.py` through the existing Canonical Work/resident bootstrap path.
- Freeze one run ID before execution.
- Preserve exact source/profile/projection hashes and per-profile before/after retained-node/HB/state/transition evidence.
- `measurement_only=true`.
- `same_run_remediation_allowed=false`.
- `automatic_retry_after_first_failure=false`.
- Preserve `PASS_CURRENT_RUN`, `PASS_HISTORICAL_EVIDENCE`, `FAILED_CURRENT_RUN`, and `NOT_REACHED` as distinct meanings.
- Do not use GitHub Actions, hosted containers, or CI output as substitute sovereign-resident evidence.

## First execution attempt — 2026-09-09

The first attempt did not enter the ten-stage convergence loop. No measurement run ID was frozen and no `receipts/sovereign-host/global-runtime-node-profile-convergence.latest.json` was produced. This was correctly treated as a pre-loop execution-start condition rather than assigning a false stage-02/stage-03 failure to all 18 lanes.

## Inspection findings

Source inspection found four concrete ingress defects behind the unconsumed request:

1. `control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py` used a fixed `REQUEST_SPECS` tuple that did not include the global measurement task, so the canonical-work resident consumer could never select it.
2. `scripts/run_canonical_work_event_bootstrap.py` admits only canonical tasks in `PROPOSED` state for the `INGRESS_ADMITTED` transition, while the measurement child had been registered as `ACTIVE`.
3. the Canonical Work consumer's stale-registry recovery required the task to exist in the monolithic `data/canonical-task-registry.json`; the newly registered measurement child was available as a canonical task shard but not in that preserved monolithic registry.
4. `scripts/install_and_run_canonical_work_event_bootstrap.py` launched `run_global_runtime_node_profile_convergence.py` only for `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001`, so a dedicated measurement child could complete Canonical Work ingress without ever starting the intended convergence visitor.

These defects explain why the staged request could remain `REQUESTED` even if the resident dispatcher and generic canonical-work consumer were otherwise functioning.

## Source remediation

Branch: `fix/global-runtime-measurement-ingress-001`

Implemented repairs:

- added explicit request `control/resident-execution-request.d/canonical-work-global-runtime-evidence-measurement-001.json` bound to `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001` and COSV `50000010100000`;
- added `GLOBAL_MEASUREMENT_SPEC` to the generic Canonical Work resident consumer with its own consumption receipt and runtime namespace;
- generalized task identity self-materialization so an exact canonical task shard may be used when a preserved resident monolithic registry is stale, without replacing that preserved registry;
- reconciled the measurement child to canonical `PROPOSED -> INGRESS_ADMITTED` lifecycle semantics while keeping its observation checkout metadata;
- added `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001` to the existing bootstrap wrapper's global-convergence trigger set alongside Runtime Profile Map;
- preserved the existing dispatcher, shared InTr listener, WorkerCoordinator, TV/TVC, HeartBeat, and measurement-only/no-retry/no-repair authority boundaries;
- added deterministic regression coverage in `tests/test_global_runtime_measurement_ingress.py` for request registration, measurement-only flags, stale-registry shard fallback, lifecycle compatibility, and convergence triggering.

No second runtime, scheduler, dispatcher, listener, WorkerCoordinator, or hosted execution path was introduced.

## Rerun contract

After this repair is validated and merged, the authentic sovereign resident should refresh from the already-local canonical source and the existing `canonical_work_coordination` dispatcher consumer should encounter:

`control/resident-execution-request.d/canonical-work-global-runtime-evidence-measurement-001.json`

The consumer should materialize the measurement task identity from its canonical source shard if the resident monolithic registry is stale, perform the ordinary Canonical Work ingress transition, and invoke the existing global node-profile convergence visitor exactly once.

The authoritative measurement artifact remains:

`receipts/sovereign-host/global-runtime-node-profile-convergence.latest.json`

The rerun is successful as a measurement when that artifact contains a frozen run ID plus current-run/historical/not-reached stage observations and before/after node/HB/transition evidence. It is not required that all 18 lanes succeed.

## Current result

`PRE_LOOP_INGRESS_SOURCE_DEFECTS_IDENTIFIED_AND_REPAIRED / AUTHENTIC_RERUN_PENDING`

No hosted substitute execution has been used. No lane has been remediated during a measurement pass.

## README impact

This repair materially changes resident Canonical Work ingress behavior by making a newly registered canonical task shard addressable even when the resident monolithic registry is stale and by giving the dedicated measurement child an explicit bounded convergence trigger. README reconciliation is required before this repair is considered documentation-complete.

## Manual work

None while source validation, README reconciliation, merge, and authentic rerun inspection remain machine-executable.
