# GADI-001 — Network-Native Defense Mirror Handoff

Status: `NOT_RETIRED / STEGOS_NETWORK_NATIVE_DEFENSE_FABRIC_MERGED / MINIMAL_DEVICE_SUBSTRATE_DIRECTION_ACTIVE / AUTHENTIC_ACTIVATION_PENDING`
Repository: `StegVerse-Labs/.github`
Canonical task: `GADI-001`
Parent handoff: `docs/GADI_MIRROR_HANDOFF.md`
COSV ID: `10100000100000`

## Canonical architectural direction

StegOS is a platform-, OS-, and device-agnostic governed operating environment. It is not defined as a replacement host OS and must not require the complete StegOS/GADI runtime to be installed on every endpoint.

Canonical layering:

```text
host OS / device
-> minimal StegOS Device Substrate
-> StegOS Resident Fabric
-> StegOS Ecosystem Services
```

The network is a defensive capability multiplier, not merely transport. It may contribute attributable observations, correlated evidence, TV/TVC-backed capability advertisements, eligible execution surfaces, topology, custody/provenance, InTr state, historical receipted outcomes, controlled simulation evidence, and current resource state.

## Merged StegOS evidence

StegOS PR #235 merged as `21efc7c03d4f13708f1f81d3a36ed18f12e7ed6a` after all four exact-head checks passed on `2e6cded44ce474167efd5c5939d92cec90d46cc5`.

Merged artifacts:

- `StegVerse-Labs/StegOS/docs/GADI_NETWORK_NATIVE_DEFENSE_FABRIC.md`
- `StegVerse-Labs/StegOS/data/gadi-network-native-defense-fabric-contract.json`
- `StegVerse-Labs/StegOS/tests/test_gadi_network_native_defense_fabric_contract.py`
- updated `StegVerse-Labs/StegOS/docs/GADI_STEGOS_MIRROR_HANDOFF.md`

The exact-head check set included repository tests plus the existing GADI capability-discovery, native defensive-control-plane, and boundary-defense validation lanes.

## Defensive opportunity graph

The Resident Fabric should maintain a bounded current set of candidate defensive paths combining observation, provenance, governed capability, execution-surface, admission, effect-observation, reassessment, and reconstruction elements.

Consequential candidate paths remain fail-closed unless all required authority evidence is present. Network popularity, peer count, discovery presence, or model confidence never substitutes for InTr admission or TV/TVC capability authority.

## Selection objective

StegOS should prefer, in order:

1. preservation of human life / prevention of imminent severe harm;
2. least-destructive effective intervention;
3. minimum scope and blast radius;
4. reversible action when comparably effective;
5. strongest attributable evidence;
6. pre-authorized organization-controlled execution surfaces;
7. minimum unnecessary data disclosure/movement;
8. continuous observability, receiptability, and reconstructability;
9. termination or relaxation as soon as the defensive predicate clears.

## Device Substrate consequence

Platform-specific work should implement only the host-native primitives that must exist at the physical boundary: device/node identity binding, KV attachment, available observation hooks, local fail-closed enforcement where the host exposes an eligible surface, receipt/journal buffering, transport/discovery participation, and capability-manifest verification.

StegOS issue #233 has been re-scoped accordingly to `minimal iOS Device Substrate defensive parity`. Do not port the entire Python GADI planner/runtime into Swift merely for parity.

## Offline rule

Network-native must not mean network-dependent. An isolated Device Substrate retains identity/KV relationship, cached fail-closed predicates, bounded pre-authorized local behavior, and local journaling, while refusing to invent unavailable network authority; state is reconciled when the Resident Fabric becomes reachable again.

## Authority split

- StegOS: observation correlation, defensive opportunity graph, native ability selection, governed command materialization.
- StegCore: threat reasoning and intervention planning where invoked.
- WorkerCoordinator: work claims/fences.
- InTr/StegGate: consequential transition admission.
- TV/TVC: credential/capability authority.
- resident runtime: effect execution and closed-loop reassessment.
- Continuity/Master Records: custody, receipts, observed reality, exact reconstruction.

## Remaining implementation

1. expand capability advertisements with freshness, locality, scope, custody, and execution-surface metadata;
2. move GADI planning from a single selected capability to multiple candidate paths with deterministic least-destructive-effective selection;
3. implement/verify minimal Device Substrate parity on iOS issue #233;
4. bind resident runtime consumption and distributed effect observations;
5. implement confrontation receipts/reconstruction;
6. prove authentic controlled end-to-end activation.

Source/CI does not prove runtime activation.
