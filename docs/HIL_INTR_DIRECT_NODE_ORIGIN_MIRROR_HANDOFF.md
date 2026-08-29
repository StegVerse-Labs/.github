# HIL InTr Direct StegOS Node Origin Mirror Handoff

Updated: 2026-08-29
Repository: `StegVerse-Labs/.github`
Issue: #421
Parent: #246

```text
goal_id: SHWP-HIL-INTR-DIRECT-NODE-ORIGIN-421
state: IMPLEMENTED_ON_BRANCH_VALIDATION_PENDING
credential_authority: TV/TVC
github_token_runtime_authority: NONE
authority_effect: NONE_INGRESS_ONLY
runtime_ingress_observed: false
```

## Purpose

Separate direct registered StegOS Node materialization triggers from TVC relay EGRESS. A browser-local HIL outbox request is a non-authorizing event trigger; it must never invent or impersonate a TVC EGRESS authorization merely to ask the existing HIL owner to materialize event-ephemerally.

The ingress now supports two explicit origins:

```text
STEGOS_NODE_OUTBOX
TVC_RELAY_EGRESS
```

### STEGOS_NODE_OUTBOX

Body schema:

```text
stegos.node_intr_materialization_trigger.v1
```

The envelope carries the complete `stegos.node_intr_outbox_entry.v1`, including the registered Node id, Interlock id, exact local outbox hash, and exact nested Universal InTr materialization request. The ingress independently recomputes the outbox-entry hash and trigger hash before extracting the materialization request.

A direct Node trigger is rejected if it presents `X-StegVerse-Authorization-Id`; Node intake may not pretend to be TVC EGRESS authorization.

### TVC_RELAY_EGRESS

The previously merged relay path remains separate and requires a non-empty TVC relay authorization identity header. Its body remains the exact materialization request.

## Shared completion boundary

Either accepted origin can only produce:

```text
INGRESS_ADMITTED
-> exact validated request persisted in runtime/intr-materialization/
```

Neither origin grants WorkerCoordinator execution authority or proves HIL receiver readiness/custody/review/publication. Claim/fence ownership remains downstream with WorkerCoordinator. G18 remains unrelated.

A first accepted ingress origin is write-once for that materialization receipt. A different origin cannot overwrite the existing ingress receipt. Same exact origin retry is idempotent.

## Required validation

```text
tests/test_hil_intr_materialization_ingress.py
organization control-plane validation
Heartbeat Worker Project validation-only workflow
```

Source/CI success is not runtime ingress evidence.
