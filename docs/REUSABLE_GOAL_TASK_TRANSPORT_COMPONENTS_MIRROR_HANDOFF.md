# Reusable Goal Task Transport Components Mirror Handoff

Updated: 2026-09-12
Consuming Goal Task: `SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004`
COSV: `71000000100110`
Status: `ACTIVE / SOURCE COMPONENTIZATION PROPOSED / VALIDATION PENDING`

## Decision

The transport architecture is not one mandatory monolithic pipeline. It is a reusable component library composed from the transport needs declared by the consuming canonical Goal Task.

The previously expressed end-to-end sequence:

```text
Complete manifest
-> governed processing
-> required governed round trips
-> evidence/custody/reconstruction
-> Publisher
-> SDK return assembly
-> final StegVerse-side egress transition
-> Interlock/InTr
-> far-side final transition
```

is now treated as the **maximal composition**, not the minimum path every task must implement.

## Canonical reusable components

1. `RTC-MANIFEST-001` — Manifest Intake and Binding
2. `RTC-GOVERNED-PROCESSING-002` — Governed Processing
3. `RTC-ROUNDTRIP-003` — Governed Round Trip, repeatable as the Goal Task requires
4. `RTC-EVIDENCE-CUSTODY-004` — Evidence Custody and Reconstruction
5. `RTC-PUBLISHER-005` — Publisher Projection, optional
6. `RTC-SDK-RETURN-006` — SDK Return Assembly, optional
7. `RTC-STEGVERSE-EGRESS-007` — StegVerse-side Final Egress Transition
8. `RTC-INTERLOCK-INTR-TRANSPORT-008` — Interlock/InTr Transport, repeatable where transitions require it
9. `RTC-FARSIDE-FINAL-009` — Far-side Final Transition, optional

Canonical source contract:

```text
data/reusable-transport-component-contract.json
```

## Goal Task consumption rule

Each canonical Goal Task that needs data transport declares a `transport_requirements` projection and selects only the reusable components required to satisfy that goal.

Examples:

```text
internal governed processing:
  manifest + governed processing + evidence/custody/reconstruction

external SDK/framework round trip:
  manifest + governed processing + round trip(s) + evidence/custody/reconstruction
  + SDK return + StegVerse egress + Interlock/InTr + far-side final transition

publication/distribution:
  manifest + governed processing + evidence/custody/reconstruction
  + Publisher + StegVerse egress + Interlock/InTr + far-side final transition
```

The current Goal Task profile is:

```text
data/goal-task-transport-profiles/SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004.json
```

It selects the maximal composition because this goal includes external collaboration, required resident/provider round trips, SDK return, public distribution, governed egress, and a far-side transition.

## Authority invariants

Component reuse creates no new authority and does not collapse existing authority roles.

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority.
- KV/SKAP Vault: sole user-verification authority.
- StegOS devices: interchangeable transport nodes, not user verifiers.
- TV/TVC: credential/provider/release authority.
- Interlock/InTr: governed transition and packet-movement authority.
- Master Records: observed reality, custody, and reconstruction authority.
- HeartBeat: timing/freshness/correlation/carriage only.
- GitHub: no runtime authority.

A prior component receipt proves that component's prior transition or observation only. It does not authorize the next component.

## Composition semantics

`RTC-ROUNDTRIP-003` and `RTC-INTERLOCK-INTR-TRANSPORT-008` may appear multiple times in one Goal Task. The number and placement of those repetitions come from the Goal Task's declared transport requirements, not from a hard-coded global sequence.

Publisher, SDK Return Assembly, and Far-side Final Transition are optional. Their omission from a Goal Task that does not need them is correct and must not be treated as an incomplete transport chain.

A missing component that the Goal Task explicitly requires fails closed. A component that the Goal Task does not require must not be added merely because another task used it.

## Current task projection

For `SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004`, the profile declares these round trips:

```text
resident_client_secret_reseal
resident_consent_listener
sovereign_callback
owner_present_provider_consent
authoritative_provider_file_probe
```

This projection is coordination/source architecture only. It does not claim that any authentic resident runtime, provider operation, custody readback, callback, consent, publication, egress, or far-side transition has occurred.

## Validation still required

The source componentization must pass the repository's deterministic validation lanes before merge. Runtime proof remains separately governed by the active task's existing authentic-observation predicates.

## README impact

The root README requires a concise architecture note pointing to the reusable component contract once the change is merged. No runtime capability claim should be added.

## Human action

None.
