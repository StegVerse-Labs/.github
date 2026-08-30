# Sovereign Node InTr Identity Mirror Handoff

Updated: 2026-08-29
Repository: StegVerse-Labs/.github
Issue: #494
Branch: fix/sovereign-node-intr-identity-494

## Source of truth

This file is the current handoff and task source of truth for binding locally derived sovereign-node declarations to the canonical InTr route-materialization identity requirement.

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
