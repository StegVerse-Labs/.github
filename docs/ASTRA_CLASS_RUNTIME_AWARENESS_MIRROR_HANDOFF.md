# Astra-Class Runtime Awareness Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Parent goal: `ASTRA-CLASS-RESILIENCE-001`  
Subgoal: `ASTRA-CLASS-RUNTIME-AWARENESS-001`  
State: `SOURCE_MERGED_VALIDATED / RESIDENT_CONSUMPTION_REQUIRED`  
Applies to: `StegVerse-001`, `StegVerse-002`, `SV-011`

## Source of truth

This handoff is subordinate to:

1. `docs/ASTRA_CLASS_ADVERSARIAL_RESILIENCE_MIRROR_HANDOFF.md`;
2. `docs/CANONICAL_RESIDENT_CARRIER_MIRROR_HANDOFF.md`;
3. `docs/ORG_MIRROR_HANDOFF.md`.

The current objective is to materialize the already-approved Astra-class frontier cyber resilience directive into the existing sovereign resident runtime for all three AI entities without creating a new heartbeat, scheduler, WorkerCoordinator, credential plane, or second user-operated machine requirement.

## Source implementation and validation

The runtime-awareness lane consists of:

- `scripts/consume_astra_class_resilience_awareness_request.py`;
- `control/resident-execution-request.d/astra-class-resilience-sv001-awareness-001.json`;
- `control/resident-execution-request.d/astra-class-resilience-sv002-awareness-001.json`;
- `control/resident-execution-request.d/astra-class-resilience-sv011-awareness-001.json`;
- dispatcher selector `astra_class_resilience_awareness` in `scripts/dispatch_resident_execution_requests.py`;
- `tests/test_astra_class_resilience_runtime_awareness.py`;
- `tests/test_astra_class_resilience_dispatch_binding.py`;
- fail-closed awareness-aware legacy dispatcher assertions in `tests/test_resident_request_dispatcher.py`.

PR `#995` merged as `dcbd6f994b6ea2becb1c0301abd79ee3dfb22d6a`.

Exact-head source validation before merge:

```text
head: 6fe06793c9dd6d09f37cde13e102083d5763fc0b
Heartbeat Worker Project: run 33944643368 SUCCESS
Cross-Framework Current-Basis Resident Request Validation: run 33944643373 SUCCESS
```

The organization-control run at that head failed only because the already-released cross-task coordination lane had added `.github/workflows/cross-task-coordination-validation.yml` without registering it in `control/workflow-surface-registry.json`. The cross-task handoff reported no active mutation claim, so the adjacent hygiene drift was repaired non-destructively by PR `#1003`, merged as `874842985154ec174daa1f3f983f7a66e63f58fc`. That repair grants no runtime authority.

Source validation and merge prove source/control consistency only. They do not prove resident awareness.

The consumer validates the existing machine-readable resilience contract, validates all three non-authorizing resident requests, and on authentic resident consumption writes one standing awareness state and one receipt per entity plus an aggregate receipt.

## Required resident outputs

```text
runtime-state/entity-awareness/stegverse-001.json
runtime-state/entity-awareness/stegverse-002.json
runtime-state/entity-awareness/sv-011.json

receipts/sovereign-host/astra-class-resilience/stegverse-001.latest.json
receipts/sovereign-host/astra-class-resilience/stegverse-002.latest.json
receipts/sovereign-host/astra-class-resilience/sv-011.latest.json
receipts/sovereign-host/astra-class-resilience-awareness.latest.json
```

## Meaning of runtime awareness

Runtime awareness is established only when the existing sovereign `WorkerCoordinator` dispatch path authentically consumes the requests and materializes all three awareness states with:

- `standing_directive_active=true`;
- the entity-specific resilience role and responsibilities;
- the frontier threat assumptions;
- the required security properties;
- the exact resilience-contract hash;
- TV/TVC as credential authority;
- capability not conferring authority;
- HeartBeat not granting execution authority;
- InTr/Interlock retained as the transition boundary;
- no second-machine dependency.

Source merge, tests, CI, request-file presence, dispatcher registration, or heartbeat progression alone do **not** prove runtime awareness.

## Continuing effect

Once authentic resident awareness is materialized, security-relevant work proposed or executed through the three bound entity selectors should consume the standing awareness state as context for future hardening work:

- `StegVerse-001` -> continuity/replay/drift and forensic reconstruction;
- `StegVerse-002` -> frontier threat classification, unknown-state preservation, and admissibility-change proposals;
- `SV-011` -> bounded adversarial hardening, minimization, isolation, replacement, and rebuild experiments.

This standing state is not authority. It cannot mint credentials, admit transitions, bypass TV/TVC, bypass InTr/Interlock, self-approve consequences, or alter canonical policy by itself.

## Current machine task

```text
Task ID: SHWP-ASTRA-CLASS-RESILIENCE-AWARENESS-001
Selector: astra_class_resilience_awareness
Owner runtime: existing heartbeat-separated native WorkerCoordinator
State: SOURCE_MERGED_REQUESTED_FOR_RESIDENT_CONSUMPTION
Success: aggregate receipt state COMPLETED, entity_count=3, runtime_awareness_materialized=true, standing_directive_active=true, and all three entity receipts are present with matching contract hashes
Failure posture: fail closed; do not infer partial awareness from fewer than three completed entity states
```

## Remaining machine work

1. materialize merged source commit `dcbd6f994b6ea2becb1c0301abd79ee3dfb22d6a` or a descendant containing it into the existing sovereign resident runtime;
2. dispatch only `astra_class_resilience_awareness` or allow the normal dispatcher to visit it;
3. inspect the aggregate and three entity receipts;
4. only after those receipts exist, classify the three entities as runtime aware;
5. make security-relevant entity task consumers consult the standing awareness state so the directive affects ongoing work rather than only initial activation;
6. build the executable adversarial-resilience catalog required by the parent handoff;
7. when release/tag readiness is reached, verify propagation to `StegVerse-Labs/Site`, `GCAT-BCAT-Engine/Publisher`, `admissibility-wiki`, and `stegguardian-wiki`.

## Known installation / integration destinations

- `StegVerse-Labs/.github`: authentic resident source materialization, awareness consumption, and receipts;
- `StegVerse-001` consumer surface: standing-awareness consultation before security-relevant autonomous work;
- `StegVerse-002` consumer surface: standing-awareness consultation before threat/admissibility work;
- `SV-011` consumer surface: standing-awareness consultation before autonomous hardening/rebuild work;
- `StegVerse-Labs/Site`: downstream architecture/publication semantics when release-ready;
- `GCAT-BCAT-Engine/Publisher`: downstream publication semantics when release-ready;
- `admissibility-wiki`: downstream admissibility semantics when release-ready;
- `stegguardian-wiki`: downstream guardian/security semantics when release-ready.

## Archive condition

The originating implementation thread is archive-ready because source integration is merged and every remaining resident-consumption/downstream-hardening requirement is now represented in durable issue `#994`, the three resident requests, and this handoff. Runtime awareness itself remains unproven until authentic resident receipts exist.
