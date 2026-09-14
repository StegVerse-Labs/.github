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

A source-only Healer repair has also been merged through `StegVerse-Labs/StegVerse-Healer#81` as `b7d37a91fa464a716a85c0a8a28cffd6e5022fb6`, validated by Test Readiness run `34880822258`. That repair is not runtime proof. It provides a non-authorizing resident-custody-root observation packet surface that must now be observed after the authorized resident carrier runs.

## Current inherited evidence

- `.github#1860` remains active and open.
- `.github#1864` merged the resident-root classification at exact head `1752803cdef0cc7f47d6b47843aac96e441dc421` as merge commit `e95af1cf5c2449480cdc1b4eba7003c3ba2d39f3`.
- Current classification: `RESIDENT_CUSTODY_ROOT_NOT_OBSERVED`.
- Healer source repair: `StegVerse-Labs/StegVerse-Healer#81`, exact head `44f69f236f90bc000446ad15cc082cef244f5284`, merge `b7d37a91fa464a716a85c0a8a28cffd6e5022fb6`, Test Readiness `34880822258`, source-only.
- Required retained receipt after a root exists:

```text
<resident-root>/receipts/sovereign-host/canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json
```

- Healer `data/reusable_task_schedule.json` keeps `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` enabled hourly through the existing neutral reusable-task scheduler carrier.
- Healer `app/reusable_task_scheduler.py` has a bounded root discovery surface: explicit `STEGVERSE_HEARTBEAT_ROOT` first, then canonical local runtime candidates, and boundary results when no materialized root exists.
- `.github/scripts/check_stegbrowser_runtime_consumption_receipts.py` is non-authorizing and requires an explicit `--runtime-root`; it must not be run against a synthetic checkout.

## First unresolved predicate

```text
POST_REPAIR_HEALER_CARRIER_PACKET_OBSERVED_FOR_RT_STEGBROWSER_RUNTIME_CONSUMPTION_001
```

## Remediation objective

Use the existing Healer resident scheduler carrier and neutral `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` path to expose the post-repair resident-custody-root observation packet. This task may add only deterministic source-side contracts, predicates, dry-run validation, and handoff bindings. It must not mint runtime proof.

## Required materialization surface

The post-repair packet must make these facts observable without relying on GitHub as runtime authority:

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
HEALER_RESIDENT_ROOT_OBSERVATION_PACKET_SOURCE_REPAIR_MERGED
NO_SECOND_SCHEDULER_OR_DISPATCHER_ADDED
NO_GITHUB_RUNTIME_AUTHORITY_ADDED
NO_SECOND_USER_OPERATED_DEVICE_REQUIRED
RESIDENT_ROOT_OBSERVATION_SURFACE_DEFINED
POST_REPAIR_PACKET_OBSERVATION_REQUIRED
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
OBSERVE_POST_REPAIR_HEALER_CARRIER_PACKET
CLASSIFY_RECEIPT_REACHABILITY_IF_ROOT_OBSERVED
BIND_NEXT_RUNTIME_DEFECT_IF_PACKET_STILL_BOUNDARY
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

When the post-repair packet observes an authentic resident root, return to `STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001` / `.github#1860` and run `scripts/check_stegbrowser_runtime_consumption_receipts.py` against that root only as a non-authorizing classifier. If the retained receipts are valid/bindable, continue through the parent completion chain: WorkerCoordinator claim/fence, Interlock/InTr admission, TVC source promotion, pinned TVC materialization/restart, immutable observer execution, owner ingress readiness, and Master Records custody/reconstruction.

## Current state

`ACTIVE / CHECKED_OUT / SUCCESSOR_OF_STEGBROWSER_RESIDENT_CUSTODY_ROOT_OBSERVATION / HEALER_PACKET_SOURCE_REPAIR_RESOLVED_SOURCE_ONLY / POST_REPAIR_PACKET_OBSERVATION_PENDING / RESIDENT_ROOT_OBSERVATION_SURFACE_NOT_YET_RUNTIME_OBSERVED / RUNTIME_CONSUMPTION_NOT_CLAIMED / REMOTE_DEVICE_NOT_REQUIRED / NO_SECOND_USER_OPERATED_DEVICE`

## Manual work

None.
