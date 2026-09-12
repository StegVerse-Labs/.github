# SDK Ecosystem Diagnostic Processor Mirror Handoff

Updated: 2026-09-11

```text
Goal Task ID: SDK-ECOSYSTEM-DIAGNOSTIC-PROCESSOR-001
Parent Task ID: ECOSYSTEM-CONTINUITY-EVALUATOR-001
COSV: 71000000101000
Repository owner: StegVerse-org/StegVerse-SDK
Coordination repository: StegVerse-Labs/.github
State: ACTIVE / SOURCE IMPLEMENTATION STARTING
Authority effect: NONE_DIAGNOSTIC_ONLY
GitHub runtime authority: NONE
Credential authority: TV/TVC
```

## Goal

Install `ecosystem_diagnostic` as a first-class StegVerse SDK processing capability so internal or external callers can submit manifested diagnostic requests through the generic SDK processing contract and receive evidence-bound diagnostic observation artifacts. ECE remains the longitudinal continuity evaluator; this SDK processor does not calculate ecosystem continuity and does not repair anything.

## Frozen separation

```text
SDK diagnostic processor = manifested diagnostic request + bounded diagnostic observations/results
ECE = dependency-aware continuity interpretation across retained observations over time
Master Records = retained observation/evaluation custody and reconstruction
StegVerse-Healer = finding intake and repair dispatch
Interlock/InTr = governed transition authority where applicable
TV/TVC = credential/provider/release authority where applicable
Site = read-only safe projection only
```

The following are prohibited:

- treating processor selection as execution or repair authority;
- using ECE continuity state as an SDK diagnostic-test result;
- allowing diagnostic tests to mutate provider/runtime state unless a separately governed operation is explicitly admitted;
- converting missing evidence into PASS;
- using GitHub Actions as runtime authority;
- bypassing Master Records custody semantics;
- creating a second scheduler, WorkerCoordinator, heartbeat, or repair engine.

## Initial capability contract

```text
processing.capability = ecosystem_diagnostic
route_id = stegverse.route.ecosystem-diagnostic.v1
artifact schema = stegverse.ecosystem-diagnostic-result.v1
request schema = stegverse.ecosystem-diagnostic-request.v1
authority_effect = NONE_DIAGNOSTIC_ONLY
```

Initial diagnostic vocabulary must preserve at least:

```text
PASS
FAIL
DEGRADED
UNKNOWN
NOT_OBSERVED
STALE
UNREACHABLE
PROBE_REQUIRED
```

Each result must bind diagnostic/test identity, component/predicate identity, observation state, observation/evidence time where available, evidence references where permitted, authority owner, and whether the diagnostic itself performed mutation (`false` for v1).

## Implementation sequence

1. Register this child task and non-colliding COSV in the canonical task surfaces.
2. Add SDK request/result schemas and installed processor declaration.
3. Bind `ecosystem_diagnostic` to a dedicated installed route/runtime handler without altering governance semantics.
4. Extend Manifest Builder so callers can construct valid diagnostic manifests with explicit processing capability and route.
5. Add deterministic tests proving capability/route/authority separation, missing-evidence fail-closed behavior, and no governance-field requirement for diagnostic manifests.
6. Add a bounded bridge for ECE periodic execution to consume SDK diagnostic-result artifacts rather than invoking diagnostic observations ad hoc.
7. Retain source/CI vs authentic runtime distinction; do not claim diagnostic execution until a real SDK diagnostic request/result is observed.

## Current proof boundary

No SDK `ecosystem_diagnostic` processor is installed on main at handoff creation. Existing generic-manifest infrastructure supports non-governance capability selection and installed-route fail-closed semantics, which this task will reuse rather than replace.

## Next

Implement the child source in `StegVerse-org/StegVerse-SDK`, validate exact-head SDK workflows, then reconcile the parent ECE handoff. Authentic SDK diagnostic runtime execution remains a separate predicate after source merge.
