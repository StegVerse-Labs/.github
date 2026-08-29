# HIL InTr Direct StegOS Node Origin Mirror Handoff

Updated: 2026-08-29
Repository: `StegVerse-Labs/.github`
Issue: #421
Parent: #246
PR: #425

```text
goal_id: SHWP-HIL-INTR-DIRECT-NODE-ORIGIN-421
state: IMPLEMENTED_VALIDATED_MERGE_PENDING
credential_authority: TV/TVC
github_token_runtime_authority: NONE
authority_effect: NONE_INGRESS_ONLY
runtime_ingress_observed: false
organization_control_plane_validation_run: 33274106833 SUCCESS
heartbeat_worker_validation_run: 33274106860 SUCCESS
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

## Exact-head validation

The fresh rematerialization onto current `.github/main` was validated on source head `d145aee89f06e8b064be8582c62abbd225e7279f`:

```text
Validate organization control plane - No GitHub Token Authority
  run 33274106833: SUCCESS
Heartbeat Worker Project - Validation Only / No GitHub Token Authority
  run 33274106860: SUCCESS
```

The handoff reconciliation commit itself must also pass those same exact-head gates before merge. Source/CI success remains non-runtime evidence; `runtime_ingress_observed` stays false until a real sovereign ingress receipt exists.
