# StegVerse-002 Public Observation Runtime Mirror Handoff

Updated: 2026-08-29
Repository: StegVerse-Labs/.github
Issue: #462
Branch: feat/sv002-public-observe-runtime-462

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

The public URL may be reachable, but experiment data is delivered only after a valid StegVerse Node genesis receipt is independently verified and the request is admitted through the canonical Interlock/InTr path.

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

## Required projection sources

Only evidence-derived material may appear:

- authentic resident self-characterization execution artifacts;
- relationship/topology state derived from those artifacts;
- explicit AVAILABLE / DISCOVERABLE / ACCESSED / REFERENCED / USED / DERIVED knowledge evidence states;
- externally observable experiment events;
- manifest/receipt references;
- Master Records custody/reconstruction state when locally available.

Missing evidence remains explicit. The runtime must not synthesize events or claim private chain-of-thought.

## Machine-owned implementation

Target files:

- scripts/serve_sv002_public_observation_runtime.py
- tests/test_sv002_public_observation_runtime.py
- docs/SV002_PUBLIC_OBSERVATION_RUNTIME_MIRROR_HANDOFF.md

The runtime is loopback by default and is intended to sit behind the existing shared Service Gateway. A second public TLS surface is not created.

## Remaining files/modules or installation destinations

- Shared Gateway route projection -> StegVerse-Labs/.github
- Resident execution request / persistent receiver lifecycle -> StegVerse-Labs/.github
- Public Site connector deployment observation -> StegVerse-Labs/Site
- Canonical experiment artifacts -> StegVerse-002/micro-node-runtime
- Custody/reconstruction projection -> master-records/orchestration
- Post-release propagation verification -> GCAT-BCAT-Engine/Publisher, StegVerse-Labs/admissibility-wiki, StegVerse-002/stegguardian-wiki

## State

```text
Site public shell: MERGED (StegVerse-Labs/Site PR #666)
receiver source: IN_PROGRESS
node genesis verification: IN_PROGRESS
read-only projection builder: IN_PROGRESS
ingress/egress receipt generation: IN_PROGRESS
shared Gateway route: PENDING
resident persistent receiver: PENDING
public deployed round trip: NOT OBSERVED
authentic resident self-characterization run: NOT OBSERVED
Master Records reconstruction: NOT OBSERVED
```

Source, CI, merge, or deployment must not be treated as authentic observation.
