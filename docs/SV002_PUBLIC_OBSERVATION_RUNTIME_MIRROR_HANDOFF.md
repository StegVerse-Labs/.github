# StegVerse-002 Public Observation Runtime Mirror Handoff

Updated: 2026-08-31
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


## Event-ephemeral receiver activation — issue #493

Issue #493 removes an always-on receiver / G18-completion prerequisite from the public observation transport initiation path.

Canonical transition:

```text
valid observer StegVerse Node
-> build exact Universal InTr transport intent
-> build non-authorizing materialization request
-> persist request in Node local outbox
-> deliver exact outbox trigger to sovereign /intr/materialization ingress when available
-> ingress validates Node/outbox/request hashes and persists exact request
-> resident event consumer invokes the already-admitted independent task-control lane
-> route materialization occurs from already-local sovereign roots
-> receiver process is started only when needed
-> receiver READY is downstream evidence, not a request prerequisite
-> original exact observation request may be retried
-> authentic ingress RECEIVED + egress FORWARDED receipts remain terminal evidence requirements
```

Required invariants:

```text
event_triggered = true
always_on_receiver_required = false
g18_completion_required = false
request_grants_execution_authority = false
claim_or_fence_minted = false
heartbeat_grants_execution_authority = false
second_user_device_required = false
receiver_unavailable_disposition = DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION
credential_authority = TV/TVC
github_token_runtime_authority = NONE
observer_direct_relation_to_stegverse_002 = false
```

This lane may create queue-admission and runtime-attempt receipts only. It may not preclaim receiver READY, public HTTPS reachability, experiment events, Master Records reconstruction, or observation round-trip completion.

Canonical event-ephemeral source:

- `workers/universal_intr_profiled_ingress.py`
- `workers/sv002_intr_materialization_consumer.py`
- `workers/sv002_observation_esrl_runtime_bridge.py`
- `workers/hil_intr_profiled_ingress.py` for backward-compatible HIL profile discovery
- `tests/test_sv002_event_ephemeral_materialization.py`
- `docs/SV002_EVENT_EPHEMERAL_OBSERVATION_MIRROR_HANDOFF.md`
- `docs/SV002_PUBLIC_OBSERVATION_RUNTIME_MIRROR_HANDOFF.md`

The earlier script-form SV002 materialization consumer/ingress is superseded and must not be materialized or dispatched.

Site-side Node outbox initiation is owned by the existing `StegVerse-Labs/Site/docs/SV002_PUBLIC_OBSERVATION_MIRROR_HANDOFF.md` lane and must remain non-authorizing.


## Event-ephemeral source closure

Issue #493 is source-complete and closed.

```text
sovereign PR: #509
sovereign merge: 33626b0aed68884f996e03b305f592aa3f727d51
organization control-plane validation: 33294636186 SUCCESS
Heartbeat Worker Project validation: 33294636189 SUCCESS
Site PR: StegVerse-Labs/Site#702
Site merge: 8398426bc740a29d47563236e84f6b829db3b371
known scoped scaffolding/stubs: 0
```

Merged source now provides:

- exact Node-bound non-authorizing SV002 materialization ingress;
- write-once request/ingress receipt binding;
- resident materialization consumer;
- event-triggered route materialization and targeted independent task execution;
- retryable nonterminal route-pending behavior;
- receiver READY as downstream evidence rather than transport-initiation prerequisite;
- G18-independent request/consumer semantics;
- source-refresh/bootstrap propagation for both new scripts;
- filesystem-event consumption of queued SV002 materialization requests;
- Site Node outbox generation and sync discovery.

Still not observed:

```text
public sovereign materialization ingress locator: NOT OBSERVED
Node outbox -> sovereign ingress delivery: NOT OBSERVED
resident materialization consumer execution: NOT OBSERVED
SV002_PUBLIC_OBSERVATION_RECEIVER_READY: NOT OBSERVED
shared Gateway public round trip: NOT OBSERVED
authentic observation ingress RECEIVED: NOT OBSERVED
authentic observation egress FORWARDED: NOT OBSERVED
authentic principal self-characterization: NOT OBSERVED
Master Records reconstruction: NOT OBSERVED
```

The next machine-execution transition is therefore runtime projection/delivery, not additional receiver-source construction.


## Duplicate-path reconciliation — issue #516

Concurrent source merges briefly left both the canonical worker-module event-ephemeral path and an earlier script-form path on `main`.

The authoritative scoped handoff `docs/SV002_EVENT_EPHEMERAL_OBSERVATION_MIRROR_HANDOFF.md` selects exactly one implementation:

```text
workers/universal_intr_profiled_ingress.py
-> workers/sv002_intr_materialization_consumer.py
-> workers/sv002_observation_esrl_runtime_bridge.py
-> existing WorkerCoordinator task SHWP-SV002-PUBLIC-OBSERVATION-RUNTIME-001
```

Issue #516 removes the superseded duplicate scripts, their dedicated `sv002-intr-materialization` filesystem watcher, bootstrap/static-copy references, and duplicate tests. The shared `intr-materialization` ingress remains the only materialization queue surface.

This reconciliation changes no runtime evidence posture and creates no new authority.

## Portable exact resident dispatch path — 2026-08-31

The existing portable local refresh-and-dispatch bridge now admits
`sv002_public_observation` as an explicit exact selector. The historical
`cross_framework_current_basis_v04` default is unchanged. The bridge refreshes only
already-local source, invokes the already-registered generic dispatcher consumer exactly
once, and requires an `EXACT_SELECTOR` receipt with one selected consumer.

This creates no new dispatcher, scheduler, heartbeat, claim/fence, credential, source
network fetch, or runtime authority. Resident request consumption, receiver readiness,
public round-trip, ingress, and egress evidence remain NOT OBSERVED until canonical
resident receipts independently establish them.



## Canonical runtime feature absorption — issue #607

The ecosystem-wide runtime search identified one already-authentically-proven application-neutral runtime fabric:

```text
StegVerse-Labs/StegOS#115
stegos/ephemeral_runtime_lease.py
stegos/canonical_runtime_lane.py
evidence/canonical-runtime/2026-08-30-first-observed-lane.json
```

The reusable feature is the canonical lease/evidence lifecycle, not the browser Web Worker used for its first authentic proof. StegOS #127 / PR #128 added a fail-closed JSON snapshot/resume contract so the same lease can cross event/process boundaries.

SV002 already used `LeaseRequest` / `LeaseMachine` for event-ephemeral materialization but stopped at `LOCAL_READY`. Issue #607 absorbs the canonical continuation contract:

```text
REQUESTED
-> ADMITTED
-> PROVISIONING
-> LOCAL_READY
-> PUBLIC_VERIFYING
-> [future authentic public identity evidence]
-> LEASE_OPEN
-> [future exact READ_OBSERVATION RECEIVED/FORWARDED]
-> continuity/return retention
-> EVIDENCE_EXPORTED
-> RELEASING
-> LEASE_CLOSED
```

The first absorption step advances only to `PUBLIC_VERIFYING`, persists the exact canonical lease snapshot inside the event runtime, hash-binds that snapshot into materialization evidence, and requires the consumer to validate the persisted state/history before dispatching the existing WorkerCoordinator task.

This does **not** preclaim receiver READY, public HTTPS verification, LEASE_OPEN, observation round-trip completion, evidence export, teardown, or LEASE_CLOSED. Those transitions must later resume the same persisted canonical lease after authentic evidence exists.

No G18 dependency, claim/fence minting, credential grant, GitHub-token runtime authority, second user machine, or direct observer relation to StegVerse-002 is introduced.

## Portable exact-dispatch merge evidence

Portable exact-dispatch source merged in PR #606 as
`574d7847ecc6295c2072ca778de0de469f9d9cc6`. Validation runs
`33388902061`, `33388902084`, and `33388902072` succeeded. The canonical
public-observation consumption and resident-refresh-dispatch receipts remained absent at
the post-merge check. The concurrent canonical-runtime lease continuation merged at
`112416c1393ac957a6ccde9ec42876da0802f687` is preserved.


## Master Records-only observation source — 2026-09-01

The public observation projection no longer reads StegVerse-002 worker receipts, principal state roots, human-readable principal output, formal output, or interaction-receipt-chain bytes directly.

Canonical observation flow is now:

```text
StegVerse-002 state changes / receipts
-> Master Records custody + reconstruction
-> StegVerse-Labs read-only projection
```

The projection may expose Master Records reconstruction status, reconstructed artifact hashes, subject identity hash, and reconstructed capability realizations. It must not maintain a competing privileged state history of StegVerse-002.

Origin-side receipt bytes may still be compared against their Master Records-custodied/reconstructed hashes by a dedicated verifier, but that comparison is an integrity check, not an independent observation history.
