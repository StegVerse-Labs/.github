# SHWP DeepSeek InTr Runtime Mirror Handoff

Updated: 2026-09-07
Repository: `StegVerse-Labs/.github`
Task: `SHWP-DEEPSEEK-INTR-RUNTIME-001`
COSV: `50000000101000`
Peer task in Group 6: `KIMI-INTR-RESIDENT-ACTIVATION-001`

## Authority and source-of-truth chain

This handoff is the task-level continuation source of truth for the resident DeepSeek InTr runtime lane. It is subordinate to and must reuse the already-installed canonical components and boundaries represented by:

- `handoffs/SHWP-DEEPSEEK-INTR-RUNTIME-001.json`
- `workers/deepseek_intr_runtime_worker.py`
- `control/resident-execution-request.d/deepseek-intr-runtime-001.json`
- `control/resident-execution-request.d/consume-deepseek-intr-runtime.py`
- `control/worker-registry.d/deepseek-intr-runtime-001.json`
- `control/process-worker-adapters.d/deepseek-intr-runtime-001.json`
- `control/task-vectors/SHWP-DEEPSEEK-INTR-RUNTIME-001.json`
- `.github/workflows/validate-deepseek-resident.yml`
- canonical StegGate / Universal InTr transition semantics
- `StegVerse-Labs/TVC` DeepSeek capability lease and non-exportable provider operation semantics
- `StegVerse-org/LLM-adapter` exact DeepSeek request/response transport and custody client semantics
- `master-records/orchestration` provider-usage custody and reconstruction
- the existing `StegVerse-Labs/.github` WorkerCoordinator resident lane

No source in this task may create a second scheduler, WorkerCoordinator, heartbeat authority, credential store, provider-secret path, governance authority, InTr authority, or Master Records authority.

## Exact execution objective

Complete one authentic same-execution DeepSeek resident cycle:

```text
fresh existing WorkerCoordinator claim/fence
-> exact DeepSeek request identity
-> canonical InTr/StegGate ingress ALLOW
-> TVC exact-bound single-use DeepSeek capability lease
-> TVC non-exportable provider operation
-> authentic DeepSeek response + TVC use receipt
-> Master Records custody_recorded=true + reconstructability=PASS
-> canonical InTr/StegGate egress ALLOW bound to exact response hash
-> LLM-adapter exact-response egress admission
-> retained resident WorkerCoordinator completion receipt
```

Transport completion is not governance approval. Governance approval is not provider execution or credential authority. TV/TVC remains the sole provider consequence / credential authority.

## Current state

```text
task: SHWP-DEEPSEEK-INTR-RUNTIME-001
cosv: 50000000101000
coordination_state: HANDOFF_READY
resident worker source: INSTALLED_ON_DEFAULT_BRANCH
resident request + consumer: INSTALLED_ON_DEFAULT_BRANCH
worker registry fragment: INSTALLED_ON_DEFAULT_BRANCH
process adapter fragment: INSTALLED_ON_DEFAULT_BRANCH
task vector: INSTALLED_ON_DEFAULT_BRANCH
validation-only workflow: INSTALLED_ON_DEFAULT_BRANCH
README resident DeepSeek section: INSTALLED_ON_DEFAULT_BRANCH
source merge proves activation: false
live same-execution resident receipt: NOT_YET_OBSERVED
activation state: IMPLEMENTED_PENDING_RUNTIME_PROOF
credential architecture duplication: PROHIBITED
provider credential plaintext in .github or LLM-adapter: PROHIBITED
heartbeat grants authority: false
github token grants runtime authority: false
release/tag authority: NOT_YET_PROVEN
```

## Activation predicates

`SHWP-DEEPSEEK-INTR-RUNTIME-001` remains incomplete until one authentic retained same-execution chain proves all of:

1. fresh existing WorkerCoordinator claim and positive fencing token;
2. exact request/session/transition identity shared across the cycle;
3. canonical ingress decision with disposition `ALLOW`;
4. exact-bound TVC DeepSeek lease;
5. TVC non-exportable provider operation with no credential export/log/retention;
6. authentic DeepSeek provider response;
7. authentic TVC use receipt;
8. Master Records `custody_recorded=true`;
9. Master Records `reconstructability=PASS`;
10. canonical egress `ALLOW` bound to the exact response hash;
11. LLM-adapter exact-response egress admission;
12. resident WorkerCoordinator completion receipt retaining the common task/session/transition/request identity.

Mocks, fixtures, CI success, source merge, workflow success, provider output alone, transport completion alone, Governance ALLOW alone, TVC readiness alone, or custody alone do not satisfy activation.

## Machine preflight and README invariant

The repository machine preflight entrypoint is `scripts/session_build_preflight.py`, with the contract in `management/session-build-preflight-contract.json`. Any future functional mutation must pass the applicable preflight and declare README impact before task creation or worker admission. The current DeepSeek runtime implementation already includes the required README resident-runtime section; this handoff addition is coordination/documentation only and does not itself require a new README behavior description.

## Next admissible work

1. Preserve the installed DeepSeek worker/runtime surfaces; do not rebuild them in parallel.
2. On the existing sovereign resident surface, consume the standing DeepSeek resident request through the existing dispatcher and WorkerCoordinator.
3. Fail closed at the first unsatisfied claim/fence, ingress, TVC, provider, custody, or egress predicate.
4. Retain the authentic same-execution completion receipt under the existing DeepSeek receipt path.
5. Only after authentic activation proof, evaluate release/tag readiness.
6. When release/tag readiness is proven, create a separate verification/update task for pertinent projections to `StegVerse-Labs/Site`, `GCAT-BCAT-Engine/Publisher`, `admissibility-wiki`, and `stegguardian-wiki`.

## Known remaining installation / execution destinations

```text
StegVerse-Labs/.github:
  NO NEW RUNTIME MODULES REQUIRED BY CURRENT SOURCE STATE
  remaining: authentic resident execution + retained same-execution receipt

StegVerse-Labs/TVC:
  REUSE existing DeepSeek lease / non-exportable provider operation; no duplicate credential semantics

StegVerse-org/LLM-adapter:
  REUSE canonical exact request/response transport and custody client semantics

master-records/orchestration:
  REUSE canonical provider-usage custody/reconstruction

Post-activation verification targets:
  StegVerse-Labs/Site
  GCAT-BCAT-Engine/Publisher
  admissibility-wiki
  stegguardian-wiki
```

## Completion boundary

This task reaches runtime completion only when the authentic same-execution resident receipt is observed and retained with all activation predicates satisfied. This handoff grants no execution, transition, credential, provider-use, custody, publication, release, or runtime-truth authority.