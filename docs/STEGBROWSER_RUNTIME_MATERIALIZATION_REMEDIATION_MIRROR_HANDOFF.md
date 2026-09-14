# StegBrowser Runtime Materialization Remediation Mirror Handoff

Updated: 2026-09-14

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- Parent/remediates: `STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001`
- Shared runtime-evidence owner: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
- Issue: `StegVerse-Labs/.github#1866`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / HEALER ROOT-BOOTSTRAP CIRCULARITY SOURCE-REPAIRED / AUTHENTIC POST-REPAIR CARRIER OBSERVATION PENDING`
- External/second user-operated device required: `false`

## Ownership reconciliation

This task remains a subject-bound lane child of `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`; it is not a second runtime-materialization owner. It may not create another scheduler, dispatcher, WorkerCoordinator, InTr implementation, credential route, GitHub runtime-authority path, runtime plane, MIR-specific transport, or second-device requirement.

## Proven underlying defect and repair

The earlier runtime classification was:

```text
RESIDENT_CUSTODY_ROOT_NOT_OBSERVED_FOR_RT_STEGBROWSER_RUNTIME_CONSUMPTION_001
```

Investigation found a concrete source circularity in the existing Healer carrier. Before the latest repair, `app/reusable_task_scheduler.py` required a valid resident root before invoking the neutral reusable scheduler, but that neutral scheduler also carries `RT-SOVEREIGN-SOURCE-REFRESH-001`, whose existing local-only implementation can create/populate the canonical resident runtime path.

```text
no valid resident root
-> neutral scheduler refused delegation
-> existing RT-SOVEREIGN-SOURCE-REFRESH-001 could not run
-> resident root could not become valid
```

StegVerse-Healer PR `#82` repairs that circularity without adding an authority surface. It merged as:

```text
2415e0bdf83bcd5ff116a388cf4c570874593e6b
```

Exact-head Test Readiness run:

```text
34884261376 = success
```

The repaired carrier now:

1. uses an already-valid resident root unchanged when one exists;
2. permits a canonical local resident-root path to be used as a non-authorizing materialization target only when the existing schedule enables `RT-SOVEREIGN-SOURCE-REFRESH-001`;
3. delegates to the same neutral reusable scheduler and existing local-only source-refresh implementation;
4. re-runs resident-root discovery after delegation;
5. remains `BLOCKED` unless authentic resident markers are present;
6. preserves the original missing-root boundary for schedules without source refresh;
7. never treats a source checkout or CI result as resident runtime proof.

## Current runtime evidence

The source repair is merged and validated, but no authentic post-`#82` Healer resident carrier packet has yet been observed in this session. Therefore:

```text
RESIDENT_CUSTODY_ROOT_AUTHENTICALLY_OBSERVED_FOR_STEGBROWSER = false
POST_REPAIR_HEALER_CARRIER_PACKET_OBSERVED_FOR_RT_STEGBROWSER_RUNTIME_CONSUMPTION_001 = false
CANONICAL_WORK_RESIDENT_CONSUMPTION_OBSERVED = false
```

No WorkerCoordinator claim/fence, Interlock/InTr admission, TVC source promotion, owner ingress readiness, Master Records reconstruction, or StegAgents targeted-consumption proof is promoted from this source repair.

## First unresolved predicate

```text
POST_REPAIR_HEALER_CARRIER_PACKET_OBSERVED_FOR_RT_STEGBROWSER_RUNTIME_CONSUMPTION_001
```

## Required authentic next observation

Observe the next authentic existing Healer resident scheduler cycle after merge `2415e0bdf83bcd5ff116a388cf4c570874593e6b` and require its retained `resident_custody_root_observation` packet.

If packet state is `RESIDENT_CUSTODY_ROOT_OBSERVED`, retain:

- exact resident root identity/path;
- `resident_runtime_root_source`;
- matched resident marker paths;
- the retained Healer carrier receipt identity/hash;
- evidence that the path is resident runtime state rather than a repository checkout.

Then run the existing non-authorizing classifier against that exact root and check:

```text
<resident-root>/receipts/sovereign-host/canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json
<resident-root>/receipts/sovereign-host/stegagents-governed-runtime-targeted-request-consumption.latest.json
```

If the StegAgents targeted receipt is absent but the root is authentic, hand that exact root immediately to `STEGAGENTS-GOVERNED-RUNTIME-001` for the already-merged `stegagents_governed_runtime_targeted` selector.

If packet state remains NOT_OBSERVED, INVALID, or AMBIGUOUS, bind the exact post-delegation reason to this same lane and shared runtime-evidence owner; do not create another runtime task.

## Authority invariants

- Task Registry: coordination only.
- Healer carrier / neutral reusable scheduler: scheduling and invocation transport only.
- `RT-SOVEREIGN-SOURCE-REFRESH-001`: already-local static source materialization only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed transition authority.
- TV/TVC: credential/provider authority.
- Master Records: observed-reality/reconstruction authority.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.
- no second user-operated device is required or authorized.

## Current state

`ACTIVE / CHECKED_OUT / HEALER_ROOT_BOOTSTRAP_CIRCULARITY_SOURCE_REPAIR_MERGED / POST_REPAIR_CARRIER_PACKET_PENDING / RESIDENT_ROOT_NOT_AUTHENTICALLY_OBSERVED / RUNTIME_CONSUMPTION_NOT_CLAIMED / NO_SECOND_USER_OPERATED_DEVICE`

## README impact

The Healer README was updated in PR #82 because runtime-carrier behavior materially changed. The `.github` root README requires no change because this reconciliation changes no `.github` authority or runtime capability.

## Manual work

None.
