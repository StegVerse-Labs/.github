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

Canonical runtime authority remains with the existing runtime lifecycle and state-transition authorities. Remote tooling cannot grant execution authority, user-verification authority, credentials, claims/fences, or Interlock/InTr admission.

KV/SKAP Vault remains the sole user-verification authority. StegOS devices remain interchangeable execution/transport nodes rather than user verifiers.
