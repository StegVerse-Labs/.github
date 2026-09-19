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

The canonical ephemeral catalog contains `StegVerseNode` and `StegBrowser`, but callable ownership is operation-specific rather than shared:

```text
StegVerseNode
  callable_task = SHWP-SV002-ACTION-TRANSITION-EVIDENCE-001
  execution_owner = StegVerse-002/.github
  operation = REQUEST_SELF_CHARACTERIZATION

StegBrowser
  callable_task = RT-STEGBROWSER-RUNTIME-CONSUMPTION-001
  execution_owner = StegVerse-Labs/.github
  operation = STEGBROWSER_MANIFEST_DEFINED_INTR_INGRESS
```

Both surfaces reuse the already-validated registered-Node -> Interlock -> Universal InTr materialization -> bounded invocation lease -> EVENT_EPHEMERAL mechanics where applicable, but the StegBrowser reusable task is not a generic callable owner for arbitrary StegVerseNode operations. The target operation retains its own task identity, organization execution owner, payload/manifest semantics, and transition evidence requirements.

Discovery never mints WorkerCoordinator claim/fence, Interlock/InTr admission, credentials, runtime identity, execution evidence, or Master Records evidence.

Canonical runtime authority remains with the existing runtime lifecycle and state-transition authorities. Remote tooling cannot grant execution authority, user-verification authority, credentials, claims/fences, or Interlock/InTr admission.

KV/SKAP Vault remains the sole user-verification authority. StegOS devices remain interchangeable execution/transport nodes rather than user verifiers.


## Canonical no-device-inventory progression rule

For ordinary StegVerse task execution, connected-device inventory is not part of the runtime dependency model.

```text
query_connected_device_inventory_for_task_progression = PROHIBITED
connected_device_inventory_as_runtime_prerequisite = PROHIBITED
connected_device_inventory_as_blocker = PROHIBITED
connected_device_inventory_as_fallback_condition = PROHIBITED
zero_connected_devices_as_stop_condition = PROHIBITED
zero_connected_devices_as_manual_work = PROHIBITED
```

A task must proceed through its actual canonical authorities and evidence path—Task Registry coordination, WorkerCoordinator claim/fence, Interlock/InTr transition authority, TV/TVC credential authority where applicable, and Master Records custody/reconstruction—without first checking whether a remote connector reports a device.

The only exception is a task whose explicit subject is connector/device-inventory management itself. Incidental knowledge that a connector has zero attached devices has no task-state meaning and must be ignored.
