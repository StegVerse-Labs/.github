# StegVerse-002 Public Observation Runtime Mirror Handoff

Updated: 2026-08-29
Issue: #462

## Canonical machine owner

```text
task: SHWP-SV002-PUBLIC-OBSERVATION-RUNTIME-001
worker: workers/sv002_public_observation_runtime_worker.py
server: scripts/serve_sv002_observation_intr_runtime.py
route materializer: scripts/materialize_sv002_observation_route_config.py
resident request: control/resident-execution-request.d/sv002-public-observation-runtime-001.json
consumer: scripts/consume_sv002_public_observation_request.py
handoff: handoffs/SHWP-SV002-PUBLIC-OBSERVATION-RUNTIME-001.json
public TLS: STEGVERSE_SHARED_SERVICE_GATEWAY
credential authority: TV/TVC
hosted runtime: forbidden
second machine: not required
```

## Governing invariant

The public URL shell is not data authority.

```text
valid viewer StegVerse Node Receipt #1
-> SV002_PUBLIC_OBSERVE manifest
-> Interlock / InTr ingress
-> read-only observation projection
-> InTr egress
-> viewer Node

no valid Node => no experiment data
```

Observer traffic terminates at the read-only projection. It does not create a direct interaction relationship with StegVerse-002.

## Evidence derivation

The projection may derive only from authentic resident evidence when present:

```text
receipts/sv002-self-characterization/SHWP-SV002-SELF-CHARACTERIZATION-001.json
<worker state_root>/EXPERIMENT_EXECUTION_RECEIPT.json
<worker state_root>/INTERACTION_RECEIPT_CHAIN.json
<worker state_root>/SELF_CHARACTERIZATION.md
<worker state_root>/SELF_CHARACTERIZATION_FORMAL.json
StegVerse-002/micro-node-runtime/experiments/self-characterization-001/CONSTRUCTION_PROVENANCE.v0.1.json
```

Missing evidence remains `NOT_OBSERVED`. Master Records reconstruction is not inferred from local experiment artifacts.

## Node validation

The viewer supplies its complete Node Receipt #1. The receiver independently recomputes the canonical SHA-256 and requires:

- schema `stegos.node_handoff_receipt.v1`;
- receipt number 1 / `NODE_REGISTERED`;
- `continuity_parent=GENESIS`;
- exact node/interlock/registration digest binding;
- `credential_authority=TV/TVC`;
- `authority_effect=NONE`.

Only then may the read-only projection be returned.

## Materialization and dispatch

The observation consumer/server/materializer are explicitly included in:

- native sovereign runtime materialization;
- local source refresh;
- sovereign bootstrap required-source checks;
- resident request dispatcher;
- source-refresh regression tests.

This prevents a merged-source-only state where the resident runtime knows about a task but lacks its executable consumer.

## Current state

```text
source receiver: IMPLEMENTED_ON_BRANCH
Node validation: IMPLEMENTED_ON_BRANCH
projection from authentic resident artifacts: IMPLEMENTED_ON_BRANCH
worker/control ownership: IMPLEMENTED_ON_BRANCH
resident request: IMPLEMENTED_ON_BRANCH
materialization/dispatch integration: IMPLEMENTED_ON_BRANCH
receiver readiness: NOT OBSERVED
authentic viewer round trip: NOT OBSERVED
public Gateway route: NOT YET PROVEN
public Site receipt pair: NOT OBSERVED
```
