# Actions Fanout Repair Mirror Handoff

Updated: 2026-08-18
Repository: `StegVerse-Labs/.github`
Branch: `main`
State: ACTIVE

## Authority and invariants

This handoff governs the hosted GitHub Actions cost/fanout repair lane only. It does not grant heartbeat, claim, lease, fence, credential, deployment, wallet, runtime, or control-plane authority.

- Primary runtime/control plane: StegVerse.
- Third-party execution: fallback only when explicitly required and admitted.
- Credential authority: TV/TVC only.
- GitHub token production/runtime authority: NONE.
- Render authority: NONE.
- Hosted workflow success is validation evidence only and never runtime/activation evidence.
- Routine heartbeat/carrier/receipt/observation/projection/event persistence must not automatically trigger paid hosted validation unless a validator genuinely depends on that persistence edge.
- Source/schema/config changes should retain automatic validation where technically useful.
- Pull requests should retain broader pre-merge validation coverage where safe.
- Expensive retained checks must remain manually dispatchable.

## Current repair objective

Reduce avoidable GitHub-hosted Actions fanout without weakening the repository's meaningful source/config/schema regression safety net.

## Repairs installed in this lane

### Previously repaired selective validators

The following validators had already been narrowed from broad state-triggered fanout to selective automatic source/config validation before this handoff was created:

- `.github/workflows/org-control-plane-validate.yml`
- `.github/workflows/heartbeat-worker-project.yml`
- `.github/workflows/org-handoff-render.yml`
- `.github/workflows/org-heartbeat.yml`

These surfaces remain non-authorizing and credential-clean.

### 2026-08-18 repair pass

1. `.github/workflows/all-org-heartbeat-federation.yml`
   - commit: `059617b7d052e3752403297f2c566939753c097b`
   - main push automatic triggers reduced to worker source + workflow definition.
   - `control/organization-federation.json`, `control/organization-task-registry.json`, `control/heartbeat-subsignals.json`, handoff/auth, and cost-basis persistence remain covered on pull requests and manual dispatch, but no longer fan out hosted CI on routine main persistence.

2. `.github/workflows/archive-readiness-validate.yml`
   - commit: `636e14918445230594331b5bb0c6e5c5ff8fbc26`
   - main push automatic triggers reduced to validator source/tests + workflow definition.
   - archive-readiness/worker-registry/prose projection persistence remains covered on pull requests and manual dispatch.

3. `.github/workflows/native-process-worker-canary.yml`
   - commit: `3fa46b8c02711d96835b70dafff8a1fe8bc087e1`
   - historical completed-canary registry/evidence persistence removed from automatic main fanout.
   - canary/process-adapter implementation changes retain automatic validation; PR coverage remains broad.

4. `.github/workflows/steggate-heartbeat-integration.yml`
   - commit: `dc361958985a446b7653d36d86c022788fcbe023`
   - main push automatic triggers reduced to StegGate worker/schema/workflow source.
   - management/control/cost/handoff/authorization persistence remains available to PR validation and manual dispatch without triggering every main-state write.

5. `.github/workflows/activate-host-self-attest-worker.yml`
   - commit: `164094f43f1d2c67a677d760cbf2b981d38da593`
   - historical completed self-attest evidence/handoff/cost persistence removed from automatic main fanout.
   - automatic main validation now occurs only when the retained workflow definition changes; broad evidence validation remains on pull requests and manual dispatch.

## Inspected and retained unchanged

The following candidates were inspected and do not currently create main-branch fanout:

- `.github/workflows/external-timing-match-validation.yml` — pull-request + manual dispatch only.
- `.github/workflows/mcp-activation-binding-test.yml` — pull-request + manual dispatch only.
- `.github/workflows/org-heartbeat-watchdog.yml` — manual diagnostic only.

No mutation was warranted for those surfaces.

## Collision/ownership check

The active machine-owned heartbeat, federation, StegGate, and sovereign-inference lanes retain their execution ownership. This repair changes hosted validation trigger surfaces only and does not acquire or mutate their claims, fences, leases, runtime receipts, deployment authority, or task state.

Relevant source-of-truth handoffs/records inspected before mutation:

- `docs/ORG_MIRROR_HANDOFF.md`
- `docs/ALL_ORGS_HEARTBEAT_FEDERATION_MIRROR_HANDOFF.md`
- `docs/ARCHIVE_GATE_PROGRESS_MIRROR_HANDOFF.md`
- `handoffs/STEGGATE-STABLE-RENDEZVOUS-WORKER-001.json`

## Validation evidence

Post-write repository reads confirmed the narrowed trigger surfaces are present on `main`. The repaired workflows retain `workflow_dispatch` and credential-clean `permissions: {}` semantics. No runtime claim, heartbeat epoch, worker fence, or credential state was mutated by this repair lane.

No hosted workflow pass is claimed as runtime proof.

## Remaining fanout review candidates

The following files remain to be inspected for source-vs-state trigger separation. They are candidates, not asserted defects until inspected against their current handoffs/owners:

- `.github/workflows/activate-sovereign-runtime-worker.yml`
- `.github/workflows/activate-ecosystem-chat-sovereign-inference-worker.yml`
- `.github/workflows/sovereign-ephemeral-console.yml`

Activation/worker workflows must not be narrowed merely for cost reduction if their trigger is itself part of an admitted machine-owned execution path. Their current handoffs/claims must be read first.

## Private-repository adjacent scope

Private-repository repair remains a separate authority/visibility lane. Do not make a private repository public, introduce broad GitHub credentials, or use hosted Actions as a substitute for TV/TVC repository authority. Any private-repository fanout fix must be applied in that repository only after reading its repository-local `*_MIRROR_HANDOFF.md` and current claim/task ownership.

## Known files/modules still to inspect or install

Destination `StegVerse-Labs/.github`:

- inspect trigger/authority semantics for `.github/workflows/activate-sovereign-runtime-worker.yml`;
- inspect trigger/authority semantics for `.github/workflows/activate-ecosystem-chat-sovereign-inference-worker.yml`;
- inspect trigger/authority semantics for `.github/workflows/sovereign-ephemeral-console.yml`;
- if a remaining state-triggered hosted validator is proven redundant, narrow its main push paths without removing source/config validation, PR validation, or manual dispatch.

No missing runtime module is asserted by this fanout lane.

## Release / propagation

No release/tag is required solely for these workflow-trigger configuration changes at this stage. Therefore no aggregate release is claimed. Site, Publisher, admissibility-wiki, and stegguardian-wiki propagation is not required unless a later repair changes a public contract or capability consumed by those surfaces.

## Completion gate

This lane is not terminal while materially redundant automatic hosted fanout remains uninspected or proven, or while a required repair is unvalidated/unintegrated. Durable recording of this handoff does not satisfy the repair objective by itself.

Current status: `DO NOT ARCHIVE THIS SESSION — UNIQUE ACTIVE WORK REMAINS.`
