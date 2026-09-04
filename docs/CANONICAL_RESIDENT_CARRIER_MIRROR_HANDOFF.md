# Canonical Resident Carrier Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Issue: `#974`  
Goal: `CANONICAL-RESIDENT-CARRIER-974`  
State: `SOURCE_COMPLETE_MERGED_VALIDATED / RUNTIME_EVIDENCE_REMAINS_TASK_SPECIFIC`  
Source merge: `b1f2bb3e33a1f93850811f0a751b2055519ab4dd`  
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

## Source completion evidence

PR `#975` merged as `b1f2bb3e33a1f93850811f0a751b2055519ab4dd` after both canonical validation lanes passed:

- organization control plane: SUCCESS;
- Heartbeat Worker Project: SUCCESS, including the complete deterministic repository suite.

The merge also repaired pre-existing denominator drift for `LEGACY-CONTINUITY-VALIDATION-WORKER-001` by installing its AE retrospective classification and canonical COSV task vector while preserving zero active unvectorized worker gaps.

Repository validation proves source/control consistency only. It is not resident execution evidence.

## Authority split

- HeartBeat: deterministic reference/timing/continuity only; `OSCILLATOR_ONLY` progression.
- HB-derived InTr carrier: exact-byte carrier coordinate and reconstruction only; no admission/execution authority.
- WorkerCoordinator: sole resident task-control runtime; independent claim/fence/admission under existing contracts.
- InTr/Interlock: governs admissible transition boundaries.
- TV/TVC: sole credential authority.
- Master Records: custody/reconstruction where required.
- Consumer-specific workers: domain execution only inside their admitted task boundary.

## Runtime evidence posture

Shared-substrate membership is now merged and source-verifiable. Product/task completion remains runtime-specific and must not be inferred from the merge.

### StegVerse-001

Authentic current-iPhone terminal evidence already exists. The canonical lineage is G23; G24 is retained duplicate non-custodial evidence because terminal reexecution was prohibited. **Do not rerun SV001 merely to prove this carrier convergence.** Continue only downstream custody/reconstruction and SV002 disposition under their current handoffs and iOS interaction serialization rules.

### StegVerse-002

The canonical request remains `REQUESTED` at `control/resident-execution-request.d/sv002-org-runtime-activation-001.json`. Continue through the existing `sv002_org_runtime_activation` consumer. Terminal evidence requires `terminal_round_trip_observed=true` from the existing HeartBeat-separated native WorkerCoordinator execution path, plus downstream governed-inference/reconstruction evidence where required by the active product goal.

### SV-011

Both canonical requests remain `REQUESTED`:

- `control/resident-execution-request.d/sv011-phase5-source-materialization-001.json`;
- `control/resident-execution-request.d/sv011-phase5-boundary-001.json`.

Continue source materialization first, then the existing `sv011_phase5` consumer. Phase 5 closes only when one WorkerCoordinator execution produces the required ALLOW five-receipt chain and DENY `consumed=false` / `consequence_reachable=false` evidence.

## Collision rule

Any future project handoff that describes a separate SV001, SV002, or SV-011 heartbeat/runtime/scheduler path is stale unless it explicitly proves the canonical substrate is technically incapable of satisfying that lane. The default repair is consumer integration into this substrate, not creation of another runtime.

## Remaining machine work

1. Existing resident WorkerCoordinator consumes the pending SV002 request through the canonical dispatcher and persists task-specific terminal evidence.
2. Existing resident WorkerCoordinator consumes SV-011 source materialization, then Phase-5 boundary execution, and persists the first-success evidence capsule when predicates are satisfied.
3. Preserve task-specific downstream reconstruction/disposition without rerunning terminal SV001.
4. Verify architecture/source propagation to Site, Publisher, admissibility-wiki, and stegguardian-wiki using `docs/CANONICAL_RESIDENT_CARRIER_POSTMERGE_PROPAGATION.md`; propagate runtime status only when each consumer's authentic evidence gate is satisfied.

No manual/current-iPhone state mutation is authorized or required by this handoff.
