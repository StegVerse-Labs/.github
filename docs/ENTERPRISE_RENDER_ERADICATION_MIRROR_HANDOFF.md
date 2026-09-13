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

## Current source-remediation state — 2026-09-13

Canonical enterprise/device correction:

- `.github` PR `#1704` merged at `570cefbd41df264948665b8d8f511560dc25d1e0` after Organization Control Plane, Heartbeat Worker, and Deterministic Repository Suite validation passed.
- `.github` progress reconciliation PR `#1710` merged at `886b55178822fc877559766edaf617a09960d664` after the same three validation lanes passed.
- The merged contract makes remote-device connector availability optional and explicitly rejects zero connected devices as a runtime blocker.

Repository cleanup projections:

- `StegVerse-Labs/TVC#421`: current branch removes hosted-fallback and remote-device prerequisite assumptions; exact-head validation remains pending/unobserved.
- `StegVerse-Labs/StegCore#212`: provider-specific live-service placement text removed on branch; exact-head repository validation remains unobserved.
- `StegVerse-org/LLM-adapter#334`: active HIL workboard provider targets removed; exact head `b0468a2e6d350fd9b1d6a080bb16cc08dfb9c002` passed repository `validate` and Work Mutation Safety and merged at `300c40b9842752f522b3d519d8f8043f2e28b408`.
- legacy `StegVerse-org/LLM-adapter#23` provider-host Blueprint PR is closed as superseded and must not be revived.
- `StegVerse-org/StegVerse-SDK#230`: hard-coded StegCore provider origin removed; explicit admitted runtime origin is required. Exact head `23d6cd76eb15c6bbc292ff2f938154b6b43c1270` passed SDK Package Artifact Validation. PR remains unmerged.
- `StegVerse-Labs/Site#1288`: provider-bound demo/debug targets removed and generic external-host guard retained. Exact head `02a7ae5b8a3af64c3435887b04ce03ef1b2ab9d7` passed Site Bootstrap, Site Handoff Orchestrator, Ecosystem Heartbeat Orchestration, and Node IndexedDB Schema Migration, then merged at `24ec65a39449ad9d0d0c102151a7b262511a33a4`.
- `StegVerse-Labs/StegVerse-SCW#45`: provider-specific UI host heuristic, StegTalk API fallback, config-seeder example, environment-template provider defaults/hooks, and supercheck diagnostic target have been removed on branch `remove-render-provider`. A CI lint failure in `scripts/ops/seed_config.py` was isolated to import formatting and one long line and corrected at `5a4099fe3fbbbad7dab15900c6831f3057eea0ee`; fresh exact-head CI is pending. `api/routes/ops.py` and diagnostic surfaces still contain active provider-specific references and remain open remediation.
- `StegVerse-Labs/StegSports-CFP#2`: ticket API hosted fallback removed; exact-head Test Readiness passed. Dashboard hosted fallback remains a residual and the PR is not enterprise-clean yet.
- `StegVerse-Labs/StegPay#4`: retired standalone provider-specific deployment instructions removed; no exact-head validation observed yet and provider config residue still requires search/remediation.
- `StegVerse-Labs/Continuity#16`: legacy provider-specific continuity configuration removed from the edited README; no exact-head validation observed yet and broader residue search remains required.

Direct PR merge attempts for some otherwise mergeable cleanup PRs were blocked by the connected mutation safety layer. Those PRs must remain classified as source-validated/unmerged where applicable; no merge is inferred.

## Remaining active remediation

1. Remove remaining SCW provider deploy-hook/config/default URL surfaces, especially `api/routes/ops.py` and diagnostics, and require fresh exact-head CI after each functional edit set.
2. Remove StegSports dashboard hosted fallback.
3. Search/clean active provider configuration in StegPay, Continuity, TVC, Site, LLM Adapter status/work surfaces, and other discovered repositories.
4. Merge source-validated SDK cleanup when the mutation surface permits; do not infer merge from CI.
5. Enumerate retained historical-provenance references separately from active dependencies.
6. Re-run enterprise search after current-tree removals and require repository validation before completion.

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
