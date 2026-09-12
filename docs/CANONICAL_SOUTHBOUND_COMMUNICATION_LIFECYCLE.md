# Canonical southbound communication lifecycle

Status: CANONICAL ARCHITECTURE CONTRACT
Scope: All Task Registry participants, external-framework communication paths, evaluator return paths, and governed ecosystem egress

## Purpose

This document materializes the existing StegVerse communication lifecycle that every Task Registry participant must preserve when a manifested request enters governed processing and later exits the ecosystem.

`SOUTH` denotes the complete governed communication path moving toward ecosystem egress. It is not a separate authority, processor, runtime, or transport.

## Canonical lifecycle

```text
initiating entity
-> canonical SDK manifested ingress
-> admitted manifest
-> manifest-declared processing capability + bound route
-> governed processing / required internal transitions
-> required external evaluator or counterparty round trip through designated Interlock/InTr when the manifest includes one
-> returned governed processing / reconciliation as declared by the manifest
-> canonical evidence custody + replay/reconstruction requirements declared by the manifest
-> Publisher presentation/evidence stage declared in the complete manifest
-> SDK return assembly bound to the original request and initiating entity
-> caller-path egress adapter when one exists
-> final StegVerse-side state transition
-> designated Interlock/InTr egress
-> far-side Interlock/InTr transition
-> initiating entity receives the manifested result/evidence projection
```

## Complete-manifest invariant

A complete communication manifest describes the required lifecycle through completion, not only the first processor invocation.

When presentation/evaluator evidence is required, Publisher is an explicit manifest stage. Publisher does not appear after the governed run as an out-of-band convenience and does not invent evidence. Publisher consumes authentic retained evidence and prepares the presentation/report/evaluator evidence required by the same manifested communication lifecycle.

The manifest must preserve the relationship between:

- original initiating entity;
- original request/manifest identity;
- selected processing capability and route;
- all required governed transitions;
- any designated Interlock/InTr round trip;
- replay/reconstruction/evidence predicates when required;
- Publisher presentation/evidence requirements;
- SDK return assembly and caller projection;
- the exact final StegVerse-side egress transition;
- the required far-side transition that completes the communication.

Publisher is not processor-selection authority, governance authority, transport authority, or evidence authority. It is the canonical presentation/evidence assembly stage when declared by the manifest.

## Southbound egress invariant

The complete communication path remains governed through ecosystem egress.

For external-framework traffic using the LLM Adapter, the LLM Adapter is the final StegVerse-side state-transition surface before the request/result enters the designated Interlock/InTr egress. The LLM Adapter may perform only the manifest-bound protocol/framing transformation required for that egress. It may not alter governed evidence semantics, substitute a processor, or terminate the communication early.

```text
... -> Publisher -> SDK return assembly -> LLM Adapter -> Interlock/InTr -> far-side transition
```

The transition at the LLM Adapter is not the terminal communication state. The final state transition occurs on the other side of Interlock/InTr. Until that far-side transition is authentically observed and correlated, the communication is not complete.

For an initiating entity that does not use the LLM Adapter, the applicable manifest-bound egress surface occupies the analogous final StegVerse-side position. The invariant is the same: the last in-ecosystem transition precedes Interlock/InTr; terminal communication state is reached only after the far-side transition.

## Manifest-driven processing remains system-wide

Source identity, provider identity, framework identity, adapter identity, transport identity, model identity, interface identity, or prior-result identity never chooses processing semantics.

```text
admitted manifest
-> processing.capability
-> processing.route_id
-> installed admissible route
-> processor
```

The southbound lifecycle does not weaken this invariant. Every processing stage and every transition remains bound to the complete manifest and the applicable governed transition contract.

## Initiator-return invariant

Publisher output returns to the SDK as the presentation/evidence product of the existing manifested lifecycle. The SDK binds that output to the original request and initiating entity and produces the caller-selected projection.

Publisher output is not automatically a new processing request. A new processing cycle exists only when a new admitted manifest explicitly requests additional processing.

The initiating entity may be a user-facing StegVerse surface, an external evaluator/tester, or an external framework. External-framework return framing may pass through the LLM Adapter only as the manifest-bound final StegVerse-side egress transition before Interlock/InTr.

## Completion rule

A communication path that requires external delivery is not complete merely because:

- governance completed;
- Publisher rendered a report;
- SDK assembled a return artifact;
- an adapter emitted bytes;
- Interlock/InTr accepted a local egress materialization.

Completion requires the authentic far-side Interlock/InTr transition bound to the same manifest/request lineage and the required caller-side consequence/receipt.

## Authority preservation

- Task Registry: work-intent and coordination truth only.
- WorkerCoordinator: execution claim/fence authority.
- Interlock/InTr: governed ingress/egress and transition authority.
- TV/TVC: credential authority.
- Master Records: observed-reality/custody/reconstruction authority.
- SDK: canonical manifested processing ingress and caller-return assembly.
- Publisher: manifest-declared presentation/evidence assembly only.
- LLM Adapter: protocol/framing adapter and, when applicable, final StegVerse-side southbound transition surface before Interlock/InTr.
- GitHub Actions: source validation/evidence transport only; runtime authority NONE.
- Heartbeat: observability only.

No component may infer completion, authority, or processing semantics from its position in this sequence.
