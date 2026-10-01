# Interlock/InTr runtime-independent protocol mirror handoff

Updated: 2026-10-01
Goal Task ID: `INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001`
Issue: #2897
COSV ID: `50000000102000`
Status: `ACTIVE / CHECKED OUT / CONFORMANCE VECTOR PREPARATION`

## Goal

Define a runtime-independent, machine-readable Interlock/InTr interoperability protocol in which registered nodes exchange manifested, payload-bound communications while each receiving framework independently determines the admissible state transition in its own runtime.

## Protocol boundary

The protocol standardizes the observable inter-system boundary, not participating runtimes. A conforming external framework is not required to adopt StegVerse internal runtime code, governance implementation, state representation, database, credential implementation, Master Records, or SDK.

Communication using Interlock/InTr requires registered-node identity and manifested intent. The protocol binds the communication to source, destination, payload commitment, applicable predecessor/state context, requested capability, disposition, receipt, resulting-state commitment where applicable, and evidence references.

The receiving framework remains authoritative for its own state machine. Incoming external data is not presumed to be governed by the originating framework. StegVerse governs its own output automatically; that property does not transfer StegVerse governance authority to the external framework.

## Disposition

Every attempted state-transition-dependent communication MUST terminate with an evidentiary disposition:

- `ALLOW`
- `DENY`
- `FAIL_CLOSED`

A transport success alone MUST NOT be represented as an allowed state transition.

## Initial interoperability profile

`MasterRecordsCheckpoint/v1` is the first bounded profile of this protocol.

Master Records remains sole checkpoint-construction/custody authority. For external checkpoint communication:
1. Master Records establishes canonical checkpoint C.
2. An egress manifest declares intent, checkpoint reference/commitment, registered destination node and requested checkpoint capability.
3. The receiving StegVerse boundary resolves applicable state and governs the permitted output projection.
4. Interlock/InTr transfers the permitted data and retains a transfer receipt.
5. External witness evidence may return through manifested registered-node ingress bound to digest(C).
6. The return is verified and receipted before any applicable resulting state/evidence is retained.

The manifest is provenance for communicating the checkpoint; it is not the checkpoint.

## Adoption/conformance boundary

No external adoption, external conformance, production interoperability, network participation, or runtime execution is claimed by this documentary task. Such claims require independently retained evidence.

## Parent

Decomposed from `MASTER-RECORDS-REPORTABLE-CHECKPOINT-001` / issue #2895.

## Reviewed implementation plan and vectors

The accepted machine-readable implementation plan is `docs/INTERLOCK_INTR_RUNTIME_INDEPENDENT_PROTOCOL_IMPLEMENTATION_PLAN_v1.json`. Synthetic non-authorizing conformance fixtures are in `test-vectors/interlock-intr-runtime-independent-protocol-v1.json` and cover ALLOW, DENY, FAIL_CLOSED, node identity, payload, predecessor/state, manifest intent, requested capability, receipt binding, and the first bounded `MasterRecordsCheckpoint/v1` profile.

Exact-head workflow evidence on the prior PR head demonstrated a missing `execution_substrate_resolution` for this documentary task. The task record now declares all runtime substrates NOT_APPLICABLE with no selected substrate. The prior test-suite ratchet also reported an unrelated/new registry-gate failure and one newly passing baseline test; fresh exact-head CI is required before attributing or repairing further defects.

No external adoption, external conformance, production interoperability, runtime execution, deployment, or merge is claimed.

## Next action

Re-observe PR state and fresh exact-head workflows after these repairs. Repair only demonstrated failures. Then trace existing Interlock/InTr and SDK surfaces against the specification without inventing missing runtime capabilities.
