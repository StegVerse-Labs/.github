# Remote Runtime Connector Optionality

This contract prevents optional remote-control tooling from becoming a false runtime prerequisite.

```text
remote_runtime_connector_role = OPTIONAL_OBSERVATION_OR_EXECUTION_TOOLING
connected_remote_device_required = false
always_on_user_machine_required = false
second_user_operated_machine_required = false
zero_connected_devices_is_runtime_blocker = false
zero_connected_devices_proves_runtime_unavailable = false
event_ephemeral_runtime_may_materialize_without_remote_connector = true
```

A connector reporting zero devices means only that the connector currently has no endpoint attached. It does not prove that StegVerse runtime capacity is absent, does not block canonical runtime materialization, and does not create a requirement for an always-on iPhone, desktop, server, or second user-operated machine.

## Execution-surface discovery classes

Canonical StegVerse discovery is implemented by `scripts/list_stegverse_execution_surfaces.py` and separates attached connector endpoints from invocation-callable execution surfaces:

```text
class=connected
  presently attached connector endpoints only

class=ephemeral
  callable execution surfaces that are not presently instantiated

class=all
  union of connected and ephemeral surfaces
```

An ephemeral surface is discovery evidence only and MUST NOT be represented as already connected, materialized, leased, admitted, executing, or completed. The canonical pre-invocation state is:

```text
class = ephemeral
availability = AVAILABLE_TO_INVOKE
instance_state = NOT_MATERIALIZED
runtime_class = EVENT_EPHEMERAL
materialization = ON_INVOCATION
persistent_connection_required = false
second_user_operated_device_required = false
authority_effect = NONE_DISCOVERY_ONLY
```

The initial canonical ephemeral surface catalog contains `StegVerseNode` and `StegBrowser`, both bound to existing reusable task `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` and the existing registered-Node -> Interlock -> Universal InTr materialization -> bounded invocation lease -> EVENT_EPHEMERAL path. Discovery never mints WorkerCoordinator claim/fence, Interlock/InTr admission, credentials, runtime identity, execution evidence, or Master Records evidence.

Canonical runtime authority remains with the existing runtime lifecycle and state-transition authorities. Remote tooling cannot grant execution authority, user-verification authority, credentials, claims/fences, or Interlock/InTr admission.

KV/SKAP Vault remains the sole user-verification authority. StegOS devices remain interchangeable execution/transport nodes rather than user verifiers.
