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
current workflow files: 12
automatic-push workflows: 9
PR/manual-only workflows: 3
Healer workflows removed with parity: 6
stable dispatchers: 2
repository hygiene owner: StegVerse-Labs/StegVerse-Healer#34
repository-wide quantitative run-history proof: AWAITING_SUPPORTED_READ
```

The two stable dispatcher candidates are now concretely established:

```text
.github/workflows/org-control-plane-validate.yml
.github/workflows/heartbeat-worker-project.yml
```

## Healer consolidations consumed

All six tranches were exact-head validated by both retained dispatcher families before merge.

| Removed standalone workflow | Retained destination | PR | Merge | Heartbeat Worker | Org control | Result |
| --- | --- | ---: | --- | ---: | ---: | --- |
| `org-handoff-render.yml` | `org-control-plane-validate.yml` | #251 | `82a5909aa37ea228e9c00dd55fc1e11ab706850b` | 32590490975 | 32590490904 | PASS |
| `archive-readiness-validate.yml` | `org-control-plane-validate.yml` | #252 | `fae7f6a1edc4d54dd67134773faf76acc87eae59` | 32590584716 | 32590584788 | PASS |
| `org-heartbeat.yml` | `heartbeat-worker-project.yml` | #253 | `2236df65a495975ca9bc7d9c8fad7d863934617f` | 32590794869 | 32590794862 | PASS |
| `org-heartbeat-watchdog.yml` | `heartbeat-worker-project.yml` manual dispatch only | #254 | `c3256be218dbabdf4fb82e877e71d2884925c904` | 32590947641 | 32590947607 | PASS |
| `native-process-worker-canary.yml` | `heartbeat-worker-project.yml` | #255 | `856d1823283f3ade54ac95094d73ec149c245d74` | 32591051012 | 32591050991 | PASS |
| `external-timing-match-validation.yml` | `heartbeat-worker-project.yml` | #256 | `278299617d17a4f410b0ef0e2d1da1a609b67fc4` | 32591188347 | 32591188133 | PASS |

### Preserved semantics

- Organization handoff rendering still executes and requires committed projection parity.
- Archive readiness still executes its validator and unittest.
- Organization heartbeat source validation moved to the stable Heartbeat Worker dispatcher without restoring routine state/receipt main-push fanout.
- Watchdog diagnostics remain manually invocable only; they were not added to automatic PR/push execution.
- Native-process canary validation now checks retained terminal evidence only. Its handoff is `COMPLETED`, successor policy `NONE`; no canary reactivation was introduced.
- External timing source/validation is `COMPLETE_RELEASED`; fixed-cadence and zero-authority assertions remain in the stable dispatcher. Live timing consumption remains owned by `.github#122`.

## Prior fanout containment retained

- Heartbeat Worker direct-main machine-commit storm fanout was removed by `f55b7d653044bb2e1be3c6b2c2e736241389c3ab`. Healer later restored automatic validation only for exact heartbeat/process-adapter source needed by absorbed workflows; routine carrier/state/receipt persistence remains excluded.
- Test-lanes direct-main validation removed by `599cac6417bc67874416d2b0125929a2601f8fe2`; PR/manual retained with concurrency cancellation.
- Organization control blanket `scripts/**`, `tests/**`, and `heartbeat_runtime/**` main fanout narrowed by PR #247 / `52c64f0fbf2b6375a5546a0a2af0d5000f4fcef4`.
- Full Heartbeat Worker suite is green: run `32588349952`, 486 tests, zero failures.
- Ecosystem Chat inference validation is green: `32588349889`; reference proof rejects `qualifies_as_large_production_llm=true`.

## Remaining `.github` workflow surface

Twelve workflow files remain. Nine still have selective automatic source pushes; three are PR/manual-only. The registry is authoritative for current classification. Active-owner-sensitive surfaces must not be removed merely to hit the two-workflow target.

Healer #34 must continue classification/consolidation/exception work. Any final count above two requires explicit technical necessity evidence.

## Site cost lane

User-provided GitHub billing evidence on 2026-08-22 showed Site as the largest observed StegVerse-Labs Actions repository cost center at `$201.44`, compared with `.github` at `$31.66` at that observation point.

Site has an existing B27 cost-reduction task/claim (`SITE-ACTIONS-COST-CONTAINMENT-001-B27`, PR #387) to retire the hourly Thought Experiments workflow. Its source changes exist, and a StegVerse-Healer native validation carrier is released, but exact-head live validation still requires the machine-owned Healer scheduler receipt. GitHub CI/source merge cannot substitute for that receipt.

A separate high-value Site candidate has also been proven but not yet mutated: `.github/workflows/va-claims-guide-surface.yml` uses a six-hour hosted schedule, `contents: write`, credential-persisting checkout, repository receipt writeback, and artifact upload while Site's credential-clean `validate.yml` already runs the same deterministic `scripts/validate_va_claims_guide_surface.py`. A distinct Site pre-work claim is required before that surface can be changed.

## Remaining work

1. Continue Healer #34 consolidation on non-owner-sensitive `.github` validation surfaces.
2. Reconcile active owners before touching runtime-sensitive/MCP/StegFin/test-lane surfaces.
3. Consume the Site B27 scheduler receipt when it exists; do not substitute hosted CI.
4. Acquire a distinct Site pre-work claim before retiring the redundant VA guide scheduled/writeback/artifact workflow.
5. Obtain repository-wide quantitative post-repair run history when a supported reader exists.

## Release / propagation

No tag/release is required solely for these workflow-validation consolidations. No public product capability contract changed.

## Completion gate

Cost reduction is materially advanced but nonterminal: `.github` is 18 -> 12 with six parity-proven removals; Healer #34 and Site remediation remain active, and repository-wide quantitative run-history evidence remains unavailable.

Current status: `DO NOT ARCHIVE THIS SESSION — UNIQUE ACTIVE WORK REMAINS.`
