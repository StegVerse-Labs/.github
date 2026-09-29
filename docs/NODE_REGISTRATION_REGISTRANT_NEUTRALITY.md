# Node registration is registrant-neutral

A device is **interchangeable** — `physical_device_identity_gate` is
`NONE_PROHIBITED` and `device_identity_is_execution_metadata_only` is true — and
a node confers **no authority**: `node_user_verifier_authority`,
`device_user_verifier_authority` and `transport_user_verifier_authority` are all
NONE, with `user_verification_authority` exclusively the KV/SKAP Vault.

Those two facts together leave nothing that could distinguish one registrant
from another. A browser device, an external framework that is an endpoint of
data transport, and another custody ecosystem present the same binding receipt
and receive the same standing. **There is no separate mechanism for external
frameworks, and none is needed.**

## `web_device` in the names is historical

The genesis receipt is `stegos.web_device_node_binding_receipt.v1` and its
counterpart field is `device_continuity_id`. Both names date from when the only
registrant was a browser device. **Neither is a constraint.**

`node_id` and `device_continuity_id` are **opaque equality keys**. They are
threaded from the genesis binding receipt through each package materialization
receipt, the aggregate receipt and the materialization proof, and compared only
against each other. Nothing parses them, and nothing checks their shape.
`tests/test_node_registration_registrant_neutrality.py` registers a framework,
a custodian and an identifier with no prefix at all, and all three validate
identically to the browser device.

The names are deliberately left alone. Retained genesis receipts carry the
schema string, so renaming it would mean either accepting two strings forever or
invalidating existing evidence — a better name bought with a permanent
compatibility branch. The receipts are the asset; the name is not.

## The one format constraint, and why it is not a gate

`workers/sv_dn1_browser_evidence_intr_ingress.py` requires a `stegnode-web-`
prefix and a `stegdevice-` prefix. Two lines above, it also requires
`observation_class == "AUTHENTIC_ESTABLISHED_STEGVERSE_WEB_NODE"`. It is a
browser validator legitimately insisting on browser identities within its own
observation class, not a general registration gate, and a registrant that is not
a browser never traverses browser evidence ingress. No other worker constrains
the shape of a node identity; the test asserts that, so the scoping cannot be
lost by a later edit.

## Registration is orthogonal to admission

Registration produces a binding receipt carrying `authority_effect: NONE` and
lands in `MATERIALIZED_UNADMITTED`. Admission is a separate Interlock/InTr
decision taken **per transition**, not per registrant.

This is why open registration costs nothing: the act confers no authority, so
there is nothing to gate at registration time. What a registrant may actually do
is decided transition by transition, on evidence, every time — and
transportability, the capability registration does confer, is a node capability
rather than a property of any device.

It also means the curated list of inbound signals from unknown external
frameworks is the node registry itself. Because genesis is a receipted
transition, that list is **reconstructable rather than maintained**.

## Boundary

This document records properties of existing behaviour. It installs nothing,
registers nothing, admits nothing and grants no authority. The accompanying test
is source validation only.
