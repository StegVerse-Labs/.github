# Enterprise Render Eradication Mirror Handoff

Goal Task ID: `ENTERPRISE-RENDER-ERADICATION-001`
Canonical issue: `StegVerse-Labs/.github#1703`
Status: `ACTIVE / ENTERPRISE SOURCE ERADICATION`

## Scope

Remove the hosting/provider named Render/Render.com from current StegVerse enterprise source truth wherever it appears as:

- hosting or fallback runtime;
- deployment target or service origin;
- provider/API URL;
- secret, token, hook, environment, or service identifier;
- operational dependency or readiness path;
- task/handoff/workflow runtime assumption;
- current receipt/status projection that directs future work to the provider.

Ordinary programming uses of `render`, `renderer`, `render_*`, visual rendering, Publisher rendering, document rendering, UI rendering, and similar non-provider meanings are explicitly out of scope.

Historical Git commits remain provenance and are not rewritten by this task. The target is current/default-branch source truth and active coordination surfaces.

## Replacement policy

This task does not authorize a replacement third-party host. Provider-specific defaults must become explicit caller/configuration requirements or bind to already-canonical StegVerse sovereign surfaces.

## Runtime/device correction

Remote Desktop or any equivalent remote-device connector is OPTIONAL observation/execution tooling only.

```text
connected_remote_device_required = false
zero_connected_devices_is_runtime_blocker = false
zero_connected_devices_proves_runtime_unavailable = false
participant_machine_required_for_event_ephemeral = false
developer_machine_required_for_event_ephemeral = false
```

No always-on user device, desktop, second machine, or persistent remote-control connection is required by the canonical event-ephemeral runtime model. A zero-device connector result must never be used as a prerequisite failure for MIR, TV/TVC, or generic canonical-runtime execution.

## Authority

- Task Registry: coordination only.
- Interlock/InTr: state-transition/admission authority.
- TV/TVC: credential/provider authority.
- WorkerCoordinator: claim/fence authority when applicable.
- KV/SKAP Vault: sole user-verification authority.
- GitHub: source/evidence coordination only; runtime authority NONE.

## Initial inventory

Confirmed current provider-specific references exist in at least:

- `StegVerse-Labs/StegVerse-SCW`
- `StegVerse-Labs/Site`
- `StegVerse-Labs/StegCore`
- `StegVerse-Labs/StegPay`
- `StegVerse-Labs/StegSports-CFP`
- `StegVerse-Labs/Continuity`
- `StegVerse-org/StegVerse-SDK`
- `StegVerse-org/LLM-adapter`
- `StegVerse-Labs/TVC`
- `StegVerse-Labs/.github`

Search inventory must distinguish provider references from the ordinary verb/function `render`.

## Completion predicates

1. No current default-branch executable code contains Render provider API calls, service URLs, deployment hooks, provider secret names, or fallback-runtime selection.
2. No current default-branch configuration/deployment file selects Render as a host or provider.
3. No active task/handoff/workflow directs future runtime work to Render.
4. No provider-specific default URL remains in SDK, Core, Site, SCW, LLM Adapter, or adjacent active runtime surfaces.
5. Current coordination truth states that zero remote devices is not a runtime blocker or prerequisite.
6. Enterprise search for provider-specific markers (`onrender.com`, `api.render.com`, provider-specific Render secret/service identifiers, provider config filenames when provider-owned) returns no active dependency references except explicitly retained historical-provenance text that cannot affect current execution; any such retention must be enumerated.
7. Repository validations pass after removals.

## Runtime evidence boundary

This is a source/dependency-eradication goal. Removing provider references does not prove sovereign runtime execution, MIR round-trip completion, or any other runtime predicate.
