# Organization GitHub Fleet Functionalization Mirror Handoff

Status: ACTIVE / CHECKED_OUT
Repository: `StegVerse-Labs/.github`
Goal Task ID: `ORG-GITHUB-FLEET-FUNCTIONALIZATION-001`
COSV profile: `task.v1`
COSV vector: `20010000100000`
Parent evidence task: `ORG-GITHUB-REPOSITORY-STATUS-SUMMARY-001`
Parent census: `reports/ORG_GITHUB_REPOSITORY_STATUS_SUMMARY_001.md`

## Goal

Convert the 22 repositories represented by the census's 15 `FULFILLING_INTENDED_ROLE` plus 7 `VALIDATED_OR_IMPLEMENTED_PARTIAL` repositories into a dependency-stable functional set, without weakening repository-specific evidence requirements or promoting source/CI evidence into runtime/provider/public proof.

The 15 repositories already satisfying their established role are preserved and dependency-hardened; the 7 partial repositories are the primary functionalization targets.

## Target set

### Already role-functional; protect dependency closure

`FREE-DOM`, `Epsteinality`, `Giuffre-ality`, `Maxwellality`, `StegBiography`, `Trumpality`, `Executive_Rhetoric_Ledger`, `StegID`, `StegCore`, `StegOS`, `hybrid-collab-bridge`, `ara-admissibility-interop`, `music-engine`, `media-runtime`, `video-engine`.

### Primary partial-to-functional targets

`.github`, `GP10`, `StegMusic`, `StegTalk`, `TVC`, `StegBrain`, `stegfin-governance`.

## Functionalization rule

A repository is functional when the evidence required by its established role is directly proven. A documentary/research repository is not required to manufacture a runtime layer that is not part of its role. A runtime/provider/product repository is not considered functional merely because source or validation passes.

`UNKNOWN`, `PENDING`, `HANDOFF_READY`, `WAITING`, `BLOCKED_DEPENDENCY_MACHINE_OWNED`, and similar nonterminal evidence states are not promoted to PASS without the required receipt.

## Cross-organization and cross-repository dependency graph

### Shared StegVerse control dependencies

- `StegVerse-Labs/.github` — Task Registry/COSV coordination, shared workers, HeartBeat carriage/reference, Universal InTr routing, reusable-task definitions; no credential/runtime authority inferred.
- `StegVerse-Labs/TV` + `StegVerse-Labs/TVC` — credential/provider/release capability authority.
- `StegVerse-Labs/StegOS` — device/node and bounded execution substrate.
- `StegVerse-002/micro-node-runtime` — sovereign local-model/runtime and event-ephemeral execution ownership used by several lanes.
- `master-records/orchestration` — passive evidence custody/reconstruction.
- `StegVerse-Labs/Continuity` + `StegVerse-Labs/StegID` — continuity/identity receipts used by Auri, finance, and other governed paths.
- `StegVerse-Labs/continuity-vault-kit` — current InTr/SKAP/KV third-party credential protocol implementation consumed by TVC callers.
- `StegVerse-Labs/Site` — public UX/playback/HIL/product integration and public-E2E evidence where applicable.
- `GCAT-BCAT-Engine/Publisher` — downstream governed publication for release-propagated artifacts.
- `StegVerse-Labs/admissibility-wiki` and `StegVerse-002/stegguardian-wiki` — downstream propagation targets when a release explicitly requires them.

### Research cluster

`FREE-DOM`, `Epsteinality`, `Giuffre-ality`, `Maxwellality`, `StegBiography`, and `Trumpality` depend on `StegVerse-Labs/Executive_Rhetoric_Ledger` as canonical research evaluation/ingestion owner. Evidence-chain policy also references `StegVerse-Labs/repo-standards`. Their current role-functional status must be preserved while ERL/standards dependencies are checked for regression.

### StegCore / StegTalk / Auri cluster

`StegTalk` Auri activation depends on `StegCore`, `Continuity`, `StegID`, and `StegAgents`; final AURI activation additionally requires canonical provider/deployment authorization evidence, a reachable authorized target, runtime proof, and final activation receipt. `StegCore` and `Continuity` already provide completed AURI gateway/receipt evidence, so the remaining Auri gap is external-authorization/runtime evidence rather than missing core source.

### StegMusic / media cluster

`StegMusic` exact private-source validation depends on `TVC-PRIVATE-SOURCE-READ-001` / `tvc.private-source-read.v1`. Product integration then depends on `StegDJ`, `Site`, the sovereign local runtime owner, and release/propagation consumers. Optional third-party music/streaming providers remain TV/TVC-admitted fallbacks only. `music-engine`, `media-runtime`, and `video-engine` are locally role-functional but should be regression-checked against StegMusic/StegDJ/Site integration rather than assumed public-E2E complete.

### StegBrain cluster

`StegBrain` live usefulness depends on `.github` live heartbeat/control-plane migration and COSV packet production, `master-records/orchestration` custody, `StegVerse-002/micro-node-runtime` for formal local runtime activation, TV/TVC for credentials where required, and `stegfin-governance` for trade-readiness consumers. Current source and deterministic replay are not equivalent to live packet-series consumption.

### StegFin cluster

`stegfin-governance` is functional through the pre-sign `WALLET_HANDOFF_READY` boundary. Full settlement depends on user-authorized wallet signing/broadcast, actual settled evidence, `master-records/orchestration` reconstruction, TV/TVC provider/credential routes, StegID/device continuity, and the sovereign micro-node runtime. The fleet task must not treat USER_ONLY signing/broadcast as a machine-remediation defect.

### GP10 cluster

`GP10` requires a passing current runtime-validation receipt plus real field-validation evidence, approved thresholds, legal/regulatory review, and optional authorized Railinc/Maximo connector activation. Release propagation then targets Site, `GCAT-BCAT-Engine/Publisher`, `admissibility-wiki`, and `stegguardian-wiki` under destination-owned verification.

### TVC cluster

TVC itself is a dependency hub. Current functionalization-sensitive dependencies include `.github` shared control/runtime carriage, `continuity-vault-kit` InTr/SKAP credential protocol, `StegVerse-002/micro-node-runtime`, `master-records/orchestration`, `StegVerse-org/StegVerse-SDK`, `Data-Continuation/core-lite`, `StegCore`, and applicable external provider/release endpoints. Credential-model consistency must remain reconciled before expanding credential semantics.

## Remediation order

1. Preserve the 15 role-functional repositories by checking their named dependency owners for regression; do not reopen completed local work without evidence.
2. Repair shared dependency hubs first: `.github`, TV/TVC, `continuity-vault-kit`, sovereign runtime, Master Records.
3. Complete deterministic/repository-native validation gaps that do not require external/user authority: GP10 runtime proof, StegMusic TVC private-source validation, StegBrain live packet-consumer path where shared carriers are available.
4. Drive integration/runtime evidence: StegMusic -> StegDJ/Site; StegTalk Auri -> authorized runtime; TVC provider/release routes; StegBrain live packet-series consumption.
5. Preserve explicit human authority: StegFin signing/broadcast and GP10 legal/regulatory approvals remain human-authority transitions, while all independent machine work proceeds.
6. Verify downstream public/release propagation only after authentic release/runtime evidence exists.

## Completion predicates

- all 15 previously role-functional repositories remain role-functional after dependency regression review;
- each of the 7 partial repositories has either reached its established functional role with direct evidence or has its remaining non-machine authority condition isolated without any unresolved machine-remediable dependency;
- shared dependency defects discovered during functionalization have canonical owners/tasks rather than being left as prose;
- README and this handoff remain current;
- no runtime/provider/public-E2E claim is made without direct evidence.

## Current state

`ACTIVE / CHECKED_OUT`. Dependency graph established. Machine-remediable work has not yet been declared complete; no user-only or external condition is being misclassified as completion.
