# ORG_FED_STEGVERSE_LABS_RETAINED_OBSERVATION_MIRROR_HANDOFF.md

Status: ACTIVE_IMPLEMENTATION
Task ID: `ORG-FED-STEGVERSE-LABS-001`
COSV ID: `50000000100000`
Canonical owner: `StegVerse-Labs/.github#12`
Parent handoff: `ORG_BOUNDARY_MIRROR_HANDOFF.md`

## Problem closed by this branch

The organization kernel already reconstructs an addressed Interlock/InTr frame and produces the canonical receipt sequence:

`INGRESS_ACCEPTED -> DISPATCHED -> CONSUMED -> RESULT_BOUND -> EGRESS_EMITTED`

However, the existing federation consumption path returns the execution result in memory and does not itself durably retain the observation. Because `ORG-FED-STEGVERSE-LABS-001` requires retained ingress/consumption/egress evidence, an authentic frame could otherwise be consumed without producing the durable evidence needed by the release condition.

## Implementation

- `org-kernel/federation_observation.py`
  - consumes addressed frames through the canonical kernel;
  - retains only `status=CONSUMED` results;
  - requires the complete canonical receipt chain;
  - requires `reconstruction.status=RECONSTRUCTED`;
  - requires destination organization match;
  - validates the terminal receipt binding;
  - writes observation evidence once under `resident-runtime/federation/observations/`;
  - explicitly records `activation_inferred=false` and `task_completion_inferred=false`.

- `org-kernel/tests/test_federation_observation.py`
  - creates a canonical Peer-Org -> StegVerse-Labs addressed frame;
  - consumes it through the resident kernel;
  - proves durable evidence retention;
  - proves complete receipt sequence and reconstruction;
  - proves idempotent/write-once re-retention;
  - proves no activation or completion inference is introduced.

## Authority boundary

This source change does not claim that a live federation observation has occurred. Test traffic is source-level validation only. Live task completion remains dependent on authentic machine-owned federation traffic at the canonical resident runtime.

GitHub Actions remain validation/evidence transport only and are not runtime authority. Credential authority remains TV/TVC.

## Next action after merge

Canonical machine-owned federation execution should use the retention path when consuming an authentically addressed Interlock/InTr frame for StegVerse-Labs. The resulting durable observation may then be reconciled into `control/organization-federation.json` and the task vector only if the live evidence independently satisfies the release condition.

## Release condition

Do not retire `ORG-FED-STEGVERSE-LABS-001` until authentic retained machine evidence proves the addressed frame traversed StegVerse-Labs ingress, consumption, result binding, and egress with reconstruction intact.
