# Actions Fanout Repair Mirror Handoff

Updated: 2026-08-26
Repository: `StegVerse-Labs/.github`
Branch: `main`
State: ACTIVE_COST_REDUCTION_AND_DEPENDENCY_FOLLOWUP

## Authority

This lane owns hosted GitHub Actions cost/fanout defects. Repository hygiene/workflow-count minimization is owned by `StegVerse-Labs/StegVerse-Healer#34`; admitted Healer outputs are consumed here and re-audited for fanout regressions.

- Primary runtime/control plane: StegVerse.
- Credential authority: TV/TVC only.
- GitHub-token production/runtime authority: NONE.
- NON-TV/TVC secret/token: prohibited.
- Render: prohibited.
- Hosted workflow success is validation evidence only, never runtime/activation evidence.
- Workflow transfer/consolidation does not satisfy runtime/product goals.

## Current live `.github` fanout state

Canonical machine evidence: `control/actions-fanout-workflow-inventory-2026-08-18.json`.

```text
baseline workflow files: 18
current workflow files: 11
automatic-push workflows: 8
PR/manual-only workflows: 3
Healer workflows removed with parity: 7
stable dispatchers: 2
repository hygiene owner: StegVerse-Labs/StegVerse-Healer#34
repository-wide quantitative run-history proof: AWAITING_SUPPORTED_READ
```

Live `main` still contains exactly these eleven workflow files:

```text
activate-ecosystem-chat-sovereign-inference-worker.yml
activate-sovereign-runtime-worker.yml
all-org-heartbeat-federation.yml
heartbeat-worker-project.yml
mcp-activation-binding-test.yml
org-control-plane-validate.yml
sovereign-ephemeral-console.yml
sovereign-runtime-self-bootstrap.yml
stegfin-early-adopter-contribution-validator-source.yml
steggate-heartbeat-integration.yml
test-lanes-autolaunch-validation.yml
```

Stable dispatchers:

```text
.github/workflows/org-control-plane-validate.yml
.github/workflows/heartbeat-worker-project.yml
```

## Healer consolidations consumed

All seven tranches were exact-head validated by both retained dispatcher families before merge.

| Removed standalone workflow | Retained destination | PR | Merge | Heartbeat Worker | Org control | Result |
| --- | --- | ---: | --- | ---: | ---: | --- |
| `org-handoff-render.yml` | `org-control-plane-validate.yml` | #251 | `82a5909aa37ea228e9c00dd55fc1e11ab706850b` | 32590490975 | 32590490904 | PASS |
| `archive-readiness-validate.yml` | `org-control-plane-validate.yml` | #252 | `fae7f6a1edc4d54dd67134773faf76acc87eae59` | 32590584716 | 32590584788 | PASS |
| `org-heartbeat.yml` | `heartbeat-worker-project.yml` | #253 | `2236df65a495975ca9bc7d9c8fad7d863934617f` | 32590794869 | 32590794862 | PASS |
| `org-heartbeat-watchdog.yml` | `heartbeat-worker-project.yml` manual dispatch only | #254 | `c3256be218dbabdf4fb82e877e71d2884925c904` | 32590947641 | 32590947607 | PASS |
| `native-process-worker-canary.yml` | `heartbeat-worker-project.yml` | #255 | `856d1823283f3ade54ac95094d73ec149c245d74` | 32591051012 | 32591050991 | PASS |
| `external-timing-match-validation.yml` | `heartbeat-worker-project.yml` | #256 | `278299617d17a4f410b0ef0e2d1da1a609b67fc4` | 32591188347 | 32591188133 | PASS |
| `activate-host-self-attest-worker.yml` | `heartbeat-worker-project.yml` | #257 | `1240cc0087f5777b08c1913561d4b7125df74cbf` | 32591396135 | 32591396122 | PASS |

Preserved semantics include deterministic handoff rendering, archive-readiness validation, heartbeat source validation without routine state/receipt main-push fanout, manual-only watchdog diagnostics, terminal native-canary/host-self-attest evidence validation, and fixed-cadence external-timing validation. Live timing consumption remains `.github#122`.

Prior containment remains installed: Heartbeat Worker routine main state fanout removal (`f55b7d653044bb2e1be3c6b2c2e736241389c3ab`), test-lanes direct-main removal (`599cac6417bc67874416d2b0125929a2601f8fe2`), and org-control blanket trigger narrowing via PR #247 / `52c64f0fbf2b6375a5546a0a2af0d5000f4fcef4`.

The full Heartbeat Worker suite is green: run `32588349952`, 486 tests, zero failures. Ecosystem Chat inference validation is green in `32588349889`, and reference proof rejects `qualifies_as_large_production_llm=true`.

## Remaining `.github` hygiene work

Healer #34 remains OPEN. Nine non-dispatcher workflows are predominantly owner-sensitive and require owner reconciliation or explicit standalone-exception evidence before any further removal. The active classes include sovereign runtime, inference, federation, MCP, StegFin, StegGate rendezvous, ephemeral console/bootstrap, and test-lane ownership. Count >2 is not terminal without evidence-backed technical exceptions.

Canonical hygiene authority:

```text
StegVerse-Labs/StegVerse-Healer/docs/HEALER_GITHUB_ROOT_WORKFLOW_HYGIENE_MIRROR_HANDOFF.md
StegVerse-Labs/StegVerse-Healer#34
```

## Site Actions cost dependency — current state

Canonical Site authority is `StegVerse-Labs/Site/docs/ACTIONS_COST_CONTAINMENT_MIRROR_HANDOFF.md` / Site #268.

The older statement that `.github/workflows/va-claims-guide-surface.yml` was merely a candidate is superseded. The VA Claims Guide cost repair is RELEASED in Site's canonical handoff (Site #428); do not recreate that lane.

### VA governed surfaces deployment observer

Site PR #473 merged as `b526c69a647b96cf8ee6e9e44aca0facc1d61241` after exact-head Site Handoff `32669715065`, Ecosystem Heartbeat `32669715039`, and Site Bootstrap `32669715040` all succeeded.

The merge removed the six-hour schedule, `contents: write`, credential-bearing checkout/setup dependencies, repository observation writeback, and artifact custody while retaining bounded `main` source-change and intentional manual deployment verification.

Canonical detailed handoff:

`StegVerse-Labs/Site/docs/VA_GOVERNED_SURFACES_DEPLOYMENT_ACTIONS_FANOUT_MIRROR_HANDOFF.md`

Current state is `MERGED_AWAITING_TASK_SPECIFIC_MAIN_OBSERVATION`, not released. The connected GitHub reader does not expose push-triggered workflow runs, so a retained task-specific current-main observer run with `VA_GOVERNED_SURFACES_DEPLOYMENT=VERIFIED`, or equivalent current-main execution receipt, is still required.

### Executive Rhetoric Ledger sync migration

Healer issue #39 / PR #40 migrated the intended daily Site Executive Rhetoric Ledger synchronization behavior into the existing sovereign Healer scheduler. PR #40 exact head `aca5b7871e2720b0d56757e33fc2a22c10291136` passed Test Readiness `32670203077` / job `97269769966` and merged as `ff3d9985b773d91dce0d90351a7a8a04a499c59b`.

Canonical detailed handoff:

`StegVerse-Labs/StegVerse-Healer/docs/SITE_ERL_SOVEREIGN_SYNC_MIRROR_HANDOFF.md`

Source state is `COMPLETE_RELEASED`; live execution remains `MACHINE_OWNED_PENDING_SCHEDULER_RECEIPT`. The required receipt is:

`receipts/healer-sovereign-scheduler/SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json`

Live inspection still returns NOT FOUND. The existing Site `sync-executive-rhetoric-ledger.yml` must remain until that receipt proves `executive-rhetoric-ledger-local-sync` COMPLETE/PASS. Retiring the Site carrier before then would create an execution gap.

The existing resident task is not duplicated: `SHWP-HEALER-SOVEREIGN-SCHEDULER-001` remains `HANDOFF_READY`, executor `AUTHORIZED`, worker available. Its machine handoff and registry already consume Healer #40 evidence.

### Site full bootstrap / `validate.yml`

The full Site bootstrap surface still has a real fanout defect opportunity, but its path remains actively claimed by `SITE-STEGFIN-IOS-LOCAL-WALLET-TRANSPORT-388-20260817`.

Current Site receipt `receipts/stegfin-ios-local-wallet-transport-388-validation.json` says:

```text
repository_integration: COMPLETE
publication_observer_state: BOUND_EXECUTION_PENDING_CORRECTED_BOOTSTRAP
classification: SOURCE_AND_SITE_MERGED_CORRECTED_PUBLICATION_PROOF_PENDING
release_blocked: true
```

Release requires credential-clean main-push publication proof for exact wallet UI blob `114b3c39052d5b1622407080407259a0040a1369` and corrected bootstrap blob `dc1a86bc564146cdaa645620c8fc698e45029440`. Only after that claim releases may Site admit trigger narrowing for `.github/workflows/validate.yml`.

### Thought Experiments B27

Site B27 remains a machine-owned native-validation continuation. Its sovereign validation carrier exists, but the same `SHWP-HEALER-SOVEREIGN-SCHEDULER-001` live receipt is still required before the B27 retirement can be finalized. Source/CI cannot substitute for that receipt.

## Heartbeat/runtime dependency relevant to cost migration

The Healer scheduler task depends on `SHWP-DURABLE-RUNTIME-ACTIVATION`. Current machine state still has no scheduler receipt. The released iPhone inline source handoff `handoffs/SHWP-IPHONE-HB30-INLINE-CAPSULE-002.json` records the outstanding physical boundary:

```text
carrier: CURRENT_USER_IPHONE
operational_state: HUMAN_PHYSICAL_EXECUTION_BOUNDARY
condition: PHYSICAL_RECEIPT_NOT_YET_OBSERVED
human_action_required: true
```

The current iPhone must execute the exact released inline capsule in an existing secure `https://stegverse.org` Safari context and transfer the portable receipt to the existing `.github#209` verifier/materializer. That physical action requires no new credential and grants no runtime/wallet/provider authority. G18 and WorkerCoordinator then own HB30 materialization/observation.

## Quantitative evidence limitation

Repository-wide quantitative post-repair Actions run-history evidence remains `AWAITING_SUPPORTED_READ`. The connected commit workflow reader exposes PR-triggered runs only and cannot supply complete push/schedule history. No GitHub token or alternate credential workaround is permitted.

## Release / propagation

No tag/release is required solely for these workflow-validation consolidations. No public product capability contract changed. Runtime/product activation and downstream publication remain governed by their own handoffs.

## Next executable actions

1. Healer #34: reconcile one remaining owner-sensitive `.github` workflow at a time; consolidate/transfer/eliminate only with parity and owner safety, otherwise record an evidence-backed standalone exception.
2. Consume a real `SHWP-HEALER-SOVEREIGN-SCHEDULER-001` receipt when it appears. Only then may Site finalize B27 and admit retirement of the legacy Executive Rhetoric Ledger GitHub-token carrier.
3. Observe the retained Site VA governed-surfaces current-main verifier and release that claim only on task-specific VERIFIED evidence.
4. After Site claim #388 actually releases, admit and implement safe `validate.yml` trigger narrowing.
5. Continue Site #268 workflow census on collision-free released/terminal responsibilities.
6. Obtain repository-wide quantitative post-repair run history only when a supported credential-free reader exists.

## Completion gate

Cost reduction is materially advanced but nonterminal. `.github` is 18 -> 11 with seven parity-proven removals; Healer #34 still has nine owner-sensitive non-dispatchers; Site #268 remains active; VA governed-surface observation, Healer scheduler live receipt, Site #388 publication proof, B27, and quantitative run-history evidence remain unresolved.

Current status: `DO NOT ARCHIVE THIS SESSION — UNIQUE ACTIVE WORK REMAINS.`
