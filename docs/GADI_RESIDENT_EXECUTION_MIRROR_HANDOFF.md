# GADI Resident Execution Mirror Handoff

Updated: 2026-09-11
Repository: `StegVerse-Labs/.github`
Goal ID: `GADI-001`
Task ID: `GADI-RESIDENT-EXECUTION-001`
Parent task: `GADI-001`
Umbrella goal: `GOVERNED-MULTILANE-MANIFOLD-ACTIVATION-001`
COSV ID: `10100000100000`
Canonical issue: `StegVerse-Labs/.github#1239`
Status: `ACTIVE / NONCLAIM_READINESS_MERGED / RUNTIME_SUBJECT_BINDING_MERGED / NATIVE_PLAN_MATERIALIZER_MERGED / LOCAL_GOVERNANCE_INTR_ADMISSION_MATERIALIZER_MERGED / NATIVE_COMMAND_ARTIFACT_BRIDGE_MERGED / AUTHENTIC_RESIDENT_EXECUTION_PENDING`

## Current canonical state

`GADI-001` remains ACTIVE / CLAIMED_INTEGRATION and is not superseded.

The source/runtime-adapter chain now contains, without introducing parallel authority planes:

- canonical runtime evidence source resolution/materialization/preflight/consumption;
- current subject-bound GADI runtime-binding observation;
- native StegOS boundary planning and exact current-plan materialization from local evidence;
- Governance-owned GADI connector profile;
- StegCore local InTr + Governance admission materialization and decision -> GADI Admission projection;
- exact native-command artifact bridge from plan + ADMITTED request + current runtime binding;
- controlled StegOS actuator-output receipt seam;
- WorkerCoordinator claim/fence normalization and targeted worker bridge;
- non-claim readiness gating and stale-consumption replay protection.

Authentic current runtime execution remains unobserved. Source, CI, profile declarations, simulation evidence, and merged adapters do not satisfy runtime predicates.

## Relevant merged trajectory

- `.github` PR #1388 -> `261b1636db05baa3d34072236557618e9607b5e7`: targeted WorkerCoordinator registration repair.
- `.github` PR #1395 -> `b1b613452406b26d8fe17a9fbb98b57054a4f046`: post-claim ProcessWorkerAdapter/GADI dispatcher bridge.
- `.github` PR #1405 -> `1fe63d76ffd2d499daaeab9a942af5dfef50b4d9`: non-claim readiness convergence and stale-consumption replay protection.
- `Governance` PR #40 -> `2765854132872078bcd15a4432a65095831b432e`: authoritative `gadi.defensive-intervention.v1` profile.
- `StegCore` PR #202 -> `282f30e9e46efc3a8d0d867f48e08c3aa6534e22`: exact Governance-decision -> GADI Admission projector.
- `.github` PR #1413 -> `71338d71c7122e7be9d4a1015e2bde353a3ff0e6`: current runtime-root/node subject binding and readiness enforcement.
- `StegOS` PR #337 -> `0409aadbc894c9d0976e41a946b588ef93c34b8d`: native command artifact bridge.
- `StegOS` PR #342 -> `918bc7d78f47bc775736ce85e5026f9fead03555`: native plan materializer plus canonical `REDIRECT_TO_SAFE_STATE` -> `QUARANTINE_INTERACTION` vocabulary repair. Final exact head `84f86b5db9b97846dc5d804b4600e0c0aa01d93e` passed all six observed StegOS/GADI validation lanes before merge.
- `StegCore` PR #204 -> `44f4240c72ae1e64cefd829e469e64a40b5034a3`: local GADI InTr/Governance admission materializer. Repaired exact head `661a1e9736db4262c91c8246068ed6061217eae8` passed both observed task-specific workflow instances before merge.

## Canonical execution chain

```text
CURRENT RESIDENT-PRESENCE SUBJECT BINDING
-> CURRENT BOUNDARY INTERACTION OBSERVATION
-> CURRENT PRE-ADMISSION NATIVE DEFENSE PLAN
-> CURRENT PENDING INTERVENTION REQUEST + RESOLVED GOVERNANCE FACTS
-> LOCAL CANONICAL INTR TRANSPORT + GOVERNANCE EVALUATION
-> CURRENT ADMITTED GADI REQUEST
-> NATIVE STEGOS COMMAND BOUND TO EXACT RUNTIME SUBJECT
-> CONTROLLED PREAUTHORIZED OUTPUT OBSERVATION
-> NON-CLAIM READINESS
-> TARGETED WORKERCOORDINATOR CLAIM/FENCE
-> SOURCE RESOLUTION WITH CLAIM DEFERRED
-> FRESH CLAIM PROJECTION
-> MATERIALIZATION
-> PREFLIGHT
-> RESIDENT CONSUMPTION
-> REASSESSMENT / TERMINATION
-> CONTINUITY / MASTER RECORDS RECONSTRUCTION
```

WorkerCoordinator remains sole claim/fence authority. HB/runtime-presence remains observation only. TV/TVC remains credential authority. Governance/InTr remains transition/admission authority. GitHub validation does not become runtime authority.

## Native plan materializer — merged

StegOS PR #342 adds `stegos/gadi_native_plan_materializer.py` and closes the missing production-caller seam for `build_native_defense_plan()`.

It consumes only already-local current boundary-interaction evidence plus exact local TVC registry and TV support evidence. It performs no network fetch and creates no admission, runtime binding, claim/fence, lease, credential, or execution authority.

The runtime interaction schema is:

```text
stegos.gadi-external-ai-interaction.v1
```

and requires explicit current `observed_at`/`expires_at`, strict observation booleans, exact GADI task/COSV identity, and `authority_effect=NONE_OBSERVATION_ONLY`.

The materializer reuses the existing `discover_capability()` implementation. The authoritative controlled-simulation capability remains:

```text
capability_id = gadi.sim.safe-state.redirect.v1
action = REDIRECT_TO_SAFE_STATE
target_class = CONTROLLED_SIMULATION
control_surface = sim://gadi/safe-state
```

The planner vocabulary now correctly maps `REDIRECT_TO_SAFE_STATE` into the existing native `QUARANTINE_INTERACTION` defensive ability. This is vocabulary compatibility only, not new authority.

CLI materialization hashes the exact local interaction/TVC/TV source bytes and explicitly records `NONE_PRE_ADMISSION_PLAN_ONLY`.

## Local Governance / InTr admission materializer — merged

StegCore PR #204 adds `scripts/materialize_gadi_local_admission.py`.

It accepts only:

1. an already-built canonical PENDING `DefensiveInterventionRequest`;
2. an already-resolved canonical Governance connector request whose `candidate_ref` and canonical request SHA-256 bind that exact PENDING request.

It does not create a threat observation or resolved Governance facts.

The materializer reuses the pinned local StegOS `governance-external-action` InTr connector, validates a completed local packet/receipt chain, derives `VerifiedTransportBindings` through the existing reference-adapter mechanism, evaluates the authoritative GADI Governance profile, and invokes the already-merged GADI admission projector.

The Governance payload cannot self-assert transport bindings. The pinned InTr registry is passed by exact local path and its SHA-256 is recorded in the resulting materialization receipt.

Projection remains:

```text
ALLOW       -> ADMITTED + intr://governance-decision/<receipt_hash>
DENY        -> DENIED
FAIL-CLOSED -> DENIED
```

and explicitly records:

```text
resolved_governance_facts_created = false
threat_observation_created = false
runtime_binding_created = false
credential_minted = false
claim_or_fence_minted = false
execution_authority_granted = false
network_fetch_performed = false
credential_authority = TV/TVC
authority_effect = NONE_ADMISSION_MATERIALIZATION_ONLY
```

## Runtime-local source reuse

The existing sovereign resident environment already allows non-secret local roots including:

```text
STEGVERSE_STEGOS_ROOT
STEGVERSE_STEGCORE_SOURCE_ROOT
STEGVERSE_TVC_ROOT
STEGVERSE_TV_ROOT
```

Existing resident consumers use these local locators with filtered non-secret environments and no network source fetch. GADI should reuse that same mechanism; no additional source-discovery or hosted fallback plane is required.

## Native command and controlled-output seams

StegOS PR #337 consumes exact plan + ADMITTED request + current subject-bound runtime binding and delegates to the existing native command materializer. It rejects capability mismatch, stale subject binding, admission mismatch, and authority drift. `execution_authority_claimed_by_stegos=false` remains mandatory.

StegOS PR #331 remains the controlled-output receipt seam. It can receipt only an effect that has already been authentically observed through the existing StegOS kernel chain; it does not execute the effect.

## Current authentic evidence boundary

The following remain unobserved until produced on the actual sovereign resident runtime:

```text
CURRENT_GADI_RUNTIME_PRESENCE_SUBJECT_NOT_OBSERVED
CURRENT_GADI_RUNTIME_BINDING_NOT_OBSERVED
CURRENT_GADI_BOUNDARY_INTERACTION_NOT_OBSERVED
CURRENT_GADI_PRE_ADMISSION_PLAN_NOT_OBSERVED
CURRENT_GADI_PENDING_INTERVENTION_REQUEST_NOT_OBSERVED
CURRENT_GADI_RESOLVED_GOVERNANCE_FACTS_NOT_OBSERVED
CURRENT_GADI_INTR_ADMISSION_NOT_OBSERVED
CURRENT_GADI_NATIVE_COMMAND_NOT_OBSERVED
CONTROLLED_PREAUTHORIZED_ACTUATOR_RESULT_NOT_OBSERVED
CURRENT_GADI_WORKERCOORDINATOR_CLAIM_FENCE_NOT_OBSERVED
CURRENT_GADI_RESIDENT_CONSUMPTION_NOT_OBSERVED
```

A future WorkerCoordinator claim is valid only when created by the actual targeted runtime invocation after all non-claim evidence is coherent. It must not be fabricated or retained from source-only state.

## Immediate continuation

1. On the actual runtime root, obtain a current canonical runtime-presence receipt and materialize the subject-bound GADI runtime binding; do not create a parallel runtime probe.
2. Materialize one current controlled-software-surface `stegos.gadi-external-ai-interaction.v1` observation from actual runtime observation.
3. Run the merged StegOS native-plan materializer against that exact interaction and the locally available authoritative TV/TVC controlled-simulation capability evidence.
4. Produce the matching current PENDING intervention request plus current resolved Governance facts from the canonical reasoning/governance input path; do not substitute source fixtures.
5. Run the merged StegCore local admission materializer and require a current ADMITTED request with exact local InTr receipt bindings.
6. Feed exact plan + ADMITTED request + current runtime binding through the merged StegOS native-command bridge.
7. Observe the controlled pre-authorized software test-surface effect and receipt it through the merged StegOS actuator seam.
8. Let `run_gadi_targeted_runtime_if_ready.py` verify all non-claim artifacts; only then visit the canonical targeted WorkerCoordinator for a fresh claim/fence.
9. Require zero-blocker materialization/preflight and a newly changed resident-consumption receipt.
10. Complete adaptive reassessment/termination, Continuity custody, Master Records reconciliation, and exact confrontation reconstruction.

## Collision boundary

No second heartbeat, runtime-presence projector, WorkerCoordinator, scheduler, resident service, runtime lease plane, claim/fence plane, InTr authority, Governance evaluator, provider transport, credential route, actuator implementation, or Master Records custody path is introduced.

## README impact

No root README mutation is required. Existing documentation already defines runtime-presence subject binding, local sovereign source reuse, Governance/InTr authority separation, WorkerCoordinator authority separation, runtime convergence, and non-authorizing HB semantics.

## Release rule

None of the merged source/runtime-adapter work above is GADI activation or release evidence. Release/tag propagation remains deferred until authentic current resident execution, adaptive reassessment/termination, complete receipt chain, exact reconstruction, and canonical activation predicates are observed.
