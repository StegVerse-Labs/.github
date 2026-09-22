# Functional Fleet Dependency Map

Goal Task: `ORG-GITHUB-FLEET-FUNCTIONALIZATION-001`
COSV: `20010000100000`
Parent census: `ORG-GITHUB-REPOSITORY-STATUS-SUMMARY-001`

## Target

The prior census's 18.5% set is 22 repositories: 15 already fulfilling their established role and 7 validated/implemented partial repositories. The functionalization objective is to preserve the 15 and close machine-remediable gaps in the 7 partials without inventing runtime/provider/public evidence.

## Dependency hubs that can prevent multiple target repositories from becoming or remaining functional

| Dependency owner | Affected target repositories | Current significance | Functionalization action |
|---|---|---|---|
| `StegVerse-Labs/.github` | `.github`, StegBrain, StegMusic, TVC, StegTalk, stegfin-governance, hybrid-collab-bridge, StegOS | Shared Task Registry/COSV, worker/control-plane, live carrier/Universal InTr coordination. Several consumers depend on live carrier/runtime evidence rather than source alone. | Treat as first shared remediation hub; do not infer runtime from merged source. |
| `StegVerse-Labs/TV` + `StegVerse-Labs/TVC` | StegMusic, StegTalk, StegBrain, stegfin-governance, StegCore, StegOS | Sole credential/provider/release authority. `TVC-PRIVATE-SOURCE-READ-001` remains `SOURCE_COMPLETE_PR146_ONLY_RESIDENT_ADMISSION_PENDING`; StegMusic is explicitly a waiting consumer. | Activate/observe the existing bounded private-source-read capability and then execute exact-source StegMusic validation; continue other provider/release routes only with their own receipts. |
| `StegVerse-Labs/continuity-vault-kit` | TVC and third-party credential consumers; indirectly StegTalk/StegMusic/StegFin | Owns machine-readable InTr/SKAP/KV third-party credential protocol implementation. TVC documents caller requirements but does not duplicate implementation. | Regression-check current InTr/SKAP/KV implementation and runtime-evidence state before declaring credentialed routes functional. |
| `StegVerse-002/micro-node-runtime` | StegOS, hybrid-collab-bridge, StegMusic, StegBrain, stegfin-governance, TVC | Canonical sovereign local-model/event-ephemeral runtime owner. Several lanes have source transferred here but live activation is a separate predicate. | Reuse existing runtime owner; verify authentic activation/consumption receipts rather than creating another runtime. |
| `master-records/orchestration` | StegBrain, StegTalk/Auri, stegfin-governance, TVC, hybrid-collab-bridge | Passive evidence custody/reconstruction; required for terminal proof in several runtime/provider flows. | Verify downstream custody/reconstruction after authentic runtime/provider operations; do not use custody to manufacture upstream proof. |
| `StegVerse-Labs/Continuity` + `StegVerse-Labs/StegID` | StegTalk/Auri, stegfin-governance, StegCore | Identity/continuity receipts and session/device continuity. | Preserve existing complete evidence and regression-check consumers against exact current receipt contracts. |
| `StegVerse-Labs/Site` | StegMusic, GP10, HIL-linked product paths; downstream public-E2E | Public UX/playback/integration owner. The parent fleet census separately classified Site as an explicit operational gap. | Site is outside the 22 target set but is a causal dependency; its applicable product integration must be repaired before public-E2E claims for dependent targets. |
| `GCAT-BCAT-Engine/Publisher` | GP10, StegMusic release propagation and other governed publication lanes | Destination-owned publication/propagation. | Verify only after release evidence exists; no propagation-by-source inference. |
| `StegVerse-Labs/admissibility-wiki` + `StegVerse-002/stegguardian-wiki` | GP10/StegMusic release propagation | Destination verification targets; admissibility-wiki is itself an explicit operational-gap repository in the parent census. | Treat as downstream causal dependencies that may need separate repair before release propagation can close. |
| `StegVerse-Labs/repo-standards` | FREE-DOM/research evidence chain and fleet repository policy | Research chain references ST-007; repo-standards itself is an explicit operational-gap repository in the parent census. | Preserve research outputs but repair standards enforcement separately rather than downgrading completed research evidence. |
| `StegVerse-Labs/Executive_Rhetoric_Ledger` | FREE-DOM, Epsteinality, Giuffre-ality, Maxwellality, StegBiography, Trumpality | Canonical research evaluation/ingestion owner. | Keep this cluster stable; dependency regression here can invalidate future research ingestion even though local research validation is complete. |

## Seven partial repositories: exact dependency closure

### `.github`

Role: shared control/coordination repository. Functionalization is not equivalent to making every ecosystem runtime active. Required work is to ensure its shared worker/task/carrier surfaces that are dependencies of the other six partial targets have direct current evidence. Priority consumers: StegBrain live packet path, TVC resident capability admission, and sovereign runtime consumers.

### `GP10`

Current work is not blocked by missing source. It needs a passing current runtime-validation receipt, real field-validation evidence, evidence-backed thresholds, and legal/regulatory release. Optional direct connector activation involves Railinc/Maximo authorization. Release propagation depends on Site, Publisher, admissibility-wiki, and stegguardian-wiki. The field/legal inputs are not machine-inventable; repository-native runtime proof and evidence ingestion remain machine-remediable.

### `StegMusic`

Immediate causal blocker is not StegMusic source: `TVC-PRIVATE-SOURCE-READ-001` currently records `SOURCE_COMPLETE_PR146_ONLY_RESIDENT_ADMISSION_PENDING`, and lists StegMusic as `WAITING_FOR_ADMITTED_EXACT_SOURCE_GRANT`. Once that bounded TVC capability is authentically resident/admitted, the existing `TVC-STEGMUSIC-VALIDATION-001` path can perform exact-current-SHA deterministic validation. Downstream functionality then depends on StegDJ/Site/runtime evidence; optional provider APIs remain TVC-only fallbacks.

### `StegTalk`

AURI-001 through AURI-006 are complete. AURI-007 requires provider/deployment authorization evidence, a reachable authorized target, runtime proof, and a final activation receipt. Supporting repositories are StegCore, Continuity/StegID, and StegAgents. This is primarily an activation/runtime dependency, not missing StegTalk implementation.

### `TVC`

TVC is both a target and a dependency hub. The private-source-read capability is source-complete but still lacks authentic resident service installation/credential presence/admission evidence for general consumers. Current caller architecture also depends on `continuity-vault-kit` for InTr/SKAP/KV protocol compatibility. Release/provider lanes have their own explicit authorization/evidence predicates; no generic GitHub credential may substitute.

### `StegBrain`

Deterministic source replay is already PASS. Functional live observation depends on `.github` heartbeat/control-plane migration and COSV state packets, plus Master Records custody. Formal local runtime activation is owned by `StegVerse-002/micro-node-runtime`; TV/TVC remains credential authority. The prior hosted Actions billing gate is not a source defect and should not be confused with live packet-consumer completion.

### `stegfin-governance`

The repository is already functional at its intended pre-sign wallet-handoff boundary: `WALLET_HANDOFF_READY` has direct evidence. Full settlement is intentionally beyond that machine boundary: signature and broadcast are `USER_ONLY`, and post-settlement reconstruction depends on actual settled evidence plus Master Records. Therefore this repository should be promoted from partial only if the fleet definition accepts its established pre-sign role; it must not be forced to auto-sign/broadcast to satisfy a machine functionalization metric.

## First remediation wave

1. `.github` shared live-evidence/carrier dependencies.
2. `TVC-PRIVATE-SOURCE-READ-001` resident admission/service evidence.
3. `TVC-STEGMUSIC-VALIDATION-001` exact-current-SHA StegMusic deterministic PASS.
4. StegBrain live packet-series consumer evidence through the existing `.github` + Master Records path.
5. GP10 current runtime proof and evidence-ingestion lane.
6. StegTalk Auri AURI-007 authorized-runtime evidence.
7. Reclassify StegFin against its explicit pre-sign role; keep USER_ONLY settlement outside machine completion.
8. Only then close downstream Site/Publisher/wiki propagation where those layers are required.

## Causal dependencies outside the 22 that may require separate repair tasks

Highest-impact: `Site`, `continuity-vault-kit`, `repo-standards`, `StegVerse-002/micro-node-runtime`, `master-records/orchestration`, `StegDJ`, `StegAgents`, `GCAT-BCAT-Engine/Publisher`, `admissibility-wiki`, and `StegVerse-002/stegguardian-wiki`.

These are not automatically failures. They are dependency owners whose current evidence must be checked before a dependent target can be promoted. If an actual defect is observed, create/reuse its canonical task rather than absorbing unrelated implementation into this fleet task.
