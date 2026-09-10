# Data Reclamation Interlock/InTr Authority Binding Mirror Handoff

Goal Task ID: `SS-DATA-RECLAMATION-INTR-AUTHORITY-BINDING-001`
Parent Goal Task ID: `SS-EVIDENCE-COMPARISON-001`
COSV: `40000100100000`
Status: `INACTIVE / UNCLAIMED`

## Scope

Bind Derived Data Authority and reclamation target actions to Interlock/InTr governed transition evaluation. Discovery, graph membership, custody, provider metadata, or a submitted request must never independently become execution authority.

## Completion predicates

- Every deletion/restriction/derivation action is represented by an exact manifested transition request.
- InTr returns a decision receipt bound to subject, target, requested action, evidence set, authority dimensions, and replay identity.
- Missing or insufficient authority fails closed.
- Replayed or materially altered requests cannot reuse an earlier decision.
- No heartbeat, scheduler, graph, KV writer, or provider adapter assumes InTr authority.

## Manual work

None at task creation.
