# StegVerse-002 Public Observation Runtime Mirror Handoff

Updated: 2026-08-29
Repository: StegVerse-Labs/.github
Issue: #462
Implementation PR: #474
Implementation merge: da1e5d1cd9761122e65c7be3b05fb24415d2abc6

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

## Merged machine-owned implementation

PR #474 merged the current-main implementation and passed both governing validation suites.

Canonical implementation includes:

- `scripts/serve_sv002_observation_intr_runtime.py`
- `scripts/materialize_sv002_observation_route_config.py`
- `scripts/consume_sv002_public_observation_request.py`
- `workers/sv002_public_observation_runtime_worker.py`
- `handoffs/SHWP-SV002-PUBLIC-OBSERVATION-RUNTIME-001.json`
- `control/worker-registry.d/sv002-public-observation-runtime-001.json`
- `control/process-worker-adapters.d/sv002-public-observation-runtime-001.json`
- `control/resident-execution-request.d/sv002-public-observation-runtime-001.json`
- `control/task-vectors/SHWP-SV002-PUBLIC-OBSERVATION-RUNTIME-001.json`
- sovereign bootstrap/native materialization/source-refresh registration
- resident request dispatcher registration
- shared Service Gateway loopback projection
- deterministic runtime/Gateway/materialization/COSV regression coverage

Source implementation, registration, materialization wiring, and Gateway projection are therefore no longer pending.

## Required projection sources

Only evidence-derived material may appear:

- authentic resident self-characterization execution artifacts;
- relationship/topology state derived from those artifacts;
- explicit AVAILABLE / DISCOVERABLE / ACCESSED / REFERENCED / USED / DERIVED knowledge evidence states;
- externally observable experiment events;
- manifest/receipt references;
- Master Records custody/reconstruction state when independently evidenced.

Missing evidence remains explicit. The runtime must not synthesize events or claim private chain-of-thought.

## Runtime request and authority

```text
task: SHWP-SV002-PUBLIC-OBSERVATION-RUNTIME-001
resident request: RESIDENT-EXEC-SV002-PUBLIC-OBSERVATION-RUNTIME-001
mode: TARGETED_INDEPENDENT_TASK_CONTROL
carrier trigger required: false
fresh fence required: true
second machine required: false
hosted execution allowed: false
network source fetch allowed: false
credential authority: TV/TVC
GitHub token runtime authority: NONE
```

The resident request is non-authorizing. It asks an already-authorized sovereign task-control runtime to refresh local source, materialize the route, and execute the bounded receiver task.

## Bounded live transport validation — 2026-08-29

Two validation-only execution proofs now exist on canonical source paths:

- StegVerse-Labs/.github PR #481 / merge `d67816930b5dcf63e44108fa6805513a9b597f17` launches the actual SV002 `BoundedHTTPServer`, sends a valid node-bound `SV002_PUBLIC_OBSERVE` request over a real loopback HTTP socket, observes a successful read-only response, verifies ingress `RECEIVED` and egress `FORWARDED` receipt lineage, persists the runtime bundle, and confirms `observer_direct_relation_to_stegverse_002=false`.
- StegVerse-org/LLM-adapter PR #230 / merge `be7e592b3cdb2d8f4781e5a2a23cad1d850b4463` sends an admitted SV002 request through the deployed Service Gateway FastAPI route to a real same-host loopback HTTP receiver and verifies exact request bytes plus admitted transport/authority headers are forwarded while credential headers are excluded.

These proofs establish:

```text
canonical SV002 receiver HTTP socket path: OBSERVED_BOUNDED_LIVE_VALIDATION
shared Service Gateway -> loopback forwarding: OBSERVED_BOUNDED_LIVE_VALIDATION
ingress/egress receipt construction over live receiver socket: OBSERVED_BOUNDED_LIVE_VALIDATION
production public Internet route: NOT OBSERVED
resident sovereign production-host receiver: NOT OBSERVED
authentic principal experiment execution: NOT OBSERVED
Master Records custody/reconstruction: NOT OBSERVED
```

CI execution remains validation-only and grants no runtime, experiment, custody, publication, or activation authority.

## Remaining machine-observable gates

The following are the actual unresolved gates after PR #474:

1. Sovereign resident source refresh observes the merged implementation.
2. `RESIDENT-EXEC-SV002-PUBLIC-OBSERVATION-RUNTIME-001` is consumed.
3. Route config materializes from a declared sovereign Node plus local StegOS and StegVerse-002 source roots.
4. `SV002_PUBLIC_OBSERVATION_RECEIVER_READY` is observed from the resident process.
5. Shared Service Gateway projects `/intr/sv002-observe` to the admitted loopback receiver.
6. A valid external StegVerse Node submits `SV002_PUBLIC_OBSERVE`.
7. Authentic InTr ingress receipt is observed with transition `RECEIVED`.
8. Authentic InTr egress receipt is observed with transition `FORWARDED`.
9. Observer direct relation to StegVerse-002 remains false.
10. Master Records custody/reconstruction is observed separately; it must not be inferred from receiver-local artifacts.
11. Authentic StegVerse-002 principal self-characterization execution remains a separate experiment gate.

## Current observed state

```text
Site public shell: MERGED (StegVerse-Labs/Site PR #666)
Site claim: RELEASED on main
receiver source: MERGED / VALIDATED (#474)
node genesis verification: MERGED / VALIDATED
read-only projection builder: MERGED / VALIDATED
ingress/egress receipt generation: MERGED / VALIDATED
shared Gateway route projection source: MERGED / VALIDATED
shared Gateway -> real loopback transport: OBSERVED_BOUNDED_LIVE_VALIDATION (#230)
resident persistent receiver source/control: MERGED / VALIDATED
receiver HTTP socket round trip: OBSERVED_BOUNDED_LIVE_VALIDATION (#481)
resident request consumption receipt: NOT OBSERVED
receiver readiness: NOT OBSERVED
public deployed round trip: NOT OBSERVED
authentic ingress receipt: NOT OBSERVED
authentic egress receipt: NOT OBSERVED
authentic resident self-characterization run: NOT OBSERVED
Master Records reconstruction: NOT OBSERVED
```

Checked-in worker runtime state is not activation evidence and currently remains historical/stale relative to the new request. Source, CI, merge, deployment, or request registration must never be treated as authentic observation.

## Next authorized machine action

The next authorized action is to continue the sovereign resident path until the request-consumption and receiver-readiness receipts exist. No second machine or manual credential entry is part of this task contract.


## Persisted round-trip integrity hardening — issue #498

The resident worker's terminal evidence scan must not trust a terminal-looking local JSON object by state label alone.

Issue #498 hardens `workers/sv002_public_observation_runtime_worker.py` so a persisted bundle can satisfy `SV002_PUBLIC_OBSERVATION_ROUND_TRIP_OBSERVED` only after independent local validation of:

```text
bundle schema = stegverse.sv002-public-observation-runtime-receipt-bundle/v1
state = SV002_PUBLIC_OBSERVATION_ROUND_TRIP_FORWARDED
observer_direct_relation_to_stegverse_002 = false
credential_authority = TV/TVC
authority_effect = NONE
request_sha256 = canonical lowercase SHA-256
observer node/interlock identity present
registration receipt SHA-256 present
ingress schema = stegverse.intr.hop_receipt/v1
ingress transition = RECEIVED
ingress boundary = DEVICE_SYSTEM -> STEGOS_ECOSYSTEM
egress schema = stegverse.intr.hop_receipt/v1
egress transition = FORWARDED
egress boundary = STEGOS_ECOSYSTEM -> DEVICE_SYSTEM
both boundary_verification = VERIFIED
both secret_plaintext_present = false
both authority_transfer = false
both receipt hashes recompute exactly
egress.prior_receipt_hash = ingress.receipt_hash
```

Corrupt, fabricated, authority-smuggling, or lineage-broken persisted evidence fails closed and cannot terminalize the resident worker.

Scoped implementation files:

- `workers/sv002_public_observation_runtime_worker.py`
- `tests/test_sv002_public_observation_runtime_worker.py`
- `docs/SV002_PUBLIC_OBSERVATION_RUNTIME_MIRROR_HANDOFF.md`

This source hardening is not resident runtime evidence and does not change the remaining authentic observation gates.
