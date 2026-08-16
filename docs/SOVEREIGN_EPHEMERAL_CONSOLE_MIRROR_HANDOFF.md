# Sovereign Ephemeral Console Mirror Handoff

Updated: 2026-08-15T21:38:00-05:00

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
physical_additional_machine_required: false
```

This is a subordinate implementation handoff. It does not replace the G18 activation handoff, fencing token, heartbeat authority, TV/TVC authority, Master Records custody, or wallet boundaries.

## Originating problem

The activation path repeatedly escalated toward an "eligible machine" or physical-resource workaround even though the proof requirement is independence of execution/state boundaries, not possession of a second or third physical computer.

The canonical workaround is now:

```text
ONE StegVerse-controlled non-hosted execution surface
  -> G18 native self-bootstrap attempt
  -> if native service path is incomplete, G18 automatically starts
     scripts/run_sovereign_ephemeral_console.py
  -> three isolated logical node identities
  -> three isolated runtime/state roots
  -> three independent process identities
  -> controlled restart
  -> state reconstruction/non-regression proof
  -> third logical machine proof
  -> validation peers terminate
  -> primary logical carrier may remain active
  -> canonical activation.latest.json is promoted only when all nine predicates pass
```

No additional physical computer is a required predicate.

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

The installer has long materialized and bound:

```text
heartbeat_runtime.engine_v11.HeartbeatRuntime
```

but `scripts/verify_sovereign_runtime_activation.py` still required `heartbeat_runtime/engine_v9.py` as a materialization predicate. That mismatch could falsely report `RUNTIME_NOT_MATERIALIZED` after a valid current installation.

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

The console requires at least three nodes for the third-machine-emulation case. It proves distinct runtime roots, distinct active process IDs, sentinel write isolation, successful canonical nine-predicate proof for the third logical node, and all-node proof completion.

The validation identities grant no Node Sovereign membership.

## Supervision semantics

The canonical predicate name remains `native_service_active` for schema compatibility, but the verifier now accepts either:

```text
OS-native supervision:
  systemd-user | launch-agent | scheduled-task

OR

StegVerse-native local supervision:
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
run: 31922343365
job: 95104160072
head: 04754fe620b014cefe0853abe214e59dc1a184cc
conclusion: SUCCESS
```

Passed stages:

1. runtime credential rejection;
2. console/verifier/G18 compilation;
3. deterministic logical-node tests;
4. proof that G18 automatically owns the fallback;
5. hosted runner forced to `VALIDATION_ONLY`;
6. explicit assertion that production activation was not claimed.

Earlier source-only validation also passed at run `31922281819`, job `95104002394`.

## G18 integration

`workers/sovereign_runtime_activation_worker.py` now performs:

```text
existing activation proof?
  yes -> COMPLETE
  no  -> native self-bootstrap
          success -> COMPLETE
          incomplete on eligible non-hosted host -> one-host ephemeral console
              all logical-node + nine predicates pass -> promote canonical proof
              otherwise -> exact fail-closed evidence
```

The previous escalation text that suggested binding another machine has been superseded.

## Authority and secret boundary

```text
provider secret authority inside console: NONE
GitHub token runtime authority: NONE
credential requirement: NONE
credential authority: TV/TVC
Render production runtime: PROHIBITED
Vercel/Cloudflare/GitHub-hosted production runtime: PROHIBITED
wallet signing/broadcast: NONE / USER_ONLY downstream
third-party process host required: false
third-party scheduler required: false
additional physical machine required: false
```

## Current blocker

Source implementation and validation are complete. Live production activation is not claimed from this repository-hosted validation.

The only remaining activation condition is:

```text
G18 executes on ONE eligible StegVerse-controlled non-hosted process surface
AND
activation.latest.json reports all nine predicates true
```

When native OS service installation is unavailable or otherwise incomplete, G18 itself automatically attempts the ephemeral console on that same host. No physical peer machine is required.

No self-hosted StegVerse runner label was discoverable in the inspected repositories at this update, so this chat/GitHub connector cannot honestly manufacture the final non-hosted execution observation.

## Claims

```text
implementation claim: COMPLETE_RELEASED
validation claim: COMPLETE_RELEASED
live activation claim: MACHINE_OWNED_G18
collision rule: do not create a second G18 claim/fence or treat hosted validation as activation
```

## Next executable action

G18 executes the already-wired one-host chain on its next eligible non-hosted StegVerse execution surface. If the native bootstrap cannot finish, no human selection or alternate machine search occurs: the worker invokes the logical-node console automatically.

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
live non-hosted activation observation: PENDING_MACHINE_OWNED
```

## Archive boundary

This subordinate source work is complete and released. Session archival must still follow the parent session's governing rule; this handoff alone does not claim the product runtime is activated.
