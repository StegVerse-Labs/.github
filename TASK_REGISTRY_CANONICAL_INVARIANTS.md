# Task Registry canonical invariants

This is a global Task Registry participant entrypoint for architecture invariants that apply across goals, repositories, adapters, evaluators, and external-framework communication paths.

All Task Registry participants must preserve the canonical contracts listed here when scoped work touches the applicable surface. These contracts are not task-local preferences and must not be reconstructed from chat prose.

## Canonical communication lifecycle

- Human-readable: `docs/CANONICAL_SOUTHBOUND_COMMUNICATION_LIFECYCLE.md`
- Machine-readable: `data/canonical-southbound-communication-lifecycle.json`

```text
complete governed communication
-> manifest-selected processing
-> all required governed transitions / external round trips
-> canonical evidence custody / replay / reconstruction when declared
-> Publisher stage when presentation or evaluator evidence is declared
-> SDK return assembly bound to original request + initiator
-> applicable final StegVerse-side egress transition
-> Interlock/InTr egress
-> far-side Interlock/InTr transition
-> initiating entity receives manifested result
```

For external-framework paths using LLM Adapter, LLM Adapter is the final StegVerse-side transition surface immediately before Interlock/InTr egress. The terminal communication transition occurs on the far side of Interlock/InTr.

Publisher is part of the complete manifest when presentation/evaluator evidence is required. It is not out-of-band post-processing.

## Authority separation

- Task Registry: work intent / coordination truth.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed ingress/egress and transition authority.
- TV/TVC: credential authority.
- Master Records: observed reality, custody, reconstruction.
- SDK: manifested processing ingress and caller-return assembly.
- Publisher: manifest-declared presentation/evidence assembly only.
- LLM Adapter: protocol/framing plus applicable final StegVerse-side egress transition only.
- Heartbeat: observability only.
- GitHub Actions: no runtime authority.

### Worker-claim field invariant

When a canonical task record uses structured `worker_claim`, `worker_claim.authority` means the authority that may mint the execution claim/fence and therefore MUST be `WORKERCOORDINATOR`. A chat/session may be the current coordination holder or source-mutation actor, but `CURRENT_SESSION`, a model identity, repository identity, transport identity, or handoff reference must never be encoded as execution claim/fence authority.

If no authentic WorkerCoordinator claim/fence has been observed, the canonical projection is:

```text
worker_claim.authority = WORKERCOORDINATOR
worker_claim.claim_ref = null
worker_claim.fence_ref = null
worker_claim.projection_only = true
```

Session ownership/coordination provenance belongs in session/check-in history and coordination metadata. It does not become WorkerCoordinator authority merely because a session is actively editing source.

## Processing invariant

Processing semantics are selected only from the admitted manifest through its declared capability and bound route. Source, provider, framework, adapter, transport, model, interface, or prior-result identity may supply provenance/policy evidence but may not independently select processing.
