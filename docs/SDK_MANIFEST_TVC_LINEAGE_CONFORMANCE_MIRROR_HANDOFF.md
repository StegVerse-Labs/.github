# SDK-MANIFEST-TVC-LINEAGE-CONFORMANCE-001 — Mirror Handoff

Updated: 2026-10-07
Goal Task ID: `SDK-MANIFEST-TVC-LINEAGE-CONFORMANCE-001`
Parent Task ID: `SDK-GENERIC-MANIFEST-ECOSYSTEM-INVARIANT-005`
COSV ID: `71000000100122`
Status: `ACTIVE / CHECKED_OUT`

## Goal

Implement and validate the existing-owner TVC source repair so provider operations inherit a non-caller-editable SDK manifest lineage binding and TVC validates, but never selects, processing capability/route before credential-bearing execution.

## Inherited invariants

- Every ACTION is a manifest-bound state transition.
- Processing semantics are selected only by admitted `processing.capability` + `processing.route_id` and installed route resolution.
- Terminal attempted-boundary disposition is `ALLOW | DENY | FAIL_CLOSED`.
- Organization ledger append is runtime reality when Organization state changes.
- Master Records is limited to organization records and reconstruction evidence and never gates Organization runtime reality.
- No external machine, listener, session, receiver liveness, hosted service, scheduler, or later observer may be awaited as a transition/completion predicate.
- Receiver unavailability follows `DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION`.

## Remaining predicates

- `TVC_PROVIDER_BOUNDARY_CLASSIFIED_AND_CONFORMANT`

## Completion discipline

Close only from exact source/runtime evidence appropriate to each predicate. Source/CI/merge evidence must not be promoted to runtime execution. Preserve historical evidence and use registered exemptions only for genuine nonconformance that cannot be repaired; reachability is not an exemption justification.


## 2026-10-07 implementation

Architecture clarification is controlling: there is no framework-specific adapter/lane that selects testing or experimental semantics. The manifest determines processing/testing/experiment parameters regardless of framework or provider. Provider/framework identity is provenance only.

TVC PR #482 merged as `248eb6df0986055bab88ee37231feb3891da49bc` from exact head `ac10d1c0906ebeb3c9de068e6a036e0cd9e857de`. TVC now requires an exact `sdk_manifest_binding` in both the provider request and single-use capability lease before credential-bearing forwarding. The binding contains only `request_sha256`, `canonical_manifest_sha256`, `processing_capability`, and `route_id`; TVC validates equality/shape and does not interpret those values to select a provider, framework, capability, route, test, or experiment.

The Universal manifest ingress now owns a generic `bind_tvc_provider_request` projection. It first validates the SDK manifest-state-transition request and then overwrites any caller-supplied binding in both request and lease with the four authenticated manifest-lineage fields. No framework-named worker is the semantic owner of this projection.

TVC exact head exposed zero GitHub workflow runs and zero combined status checks, so no CI-green claim is made. Added source regressions cover missing/mutated lineage fields and prove capability/route values are validation-only at TVC.

