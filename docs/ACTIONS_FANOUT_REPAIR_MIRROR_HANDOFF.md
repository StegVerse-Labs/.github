# Actions Fanout Repair Mirror Handoff

Updated: 2026-08-22
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

## Current live fanout state

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

### Preserved semantics

- Organization handoff rendering still executes and requires committed projection parity.
- Archive readiness still executes its validator and unittest.
- Organization heartbeat source validation moved to the stable Heartbeat Worker dispatcher without restoring routine state/receipt main-push fanout.
- Watchdog diagnostics remain manually invocable only; they were not added to automatic PR/push execution.
- Native-process canary and host self-attest are both terminal `COMPLETED` tasks with successor policy `NONE`; only retained evidence validation remains and no task reactivation was introduced.
- External timing source/validation is `COMPLETE_RELEASED`; fixed-cadence and zero-authority assertions remain in the stable dispatcher. Live timing consumption remains owned by `.github#122`.

## Prior fanout containment retained

- Heartbeat Worker direct-main machine-commit storm fanout was removed by `f55b7d653044bb2e1be3c6b2c2e736241389c3ab`. Healer later restored automatic validation only for exact source needed by absorbed workflows; routine carrier/state/receipt persistence remains excluded.
- Test-lanes direct-main validation removed by `599cac6417bc67874416d2b0125929a2601f8fe2`; PR/manual retained with concurrency cancellation.
- Organization control blanket `scripts/**`, `tests/**`, and `heartbeat_runtime/**` main fanout narrowed by PR #247 / `52c64f0fbf2b6375a5546a0a2af0d5000f4fcef4`.
- Full Heartbeat Worker suite is green: run `32588349952`, 486 tests, zero failures.
- Ecosystem Chat inference validation is green: `32588349889`; reference proof rejects `qualifies_as_large_production_llm=true`.

## Remaining `.github` workflow surface

Eleven workflow files remain. Eight have selective automatic source pushes; three are PR/manual-only. The registry is authoritative for current classification.

The remaining non-dispatcher surfaces are now predominantly active-owner-sensitive. For example, `STEGGATE-STABLE-RENDEZVOUS-WORKER-001` remains `HANDOFF_READY` with live deployment/runtime work unfinished, so its validator is retained pending owner reconciliation rather than removed merely to lower the count. Sovereign runtime, federation, inference, MCP, StegFin, and test-lane surfaces likewise require owner-safe classification.

Healer #34 remains open. Any final count above two requires explicit technical necessity evidence.

## Site cost lane

User-provided GitHub billing evidence on 2026-08-22 showed Site as the largest observed StegVerse-Labs Actions repository cost center at `$201.44`, compared with `.github` at `$31.66` at that observation point.

Site has an existing B27 cost-reduction task/claim (`SITE-ACTIONS-COST-CONTAINMENT-001-B27`, PR #387) to retire the hourly Thought Experiments workflow. Source changes and the Healer native validation carrier exist, but exact-head live validation still requires the machine-owned `SHWP-HEALER-SOVEREIGN-SCHEDULER-001` receipt. The scheduler handoff remains `HANDOFF_READY`; no scheduler receipt is present. GitHub CI/source merge cannot substitute for that transition.

A separate high-value Site candidate has been proven but not mutated: `.github/workflows/va-claims-guide-surface.yml` uses a six-hour hosted schedule, `contents: write`, credential-persisting checkout, repository receipt writeback, and artifact upload while credential-clean `validate.yml` already runs the same deterministic `scripts/validate_va_claims_guide_surface.py`. A distinct Site pre-work claim is required before mutation.

### 2026-08-22 Site bootstrap fanout finding

A second material Site cost source is now proven from current `main`: `.github/workflows/validate.yml` has unfiltered `push:` and `pull_request:` triggers. The workflow performs the full Site bootstrap lane, including deterministic HIL, Master Records import checks, SV-CONTINUITY-109, VA guided workflow checks, child-safety contract checks, workflow inventory, Site handoff orchestration, ecosystem-heartbeat orchestration, canonical application validation, iPhone heartbeat projection, ST-017 sandbox validation, StegFin phone projection, and the main-push public-wallet observer.

This means routine commits outside those source/config surfaces can still start the complete hosted Site bootstrap job. The workflow is credential-clean (`permissions: {}` and explicit GitHub credential refusal), but credential cleanliness does not remove its hosted-runner cost. The safe repair is trigger narrowing, not disabling validation: retain automatic execution for source/schema/config/workflow changes that affect the validators, exclude routine heartbeat carrier state, receipts, observations, projections, and unrelated persistence, and preserve `workflow_dispatch` for intentional full checks.

Direct mutation was not performed in this pass because the live Site claim registry currently contains an active validation claim (`SITE-STEGFIN-IOS-LOCAL-WALLET-TRANSPORT-388-20260817`) whose `claimed_paths` explicitly include `.github/workflows/validate.yml`; the Site pre-work policy requires one active owner per dependency surface. The fanout defect therefore remains open until that claim releases or the canonical Site claim gate admits a non-overlapping repair.

## Remaining work

1. Continue Healer #34 only after active-owner reconciliation for the remaining owner-sensitive `.github` surfaces.
2. Consume the Site B27 sovereign scheduler receipt when it actually exists; do not substitute hosted CI.
3. Acquire a distinct Site pre-work claim before retiring the redundant VA guide scheduled/writeback/artifact workflow.
4. After the active Site publication-validation claim releases, admit and implement trigger narrowing for `.github/workflows/validate.yml` while preserving source/schema/config automatic validation and manual full validation.
5. Obtain repository-wide quantitative post-repair run history when a supported reader exists.

## Release / propagation

No tag/release is required solely for these workflow-validation consolidations. No public product capability contract changed.

## Completion gate

Cost reduction is materially advanced but nonterminal: `.github` is 18 -> 11 with seven parity-proven removals; remaining `.github` workflows require owner reconciliation, Site remediation remains active, and repository-wide quantitative run-history evidence remains unavailable.

Current status: `DO NOT ARCHIVE THIS SESSION — UNIQUE ACTIVE WORK REMAINS.`
