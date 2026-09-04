# Canonical Resident Carrier Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Issue: `#974`  
Goal: `CANONICAL-RESIDENT-CARRIER-974`  
State: SOURCE_INTEGRATION_ACTIVE / RUNTIME_EVIDENCE_REMAINS_TASK_SPECIFIC  
Credential authority: `TV/TVC`  
GitHub token runtime authority: `NONE`

## Source of truth

This file is the scoped continuation record for convergence of StegVerse-001, StegVerse-002, and SV-011 onto the already-existing canonical resident substrate. It is subordinate to `docs/ORG_MIRROR_HANDOFF.md`, `docs/HEARTBEAT_RUNTIME_SEPARATION_MIRROR_HANDOFF.md`, and `docs/HB_DERIVED_INTR_CARRIER_MIRROR_HANDOFF.md`.

## Canonical substrate

```text
HB32 independent 10 ms / 100 Hz oscillator reference
-> HB-derived exact-byte Universal InTr carrier (non-authorizing)
-> one heartbeat_runtime.worker_runtime.WorkerCoordinator
-> one scripts/dispatch_resident_execution_requests.py dispatcher
-> task-specific fail-closed consumer
-> task-specific durable receipt/reconstruction/disposition
```

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

## Authority split

- HeartBeat: deterministic reference/timing/continuity only; `OSCILLATOR_ONLY` progression.
- HB-derived InTr carrier: exact-byte carrier coordinate and reconstruction only; no admission/execution authority.
- WorkerCoordinator: sole resident task-control runtime; independent claim/fence/admission under existing contracts.
- InTr/Interlock: governs admissible transition boundaries.
- TV/TVC: sole credential authority.
- Master Records: custody/reconstruction where required.
- Consumer-specific workers: domain execution only inside their admitted task boundary.

## Runtime evidence posture

Shared-substrate membership is source-verifiable. Product/task completion remains runtime-specific and must not be inferred from this merge.

### StegVerse-001

Authentic current-iPhone terminal evidence already exists. The canonical lineage is G23; G24 is retained duplicate non-custodial evidence because terminal reexecution was prohibited. **Do not rerun SV001 merely to prove this carrier convergence.** Continue only downstream custody/reconstruction and SV002 disposition under their current handoffs and iOS interaction serialization rules.

### StegVerse-002

Continue through the existing `sv002_org_runtime_activation` consumer. Terminal evidence requires `terminal_round_trip_observed=true` from the existing HeartBeat-separated native WorkerCoordinator execution path, plus downstream governed-inference/reconstruction evidence where required by the active product goal.

### SV-011

Continue source materialization first, then the existing `sv011_phase5` consumer. Phase 5 closes only when one WorkerCoordinator execution produces the required ALLOW five-receipt chain and DENY `consumed=false` / `consequence_reachable=false` evidence.

## Collision rule

Any future project handoff that describes a separate SV001, SV002, or SV-011 heartbeat/runtime/scheduler path is stale unless it explicitly proves the canonical substrate is technically incapable of satisfying that lane. The default repair is consumer integration into this substrate, not creation of another runtime.

## Remaining machine work

1. Merge the source contract/validator for this convergence goal.
2. Allow the existing resident WorkerCoordinator to consume pending SV002 and SV-011 requests through the canonical dispatcher.
3. Preserve task-specific authentic receipts and downstream reconstruction/disposition.
4. Propagate capability-state changes to Site, Publisher, admissibility-wiki, and stegguardian-wiki only when their individual release gates are satisfied.

No manual/current-iPhone state mutation is authorized by this handoff.
