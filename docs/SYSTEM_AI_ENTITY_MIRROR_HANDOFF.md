# SYSTEM_AI_ENTITY_MIRROR_HANDOFF

## Authority

This is the canonical organization-level handoff for StegVerse system AI entity identity and lifecycle semantics.

Live repository state, `control/system-ai-entity-registry.json`, the single HeartBeat federation, runtime receipts, TV/TVC authority records, LLM-adapter execution evidence, and Master Records reconstruction supersede historical chat descriptions.

## Canonical insight now encoded

A StegVerse system AI entity is not defined by model sophistication alone.

It is a governed runtime participant that:

1. has an explicit identity and runtime repository;
2. is registered in the single StegVerse HeartBeat federation;
3. is observed as present through valid HeartBeat coverage evidence;
4. can perform governed local/private model execution;
5. does not receive execution, credential, policy, route, custody, or governance authority merely from HeartBeat participation or model output;
6. reaches `SYSTEM_AI_ACTIVE` only after the same governed execution has both inference evidence and reconstruction evidence.

## StegVerse-002

`StegVerse-002` is the first registered system AI entity.

Canonical runtime:

`StegVerse-002/micro-node-runtime`

Current state:

```text
entity_class: SOVEREIGN_AI_RUNTIME_ENTITY
lifecycle_state: FEDERATION_REGISTERED
federation_membership_established: true
heartbeat_presence_proven: false
governed_inference_proven: false
same_execution_reconstruction_proven: false
active: false
```

This state means the system recognizes StegVerse-002 as a required AI runtime participant, but does not yet claim continuous live presence or full system-AI activation.

## Lifecycle

```text
DECLARED
-> FEDERATION_REGISTERED
-> HEARTBEAT_PRESENT
-> INFERENCE_PROVEN
-> SYSTEM_AI_ACTIVE
```

`DEGRADED` and `RETIRED` are terminal/exception states for loss of required evidence or deliberate removal.

### FEDERATION_REGISTERED

Required:
- entity exists in `control/system-ai-entity-registry.json`;
- runtime repository is a required `RUNTIME` participant in `control/repo-heartbeat-federation.json`;
- HeartBeat grants no execution authority.

### HEARTBEAT_PRESENT

Requires an actual federation coverage receipt in:

`receipts/repo-heartbeat-federation/SHWP-REPO-HEARTBEAT-FEDERATION-001.json`

The receipt must show the entity's runtime participant valid, fresh, nonfailed, and non-dependency-blocked.

### INFERENCE_PROVEN

Requires a real local/private model execution through the governed route:

```text
StegVerse-002/micro-node-runtime
-> TV/TVC route admission
-> StegVerse-org/LLM-adapter
-> measured execution evidence
```

Static source, hosted CI, a fixture, or a model process without governed routing does not satisfy this state.

### SYSTEM_AI_ACTIVE

Requires all of:
- federation membership established;
- HeartBeat presence proven;
- governed inference proven;
- same-execution Master Records provider-usage reconstruction PASS;
- same-execution transition reconstruction PASS.

No model output itself can satisfy these predicates.

## Authority invariants

```text
credential_authority: TV/TVC
policy_authority: StegVerse-Labs/TV
route_authority: StegVerse-Labs/TVC
heartbeat_authority_effect: NONE
model_output_authority: NONE
github_token_runtime_authority: NONE
custody/reconstruction: master-records/orchestration
```

HeartBeat observes continuity and topology. It does not elevate the AI entity into governance authority.

## Required propagation after activation

Once `SYSTEM_AI_ACTIVE` is evidenced and released, verify capability projection into:

- StegVerse-Labs/Site
- GCAT-BCAT-Engine/Publisher
- StegVerse-Labs/admissibility-wiki
- StegVerse-002/stegguardian-wiki

No propagation may infer activation from source release alone.

## Remaining activation work

1. Produce the canonical repo-HeartBeat federation coverage receipt with StegVerse-002 healthy.
2. Execute the real governed local/private inference chain.
3. Persist measured execution evidence.
4. Produce same-execution Master Records reconstruction PASS.
5. Advance `StegVerse-002` to `SYSTEM_AI_ACTIVE` only from those receipts.
