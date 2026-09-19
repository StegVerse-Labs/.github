# Enterprise Host-Provider Eradication Mirror Handoff

Goal Task ID: `ENTERPRISE-HOST-PROVIDER-ERADICATION-001`
Canonical issue: `StegVerse-Labs/.github#1703`
Status: `ACTIVE / ENTERPRISE SOURCE ERADICATION`

## Scope

Remove named third-party hosting-provider dependencies and provider-identifying active references from current StegVerse enterprise source truth wherever they appear as:

- hosting or fallback runtime;
- deployment target or service origin;
- provider/API URL;
- provider secret, token, hook, environment, service or workspace identifier;
- operational dependency or readiness path;
- task/handoff/workflow runtime assumption;
- current receipt/status projection that directs future work to a third-party host.

Ordinary programming uses of words such as `render`, `renderer`, visual/document/UI rendering, and similarly named local functions are out of scope.

Historical Git commits remain immutable provenance and are not rewritten. The target is current/default-branch source truth and active coordination surfaces. Current source must not retain provider-identifying references merely to say they are prohibited.

## Replacement policy

No replacement third-party host is authorized by this task. Provider-specific defaults must become explicit caller/configuration requirements or bind to already-canonical StegVerse sovereign surfaces.

## Runtime/device correction

Remote-device connector availability is optional observation/execution tooling only.

```text
connected_remote_device_required = false
zero_connected_devices_is_runtime_blocker = false
zero_connected_devices_proves_runtime_unavailable = false
participant_machine_required_for_event_ephemeral = false
developer_machine_required_for_event_ephemeral = false
```

No always-on user device, desktop, second machine, or persistent remote-control connection is required by the canonical event-ephemeral runtime model.

## Authority

- Task Registry: coordination only.
- Interlock/InTr: state-transition/admission authority.
- TV/TVC: credential/provider authority.
- WorkerCoordinator: claim/fence authority when applicable.
- KV/SKAP Vault: sole user-verification authority.
- GitHub: source/evidence coordination only; runtime authority NONE.

## Existing enterprise inventory

Current cleanup scope includes at least:

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
- `master-records/orchestration`

Search inventory must distinguish provider references from ordinary rendering terminology.

## Reconciled cleanup progress — 2026-09-18

Merged cleanups:

```text
StegVerse-org/StegVerse-SDK#230 -> 3f92024e49ba492008caea99ffd9a2ddb3db2e86
StegVerse-Labs/StegVerse-SCW#45 -> aca3d203b4d216a4853ecfbf35103d9602ae0045
StegVerse-Labs/StegPay#4 -> 41141f97af34c19dd2560874b98d621d68133173
StegVerse-Labs/Continuity#16 -> ee41749d66dae49e90a4b2bfec2d570687d5f2c1
StegVerse-Labs/TVC#421 -> e7dde5d8fe28442146a4f2b2db992bbf0de32225
StegVerse-Labs/StegCore#212 -> 308ec5277d85cc93e59c97eb721819bff7fddf47
StegVerse-Labs/StegSports-CFP#2 -> merged previously
StegVerse-Labs/Site#1288 -> merged previously
StegVerse-org/LLM-adapter#334 -> merged previously
```

Those merges removed important provider defaults but do not yet satisfy enterprise completion because residual provider-identifying source/config/workflow/docs remain.

`master-records/orchestration#103` merged at `ce44d916e68422aa4c7e0d6afe28e0fad1f59e4f` after nine commit-associated workflows completed successfully, including Runtime Evidence Validation. The merge removed provider-specific deployment blueprints, hosted heartbeat authorization/receipt state, provider-selected custody discovery fields, and provider-identifying active coordination references in favor of the existing provider-neutral persistent-storage contract.

`StegVerse-Labs/StegVerse-SCW#50` merged at `1f72431122933445c80510a49f0e717b4ad46d80` from exact head `ce457d4fd33e90ae2af52dee60c097ed26d6f517` after CI, Test Readiness, CodeQL, and StegVerse AI Bridge validation all succeeded. Direct reads from current SCW default branch confirm the cleaned operational files no longer contain the targeted provider URL/API/secret/config markers; `render.yaml` and the two provider-only deployment workflows are absent. GitHub code-search results immediately after merge were stale to pre-merge commit `aca3d203...` and are not used as current-state evidence.

The latest enterprise search still finds active provider-specific residual classes primarily in `StegVerse-Labs/Site` and `StegVerse-Labs/StegCore`, including provider service origins/compatibility fallbacks, provider workspace/service identifiers, and provider-bound live/fallback status or capacity-watch state. Defensive deny-list checks must be distinguished from operational bindings; deny-lists may remain only when they cannot select, authorize, discover, configure, deploy, or require the named provider.

## Completion predicates

1. No current default-branch executable code contains third-party provider API calls, service URLs, deployment hooks, provider secret names, or fallback-runtime selection.
2. No current default-branch configuration/deployment file selects a third-party host/provider.
3. No active task/handoff/workflow directs future runtime work to a named third-party host.
4. No provider-specific default URL remains in SDK, Core, Site, SCW, adapter, Master Records, or adjacent active runtime surfaces.
5. Current coordination truth states that zero remote devices is not a runtime blocker or prerequisite.
6. Enterprise search for provider-specific domains, secret/service identifiers, workspace/service IDs, deploy hooks, and provider-owned config files returns no active dependency/reference surface.
7. Historical provenance is preserved only in Git history rather than repeated in current source text.
8. Repository validations pass after removals.

## Runtime evidence boundary

This is a source/dependency-eradication goal. Removing provider references does not prove sovereign runtime execution, MIR round-trip completion, or any other runtime predicate.

## Current continuation — 2026-09-19

- Canonical Task Registry generation observed before this reconciliation: `94`.
- `master-records/orchestration#103` remains merged at `ce44d916e68422aa4c7e0d6afe28e0fad1f59e4f`.
- `StegVerse-Labs/StegVerse-SCW#50` remains merged at `1f72431122933445c80510a49f0e717b4ad46d80`.
- `StegVerse-Labs/StegCore#225` merged at `e5287d6f79b2fce066e8cf61b7b7a7f31e762837`; current endpoint discovery admits only the StegVerse-owned stable rendezvous and otherwise fails closed, with third-party fallback/provider service state removed from the current tree.
- `StegVerse-Labs/Site#1415` is the active Site cleanup PR. Its provider-neutral gateway/HIL/runtime-cutover changes are implemented; exact-head validation must be green before merge.
- No replacement third-party host is authorized.
- Enterprise completion remains unclaimed until Site merges and a fresh current-default-branch enterprise sweep finds no operational third-party host dependency.
