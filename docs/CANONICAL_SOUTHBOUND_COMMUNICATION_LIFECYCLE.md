# Canonical southbound communication lifecycle

Status: CANONICAL ARCHITECTURE CONTRACT
Scope: All Task Registry participants

`SOUTH` denotes the complete governed communication path toward ecosystem egress. It is not a processor, runtime, authority, or transport.

## Canonical lifecycle

```text
initiating entity
-> canonical SDK manifested ingress
-> admitted manifest
-> manifest-declared processing capability + bound route
-> governed processing / required internal transitions
-> required external evaluator/counterparty Interlock/InTr round trip when declared
-> returned governed processing / reconciliation declared by manifest
-> canonical custody + replay/reconstruction/evidence stages when declared
-> Publisher presentation/evidence stage when declared
-> SDK return assembly bound to original request + initiating entity
-> applicable caller-path egress adapter
-> final StegVerse-side state transition
-> designated Interlock/InTr egress
-> far-side Interlock/InTr state transition
-> initiating entity receives manifested result/evidence projection
```

## Complete-manifest invariant

A complete communication manifest describes the lifecycle through completion, not merely the first processor invocation. When presentation/report/evaluator evidence is required, Publisher is an explicit manifest stage. Publisher consumes authentic retained evidence and prepares the required package; it does not invent evidence or become governance, processing-selection, transport, credential, or caller-routing authority.

The manifest preserves the original initiator/request identity, selected capability/route, required transitions and round trips, custody/replay/reconstruction predicates, Publisher requirements, SDK caller projection, final StegVerse-side egress transition, Interlock/InTr egress, and the far-side transition that completes communication.

## Framework path / LLM Adapter

For external-framework traffic using the LLM Adapter:

```text
... -> Publisher -> SDK return assembly -> LLM Adapter -> Interlock/InTr -> far-side transition
```

The LLM Adapter is the final StegVerse-side state-transition surface before Interlock/InTr egress. It may perform only manifest-bound protocol/framing transformation. It is not the terminal communication state. The terminal transition occurs on the far side of Interlock/InTr.

For initiators that do not use LLM Adapter, the applicable manifest-bound egress surface occupies the analogous final StegVerse-side position.

## System-wide processing invariant

Source/provider/framework/adapter/transport/model/interface/prior-result identity may contribute provenance or policy evidence but may not select processing semantics.

```text
admitted manifest
-> processing.capability
-> processing.route_id
-> installed admissible route
-> processor
```

## Initiator-return invariant

Publisher output returns to SDK as the presentation/evidence result of the same manifested lifecycle. SDK binds it to the original request and initiating entity. Publisher output is not automatically a new processing request; a new cycle exists only when a new admitted manifest explicitly requests additional processing.

## Completion rule

Governance completion, Publisher rendering, SDK return assembly, adapter emission, or local Interlock/InTr egress staging is not terminal communication completion. Completion requires the authentic far-side Interlock/InTr transition bound to the same manifest/request lineage and the required caller-side consequence/receipt.

## Authority preservation

- Task Registry: work intent / coordination truth only.
- WorkerCoordinator: execution claim/fence authority.
- Interlock/InTr: governed ingress/egress and transition authority.
- TV/TVC: credential authority.
- Master Records: observed reality, custody, reconstruction.
- SDK: manifested processing ingress and caller-return assembly.
- Publisher: manifest-declared presentation/evidence assembly only.
- LLM Adapter: protocol/framing and applicable final StegVerse-side egress transition only.
- Heartbeat: observability only.
- GitHub Actions: runtime authority NONE.
