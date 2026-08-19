# Actions Fanout Repair Mirror Handoff

Updated: 2026-08-18
Repository: `StegVerse-Labs/.github`
Branch: `main`
State: ACTIVE

## Authority and invariants

This handoff governs the hosted GitHub Actions cost/fanout repair lane only. It does not grant heartbeat, claim, lease, fence, credential, deployment, wallet, runtime, repository-visibility, repository-hygiene, or control-plane authority.

- Primary runtime/control plane: StegVerse.
- Third-party execution: fallback only when explicitly required and admitted.
- Credential authority: TV/TVC only.
- GitHub token production/runtime authority: NONE.
- Render authority: NONE.
- Hosted workflow success is validation evidence only and never runtime/activation evidence.
- Routine heartbeat/carrier/receipt/observation/projection/event persistence must not automatically trigger paid hosted validation unless a validator genuinely depends on that persistence edge.
- Source/schema/config changes retain automatic validation where technically useful.
- Pull requests retain broader pre-merge validation coverage where safe.
- Intentionally expensive checks remain manually dispatchable where applicable.
- Repository hygiene and workflow-count minimization belong to `StegVerse-Labs/StegVerse-Healer`; this lane must not independently consolidate/delete workflows merely to reach the <=2 hygiene target.

## Current objective

Reduce avoidable GitHub-hosted Actions fanout without weakening meaningful source/config/schema regression coverage. Detect and repair concrete cost-trigger defects. Do not duplicate the separate StegVerse-Healer hygiene evaluation/cleanup lane.

## Exact live inventory

Canonical machine-readable inventory:

`control/actions-fanout-workflow-inventory-2026-08-18.json`

The inventory contains 18 workflow files: 14 automatic-push validation surfaces and 4 intentionally non-push surfaces. Classification is retained as fanout evidence, but workflow-retention/consolidation authority is now explicitly outside this lane.

```text
live workflow files: 18
automatic-push workflows: 14
non-push workflows: 4
workflow-count hygiene owner: StegVerse-Labs/StegVerse-Healer
Healer evaluation: PR #20 OPEN / MERGEABLE
quantitative post-repair run-history evidence: awaiting supported repository-level run-history read
```

## Selective repairs installed

Earlier repair sequence covered:

- `.github/workflows/all-org-heartbeat-federation.yml`
- `.github/workflows/archive-readiness-validate.yml`
- `.github/workflows/native-process-worker-canary.yml`
- `.github/workflows/steggate-heartbeat-integration.yml`
- `.github/workflows/activate-host-self-attest-worker.yml`
- `.github/workflows/activate-sovereign-runtime-worker.yml`
- `.github/workflows/activate-ecosystem-chat-sovereign-inference-worker.yml`
- `.github/workflows/sovereign-ephemeral-console.yml`
- `.github/workflows/test-lanes-autolaunch-validation.yml`
- `.github/workflows/sovereign-runtime-self-bootstrap.yml`
- `.github/workflows/org-handoff-render.yml`
- `.github/workflows/org-heartbeat.yml`

Direct re-audit then found two stale broad main-push edges and corrected them.

### Corrective repair: organization control-plane validator

PR #229 merged as `f99f4c3eac76bcac8590c4737f62250ac39330df`.

Before correction, `.github/workflows/org-control-plane-validate.yml` still included `handoffs/**` under `push.paths`, so routine executable-handoff persistence could launch the broad organization validator. The repair:

- removed `handoffs/**` from automatic main-push validation;
- retained `handoffs/**` under pull-request coverage;
- retained manual dispatch;
- added the workflow definition itself to automatic push validation;
- changed no validator body, runtime authority, credential semantics, claims, fences, heartbeat state, wallet state, deployment state, or repository visibility.

### Corrective repair: Heartbeat Worker Project

PR #230 merged as `cf4a028047b2359c333cfae150963448e1c41522`.

Before correction, `.github/workflows/heartbeat-worker-project.yml` still included both `handoffs/**` and `cost-basis/worker-runtime/**` under `push.paths`. That meant routine handoff and worker-cost persistence could launch the complete deterministic repository suite plus heartbeat validation. The repair:

- removed `handoffs/**` and `cost-basis/worker-runtime/**` from automatic main-push validation;
- retained both surfaces under pull-request validation;
- retained manual dispatch;
- kept `heartbeat_runtime/**`, `workers/**`, `tests/**`, `schemas/**`, and `scripts/**` automatic;
- added the workflow definition itself to the automatic push surface;
- changed no validation body or runtime/control-plane authority.

## Retained unchanged after inspection

- `.github/workflows/external-timing-match-validation.yml` — pull-request + manual dispatch only.
- `.github/workflows/mcp-activation-binding-test.yml` — pull-request + manual dispatch only.
- `.github/workflows/org-heartbeat-watchdog.yml` — manual diagnostic only.
- `.github/workflows/stegfin-early-adopter-contribution-validator-source.yml` — pull-request only, `permissions: {}`, empty GitHub credential authority, and fail-closed behavior when private source is absent.
- `.github/workflows/native-process-worker-canary.yml` — implementation-only main trigger; handoff/cost/control state remains PR-only.
- `.github/workflows/activate-host-self-attest-worker.yml` — workflow-definition-only main trigger; retained evidence/handoff/cost surfaces remain PR-only.
- `.github/workflows/org-heartbeat.yml` — heartbeat runtime/source only on main; mutable claim/org-state surfaces remain PR-only.
- `.github/workflows/all-org-heartbeat-federation.yml` — worker/workflow source only on main; mutable federation/handoff/auth/cost surfaces remain PR-only.
- `.github/workflows/steggate-heartbeat-integration.yml` — worker/schema/workflow source only on main; mutable integration/handoff/auth/cost surfaces remain PR-only.
- `.github/workflows/test-lanes-autolaunch-validation.yml` — matrix/config/worker/test/workflow source on main; worker-registry/handoff/auth/cost state remains PR-only.

## Healer hygiene dependency boundary

Repository hygiene and the preferred `0/1/2` workflow-surface policy are now treated as `StegVerse-Labs/StegVerse-Healer` responsibilities.

Current durable dependency:

```text
repository: StegVerse-Labs/StegVerse-Healer
PR: #20
state: OPEN / MERGEABLE
title: Evaluate .github workflow hygiene and 18→2 consolidation hypothesis
head: eval/github-root-workflow-hygiene-v2
head_sha: 4882a0c3c7b52cb7e1e5c2df93f77b2bdcc72e15
```

PR #20 transfers the evidence and 18→2 hypothesis for Healer evaluation only. It does not authorize deletion and does not prove parity, consolidation, runtime activation, or hygiene completion.

This fanout lane must therefore:

- continue repairing concrete trigger/failure/cost defects when independently proven;
- provide evidence to Healer when a workflow is a consolidation/transfer candidate;
- not delete, merge, or reorganize workflow surfaces solely for hygiene-count reduction while Healer owns that evaluation;
- consume Healer's accepted outcome once it becomes durable, then re-audit cost/fanout behavior of the resulting workflow surface.

## Collision / ownership boundaries

The active machine-owned heartbeat, federation, StegGate, durable-runtime, sovereign-inference, canonical test-lanes, StegFin, oscillator-live-proof, repository-visibility, and Healer hygiene lanes retain their own execution authority. This fanout lane does not acquire or mutate their claims, fences, leases, runtime receipts, deployment state, wallet authority, provider authority, task state, canonical test-run claims, repository visibility, or hygiene decisions.

## Validation evidence

- Direct live reads proved the stale `org-control-plane-validate.yml` and `heartbeat-worker-project.yml` main-push edges.
- PR #229 merged `f99f4c3eac76bcac8590c4737f62250ac39330df`.
- PR #230 merged `cf4a028047b2359c333cfae150963448e1c41522`.
- Current Healer PR #20 is independently observed OPEN and MERGEABLE at head `4882a0c3c7b52cb7e1e5c2df93f77b2bdcc72e15`.
- No runtime claim, heartbeat epoch, worker fence, credential state, repository visibility, deployment state, wallet state, oscillator runtime state, canonical test-run claim, or hygiene cleanup authority was mutated by this lane.

## Remaining work

Destination `StegVerse-Labs/.github`:

- continue direct live-file audit only for concrete automatic-trigger/failure/cost defects not already repaired;
- update the machine-readable inventory if further fanout defects are proven;
- obtain repository-wide post-repair Actions run-history evidence sufficient to quantify actual fanout reduction once a supported read path is available;
- consume the eventual StegVerse-Healer workflow-hygiene decision and re-audit the resulting stable workflow surface for cost/fanout regressions.

Destination `StegVerse-Labs/StegVerse-Healer` (dependency lane; do not duplicate here):

- evaluate PR #20 reasoning;
- independently classify the current `.github` workflow surface;
- if admitted, implement workflow consolidation/transfer/elimination with validation-parity evidence and owner reconciliation;
- record any >2 standalone exceptions with technical necessity.

The connected GitHub workflow-run reader exposes commit-associated pull-request runs but not the repository-wide run listing required for quantitative before/after proof. No unsupported credential-bearing workaround is authorized.

## Release / propagation

No release/tag is required solely for these validation-trigger/inventory/handoff changes. No aggregate release is claimed. Site, Publisher, admissibility-wiki, and stegguardian-wiki propagation is not required unless a later repair changes a public contract or capability consumed by those surfaces.

## Completion gate

The fanout lane remains nonterminal because repository-wide quantitative post-repair run-history evidence is unavailable and future Healer consolidation output must be consumed/re-audited. Workflow-count hygiene itself is an active dependency lane, not unique work owned here.

Current status: `DO NOT ARCHIVE THIS SESSION — REQUIRED EXECUTION REMAINS IN AN ACTIVE DEPENDENCY LANE.`
