# Heartbeat Carrier Signal Mirror Handoff

## Authority

```text
goal_id: HEARTBEAT-CARRIER-SIGNAL-SEMANTICS-120
repository: StegVerse-Labs/.github
branch: feat/heartbeat-carrier-signal-architecture-120
canonical_issue: #120
canonical_owner: StegVerse-Labs/.github
role: architecture reconciliation / documentation correction
credential_authority: TV/TVC
non_TV_TVC_runtime_credentials: PROHIBITED
active_implementation_claim: current-session-carrier-signal-doc-reconciliation
claim_release_condition: canonical contract and audit inventory are merged or explicitly transferred with evidence
```

This handoff is subordinate to `docs/ORG_MIRROR_HANDOFF.md` for organization-wide execution ownership. It is authoritative for correcting heartbeat semantics that were previously conflated with orchestration, worker scheduling, message exchange, task dispatch, route execution, or subsystem communication.

## Canonical correction

The StegVerse heartbeat is the **carrier/synchronization signal** of the ecosystem.

It does not itself communicate application messages between subsystems. It does not issue tasks, claims, fences, routes, credentials, instructions, records, provider calls, or execution authority. It does not own worker behavior. It does not replace manifest packets, control logic, gates, or Master Records custody.

Its functions are limited to:

1. provide the common carrier/synchronization reference used by participating subsystems;
2. preserve a continuously observable primary-signal continuity condition;
3. let subsystems remain synchronized and aware of continuity by observing that primary signal;
4. provide continuity observations that other governed mechanisms may reference as evidence.

A subsystem can react to an observation of heartbeat continuity or loss only through its own gates, authority, policy, and packet/control-plane logic. The heartbeat itself does not command the reaction.

## Carrier amplitude rule

Heartbeat amplitude is not an arbitrary maximum and is not a policy score. It is sized only large enough to carry the full set of simultaneously present system signal components with a bounded engineering margin.

Canonical rule:

```text
A_carrier = A_required(maximum admissible simultaneous composite signal load) + epsilon_margin
```

where `epsilon_margin` is the smallest bounded headroom required by the physical/logical carrier implementation to avoid clipping, loss of distinguishability, or equivalent saturation failure.

The implementation must not increase amplitude merely to imply urgency, authority, task priority, or semantic importance.

## Carrier frequency rule

There is no universal normative heartbeat interval such as `10 ms`, `100 Hz`, `MHz`, or a fixed polling period.

Carrier frequency is derived by the respective gates and signal path constraints so that the admissible passband can carry:

- every subsystem signal frequency that is allowed to traverse the relevant path;
- simultaneous to/from destination traffic required by those paths;
- terminal Master Records packet return traffic;
- synchronization/continuity observability with sufficient margin for efficient system operation.

Canonical requirement:

```text
f_carrier = derive_from(gate_passbands, admitted_signal_spectrum,
                        simultaneous_load, destination_paths,
                        master_records_return_path, bounded_margin)
```

The exact derivation is implementation/medium dependent and must be proven by the owning gates. A fixed wall-clock cadence may exist as an implementation observation or test fixture, but it is not the architectural definition of heartbeat frequency.

## Communication packet rule

All subsystem-to-subsystem communication is represented as exactly this logical composition:

```text
manifest packet
+ expiration wrapper
+ data packet
```

The manifest establishes the declared communication objective, source/destination identity, route/gate constraints, applicable authority/policy references, and identity/provenance necessary to interpret the data packet.

The expiration wrapper bounds the communication object's usable lifetime and carries the conditions under which it must stop being an active communication object.

The data packet contains the communication payload. The heartbeat is not the data packet.

## Master Records End-Of-Life rule

Every active communication object has two terminal triggers:

```text
A. endpoint objective completed
B. expiration reached before or after endpoint processing
```

Either trigger transforms the complete communication object into a **Master Records packet** while preserving its identity and history:

```text
manifest packet + expiration wrapper + data packet
    -> ENDPOINT_COMPLETE | EXPIRED
    -> Master Records packet
    -> Master Records intake/custody
    -> END_OF_LIFE
```

Master Records is therefore the End-Of-Life state/destination for **every Transition Table element**. End-Of-Life does not mean deletion. It means the element is no longer an active communication transition and its terminal state is durably represented in Master Records for reconstruction, provenance, audit, succession, and historical continuity.

Completion and expiration must remain distinguishable terminal reasons. Expiration does not erase the packet, and completion does not exempt the packet from terminal custody.

## Separation of planes

The architecture contains distinct mechanisms that must not be collapsed into heartbeat semantics:

```text
carrier/synchronization plane
  heartbeat primary signal continuity

communication plane
  manifest packet + expiration wrapper + data packet

control/execution plane
  gates, admissibility, task/worker logic, claims, fences, leases, routing decisions

credential plane
  TV/TVC

custody / End-Of-Life plane
  Master Records packet intake, retention, reconstruction
```

A control-plane process may use heartbeat continuity as an input signal. That does not make the control-plane process part of the heartbeat.

A communication packet may traverse infrastructure synchronized to the heartbeat carrier. That does not make the packet a heartbeat message.

A Master Records packet may retain heartbeat continuity observations as evidence. That does not make heartbeat the custody transport.

## Superseded terminology

The following formulations are architecturally incorrect when used literally and must be removed from normative documentation or clearly marked historical/superseded:

```text
heartbeat sends/receives subsystem messages
heartbeat task dispatcher
heartbeat worker scheduler
heartbeat issues claims/fences
heartbeat routes provider/model traffic
heartbeat owns work execution
heartbeat response network as application message exchange
heartbeat packet as subsystem communication object
fixed 10 ms / 100 Hz universal heartbeat frequency
MHz heartbeat as an architectural requirement
heartbeat advances progress because a task transition occurred
```

Where existing source code uses `heartbeat_*` names for worker orchestration or task scheduling, documentation must distinguish the historical implementation name from the canonical architectural role until a runtime refactor is separately claimed and validated.

## Documentation review findings

Directly inspected conflicting or incomplete surfaces:

```text
StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md
  conflict: describes resident heartbeat as active runtime owner/executor and claim/fence/task continuation carrier

StegVerse-Labs/.github/docs/HEARTBEAT_CONTINUITY_WORKER_MIRROR_HANDOFF.md
  conflict: heartbeat -> TVC route, heartbeat-owned worker execution, live claim/fence execution

StegVerse-Labs/.github/docs/ALL_ORGS_HEARTBEAT_FEDERATION_MIRROR_HANDOFF.md
  conflict: heartbeat-owned worker/task registry, response-network convergence, worker lease clock treated as heartbeat behavior

StegVerse-Labs/Site/docs/ECOSYSTEM_HEARTBEAT_ORCHESTRATION.md
  conflict: live state receiver/transmitter of heartbeat data; task transitions described as heartbeat production

StegVerse-Labs/Site/docs/ECOSYSTEM_HEARTBEAT_RESPONSE_NETWORK.md
  conflict: heartbeat exchange/envelope used for MEMORY/ACTION/AWARENESS/AUTHORITY/EVIDENCE/BLOCKER/CAPABILITY/CONTEXT messages

StegVerse-Labs/StegCore/docs/STEGCORE_ORG_HEARTBEAT_MIRROR_HANDOFF.md
  conflict: organization heartbeat returns and repository federation manifests modeled as heartbeat exchange artifacts

StegVerse-Labs/admissibility-wiki/docs/research/heartbeat-guided-path-selection-and-iict.md
  conflict: heartbeat coordinates token rotation/refresh/path selection; speculative fixed MHz range

StegVerse-Labs/repo-standards/standards/ST-004_TRANSITION_TABLE_ELEMENTS.standard.md
  gap: no explicit Master Records End-Of-Life packet rule for every Transition Table element

master-records/orchestration
  gap: manifested custody exists but canonical conversion of completed/expired communication object into a Master Records packet is not yet defined as the universal Transition Table EOL rule
```

## Durable downstream tasks

```text
StegVerse-Labs/.github#120       canonical correction and audit owner
StegVerse-Labs/Site#264          Site heartbeat doc reconciliation
StegVerse-Labs/StegCore#104      StegCore heartbeat doc reconciliation
StegVerse-Labs/admissibility-wiki#99
                                 research reconciliation
StegVerse-Labs/repo-standards#39 transition-table standard / EOL semantics
master-records/orchestration#33  Master Records packet terminal intake semantics
```

Publisher, Site public copy, admissibility-wiki, and stegguardian-wiki propagation must follow the owning release/standards path after the canonical contract is accepted. Historical receipts and immutable evidence are not rewritten.

## Runtime implication

Current `heartbeat_runtime` code and worker registries have accumulated scheduler/orchestrator behavior under heartbeat naming. This documentation correction does **not** silently declare that runtime correct.

A separate implementation task is required to determine which existing behaviors belong to:

- carrier observation;
- gate/control-plane orchestration;
- communication packet transport;
- Master Records terminal custody.

Until that refactor is implemented and validated, runtime evidence may prove the behavior of the existing implementation but must not be cited as proof that the canonical carrier-signal architecture is fully activated.

## Validation requirements

Documentation/contract validation must prove:

```text
heartbeat_has_application_payload = false
heartbeat_grants_authority = false
heartbeat_dispatches_tasks = false
heartbeat_issues_claims_or_fences = false
heartbeat_routes_packets = false
heartbeat_is_master_records_transport = false
communication_object = manifest + expiration_wrapper + data
terminal_triggers = endpoint_complete | expired
terminal_object = master_records_packet
transition_table_eol = master_records
carrier_frequency_fixed_universal = false
carrier_frequency_gate_derived = true
carrier_amplitude_semantic_priority = false
credential_authority = TV/TVC
```

## Session consolidation state

This architecture correction is new unique work surfaced in the current session. It is not merged into the previous local-model activation lane or Master Records issue #31. The canonical continuation is this handoff plus issue #120 and the downstream issues listed above.

## Completion accounting

```text
canonical architecture contract: CREATED_ON_BRANCH
scoped handoff: CREATED_ON_BRANCH
documentation audit: INITIAL_DIRECT_REVIEW_COMPLETE
canonical .github conflicting docs reconciled: PENDING
downstream corrective issues: CREATED
runtime semantic separation: PENDING_SEPARATE_IMPLEMENTATION
Master Records EOL packet implementation: PENDING_OWNER #33
standards propagation: PENDING_OWNER #39
release/tag: NOT_READY
archive state: ACTIVE_UNIQUE_WORK
```
