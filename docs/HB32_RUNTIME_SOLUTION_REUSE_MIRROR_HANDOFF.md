# HB32 Runtime Solution Reuse Mirror Handoff

Repository: `StegVerse-Labs/.github`  
State: `DISCOVERY_INDEX_IMPLEMENTED / VALIDATION_PENDING`  
Preflight: `receipts/preflight/HB32-RUNTIME-SOLUTION-REUSE-POLICY-001.json`  
Authority effect: `NONE_DISCOVERY_ONLY`

## Purpose

Runtime failures involving HeartBeat, oscillator/carrier state, WorkerCoordinator presence/freshness, local source refresh, resident request dispatch, or task-runtime absence must first be compared against the runtime remedies already installed in this repository.

Canonical discovery index:

`data/runtime-solution-registry.d/hb32-existing-runtime-solutions.json`

This avoids treating a missing runtime signal as evidence that a new heartbeat, oscillator, scheduler, WorkerCoordinator, resident runtime, request, claim/fence plane, or hosted runtime needs to be created.

## Current canonical repairs to reuse

- `ec92570ccfa4ef9b87bef77c4596f0f341ff33b7`: native heartbeat-carrier CLI and fail-closed oscillator progression proof.
- `511b82e26dcfce0d799f861df23b605fb837ac56`: recycle a previously proven but stale/non-task-capable WorkerCoordinator using the existing carrier self-heal.
- `55c03313d72dde2f067434c87cd3691ec0682c14`: persist the WorkerCoordinator task-capable cycle before potentially long tick-zero resident maintenance so self-heal does not falsely kill a healthy restarted worker.
- `543fb39498cdba042796a09d70292c2bd7396e1a`: restore standing-awareness runtime dependencies through the existing local-only source-refresh path.
- `72e80ce645858c02877277845ffe624cd71ec1e6`: reuse the existing same-host sovereign runtime fallback for G18 before declaring a generic runtime blocker.

## Runtime issue rule

For a runtime symptom:

1. Resolve the current HB/oscillator and resident self-heal handoffs.
2. Match the problem class against the runtime-solution registry.
3. Reuse the matching existing solution and its evidence predicates.
4. Keep carrier presence, WorkerCoordinator presence, request consumption, task execution, claim/fence, and completion separate.
5. Only create a successor functional repair when authentic evidence identifies a specific gap in the existing solution.
6. Run a new machine preflight, including README completeness, before that successor functional mutation.

The index itself does not alter runtime behavior or authority. It is a durable discovery/continuation aid. The functional fixes listed above remain authoritative from their own commits, handoffs, tests, and runtime evidence boundaries.

## HIL continuation

For HIL request `RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002`, a missing consumption receipt must first be evaluated through the existing HB32 carrier/self-heal, current WorkerCoordinator, local source refresh, resident request dispatcher, and HIL-specific consumer. Do not construct a HIL-specific heartbeat/runtime merely because the consumption predicate remains unknown.

The current source fixes do not themselves prove authentic HIL request consumption, a real HIL claim/fence, receiver READY, custody, TVC lifecycle admission, or activation.

## README completeness

This index is nonfunctional discovery guidance. The material runtime fixes are already described in `README.md`. The preflight records an evidence-supported determination that this index requires no additional README mutation.
