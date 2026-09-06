# HB32 Carrier-First Bootstrap Reconciliation Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Issue: `#1091`  
Preflight: `receipts/preflight/HB32-CARRIER-FIRST-BOOTSTRAP-RECONCILIATION-1091.json`  
State: `SOURCE_REPAIR_MERGED_VALIDATED / AUTHENTIC_RUNTIME_EVIDENCE_PENDING`  
Authority effect: `NONE_SOURCE_COORDINATION_ONLY`  
Credential authority: `TV/TVC`  
GitHub token runtime authority: `NONE`

## Canonical sources resolved

This repair is subordinate to and reuses:

- `handoffs/HEARTBEAT-OSCILLATOR-RESIDENT-START-012.json`;
- `data/runtime-solution-registry.d/hb32-existing-runtime-solutions.json`;
- `docs/HB32_RUNTIME_SOLUTION_REUSE_MIRROR_HANDOFF.md`;
- `docs/RESIDENT_WORKER_SELF_HEAL_MIRROR_HANDOFF.md`;
- `handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json`;
- the existing G18 fence-18 cross-task claim;
- Master Records runtime-presence custody/reconstruction without cross-task reuse authority.

No new heartbeat, oscillator, scheduler, WorkerCoordinator, claim/fence plane, credential path, hosted runtime, or second physical machine is created.

## Existing runtime remedies preserved

The current-main repairs remain authoritative and are not replaced:

- `ec92570ccfa4ef9b87bef77c4596f0f341ff33b7` — direct carrier CLI plus fail-closed oscillator progression proof;
- `511b82e26dcfce0d799f861df23b605fb837ac56` — stale/missing WorkerCoordinator recycling through existing self-heal;
- `55c03313d72dde2f067434c87cd3691ec0682c14` — persist first task-capable WorkerCoordinator cycle before long tick-zero maintenance;
- `543fb39498cdba042796a09d70292c2bd7396e1a` — existing local-only runtime source refresh;
- `72e80ce645858c02877277845ffe624cd71ec1e6` — G18 existing same-host fallback when native bootstrap proof is incomplete.

## Exact source drift repaired

The pre-repair durable bootstrap still entered `scripts/install_sovereign_heartbeat_service.py` from `scripts/bootstrap_sovereign_runtime.py`, even though the canonical resident-start handoff explicitly requires the direct carrier-only installer and states `workercoordinator_required_for_carrier_start=false`.

The pre-repair activation verifier also restarted both HeartBeat and WorkerCoordinator directly when testing controlled restart, making WorkerCoordinator restart appear to be part of HeartBeat reconstruction.

The repaired sequence is:

```text
existing install_sovereign_heartbeat_carrier.py
→ require carrier-activation.latest.json with carrier_active=true
→ require oscillator-produced progression already proven by that installer
→ observe existing carrier-side WorkerCoordinator self-heal/runtime presence
→ continue existing WorkerCoordinator resident dispatch/admission path
→ verify separated runtime
→ controlled restart restarts only HeartBeat carrier
→ require reconstructed carrier plus independently fresh task-capable WorkerCoordinator progress
```

WorkerCoordinator remains the claim/fence/admission authority. Interlock/InTr remains transition authority. HeartBeat/oscillator remains non-authorizing. TV/TVC remains sole credential authority.

## Validation and merge evidence

The repaired functional delta was validated at exact PR head `ff39cef7be399cbd3dedc0c0c5ce985dd4b5cbff`.

Required validation lanes:

- Heartbeat Worker Project - Validation Only / No GitHub Token Authority: run `34035271744` — `SUCCESS`;
- Validate organization control plane - No GitHub Token Authority: run `34035271730` — `SUCCESS`.

PR `#1105` merged the validated repair as `7146b112e37781517e37f9815d5bb05a213b0677`.

These results establish source/control validation and merge only. They do not establish current resident carrier presence, current WorkerCoordinator presence, request consumption, G18 completion, Master Records custody, or runtime activation.

## Cross-task and Master Records boundaries

The G18 coordination record remains untouched: claim `SHWP-SHWP-DURABLE-RUNTIME-ACTIVATION-G18`, fencing token `18`. This repair does not mint, renew, release, transfer, or reuse that claim.

Master Records remains `CUSTODY_AND_RECONSTRUCTION_ONLY`. Authentic runtime-presence input is still pending; source repair, hosted validation, or merge cannot satisfy that evidence predicate.

## README completeness

Preflight resolved README impact against current `main`. Current README already documents the direct carrier-only entrypoint and oscillator-progress requirement, existing WorkerCoordinator self-heal and first-cycle ordering, and G18 same-host fallback. No additional README mutation is required because this successor repairs stale bootstrap/verifier implementation to match those already-documented runtime semantics; it introduces no new behavior or authority model.

This validation-state reconciliation changes only the handoff's evidence status. It does not change repository behavior, runtime semantics, interfaces, governance or authority boundaries, evidence semantics, prerequisites, dependencies, failure behavior, or capability meaning; therefore no additional README change is required for this reconciliation commit.

## Truth boundary

Until deployment-local execution produces qualifying current receipts:

- carrier source repair: merged and source-validated;
- authentic resident carrier start: not inferred;
- current WorkerCoordinator presence: not inferred;
- request consumption: not inferred;
- G18 completion: not inferred;
- Master Records custody: not inferred;
- runtime activation: not inferred.
