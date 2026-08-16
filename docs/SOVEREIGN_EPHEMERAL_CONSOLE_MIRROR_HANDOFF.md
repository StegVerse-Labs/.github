# Sovereign Ephemeral Console Mirror Handoff

Updated: 2026-08-15T22:45:00-05:00

## Source of truth

```text
goal_id: SHWP-SOVEREIGN-EPHEMERAL-CONSOLE-002
repository: StegVerse-Labs/.github
branch: main
parent_goal: SHWP-DURABLE-RUNTIME-ACTIVATION
parent_handoff: handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json
live_owner: G18 / SHWP-DURABLE-RUNTIME-ACTIVATION fencing token 18
source_claim: COMPLETE_RELEASED
credential_authority: TV/TVC
non_tv_tvc_secret_or_token_allowed: false
render_allowed: false
physical_host_cardinality_default: 1
physical_additional_machine_required: false
third_party_machine_or_service_required: false
```

This is a subordinate implementation handoff. It does not replace the G18 activation handoff, fencing token, heartbeat authority, TV/TVC authority, Master Records custody, or wallet boundaries.

## Global sovereignty invariant

Canonical policy: `control/sovereign-runtime-platform-policy.json`.

A StegVerse deployment is sovereign only when every required production process, scheduler, runtime, state store, validation execution boundary, control-plane executor, and continuity dependency is satisfied by the deployment's own sovereign physical host and StegVerse-controlled logical boundaries on that host.

```text
ONE deployment = ONE sovereign physical host by default
additional physical machine required: FALSE
third-party process host required: FALSE
third-party scheduler required: FALSE
third-party state host required: FALSE
third-party control-plane executor required: FALSE
hosted validation may create production authority: FALSE
```

External providers/networks may be optional user-selected inputs, but their loss may not prevent the sovereign StegVerse runtime, governance, proof, replay, reconstruction, continuity, or local control plane from operating within its declared scope.

## Originating problem

The activation path repeatedly escalated toward an "eligible machine" or physical-resource workaround even though the proof requirement is independence of execution/state boundaries, not possession of a second or third physical computer.

That interpretation is now prohibited.

The canonical topology is:

```text
THE deployment's ONE sovereign physical StegVerse host
  -> canonical persistent StegVerse runtime
  -> G18 native self-bootstrap attempt
  -> when independent-peer proof is required or native service proof is incomplete,
     G18 automatically starts scripts/run_sovereign_ephemeral_console.py
  -> isolated logical node 1
  -> isolated logical node 2
  -> isolated logical node 3
  -> separate identities / runtime roots / state trees / receipt trees / process PIDs
  -> controlled restart
  -> state reconstruction / non-regression
  -> collision / fencing isolation
  -> canonical nine-predicate proof
  -> validation peers terminate
  -> primary local carrier may remain active
```

No additional physical computer is a valid required predicate. No third-party machine or service may substitute for the deployment's sovereign host.

## Implemented files

```text
scripts/run_sovereign_ephemeral_console.py
scripts/restart_sovereign_ephemeral_node.py
scripts/verify_sovereign_runtime_activation.py
workers/sovereign_runtime_activation_worker.py
tests/test_sovereign_ephemeral_console.py
.github/workflows/sovereign-ephemeral-console.yml
control/session-implementation-claim-2026-08-15-sovereign-ephemeral-console.json
```

## Corrected verifier defect

The installer materializes and binds:

```text
heartbeat_runtime.engine_v11.HeartbeatRuntime
```

but `scripts/verify_sovereign_runtime_activation.py` had still required `heartbeat_runtime/engine_v9.py` as a materialization predicate. That mismatch could falsely report `RUNTIME_NOT_MATERIALIZED` after a valid current installation.

The verifier now requires `engine_v11.py` and records missing runtime files explicitly.

## Logical-node proof invariants

Each ephemeral logical node has an independent:

```text
node identity
runtime root
heartbeat-state tree
worker-registry copy
checkpoint tree
receipt tree
process PID
restart lifecycle
```

The console requires at least three logical nodes for the former third-machine-emulation case. It proves distinct runtime roots, distinct active process IDs, sentinel write isolation, successful canonical nine-predicate proof for the third logical node, and all-node proof completion.

The validation identities grant no Node Sovereign membership.

## Supervision semantics

The canonical predicate name remains `native_service_active` for schema compatibility, but the verifier accepts either:

```text
OS-native supervision:
  systemd-user | launch-agent | scheduled-task

OR

StegVerse-native same-host supervision:
  registration_kind: stegverse-ephemeral-console
  stegverse_process_supervision: true
  third_party_process_host_required: false
  explicit local restart_command bound in the service receipt
```

This is not a third-party process host and introduces no external scheduler.

## Hosted validation boundary

GitHub Actions is validation-only.

A hosted execution must return:

```text
state: VALIDATION_ONLY
hosted_environment_observed: true
canonical_proof_promoted: false
```

The hosted job may compile and test source semantics but cannot create sovereign production activation evidence.

## Validation evidence

```text
workflow: .github/workflows/sovereign-ephemeral-console.yml
run: 31922398210
job: 95104297651
head: e9df7ebd7824a3ad822528ca1092b72c13cf57c0
conclusion: SUCCESS
```

Passed stages:

1. runtime credential rejection;
2. console/verifier/G18 compilation;
3. deterministic logical-node tests;
4. proof that G18 automatically owns the fallback;
5. hosted runner forced to `VALIDATION_ONLY`;
6. explicit assertion that production activation was not claimed.

Earlier source validation also passed at runs `31922281819` and `31922343365`.

## G18 integration

`workers/sovereign_runtime_activation_worker.py` performs:

```text
existing activation proof?
  yes -> COMPLETE
  no  -> native self-bootstrap on THE deployment host
          success -> COMPLETE
          incomplete -> same-host ephemeral console
              all logical-node + nine predicates pass -> promote canonical proof
              otherwise -> exact fail-closed evidence
```

No alternate-machine search or federated-host selection is part of the canonical deployment path.

## Authority and secret boundary

```text
provider secret authority inside console: NONE
GitHub token runtime authority: NONE
credential requirement: NONE
credential authority: TV/TVC
Render production runtime: PROHIBITED
Vercel/Cloudflare/GitHub-hosted production runtime: PROHIBITED
third-party machine as production dependency: PROHIBITED
third-party process host required: false
third-party scheduler required: false
third-party state host required: false
additional physical machine required: false
wallet signing/broadcast: NONE / USER_ONLY downstream
```

## Current activation condition

Source implementation and validation are complete. Hosted validation does not claim production activation.

The only valid activation condition is:

```text
G18 executes on THE deployment's existing sovereign StegVerse physical host
AND
activation.latest.json reports all nine predicates true
```

When independent execution boundaries are needed, G18 creates them as logical nodes on that same host. It must not search for, wait for, or require another machine.

The current chat connector can mutate and validate repository state but does not expose process execution on the deployment's physical StegVerse host. That is a connector/control-plane reachability boundary, not a requirement for another machine and not permission to introduce a third-party runtime.

## Claims

```text
implementation claim: COMPLETE_RELEASED
validation claim: COMPLETE_RELEASED
live activation claim: MACHINE_OWNED_G18
collision rule: do not create a second G18 claim/fence; do not treat hosted validation as activation; do not introduce another physical-machine requirement
```

## Next executable action

G18 executes the already-wired chain on the deployment's existing sovereign host. If native bootstrap cannot finish, G18 invokes the logical-node console automatically on that same host. No human machine selection, alternate-host search, cloud fallback, or third-party execution service is authorized.

## Completion accounting

```text
required source/control files: 7
implemented: 7/7
scaffolding/stubs: 0
hosted validations required: 1
hosted validations passed: 1/1
G18 integration required: 1
G18 integration complete: 1/1
physical-machine dependency removal: COMPLETE
single-host sovereignty policy normalization: COMPLETE
live deployment-host activation observation: PENDING_MACHINE_OWNED
```

## Archive boundary

This subordinate source work is complete and released. Session archival must still follow the parent session's governing rule; this handoff alone does not claim the product runtime is activated.
