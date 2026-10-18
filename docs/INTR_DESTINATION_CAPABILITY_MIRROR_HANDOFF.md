# InTr Destination Capability Mirror Handoff

**Repository:** `StegVerse-Labs/.github`
**Mirrors:** [StegVerse-org/.github#175](https://github.com/StegVerse-org/.github/pull/175)
**Coordinating issue:** [StegVerse-Labs/.github#2897](https://github.com/StegVerse-Labs/.github/issues/2897)
**Capability:** `intr-destination` / `InTr:Destination` / `DIAGNOSTIC_CROSSING`
**Address:** `stegverse-labs.intr-destination` → `ORGANIZATION_INTR_DESTINATION_INGRESS`
**Operation:** `resident-runtime/intr_destination_ingress.py`
**Boundary document:** `org-runtime/interlock-intr.json` → `ingress.capability_endpoint_bindings`, `egress.peer_capability_resolution`
**Status:** ADVERTISED_AND_SERVED_HERE_PEER_INSTALLATION_UNPROVEN

## 2026-10-17 conformance reconciliation

Read at main `5b3fc476`. This section changes no code. The goal handoff is `docs/INTERLOCK_INTR_RUNTIME_INDEPENDENT_PROTOCOL_MIRROR_HANDOFF.md`, and the coordinating issues are [#2897](https://github.com/StegVerse-Labs/.github/issues/2897) and StegVerse-org/.github#162.

- **No Task ID of its own.** This capability is tracked under `INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001` until the Registry owner registers it, either there or as a child task.
- **`close` returns a bare `PENDING`.** In `resident-runtime/organization_egress_boundary.py`, `close()` (L800–826) returns `disposition: PENDING`, with no six fields and no durable-queue disposition, when no response is in the mesh. A caller that wants a closure has to call again, which is a poll. Conformance items 3 and 5 require the unavailable receiver to be answered by `DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION`, and a bare status is not a finding. Not recording an absence on the ledger is still correct.
  - `failure_code`: `CLOSE_ABSENCE_RETURNS_BARE_PENDING`
  - `failed_predicate`: `UNAVAILABLE_RECEIVER_ANSWERED_BY_DURABLE_QUEUE_WITH_SIX_FIELDS`
  - `required_evidence_or_repair`: the no-response branch returns `DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION` with the six fields (`next_attempt` names the response-frame arrival event, not a clock or a poll), still records nothing on the ledger, and has a regression test. The same change goes to the org twin and the hop branches.
  - `retry_entrypoint`: `resident-runtime/organization_egress_boundary.py::close`
  - `owning_existing_goal`: `INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001`
  - `next_attempt`: Lane B's next six-field PR (#3213 or a follow-up)
- **The fabricated far side stays test scaffolding.** The fabricated temporary-mesh far side described above must not become a required runtime component.

## Why this capability exists

A peer could be addressed at a purpose route — governance — or at
`org-control`. Neither is a universal destination. Governance is decided by
the organization that owns StegCore. `org-control` answers a control message.
A diagnostic that only asks whether an organization is reachable as an InTr
destination had to borrow one of those, and a borrowed purpose route reads as
that purpose.

`intr-destination` is the mesh primitive those routes sit on. Every
organization can advertise it. A crossing that uses it is a purpose-neutral
diagnostic: an `ecosystem.communication` whose body schema is
`stegverse.org-intr-destination-diagnostic/v1`. It acknowledges. It does not
govern, classify, admit, route, or execute.

## What is declared here

The overlay remains the single authority. One binding, owned here, granting
nothing:

```text
profile_id     intr-destination
profile_name   InTr:Destination
operation      DIAGNOSTIC_CROSSING
reader         ECOSYSTEM_COMMUNICATION
address        stegverse-labs.intr-destination
role           BOUNDARY_LOCAL_CAPABILITY_INGRESS
operation_id   ORGANIZATION_INTR_DESTINATION_INGRESS
authority      NONE_BINDING_ONLY
```

`address_grants_admission_authority` and `selects_processing_at_this_address`
are false on the registry row and on the binding. An address cannot grant
itself the capability: `capability_ingress.receive` refuses a row the overlay
does not name, and it refuses a module whose `OPERATION_ID` is not the one the
binding publishes.

The profile name is local. The pinned SDK subsystem baseline does not declare
it, and `StegVerse-Labs/StegOS` `specs/universal-intr-connector-profiles.v1.json`
was not readable when this binding was added. This repository therefore does
not claim the canonical connector registry already named `InTr:Destination`.
The declaration owner is `StegVerse-Labs/.github`.

`SUBMIT_MANIFEST` still uses the manifest reader. The diagnostic names
`ECOSYSTEM_COMMUNICATION`, so a communication is not refused for lacking a
manifest and a manifest is not accepted as a diagnostic. The validator refuses
a non-manifest operation that tries to inherit the manifest reader.

Labs dispatch previously refused `BOUNDARY_LOCAL_CAPABILITY_INGRESS` as an
uninstalled endpoint adapter. Serving the address required the kernel to
resolve that role through `capability_ingress.receive`. The receiving
operation records both ledger levels itself. The kernel does not write a
second federation-crossing receipt for the same frame. A refusal at this
address is raised, not swallowed as a federation refusal, because the
operation records its own refusal.

The organization append owner is `aggregate_transition`, the same owner the
manifest ingress uses. The binding names that function.

## What a peer address is

`resolve_destination(peer, capability="intr-destination")` derives
`organization_slug(peer) + "." + "intr-destination"`. That is the same rule as
`sdk-manifest-ingress`. Peer capability services are not written into
`federation.json`. `peer_serves_this_capability_is_proven_here` stays false at
resolution. An unserved address does not close.

`proven_on_this_organization` names every capability address **this**
organization serves:

```text
stegverse-labs.sdk-manifest-ingress
stegverse-labs.intr-destination
```

A string still names the one address a single-capability organization serves.
Two addresses are a list, because a string can name only one and naming one of
two would understate what is served here. A peer address in that list is
refused. The field is not a peer map. `stegverse-org.intr-destination` is
derived when Labs emits outbound. It is not listed as proven here.

## What the crossing proves

| | |
| --- | --- |
| This organization advertises and serves the address | yes — a frame published by StegVerse-org at `stegverse-labs.intr-destination` is consumed and receipted at both ledger levels |
| The acknowledgement grants authority | no |
| A peer address is derived, not enumerated | yes — outbound emission addresses `stegverse-org.intr-destination` |
| The peer installed the receiving operation | **not proven at resolution** |
| Something at the addressed service ran this packet | yes, **at closure**, when the far-side terminal receipt recomputes |
| Which organization that boundary belongs to | **no** |
| The far side persisted the chain on its own ledger | **no** |
| No answer is a close | no — `close` returns `PENDING` and writes nothing |

The unit test's far side is this repository's `kernel.receipt` and
`build_control_response`, the same stand-in the governance route uses. That is
a fabricated answer in a temporary mesh. It is not a live peer, and it is not
an authentic production receipt.

`capability_destination_bindings` are unchanged: `governance` and
`governance-to-org`. Those remain purpose routes. This change does not add a
remediation destination binding.

## Verified

`tests.test_intr_destination_capability` covers the declaration, the overlay
fail-closed miswires, derived resolution, the refused undeclared capability,
receipt of a diagnostic at this address, emit `ALLOW`, close `PENDING` with no
answer, and close `ALLOW` when the fabricated far side answers.

`org-runtime/runtime_boundary.py validate` includes `capability_addresses_resolve`
and `peer_capability_addresses_derive`.

Both ledger roots in the unittest and in CI are redirected. The mesh is a
temporary directory.

## What other organizations do next

StegVerse-org/.github#175 is the template this repository mirrors. Other
federation organizations mirror the same binding in their own `.github`
repositories. This change does not install the capability for them, and it
does not claim they already serve it.

Nothing here grants authority.
