# Heartbeat Carrier Signal Mirror Handoff

Updated: 2026-08-14T16:25:00-05:00

## Authority and current state

```text
goal_id: HEARTBEAT-CARRIER-SIGNAL-SEMANTICS-120
repository: StegVerse-Labs/.github
branch: reconcile/heartbeat-carrier-contract-120-v2
canonical_issue: StegVerse-Labs/.github#120
canonical_pr: StegVerse-Labs/.github#140
superseded_pr: StegVerse-Labs/.github#121 CLOSED_SUPERSEDED
canonical_owner: StegVerse-Labs/.github
implementation_claim: RELEASED_AFTER_SOURCE_AND_VALIDATION
active_validation_claim: COMPLETE
active_integration_claim: current-session / merge-and-release support only
integration_release_condition: PR #140 is merged by an authorized repository integration path and #120 records release evidence
credential_authority: TV/TVC
github_token_runtime_authority: NONE
non_tv_tvc_secret_or_token_required: false
```

This handoff is authoritative for heartbeat semantics. Older organization/worker/federation documents remain historical implementation evidence, but any wording that makes heartbeat a scheduler, task dispatcher, route executor, message bus, claim/fence issuer, credential authority, or Master Records transport is normatively superseded by this contract.

## Canonical architecture

Heartbeat is the StegVerse **carrier/synchronization signal** only. It provides an observable primary-signal continuity reference so subsystems can remain synchronized and continuity-aware. It does not dispatch tasks/workers, issue claims/fences/leases, choose/execute routes, grant credentials/execution authority, perform provider/model operations, or perform Master Records custody. Subsystem signals may be present on the carrier without making heartbeat itself the application protocol.

Carrier amplitude is the minimum sufficient amplitude for the maximum admissible simultaneous composite signal load plus bounded engineering margin:

```text
A_carrier = A_required(max_admissible_simultaneous_composite_load) + epsilon_margin
```

Carrier frequency is derived from the relevant gate/passband and path requirements:

```text
f_carrier = derive_from(gate_passbands,
                        admitted_signal_spectrum,
                        simultaneous_load,
                        destination_paths,
                        master_records_return_path,
                        bounded_margin)
```

No universal `10 ms`, `100 Hz`, `MHz`, minute-based or other fixed cadence is architecturally normative.

Subsystem communication is:

```text
manifest packet + expiration wrapper + data packet
```

Terminal lifecycle:

```text
manifest + expiration wrapper + data
  -> ENDPOINT_OBJECTIVE_COMPLETE | EXPIRED
  -> Master Records packet
  -> Master Records custody
  -> END_OF_LIFE
```

Master Records is the End-Of-Life state/destination for every Transition Table element. End Of Life is terminal transition custody, not deletion.

## Worker lifecycle record-pair contract

Worker lifecycle custody begins when a live task observed in the Worker Task Registry causes an admitted worker process to be initiated. That initiation event creates the **opening worker record** in Master Records. The opening record binds at minimum the task/goal identity, worker/instance identity, claim and initial fencing token, authority source/policy version, start reference frame, admitted expiration basis/window, and the expected terminal closure identity.

The worker lifecycle is not complete merely because the process stops or the expiration predicate is reached. Every opening worker record requires a corresponding **closure worker record**.

For normal completion, the closure record is generated from the terminal worker result. For expiration, active worker authority ends first and an expired-worker history data packet becomes the closure object. That packet is emitted as an `expired_worker_history` subsystem signal carried on the heartbeat carrier, or on the explicitly admitted equivalent reference frame if the governing gate/passband requires a different carrier frame for the return path.

The closure timing invariant is:

```text
worker_expiration_reference = R_expire
closure_packet_required_by <= next_admissible_carrier_reference(R_expire)
```

In the ordinary heartbeat reference frame this means **within one heartbeat of the worker's established expiration**. If the applicable communication path uses another admitted reference frame, the equivalent requirement is the first admissible return frame that can carry the expired-worker packet to Master Records without violating the governing gate/passband.

The expired worker itself does not survive this transition. Its execution authority, active claim, active lease, and collision ownership are terminal. Only its immutable history/closure packet remains.

This creates the canonical completeness test in Master Records:

```text
opening worker record exists
+ terminal closure record exists and matches expected identity/lineage
= COMPLETE LIFECYCLE RECORD

opening worker record exists
+ closure deadline/reference passed
+ no matching terminal closure record
= MISSING RECORD
```

The opening record therefore establishes what closure Master Records must later observe, and the carrier/reference-frame deadline establishes when absence becomes a determinable missing-record condition rather than merely an in-flight packet.

Missing-record handling belongs to Master Records custody/reconstruction. It may reconstruct or install the missing terminal record from the expired-worker history packet plus immutable lineage, quarantine corrupt/mismatched records, or idempotently acknowledge an exact duplicate. It may not resurrect the expired worker, restore its claim/fence, or preserve its collision ownership.

## Admissible-Existence structural binding

StegCore issue #105 / PR #119 is COMPLETE_RELEASED and now structurally separates:

```text
stegverse:capability:heartbeat-carrier:v1               DECLARED
stegverse:capability:worker-control-plane:v1            DECLARED
stegverse:capability:manifest-communication:v1          DECLARED
stegverse:capability:master-records-terminal-custody:v1 DECLARED
```

Carrier continuity is not activation proof for any other capability. The sovereign local model remains `ADMISSIBLE` until independent control-plane route activation proof exists.

## Canonical installed branch surfaces

```text
docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md
control/heartbeat-documentation-semantics-audit.json
scripts/validate_heartbeat_carrier_contract.py
.github/workflows/org-control-plane-validate.yml
```

A necessary current-main validation repair was also applied to `docs/STALE_HEARTBEAT_RECLAMATION_MIRROR_HANDOFF.md` by adding the required execution-ownership partition; no stale-heartbeat product behavior was changed.

## Validation evidence

PR #140 head after ownership repair:

```text
head: f60268e7616d254fc77544f0f5d9ab1a49ee5f80
organization control-plane run: 31841173561 SUCCESS
job: 94898170191 SUCCESS
Heartbeat Worker Project run: 31841173579 SUCCESS
Render Organization Handoff State run: 31841173557 SUCCESS
```

Inspected organization-control-plane job/log evidence includes:

```text
ACTIVE_WORKER_STATE_INVARIANT_PASS fragment_active_tasks=18
HANDOFF_EXECUTION_OWNERSHIP_PASS handoffs=18
AE_RETROSPECTIVE_CONFORMANCE_PASS effective_tasks=26 classified=26 pass=22 review_required=4 fail_closed=0
AE_CONTROL_PLANE_VALIDATION_PASS handoffs=25 registry_tasks=26
HEARTBEAT_CARRIER_CONTRACT_PASS heartbeat=carrier_only communication=manifest+expiration+data eol=master_records frequency=gate_derived credential_authority=TV/TVC
ORG_CONTROL_VALIDATION_NON_AUTHORIZING_PASS
```

The validation workflow performs anonymous checkout with no `GITHUB_TOKEN` or `GH_TOKEN` in the validation process and `permissions: {}`. Hosted validation remains evidence only and grants no StegVerse runtime authority.

## Cross-repository continuation

```text
runtime/control-plane semantic separation: StegVerse-Labs/.github#122
Site heartbeat prose: StegVerse-Labs/Site#264
StegCore remaining heartbeat prose: StegVerse-Labs/StegCore#104
StegCore AE carrier structure: StegVerse-Labs/StegCore#105 COMPLETE_RELEASED
admissibility research: StegVerse-Labs/admissibility-wiki#99
packet/Transition Table standard: StegVerse-Labs/repo-standards#39
Master Records terminal packet/EOL: master-records/orchestration#33
Publisher transport reclassification: GCAT-BCAT-Engine/Publisher#27
```

Historical receipts are immutable; downstream owners must adopt the corrected semantics without rewriting provenance.

## Local-model and trade convergence

```text
formal local model/runtime: COMPLETE_RELEASED at StegVerse-002/micro-node-runtime
local discovery/launch/inference/proof: COMPLETE_RELEASED
canonical HANDOFF + Worker Registry AE verifier: COMPLETE_RELEASED
retrospective AE classification: COMPLETE_RELEASED, now 26/26 effective tasks under current main
trade source readiness: 7/8; terminal WALLET_HANDOFF_READY remains machine-owned
wallet signing/broadcast after WALLET_HANDOFF_READY: USER_ONLY
```

No local-model/runtime reimplementation is authorized in this repository.

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```yaml
- task_id: HEARTBEAT-CARRIER-SIGNAL-SEMANTICS-120-INTEGRATION
  execution_owner: current bounded integration/release support session
  manual_execution_allowed: true
  worker_registry_ref: NONE
  collision_scope: PR #140 merge/release evidence and issue/handoff reconciliation only; no live runtime, claim, fence, lease, route, credential or custody mutation
  release_condition: PR #140 merged by an authorized repository integration path and #120 records canonical release evidence
  next_executable_action: observe/complete authorized PR integration, then release this support role
```

### WORKER-OWNED / DO NOT COMPETE

```yaml
- task_id: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122
  execution_owner: StegVerse-Labs/.github#122 + current runtime owners
  manual_execution_allowed: false
  worker_registry_ref: control/worker-registry.json + issue #122
  collision_scope: heartbeat runtime/schema, worker coordination, claims, fences, leases, route state and live carrier operation
  release_condition: #122 installs validated carrier/control-plane separation or releases an exact bounded scope
  next_executable_action: #122 owner continues after canonical contract integration

- task_id: STEGFIN-CONTINUITY-CARRIER-007
  execution_owner: canonical StegFin continuity worker + TV/TVC
  manual_execution_allowed: false
  worker_registry_ref: control/worker-registry.d/stegfin-continuity-carrier-007.json
  collision_scope: live claim, TV/TVC transport, Inventory N, quote/pretrade and WALLET_HANDOFF_READY
  release_condition: terminal machine receipt or fail-closed owner state
  next_executable_action: machine worker executes when authorized carrier/transport predicates are present
```

### ESCALATED / AUTHORITY-OWNED

```yaml
- task_id: HEARTBEAT-CARRIER-AUTHORITY-COLLISION
  execution_owner: StegCore/StegGate + TV/TVC + repository/component owners
  manual_execution_allowed: false
  worker_registry_ref: applicable canonical owner records
  collision_scope: admissibility, credential/route authority, custody and standards conflicts
  release_condition: exact canonical owner resolves the conflict
  next_executable_action: fail closed and route to the exact owner
```

### COMPLETED / SUPERSEDED

```yaml
- task_id: HEARTBEAT-CARRIER-STALE-PR-121
  execution_owner: NONE
  manual_execution_allowed: false
  worker_registry_ref: NONE
  collision_scope: stale branch only
  release_condition: COMPLETE_SUPERSEDED_BY_PR_140
  next_executable_action: NONE
```

## Completion and archive accounting

For `HEARTBEAT-CARRIER-SIGNAL-SEMANTICS-120`, required deliverables are five:

```text
1 current-main canonical handoff: COMPLETE_ON_PR_140
2 current-main machine-readable audit: COMPLETE_ON_PR_140
3 conflicting .github heartbeat prose explicitly subordinated by canonical contract: COMPLETE_ON_PR_140
4 deterministic validator + mandatory no-token workflow gate: COMPLETE_VALIDATED
5 merge/release evidence: PENDING_AUTHORIZED_INTEGRATION
```

```text
developed files: 4/4
scaffolding/stubs: 0
missing required files: 0
validation: 2/2 PASS
integration: 0/1 pending merge
propagation: downstream owner tasks durable; owner execution pending
session consolidation: all unique requirements durable; this session retains only PR #140 integration/release support
archive_ready: false until integration role is released or durably transferred
```
