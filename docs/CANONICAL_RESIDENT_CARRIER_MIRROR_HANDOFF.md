# Canonical Resident Carrier Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Issue: `#974`  
Goal: `CANONICAL-RESIDENT-CARRIER-974`  
State: `SOURCE_AND_ARCHITECTURE_PROPAGATION_COMPLETE / RUNTIME_EVIDENCE_REMAINS_TASK_SPECIFIC`  
Source merge: `b1f2bb3e33a1f93850811f0a751b2055519ab4dd`  
Credential authority: `TV/TVC`  
GitHub token runtime authority: `NONE`

## Source of truth

This file is the scoped continuation record for convergence of StegVerse-001, StegVerse-002, and SV-011 onto the already-existing canonical resident substrate. It is subordinate to `docs/ORG_MIRROR_HANDOFF.md`, `docs/HEARTBEAT_RUNTIME_SEPARATION_MIRROR_HANDOFF.md`, and `docs/HB_DERIVED_INTR_CARRIER_MIRROR_HANDOFF.md`.

## Canonical substrate

```text
HB32 independent 10 ms / 100 Hz oscillator reference
-> HB-derived exact-byte Universal InTr carrier (non-authorizing)
-> one canonical StegVerse-Labs/.github WorkerCoordinator authority
   -> native resident process surface where applicable
   -> CURRENT_USER_IPHONE portable checkout surface where applicable
-> task-specific fail-closed consumer
-> task-specific durable receipt/reconstruction/disposition
```

HB32 progression is `OSCILLATOR_ONLY`: the protocol reference does not require a continuously running carrier sampler or native WorkerCoordinator process. The native and portable WorkerCoordinator surfaces are two execution expressions of the same canonical authority, not two WorkerCoordinators.

This convergence creates no new heartbeat, oscillator, scheduler, WorkerCoordinator, runtime owner, credential lane, claim/fence authority, route authority, transition authority, publication authority, custody authority, or second user-operated machine requirement.

## Machine-readable contract

`control/canonical-resident-carrier-contract.json`

The contract binds these selectors to the common substrate:

```text
StegVerse-001 -> stegverse001_bounded_autonomy
StegVerse-002 -> sv002_org_runtime_activation
SV-011 predecessor -> sv011_phase5_source_materialization
SV-011 -> sv011_phase5
```

## HB32 portable runtime-selection repair — 2026-09-06

A runtime review found a classification defect rather than a missing heartbeat/runtime implementation. The canonical HB32 deployment already defines daemon-free independent oscillator progression, and the canonical WorkerCoordinator already has a `CURRENT_USER_IPHONE` portable checkout implementation. Authentic StegOS iOS device-local execution has also already been observed in the runtime-observability record. Therefore failure to observe a continuously supervised native WorkerCoordinator process must not be reported as **generic runtime absence** for a task whose applicable canonical surface is portable current-iPhone execution.

The runtime-presence projector now preserves the old native process predicate unchanged while adding a distinct fail-closed task-control observation:

```text
resident.present_worker_runtime_observed
  = fresh task-capable native WorkerCoordinator process presence only

portable_workercoordinator.observed
  = exact subject-bound stegverse.workercoordinator-portable-checkout-receipt/v1
    from CURRENT_USER_IPHONE only

resident.task_control_runtime_observed
  = native present-worker predicate OR valid task-scoped portable checkout observation
```

The portable receipt must bind the canonical `.github` WorkerCoordinator authority owner, independent-task-control domain, exact task/worker/claim/fence, TV/TVC boundary, no GitHub runtime authority, no external non-StegVerse machine, and no parallel WorkerCoordinator issuance. Static package/source presence does not qualify. Portable checkout proves the claim/fence transaction happened on the bound current-iPhone surface; it does **not** prove request consumption, task execution, transition completion, custody, reconstruction, or product activation.

This repair reuses:

- `docs/SOVEREIGN_HEARTBEAT_DEPLOYMENT_MIRROR_HANDOFF.md` and its HB32 daemon-free oscillator semantics;
- `docs/WORKERCOORDINATOR_PORTABLE_IPHONE_EXECUTION_MIRROR_HANDOFF.md`;
- `workercoordinator/portable_checkout.js`;
- `docs/HB_RUNTIME_PRESENCE_RESIDENT_OBSERVABILITY_MIRROR_HANDOFF.md`;
- `receipts/preflight/sv002-current-iphone-portable-consumer-20260905.json`;
- the existing StegOS same-device native SV002 chain.

Preflight: `receipts/preflight/HB32-PORTABLE-RUNTIME-SELECTION-20260906.json`.

README impact is material and is satisfied in the same change set because this repair changes runtime availability/failure semantics and the supported execution-prerequisite interpretation.

## Autonomous governed progression adoption — 2026-09-04

Canonical progression rule:

- `docs/ENTITY_AUTONOMOUS_GOVERNED_PROGRESSION_MIRROR_HANDOFF.md`
- `control/entity-autonomous-governed-progression-contract.json`
- `scripts/evaluate_entity_transition_ownership.py`

StegVerse-001, StegVerse-002, and SV-011 are now source-bound to `MACHINE_GOVERNED_AUTONOMOUS` progression for machine-owned transitions.

The rule is not standing/reused authority. Every state change remains contemporaneously governed:

```text
observe current state
-> propose exact next transition
-> Interlock/InTr governance now
-> TV/TVC now if credential authority is required
-> retain ALLOW/DENY receipt
-> ALLOW: execute/consume
-> retain state receipt
-> reconstruct
-> continue to next governed transition
```

The entity does not stop to ask the user to approve the next machine transition set. Human interaction occurs only when the exact transition contract declares a human/user-only authority class.

The current-user iOS interaction queue is explicitly excluded from scheduling or approving machine-owned resident/service-worker transitions. Execution on `CURRENT_USER_IPHONE` does not make a transition human-owned.

This source adoption does not claim any entity is presently alive/executing. It removes manual human approval as a default orchestration dependency from the canonical resident contract.

## Source completion evidence

PR `#975` merged as `b1f2bb3e33a1f93850811f0a751b2055519ab4dd` after both canonical validation lanes passed:

- organization control plane: SUCCESS;
- Heartbeat Worker Project: SUCCESS, including the complete deterministic repository suite.

The merge also repaired pre-existing denominator drift for `LEGACY-CONTINUITY-VALIDATION-WORKER-001` by installing its AE retrospective classification and canonical COSV task vector while preserving zero active unvectorized worker gaps.

Repository validation proves source/control consistency only. It is not resident execution evidence.

## Architecture propagation completion

`CANONICAL-RESIDENT-CARRIER-PROPAGATION-VERIFY-001` is complete. Evidence is retained at `receipts/canonical-resident-carrier/propagation-verification-001.json`.

- `StegVerse-Labs/Site`: `NO_CHANGE_REQUIRED`; inspected Site surfaces already express the canonical `.github` WorkerCoordinator and non-authorizing iPhone/HB portability semantics.
- `GCAT-BCAT-Engine/Publisher`: PR `#53`, merge `a22891bd7a30d6e410c42189361b77a0456b7558`.
- `StegVerse-Labs/admissibility-wiki`: PR `#127`, merge `fe5a48728466af13ae368b52109a795e509d0cb5`.
- `StegVerse-002/stegguardian-wiki`: PR `#36`, merge `9732c439b7a4a67c9430b7fc1194126b8ea3fd78`.

Architecture/source propagation is complete. Runtime-status propagation remains separately gated by authentic consumer-specific resident evidence.

## Authority split

- HeartBeat: deterministic reference/timing/continuity only; `OSCILLATOR_ONLY` progression; no continuously running sampler required for progression.
- HB-derived InTr carrier: exact-byte carrier coordinate and reconstruction only; no admission/execution authority.
- WorkerCoordinator: sole task-control claim/fence authority, expressed through the canonical native process surface or canonical portable current-iPhone checkout surface as applicable.
- InTr/Interlock: governs admissible transition boundaries.
- TV/TVC: sole credential authority.
- Master Records: custody/reconstruction where required.
- Consumer-specific workers: domain execution only inside their admitted task boundary.

## Runtime evidence posture

Shared-substrate membership and downstream architecture propagation are merged and source-verifiable. Product/task completion remains runtime-specific and must not be inferred from those merges.

### StegVerse-001

Authentic current-iPhone terminal evidence already exists. The canonical lineage is G23; G24 is retained duplicate non-custodial evidence because terminal reexecution was prohibited. **Do not rerun SV001 merely to prove this carrier convergence.** Continue only downstream custody/reconstruction and SV002 disposition under current governance. Machine-owned continuation must not be converted into a user approval sequence.

### StegVerse-002

The canonical request remains `REQUESTED` at `control/resident-execution-request.d/sv002-org-runtime-activation-001.json`. The expected authentic terminal receipt `receipts/sovereign-host/sv002-org-runtime-activation.latest.json` is not currently present on canonical `main`.

The previously identified runtime gap must be interpreted through the already-created HB/oscillator and portable runtime solutions, not as a demand for another resident daemon or another machine. `receipts/preflight/sv002-current-iphone-portable-consumer-20260905.json` already resolved the admissible continuation as reuse/extension of the canonical `CURRENT_USER_IPHONE` portable WorkerCoordinator. The StegOS same-device non-reference native chain is source-complete and released; its remaining physical predicate is exact bundle/package materialization and target-organization execution on the current iPhone.

Continue through the existing `sv002_org_runtime_activation` identity and autonomous governed progression path while consuming the portable current-iPhone WorkerCoordinator surface where that is the applicable execution substrate. Do not reintroduce the Python/local-repository second-machine path merely because native-process presence is absent.

Terminal evidence still requires the exact task-specific request-consumption/principal/output/transition/reconstruction chain. A portable checkout is claim/fence evidence only and cannot satisfy terminal round-trip or Master Records predicates by itself.

### SV-011

Both canonical requests remain `REQUESTED`:

- `control/resident-execution-request.d/sv011-phase5-source-materialization-001.json`;
- `control/resident-execution-request.d/sv011-phase5-boundary-001.json`.

The expected authentic source-materialization consumption receipt `receipts/sovereign-host/sv011-phase5-source-materialization-request-consumption.latest.json` and first-success capsule `receipts/sv011-phase5-boundary/success/first-success.json` are not currently present on canonical `main`.

Continue source materialization first, then the existing `sv011_phase5` consumer under autonomous governed progression. Phase 5 closes only when one WorkerCoordinator execution produces the required ALLOW five-receipt chain and DENY `consumed=false` / `consequence_reachable=false` evidence.

## Collision rule

Any future project handoff that describes a separate SV001, SV002, or SV-011 heartbeat/runtime/scheduler path is stale unless it explicitly proves the canonical substrate is technically incapable of satisfying that lane. The default repair is consumer integration into this substrate, not creation of another runtime.

A handoff or diagnostic that equates absent continuously supervised native WorkerCoordinator process presence with universal runtime absence is also stale when the task is eligible for the canonical portable current-iPhone execution surface. The correct repair is to resolve the applicable execution surface and require its direct task-scoped evidence.

## Remaining machine work

1. For each pending task, resolve whether its canonical execution surface is native resident process, portable `CURRENT_USER_IPHONE`, or another already-authorized StegVerse surface before declaring runtime absence.
2. Existing WorkerCoordinator authority consumes the pending SV002 request through the already-admitted same-device path; current-iPhone portable checkout may provide the claim/fence transaction without requiring native daemon presence, but exact target execution and reconstruction remain independently required.
3. Existing WorkerCoordinator consumes SV-011 source materialization, then Phase-5 boundary execution, and autonomously continues governed machine transitions until the first-success evidence capsule is produced or an actual governed DENY/blocker is reached.
4. Preserve task-specific downstream reconstruction/disposition without rerunning terminal SV001; machine-owned Master Records/SV002 continuation must execute without routing through the human interaction queue.
5. Runtime consumers must adopt the exact ownership classifier so `CURRENT_USER_IPHONE` execution is not mistaken for `USER_ONLY` authority and native-process absence is not mistaken for absence of every canonical runtime surface.

No manual/current-iPhone transition approval is authorized or required by this handoff unless an exact next transition explicitly declares a human/user-only authority class.
