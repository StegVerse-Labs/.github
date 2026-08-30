# StegVerse-002 Public Observation Runtime Mirror Handoff

Updated: 2026-08-29
Repository: StegVerse-Labs/.github
Issue: #462

## Source of truth

This file is the current handoff and task source of truth for the sovereign receiving side of the StegVerse-002 public observation lane.

## Governing contract

```text
request schema: stegverse.sv002.public_observation.interlock_request.v1
request_class: SV002_PUBLIC_OBSERVE
operation: READ_OBSERVATION
transport: InTr
credential_authority: TV/TVC
github_token_runtime_authority: NONE
authority_effect: NONE
```

The public URL may be reachable, but experiment data is delivered only after a valid StegVerse Node genesis receipt is independently verified and the request is admitted through canonical Interlock/InTr.

```text
valid StegVerse Node
-> shared StegVerse Service Gateway
-> canonical InTr ingress
-> sovereign SV002 public-observation runtime
-> read-only evidence projection
-> canonical InTr egress
-> observer browser

no valid Node => no experiment data
```

Observer traffic terminates at the read-only observation projection. It does not become a direct experimental interaction with StegVerse-002.

## Canonical implementation

The canonical runtime implementation is:

- `scripts/serve_sv002_observation_intr_runtime.py`
- `workers/sv002_public_observation_runtime_worker.py`
- `scripts/materialize_sv002_observation_route_config.py`
- `scripts/consume_sv002_public_observation_request.py`
- `control/resident-execution-request.d/sv002-public-observation-runtime-001.json`
- `control/worker-registry.d/sv002-public-observation-runtime-001.json`
- `control/process-worker-adapters.d/sv002-public-observation-runtime-001.json`
- `handoffs/SHWP-SV002-PUBLIC-OBSERVATION-RUNTIME-001.json`
- `tests/test_sv002_public_observation_runtime.py`

The runtime is loopback-only under the current route materializer and sits behind the existing shared Service Gateway. No second public TLS surface is created.

The earlier `scripts/serve_sv002_public_observation_runtime.py` implementation was a superseded duplicate and is removed by the canonicalization follow-on. Runtime ownership, bootstrap/source refresh, resident dispatch, worker registration, and Gateway projection all point to `serve_sv002_observation_intr_runtime.py`.

## Required projection sources

Only evidence-derived material may appear:

- authentic resident self-characterization execution artifacts;
- relationship/topology state derived from those artifacts;
- explicit AVAILABLE / DISCOVERABLE / ACCESSED / REFERENCED / USED / DERIVED knowledge evidence states;
- externally observable experiment events;
- manifest/receipt references;
- Master Records custody/reconstruction state when locally available.

Admissible-Existence is known as AVAILABLE from construction provenance when that provenance is present. It remains NOT_CONNECTED unless an authentic Interlock relationship is separately evidenced.

Missing evidence remains explicit. The runtime must not synthesize events or claim private chain-of-thought.

## Current machine state

```text
Site public shell: MERGED (StegVerse-Labs/Site PR #666)
receiver source: MERGED
node genesis verification: IMPLEMENTED
read-only projection builder: IMPLEMENTED
ingress/egress receipt generation: IMPLEMENTED
shared Gateway route projection: IMPLEMENTED
resident route materializer: IMPLEMENTED
resident execution request: REGISTERED
persistent receiver worker: REGISTERED
resident request dispatcher binding: IMPLEMENTED
bootstrap/source-refresh carriage: IMPLEMENTED
public deployed round trip: NOT OBSERVED
authentic resident self-characterization run: NOT OBSERVED
Master Records reconstruction: NOT OBSERVED
```

Readiness is not inferred from source. `SV002_PUBLIC_OBSERVATION_RECEIVER_READY` requires an authentic resident process and readiness receipt. Terminal completion requires `SV002_PUBLIC_OBSERVATION_ROUND_TRIP_OBSERVED` with authentic ingress/egress evidence and `observer_direct_relation_to_stegverse_002=false`.

## Remaining files/modules or installation destinations

- Authentic resident receiver readiness and round trip -> StegVerse-Labs/.github sovereign runtime
- Public Site connector deployment observation -> StegVerse-Labs/Site
- Canonical principal experiment artifacts -> StegVerse-002/micro-node-runtime
- Custody/reconstruction projection -> master-records/orchestration
- Post-release propagation verification -> GCAT-BCAT-Engine/Publisher, StegVerse-Labs/admissibility-wiki, StegVerse-002/stegguardian-wiki

## Next machine-owned sequence

```text
resident dispatcher consumes SV002 public observation request
-> materialize non-secret loopback route config
-> acquire fresh independent-task-control fence
-> start/confirm persistent loopback receiver
-> observe /intr/sv002-observe/readiness READY
-> shared Service Gateway projects the route
-> valid Site StegVerse Node submits SV002_PUBLIC_OBSERVE
-> persist ingress RECEIVED + egress FORWARDED receipt bundle
-> mark SV002_PUBLIC_OBSERVATION_ROUND_TRIP_OBSERVED
-> separately ingest authentic principal artifacts / Master Records reconstruction
```

No second user machine, GitHub credential, hosted runtime, or third-party execution substrate is authorized or required by this lane.

Source, CI, merge, deployment, or receiver readiness must not be treated as authentic experiment execution or as the final public observation round trip.
