# Repository Visibility Boundary Mirror Handoff

Updated: 2026-08-17T09:39:00-05:00

## Canonical authority

```text
goal_id: REPOSITORY-VISIBILITY-BOUNDARY-001
originating_session_goal: Re-evaluate public/private repository boundaries after StegVerse-SDK became the canonical public evaluator/proof surface; privatize implementation repositories that no longer need to be public.
repository: StegVerse-Labs/.github
branch: main
credential_authority: TV/TVC
NON-TV/TVC secret/token authority: PROHIBITED
GitHub token runtime authority: NONE
Render production runtime: PROHIBITED
canonical_owner: StegVerse-Labs/.github organization control plane
active_implementation_claim: SESSION-REPOSITORY-VISIBILITY-AUDIT-20260817
active_validation_claim: NONE
claim_created: 2026-08-17T09:39:00-05:00
claim_release_condition: committed estate inventory + deterministic classifications + durable execution task for each visibility mutation + post-mutation verification receipt
state: ACTIVE_UNDER_AUDIT
```

This handoff is the canonical session-scoped source of truth for repository visibility after the public SDK expansion. It does not supersede repository-local product handoffs. It governs only whether a repository must remain public for contractual, proof/demo, documentation, publication, or external-interoperability reasons, or should default private because it contains implementation, orchestration, authority, custody, worker, adapter, runtime, or internal integration machinery.

## Governing rule

```text
public necessity must be affirmative, not inherited
public evaluator access should route through StegVerse-org/StegVerse-SDK wherever the SDK already exposes the contract/capability
implementation source is not required public merely because its outputs are externally verifiable
historically public material must be treated as disclosed even after privatization
visibility changes must not introduce or depend on NON-TV/TVC secret/token authority
```

Canonical public aperture:

```text
StegVerse-org/StegVerse-SDK
+ intentionally public schemas/specifications/verifiers
+ intentionally public sanitized proof/demo artifacts
+ public documentation/publication surfaces
```

Default private classes:

```text
implementation engines
internal orchestration
workers/control planes
provider/runtime adapters not required for interoperability
credential/authority/custody surfaces
internal bridges
private deployment/runtime machinery
```

## Session convergence

The local model/runtime and formal local-model goals are already complete and must not be recreated. Canonical source:

```text
StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
```

The trade-readiness goal is already machine/current-authority owned and this session must not compete with its live execution. Canonical sources:

```text
StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md
StegVerse-Labs/.github/docs/SESSION_ASSISTANCE_SCOPE_MIRROR_HANDOFF.md
```

This session therefore takes the distinct role `CLAIMED_FOR_IMPLEMENTATION` for the new repository-visibility governance lane and remains observation-only for the live trade/runtime lanes.

## Initial live evidence

Direct repository metadata observed in this session confirms the SDK is public and multiple implementation repositories remain public. Examples requiring classification include:

```text
StegVerse-org/StegVerse-SDK                         public   public-aperture candidate
StegVerse-Labs/Site                                 public   publication-surface candidate
StegVerse-Labs/StegCore                             public   implementation privatization candidate
StegVerse-Labs/Continuity                           public   implementation/contract split review
StegVerse-Labs/hybrid-collab-bridge                 public   internal-bridge privatization candidate
StegVerse-Labs/StegVerse-Healer                     public   implementation privatization candidate
StegVerse-Labs/StegSocials                          public   implementation/public-product review
StegVerse-org/LLM-adapter                           public   transport/adapter privatization candidate
StegVerse-org/demo_ingest_engine                    public   proof/demo review
StegVerse-org/demo-suite-runner                     public   proof/demo review
StegVerse-org/stegverse-demo-suite                  public   proof/demo review
StegVerse-org/discovery                             public   discovery surface review
StegVerse-org/manifests                             public   contract/artifact review
```

No repository is to be made private solely from its name. Each mutation requires a classification reason and dependency check.

## Required deliverables

```text
1 canonical mirror handoff                                  IN_PROGRESS
2 machine-readable estate visibility inventory             PENDING
3 deterministic classification policy                       PENDING
4 per-repository visibility decision/evidence               PENDING
5 mutation task registry with exact owner/release condition PENDING
6 actual visibility mutations where tool/authority permits  PENDING
7 post-mutation metadata verification                       PENDING
8 public-aperture regression check                          PENDING
9 historical-disclosure note for privatized repositories   PENDING
10 session consolidation receipt                            PENDING
```

## Claim / collision boundary

```yaml
task_id: REPOSITORY-VISIBILITY-BOUNDARY-001
originating_goal: SDK-driven whole-estate public/private boundary reduction
claimant: current ChatGPT repository-governance implementation lane
role: CLAIMED_FOR_IMPLEMENTATION
branch: main
files:
  - docs/REPOSITORY_VISIBILITY_BOUNDARY_MIRROR_HANDOFF.md
  - control/repository-visibility-boundary-2026-08-17.json
  - handoffs/REPOSITORY-VISIBILITY-BOUNDARY-001.json
collision_scope: visibility policy, estate classification inventory, mutation ownership, verification receipts
claim_timestamp: 2026-08-17T09:39:00-05:00
claim_expiration: release immediately after durable inventory/task handoff is installed and all mutations available to this connector are executed/verified
expected_evidence: immutable commits + live repository metadata + exact mutation/verification task records
next_task_after_release: machine/current-org-admin visibility executor applies remaining approved visibility transitions and persists verification receipt
```

## Authority boundary

The currently connected GitHub mutation surface can create/update repository files, issues, branches, PRs and related records but does not expose a repository-visibility mutation action. Therefore a visibility decision is not counted as applied until live repository metadata reports the target visibility. Any unexecutable visibility transition must be assigned to a durable exact owner/task rather than described as future/manual work.

The execution owner for visibility changes that require GitHub organization-administration capability is:

```text
owner: TV/TVC-governed GitHub organization administration authority
credential rule: no NON-TV/TVC secret or token may be introduced or exported
release condition: live GitHub repository metadata visibility == approved target AND verification receipt persisted
```

## Validation commands / observations

Validation is metadata based:

```text
GitHub get-repository/list-repository metadata -> visibility/private fields
SDK README + SDK_MIRROR_HANDOFF -> verify public evaluator aperture remains sufficient
repository-local *_MIRROR_HANDOFF.md -> check public dependency/publication obligations before mutation
post-mutation metadata re-read -> exact visibility confirmation
```

## Cross-repository obligations

Before privatizing a repository, determine whether its public source is explicitly required by:

```text
StegVerse-Labs/Site
GCAT-BCAT-Engine/Publisher
StegVerse-Labs/admissibility-wiki
StegVerse-Labs/stegguardian-wiki
master-records
StegVerse-org/StegVerse-SDK
```

No propagation is claimed until destination evidence is directly inspected.

## Archive conditions

Archive only when:

```text
all session-specific visibility requirements are in durable records
all repositories in the reachable estate have a classification or explicit UNKNOWN/BLOCKED record
all mutations available to the current connector are executed and verified
all remaining mutations have exact machine/current-authority owners and machine-observable release conditions
no visibility requirement remains only in chat
claim is released or transferred
session consolidation receipt is committed
```

## Completion accounting

```text
developed files: 1/3
validation: 0/4
integration: 0/3
goal activation: 10%
session consolidation: 0/1
archive_ready: false
```
