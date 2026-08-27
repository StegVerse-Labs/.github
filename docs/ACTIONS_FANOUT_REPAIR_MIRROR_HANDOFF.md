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
current workflow files: 2
automatic-push workflows: 2
PR/manual-only workflows: 1
Healer workflows removed with parity: 16
stable dispatchers: 2
repository hygiene owner: StegVerse-Labs/StegVerse-Healer#34
repository-wide quantitative run-history proof: AWAITING_SUPPORTED_READ
```

Live `main` now contains exactly these two workflow files:

```text
heartbeat-worker-project.yml
org-control-plane-validate.yml
```text
heartbeat-worker-project.yml
org-control-plane-validate.yml
stegfin-early-adopter-contribution-validator-source.yml
```text
activate-ecosystem-chat-sovereign-inference-worker.yml
heartbeat-worker-project.yml
org-control-plane-validate.yml
stegfin-early-adopter-contribution-validator-source.yml
steggate-heartbeat-integration.yml
```text
activate-ecosystem-chat-sovereign-inference-worker.yml
activate-sovereign-runtime-worker.yml
heartbeat-worker-project.yml
org-control-plane-validate.yml
sovereign-ephemeral-console.yml
sovereign-runtime-self-bootstrap.yml
stegfin-early-adopter-contribution-validator-source.yml
steggate-heartbeat-integration.yml
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

Healer #34 remains OPEN. No non-dispatcher workflows remain and require owner reconciliation or explicit standalone-exception evidence before any further removal. The active classes include sovereign runtime, inference, federation, MCP, StegFin, StegGate rendezvous, ephemeral console/bootstrap, and test-lane ownership. Count >2 is not terminal without evidence-backed technical exceptions.

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

## Sovereign runtime dependency relevant to cost migration — corrected 2026-08-26

Heartbeat activation is terminal and is **not** a blocker for Actions cost migration. The canonical heartbeat is HB32 protocol-derived / 10 ms / 100 Hz / `OSCILLATOR_ONLY`; LIVE-009 is completed and issue #12 is closed.

The remaining upstream dependency for the Healer scheduler is the separate `SHWP-DURABLE-RUNTIME-ACTIVATION` worker/runtime substrate. Current authoritative evidence:

```text
handoff: handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json
receipt: receipts/sovereign-runtime-activation/SHWP-DURABLE-RUNTIME-ACTIVATION.json
state: BLOCKED
blocker: SOVEREIGN_NODE_DECLARATION_NOT_PRESENT
claim: existing G18 / fence18 machine-owned
heartbeat dependency: false
third-party primary runtime required: false
current iPhone HB30 action required: false
```

The historical `SHWP-IPHONE-HB30-INLINE-CAPSULE-002` physical boundary is satisfied/superseded: HB30/HB31 provenance and its verified portable-transition digest are already present, and current heartbeat authority is the HB32 protocol anchor. Do **not** rerun the HB30 capsule.

To unblock the scheduler, identify/provision an eligible StegVerse-owned/federated sovereign node and let the existing G18 runtime worker perform canonical native installation/verification. No new scheduler, heartbeat, GitHub-token runtime, Render path, or NON-TV/TVC credential lane is authorized.

## 2026-08-26 test-lanes validation consolidation

`.github/workflows/test-lanes-autolaunch-validation.yml` was retired as a redundant PR/manual-only validation carrier.

Coverage was preserved by moving its workflow-only native binding assertions into `tests/test_test_lanes_autolaunch_binding.py`, which is consumed by the stable `heartbeat-worker-project.yml` complete deterministic unittest suite on relevant pull requests. Existing matrix, worker-boundary, registry-fragment, handoff, authorization and cost-basis surfaces remain unchanged.

```text
workflow count: 11 -> 10
automatic-push workflows: 2 -> 8
PR/manual-only workflows: 1 -> 2
standalone workflows removed with parity preservation: 7 -> 8
runtime authority effect: NONE
test-lanes runtime task changed: false
credential authority: TV/TVC
```

## 2026-08-27 federation and MCP consolidation

Two more standalone validation workflows were removed after preserving their unique validation semantics in the stable heartbeat-worker dispatcher:

```text
removed: .github/workflows/all-org-heartbeat-federation.yml
preserved federation coverage: tests/test_organization_federation_binding.py + existing federation worker/emitter suites
removed: .github/workflows/mcp-activation-binding-test.yml
preserved MCP coverage: tests/test_sdk_mcp_activation_binding.py + tests/test_sdk_mcp_canonical_validation_worker.py
stable destination: .github/workflows/heartbeat-worker-project.yml
runtime/task ownership changed: false
credential authority: TV/TVC
GitHub runtime authority: NONE
```

The federation issue #81 and SDK MCP canonical execution task remain nonterminal machine-owned runtime goals; removing duplicate hosted validation carriers does not complete or cancel those tasks.

Current live workflow census after direct repository listing:

```text
workflow files: 8
automatic-push workflows: 2
PR-only workflows: 0
stable dispatchers: 2
non-dispatchers remaining: 6
```

## 2026-08-27 sovereign runtime validation consolidation

Three sovereign-runtime validation-only workflows were consolidated into the stable heartbeat-worker dispatcher:

```text
removed: .github/workflows/activate-sovereign-runtime-worker.yml
removed: .github/workflows/sovereign-runtime-self-bootstrap.yml
removed: .github/workflows/sovereign-ephemeral-console.yml
stable destination: .github/workflows/heartbeat-worker-project.yml
preserved suites:
  tests/test_bootstrap_sovereign_runtime.py
  tests/test_sovereign_ephemeral_console.py
  tests/test_ephemeral_separated_runtime_supervision.py
  tests/test_g18_self_bootstrap_worker.py
  tests/test_g18_task_capable_release_guard.py
  tests/test_hb29_state_transition_carrier_contract.py
  tests/test_sovereign_runtime_handoff_v12_contract.py
runtime task changed: false
G18 claim/fence changed: false
sovereign-node blocker changed: false
credential authority: TV/TVC
GitHub runtime authority: NONE
```

The stable dispatcher now watches the corresponding runtime source/test/contract paths on main and pull requests, so the hosted validation surface is reduced without deleting the native runtime implementation or converting CI into runtime authority.

Current live workflow census:

```text
workflow files: 5
automatic-push workflows: 2
PR-only workflows: 0
stable dispatchers: 2
non-dispatchers remaining: 3
```

## 2026-08-27 inference and StegGate consolidation

Two additional validation-only hosted lanes were folded into the stable heartbeat-worker dispatcher:

```text
removed: .github/workflows/activate-ecosystem-chat-sovereign-inference-worker.yml
preserved: tests/test_ecosystem_chat_inference_binding.py
preserved existing runtime-source suites:
  tests/test_independent_ecosystem_chat_parent_executor.py
  tests/test_llm_adapter_sovereign_execution_bridge.py
  tests/test_master_records_sovereign_reconstruction_bridge.py

removed: .github/workflows/steggate-heartbeat-integration.yml
preserved: tests/test_steggate_integration_binding.py
stable destination: .github/workflows/heartbeat-worker-project.yml

inference machine-owned task changed: false
StegGate rendezvous task changed: false
credential authority: TV/TVC
GitHub runtime authority: NONE
```

The stable dispatcher now watches the corresponding inference and StegGate source/authorization/handoff paths. Runtime execution, fresh fences, TVC route admission, rendezvous execution and Master Records reconstruction remain separate machine-owned outcomes.

Current live workflow census:

```text
workflow files: 3
automatic-push workflows: 2
PR-only workflows: 0
stable dispatchers: 2
non-dispatcher remaining: 1
```

## 2026-08-27 StegFin source-validation consolidation

The final non-dispatcher, `.github/workflows/stegfin-early-adopter-contribution-validator-source.yml`, was consolidated after its public boundary tests were converted to dependency-free `unittest` and absorbed into `heartbeat-worker-project.yml`.

```text
removed standalone workflow: stegfin-early-adopter-contribution-validator-source.yml
private-source worker task changed: false
private StegFin source materialized: false
hosted pytest installation removed: true
stable workflow count: 2
automatic-push workflows: 2
PR-only standalone workflows: 0
non-dispatchers: 0
preferred workflow target: SATISFIED
credential authority: TV/TVC
GitHub runtime authority: NONE
```

The exact private-source validation outcome remains pending under its machine-owned handoff; workflow minimization does not imply private-source validation completion.

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

Cost reduction is materially advanced but nonterminal. `````.github` is 18 -> 2 with sixteen parity-preserving removals/consolidations; the preferred 0/1/2 target is reached; Site #268 remains active; VA governed-surface observation, Healer scheduler live receipt, Site #388 publication proof, B27, and quantitative run-history evidence remain unresolved.

Current status: `DO NOT ARCHIVE THIS SESSION — UNIQUE ACTIVE WORK REMAINS.`
