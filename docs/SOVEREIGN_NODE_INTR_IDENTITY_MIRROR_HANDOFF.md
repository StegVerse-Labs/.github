# Sovereign Node InTr Identity Mirror Handoff

Updated: 2026-08-29
Repository: StegVerse-Labs/.github
Issue: #494
Branch: main

## Source of truth

This file is the current handoff and task source of truth for binding locally derived sovereign-node declarations to the canonical InTr route-materialization identity requirement.

## Source closure

```text
issue: #494 CLOSED
PR: #495
merge: 099d8c57e4433782c0282810645d1302d1e23a24
organization control-plane validation: 33293529857 SUCCESS
Heartbeat Worker Project validation: 33293529864 SUCCESS
scoped files fully developed: 100%
known scaffolding/stubs: 0
```

Both canonical v0.4 node-derivation paths now emit the same deterministic authority-neutral `SV-NODE-<24 hex>` identity. The exact derived marker is regression-tested through both evaluator and SV002 route materializers.

This closes the source compatibility defect. It does not establish a live sovereign node or receiver.

## Defect

The canonical v0.4 local node derivation paths can currently emit:

```text
schema: stegverse.sovereign-node-declaration/v0.4
declared: true
canonical_runtime_complete: true
durable_state_writable: true
credential_authority: TV/TVC
github_token_required: false
```

without any of:

```text
node_id
node_ref
boundary_identity_ref
```

The evaluator and StegVerse-002 observation route materializers both require one of those identity fields before creating a loopback route configuration. A lawfully derived node can therefore exist while both InTr routes remain stuck at:

```text
PREDICATE_PENDING: node boundary identity unavailable
```

## Canonical identity rule

For a derived local sovereign node, `node_id` is an authority-neutral stable identifier, not a credential, route grant, hardware attestation, or proof of runtime liveness.

Use the existing StegVerse Node identifier shape:

```text
SV-NODE-<24 lowercase hexadecimal characters>
```

Derive it deterministically from the exact non-secret local declaration basis:

```text
schema
source_root
state_root
canonical_carrier_runtime
continuity_model
credential_authority
```

using canonical JSON and SHA-256. The same exact basis must produce the same node ID across the bootstrap and repository-resolution derivation paths.

The identifier MUST NOT be derived from a secret, credential, GitHub token, wall-clock time, random value, or hosted execution artifact.

## Scope

Files authorized for this repair:

- `scripts/bootstrap_sovereign_runtime.py`
- `workers/sovereign_node_repository_resolution_worker.py`
- `tests/test_sovereign_node_derived_declaration.py`
- route-materialization regression tests
- `docs/SOVEREIGN_NODE_INTR_IDENTITY_MIRROR_HANDOFF.md`

## Required regression proof

1. Both v0.4 derivation paths emit the same deterministic `SV-NODE-...` identity for the same declaration basis.
2. Repeated derivation is stable.
3. Hosted execution remains ineligible.
4. Incomplete canonical runtime source remains ineligible.
5. A derived marker is accepted by evaluator InTr route materialization.
6. The same derived marker is accepted by SV002 observation route materialization.
7. Route configs continue to use loopback and preserve TV/TVC / GitHub-token-NONE authority boundaries.

## Non-claims

Source completion does not establish:

- a live sovereign node;
- G18 completion;
- resident WorkerCoordinator execution;
- evaluator receiver readiness;
- SV002 receiver readiness;
- public HTTPS reachability;
- an authentic external-node observation round trip.

## Remaining integration destinations

- node derivation/runtime: StegVerse-Labs/.github
- canonical InTr implementation: StegVerse-Labs/StegOS
- shared Service Gateway: StegVerse-org/LLM-adapter
- TV/TVC credential/TLS authority: StegVerse-Labs/TV + StegVerse-Labs/TVC
- Site observer/node surfaces: StegVerse-Labs/Site

No new credential authority, route authority, heartbeat, scheduler, or runtime is created by this task.


## Current observed state

```text
derived node identity source: MERGED / VALIDATED
evaluator route identity compatibility: MERGED / VALIDATED
SV002 route identity compatibility: MERGED / VALIDATED
live non-hosted node derivation: NOT OBSERVED
resident evaluator route materialization: NOT OBSERVED
resident SV002 route materialization: NOT OBSERVED
receiver readiness: NOT OBSERVED
public HTTPS round trip: NOT OBSERVED
user action required: false
```
