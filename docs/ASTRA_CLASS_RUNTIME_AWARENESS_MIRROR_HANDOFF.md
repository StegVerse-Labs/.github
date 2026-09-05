# Astra-Class Runtime Awareness Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Parent goal: `ASTRA-CLASS-RESILIENCE-001`  
Subgoal: `ASTRA-CLASS-RUNTIME-AWARENESS-001`  
State: `SOURCE_IMPLEMENTED / RESIDENT_CONSUMPTION_REQUIRED`  
Applies to: `StegVerse-001`, `StegVerse-002`, `SV-011`

## Source of truth

This handoff is subordinate to:

1. `docs/ASTRA_CLASS_ADVERSARIAL_RESILIENCE_MIRROR_HANDOFF.md`;
2. `docs/CANONICAL_RESIDENT_CARRIER_MIRROR_HANDOFF.md`;
3. `docs/ORG_MIRROR_HANDOFF.md`.

The current objective is to materialize the already-approved Astra-class frontier cyber resilience directive into the existing sovereign resident runtime for all three AI entities without creating a new heartbeat, scheduler, WorkerCoordinator, credential plane, or second user-operated machine requirement.

## Source implementation

The runtime-awareness lane consists of:

- `scripts/consume_astra_class_resilience_awareness_request.py`;
- `control/resident-execution-request.d/astra-class-resilience-sv001-awareness-001.json`;
- `control/resident-execution-request.d/astra-class-resilience-sv002-awareness-001.json`;
- `control/resident-execution-request.d/astra-class-resilience-sv011-awareness-001.json`;
- dispatcher selector `astra_class_resilience_awareness` in `scripts/dispatch_resident_execution_requests.py`;
- `tests/test_astra_class_resilience_runtime_awareness.py`;
- `tests/test_astra_class_resilience_dispatch_binding.py`.

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
State: REQUESTED_AFTER_SOURCE_MERGE
Success: aggregate receipt state COMPLETED, entity_count=3, runtime_awareness_materialized=true, standing_directive_active=true, and all three entity receipts are present with matching contract hashes
Failure posture: fail closed; do not infer partial awareness from fewer than three completed entity states
```

## Remaining machine work

1. validate and merge the source integration PR;
2. materialize the merged source into the existing sovereign resident runtime;
3. dispatch only `astra_class_resilience_awareness` or allow the normal dispatcher to visit it;
4. inspect the aggregate and three entity receipts;
5. only after those receipts exist, classify the three entities as runtime aware;
6. next, make security-relevant entity task consumers consult the standing awareness state so the directive affects ongoing work rather than only initial activation;
7. build the executable adversarial-resilience catalog required by the parent handoff;
8. when release/tag readiness is reached, verify propagation to `StegVerse-Labs/Site`, `GCAT-BCAT-Engine/Publisher`, `admissibility-wiki`, and `stegguardian-wiki`.

## Archive condition

This originating session can be archived after the source integration is merged and all remaining resident consumption and downstream hardening work are represented by durable repository-native tasks and handoffs. Runtime awareness itself must not be claimed until authentic resident receipts exist.
