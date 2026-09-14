# StegBrowser Runtime Materialization Remediation Mirror Handoff

Updated: 2026-09-14

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- Parent/remediates: `STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001`
- Parent issue: `StegVerse-Labs/.github#1860`
- Issue: `StegVerse-Labs/.github#1866`
- COSV: `40000100100000`
- Canonical task record: `data/canonical-task-records/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json`
- Evidence predicates: `data/runtime-materialization-remediation/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.predicates.json`
- Status: `ACTIVE / CHECKED_OUT`
- External/second user-operated device required: `false`

## Why this exists

`STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001` classified the current available evidence as `RESIDENT_CUSTODY_ROOT_NOT_OBSERVED` and bound the next exact defect:

```text
RESIDENT_CUSTODY_ROOT_NOT_OBSERVED_FOR_RT_STEGBROWSER_RUNTIME_CONSUMPTION_001
```

The current defect is not source readiness for the StegBrowser runtime-consumption task. The defect is that the existing authorized resident carrier does not yet expose an authentic resident-root observation surface that can be used by `scripts/check_stegbrowser_runtime_consumption_receipts.py`.

## Current inherited evidence

- `.github#1860` remains active and open.
- `.github#1864` merged the resident-root classification at exact head `1752803cdef0cc7f47d6b47843aac96e441dc421` as merge commit `e95af1cf5c2449480cdc1b4eba7003c3ba2d39f3`.
- Current classification: `RESIDENT_CUSTODY_ROOT_NOT_OBSERVED`.
- Required retained receipt after a root exists:

```text
<resident-root>/receipts/sovereign-host/canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json
```

- Healer `data/reusable_task_schedule.json` keeps `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` enabled hourly through the existing neutral reusable-task scheduler carrier.
- Healer `app/reusable_task_scheduler.py` already has a bounded root discovery surface: explicit `STEGVERSE_HEARTBEAT_ROOT` first, then canonical local runtime candidates, and boundary results when no materialized root exists.
- `.github/scripts/check_stegbrowser_runtime_consumption_receipts.py` is non-authorizing and requires an explicit `--runtime-root`; it must not be run against a synthetic checkout.

## First unresolved predicate

```text
RESIDENT_RUNTIME_ROOT_OBSERVATION_SURFACE_MATERIALIZED_FOR_RT_STEGBROWSER_RUNTIME_CONSUMPTION_001
```

## Remediation objective

Cause the existing Healer resident scheduler carrier and neutral `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` path to materialize or expose an observable resident-root evidence surface when the authorized resident environment exists. This task may add only deterministic source-side contracts, predicates, dry-run validation, and handoff bindings. It must not mint runtime proof.

## Required materialization surface

The materialization surface must make these facts observable without relying on GitHub as runtime authority:

1. Whether a current resident root was obtained from `STEGVERSE_HEARTBEAT_ROOT` or canonical local runtime discovery.
2. Which exact resident-root candidate path was accepted or why no candidate was accepted.
3. Whether the required retained StegBrowser receipt path exists under that root.
4. Whether the existing non-authorizing classifier can run against that root.
5. If no root exists, the exact boundary reason that must be remediated by the authorized resident carrier.

## Required evidence predicates

See `data/runtime-materialization-remediation/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.predicates.json`.

Minimum predicates:

```text
HEALER_NEUTRAL_RT_STEGBROWSER_ROUTE_REUSED
NO_SECOND_SCHEDULER_OR_DISPATCHER_ADDED
NO_GITHUB_RUNTIME_AUTHORITY_ADDED
NO_SECOND_USER_OPERATED_DEVICE_REQUIRED
RESIDENT_ROOT_OBSERVATION_SURFACE_DEFINED
NON_AUTHORIZING_DRY_RUN_VALIDATION_DEFINED
CLASSIFIER_RUN_REMAINS_GATED_BY_AUTHENTIC_RUNTIME_ROOT
RETURN_PATH_TO_PARENT_RECEIPT_CLASSIFICATION_DEFINED
```

## Dry-run / non-authorizing validation

Dry-run validation may prove only that the repository contains a deterministic remediation contract and that it does not introduce a second scheduler, dispatcher, credential path, GitHub authority path, runtime plane, MIR-specific transport, or second user-operated device. Dry-run validation may not claim:

- resident runtime consumption,
- `RESIDENT_CUSTODY_ROOT_AUTHENTICALLY_OBSERVED_FOR_STEGBROWSER`,
- WorkerCoordinator claim/fence,
- Interlock/InTr admission,
- TVC source promotion,
- owner ingress readiness,
- Master Records custody/reconstruction.

## Allowed next transitions

```text
DEFINE_ROOT_OBSERVATION_SURFACE
VALIDATE_NON_AUTHORIZING_MATERIALIZATION_CONTRACT
RETURN_TO_RESIDENT_CUSTODY_ROOT_OBSERVATION
```

## Prohibited transitions

```text
ADD_SECOND_SCHEDULER
ADD_SECOND_DISPATCHER
ADD_CREDENTIAL_ROUTE
ADD_GITHUB_RUNTIME_AUTHORITY
ADD_RUNTIME_PLANE
ADD_MIR_SPECIFIC_TRANSPORT
REQUIRE_SECOND_USER_OPERATED_DEVICE
CLAIM_RUNTIME_COMPLETION_FROM_SOURCE_STATE
```

## Return path

When an authentic resident root is observable, return to `STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001` / `.github#1860` and run `scripts/check_stegbrowser_runtime_consumption_receipts.py` against that root only as a non-authorizing classifier. If the retained receipts are valid/bindable, continue through the parent completion chain: WorkerCoordinator claim/fence, Interlock/InTr admission, TVC source promotion, pinned TVC materialization/restart, immutable observer execution, owner ingress readiness, and Master Records custody/reconstruction.

## Current state

`ACTIVE / CHECKED_OUT / SUCCESSOR_OF_STEGBROWSER_RESIDENT_CUSTODY_ROOT_OBSERVATION / RESIDENT_ROOT_OBSERVATION_SURFACE_NOT_YET_MATERIALIZED / RUNTIME_CONSUMPTION_NOT_CLAIMED / REMOTE_DEVICE_NOT_REQUIRED / NO_SECOND_USER_OPERATED_DEVICE`

## Manual work

None.
