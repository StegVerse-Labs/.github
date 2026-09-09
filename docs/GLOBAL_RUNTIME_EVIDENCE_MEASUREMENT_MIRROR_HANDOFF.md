# Global Runtime Evidence Measurement Mirror Handoff

Goal Task ID: `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001`
Parent Goal: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
COSV: `50000010100000`
Canonical issue: `StegVerse-Labs/.github#1294`
Status: `ACTIVE / INGRESS SOURCE REPAIRED AND MERGED / RERUN REACHED SOURCE-DEVICE MATERIALIZATION CONDITION / CURRENT-IPHONE RESIDENT NOT YET OBSERVED`

## Purpose

Execute exactly one authentic current-device/sovereign-resident measurement-only global runtime profile convergence cycle, preserving the frozen run baseline, exact first-failure observations, and before/after retained-node/HB/transition evidence without same-run remediation.

## Measurement invariants

- freeze one run ID before the ten-stage visitor begins;
- preserve exact source/profile/projection hashes;
- preserve before/after retained-node, source/current HB, state and transition commitments;
- `measurement_only=true`;
- `same_run_remediation_allowed=false`;
- `automatic_retry_after_first_failure=false`;
- preserve `PASS_CURRENT_RUN`, `PASS_HISTORICAL_EVIDENCE`, `FAILED_CURRENT_RUN`, and `NOT_REACHED` as distinct meanings;
- do not substitute GitHub Actions, hosted containers, source merge, or unsigned build evidence for authentic source-device runtime evidence.

## Attempt 1 — pre-loop ingress failure

The first measurement attempt never entered the ten-stage convergence loop. No measurement run ID was frozen and no `receipts/sovereign-host/global-runtime-node-profile-convergence.latest.json` was produced.

Inspection found four concrete source defects:

1. the generic Canonical Work resident consumer did not include the global measurement request in its fixed `REQUEST_SPECS` set;
2. the measurement child was `ACTIVE`, while Canonical Work ingress requires the `PROPOSED -> INGRESS_ADMITTED` lifecycle;
3. stale resident monolithic-registry recovery could not resolve a newly registered exact canonical task shard;
4. the Canonical Work bootstrap triggered global node-profile convergence only for Runtime Profile Map, not for the dedicated measurement child.

## Remediation

PR `StegVerse-Labs/.github#1296` repaired all four defects and merged at:

`607cedc2fed1c81cf20ff6250fa3421089284a8a`

The final README-complete source head `971877bbae3225704ab7fb03126f47c8fd86ae1c` passed exact-head deterministic, Heartbeat, organization validation, and resident-oriented validation checks before merge.

Merged behavior now includes:

- explicit request `control/resident-execution-request.d/canonical-work-global-runtime-evidence-measurement-001.json`;
- `GLOBAL_MEASUREMENT_SPEC` in the existing Canonical Work resident consumer;
- exact canonical task-shard fallback when a preserved resident monolithic registry is stale;
- canonical `PROPOSED -> INGRESS_ADMITTED` lifecycle for the measurement child;
- dedicated measurement child invocation of the existing global node-profile convergence visitor;
- deterministic ingress regressions;
- README documentation of shard recovery and measurement-only child behavior.

No second dispatcher, scheduler, listener, WorkerCoordinator, heartbeat, or hosted runtime was introduced.

## Attempt 2 — post-repair rerun

After PR #1296 merged, the authentic evidence surfaces were inspected again.

Observed:

```text
measurement-child source request: MERGED
measurement-child consumer selector: MERGED
stale-registry shard recovery: MERGED
measurement-child convergence trigger: MERGED
measurement consumption receipt: NOT OBSERVED
global convergence receipt: NOT OBSERVED
frozen measurement run ID: NOT OBSERVED
ten-stage visitor entered: NO
```

Therefore the repaired source ingress is no longer the first unresolved condition. None of the 18 lanes may honestly be assigned a stage-01 through stage-10 failure from this rerun.

## Source-device propagation finding

`scripts/refresh_sovereign_worker_runtime_source.py` explicitly refreshes from an **already-local canonical source tree**. It deliberately performs no clone, fetch, pull, network lookup, credential acquisition, or source transport.

`scripts/install_sovereign_worker_source_refresh_service.py` likewise watches an already-local source tree and is currently Linux/systemd-user specific. It cannot cause a remote GitHub merge to become source-device-local code on the current iPhone.

Once canonical source is local, the refresh layer is capable of propagating the repaired request/task-shard/consumer/bootstrap source into runtime. The missing transition occurs before that refresh: authentic source-device resident materialization/source delivery.

## Current-iPhone retained-node truth

`StegVerse-Labs/StegOS#277` remains open for signed StegOSMobile/TestFlight materialization. Current source/build evidence proves the native StegOSMobile retained-node, same-device discovery, HB-lineage and receipt-to-transition implementation exists, but signed current-iPhone installation/runtime evidence is not yet observed.

`StegVerse-Labs/StegOS/docs/STEGBROWSER_RETAINED_NODE_BOOTSTRAP_MIRROR_HANDOFF.md` likewise records:

```text
current-iPhone retained node materialization: NOT OBSERVED
same-node-before/after-session proof: NOT OBSERVED
source-HB-root persistence runtime proof: NOT OBSERVED
authentic receipt-to-transition runtime execution: NOT OBSERVED
```

The current first unresolved condition is therefore:

`PRE_LOOP_AUTHENTIC_SOURCE_DEVICE_RESIDENT_NOT_MATERIALIZED`

This is outside the ten measured runtime stages. It is not evidence that any of the 18 component lanes failed profile resolution, node continuity, request consumption, or a later predicate.

## Architectural implication

The persistent-node/ephemeral-operation architecture strengthens this diagnosis: continuity should live in the profile-derived current-iPhone StegOS node. The Linux/local-source Python worker path can remain an execution substrate where applicable, but it cannot be treated as the authentic source-device continuity carrier for an iPhone-only deployment.

The next physical/runtime evidence must establish the current-iPhone retained node first; subsequent measurement/control operations may then remain bounded and ephemeral through Interlock/InTr.

## Next execution sequence

1. continue the already-canonical StegOS #277 TestFlight/current-iPhone materialization path rather than creating another resident runtime;
2. obtain authentic retained-node materialization and same-device discovery evidence;
3. deliver/materialize the current canonical measurement source through the applicable source-device/StegOS path;
4. rerun exactly one measurement-only convergence pass;
5. require a frozen run ID and `global-runtime-node-profile-convergence.latest.json` before interpreting any 18-lane histogram;
6. remediate measured lane failures only after preserving that first authentic receipt.

## Current result

`INGRESS_SOURCE_REPAIRED_MERGED / AUTHENTIC_RERUN_EXECUTED_AS_OBSERVATION / PRE_LOOP_AUTHENTIC_SOURCE_DEVICE_RESIDENT_NOT_MATERIALIZED`

Evidence note posted to `.github#1294` as comment `5606498215`.

## README impact

README reconciliation for the ingress source repair is merged. This rerun result changes evidence/state, not repository behavior, so no additional README mutation is required for this documentation update.

## Manual work

None for this reconciliation step. Physical TestFlight/current-iPhone materialization remains tracked by the existing StegOS task and should be continued there with its exact prerequisites.
