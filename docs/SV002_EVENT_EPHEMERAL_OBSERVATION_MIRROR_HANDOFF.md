# SV002 Event-Ephemeral Public Observation Mirror Handoff

Updated: 2026-08-30
Repository: `StegVerse-Labs/.github`
Issue: #493

## Goal

Remove the false dependency on G18 terminalization or an already-running persistent receiver from StegVerse-002 public observation. A valid StegVerse Node may initiate a non-authorizing Universal Interlock/InTr materialization event; receiver READY is downstream evidence.

## Governing path

```text
valid observer Node
-> exact SV002_PUBLIC_OBSERVE request prepared locally
-> stegverse.universal-intr-transport/v1 intent
-> stegverse.universal-intr-materialization-request/v1
-> node-bound write-once InTr trigger
-> shared /intr/materialization ingress
-> stegverse.sv002-intr-materialization-ingress/v1 receipt
-> credential-scrubbed event consumer dispatch
-> StegOS ESRL EVENT_EPHEMERAL runtime materialization
-> existing WorkerCoordinator targeted execution
-> SHWP-SV002-PUBLIC-OBSERVATION-RUNTIME-001
-> receiver READY observation
-> exact original SV002_PUBLIC_OBSERVE request
-> canonical ingress/egress observation receipts
-> read-only projection
```

## Authority boundary

```text
materialization request grants execution authority: false
ingress grants execution authority: false
ingress mints claim/fence: false
consumer mints claim/fence: false
WorkerCoordinator remains claim/fence authority: true
credential authority: TV/TVC
GitHub token runtime authority: NONE
G18 completion required: false
always-on receiver required before event: false
second user machine required: false
observer direct relation to StegVerse-002: false
```

The ingress event may launch a detached credential-scrubbed consumer process. That process is a dispatch mechanism only. It may request the already-admitted task; it cannot manufacture task authority, standing, experiment interaction, custody, publication, or Master Records evidence.

## Compatibility

The existing HIL `POST /intr/materialization` admission function remains the unchanged handler for HIL destinations. `workers/hil_intr_profiled_ingress.py` preserves the existing `stegverse.hil-intr-materialization-ingress-profile/v1` discovery schema while delegating POST handling to the shared dispatcher and advertising `SV002:PublicObservation` as an additional materialization profile.

## Implemented source

- `workers/universal_intr_profiled_ingress.py`
- `workers/sv002_intr_materialization_consumer.py`
- `workers/sv002_observation_esrl_runtime_bridge.py`
- `tests/test_sv002_event_ephemeral_materialization.py`

A prior script-form consumer on the development branch is superseded by the worker-module consumer because `workers/**` is already part of canonical sovereign static source materialization.

## Evidence semantics

Source, tests, CI, merge, request admission, consumer dispatch, and ESRL local materialization are distinct states. None may be represented as the public observation round trip or principal experiment execution.

Terminal public observation still requires independently observed:

1. SV002 materialization ingress admission from a valid external Node;
2. consumer execution attempt;
3. event-ephemeral runtime materialization;
4. `SV002_PUBLIC_OBSERVATION_RECEIVER_READY`;
5. exact read-only browser request delivered through shared Gateway/InTr;
6. authentic ingress `RECEIVED` receipt;
7. authentic egress `FORWARDED` receipt;
8. observer direct relation to StegVerse-002 remains false.

Master Records custody/reconstruction and authentic principal self-characterization remain separate evidence gates.
