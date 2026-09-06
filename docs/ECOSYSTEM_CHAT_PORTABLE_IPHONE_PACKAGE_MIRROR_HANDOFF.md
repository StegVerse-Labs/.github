# Ecosystem Chat Portable iPhone Package Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-Labs/.github`
Architecture owner: `StegVerse-Labs/.github#201`
Parent task: `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`
State: `PACKAGE_RELEASED_STEGOS_SOURCE_PROJECTED_AUTHENTIC_CHECKOUT_PENDING`

## Goal

Bind the already-authorized clean Ecosystem Chat parent task to the existing canonical portable WorkerCoordinator checkout surface so `CURRENT_USER_IPHONE` can acquire a fresh parent claim/fence without another machine, another WorkerCoordinator, or browser-owned global authority.

## Canonical preflight

Resolved before the package mutation:
- `docs/ORG_MIRROR_HANDOFF.md`;
- `docs/ARCHIVE_GATE_PROGRESS_MIRROR_HANDOFF.md` and `control/archive-readiness.json`;
- `docs/ECOSYSTEM_CHAT_ORPHAN_RECOVERY_MIRROR_HANDOFF.md`;
- `handoffs/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json`;
- `control/worker-registry.json` and `control/worker-registry.d/ecosystem-chat-sovereign-inference-parent-001.json`;
- `control/task-vectors/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json`;
- `workercoordinator/portable_checkout.js` and `docs/WORKERCOORDINATOR_PORTABLE_IPHONE_EXECUTION_MIRROR_HANDOFF.md`;
- current same-device invariant `.github#201`.

Recovery G22 is terminal and is not replayed. Parent authority remains a separately admitted fresh independent-task-control fence.

## Installed package

```text
control/portable-workercoordinator-packages/ecosystem-chat-sovereign-inference.json
```

The package reuses:

```text
portable authority epoch: WC-PORTABLE-IPHONE-20260902
canonical authority owner: StegVerse-Labs/.github WorkerCoordinator
authority domain: INDEPENDENT_TASK_CONTROL
execution surface: CURRENT_USER_IPHONE
credential authority: TV/TVC
GitHub runtime authority: NONE
HB execution authority: false
parallel WorkerCoordinator issuance: false
```

## Fresh-fence reset safety

Observed portable lineage already contains an authentic canonical G23 and an authentic duplicate/non-custodial G24. Therefore a fresh/reset portable state must not begin from historical registry generation 22 and reuse G23/G24.

This package sets:

```text
predecessor_generation_floor: 24
minimum_fencing_token_exclusive: 24
fresh/reset first possible Ecosystem Chat fence: G25
```

An existing persisted portable state with a higher generation remains monotonic and advances from that state. This does not promote G24 to custody-eligible status; it only prevents fence-number reuse.

## Downstream StegOS projection status

The source-projection steps previously listed as pending have now completed without widening authority:

```text
StegVerse-Labs/StegOS #214: exact source/package pins merged
StegVerse-Labs/StegOS #215: bounded adapter source merged
StegVerse-Labs/StegOS #216: material existing-service-worker integration merged
StegOS source merge: 4ef5e1e3e06969ed538cf0538d5657652abb26e1
StegOS exact-head CI: 34021150351 SUCCESS
StegVerse-Labs/StegOS #217: source claim released
StegOS claim-release merge: 7a34d282b0eba3ff7d51ed6fb316b4332eb09a51
```

The projected StegOS source reuses the exact package and canonical WorkerCoordinator checkout plus the exact TVC/LLM-adapter/Master-Records web runtime owners. It exposes one bounded existing-service-worker interface on `CURRENT_USER_IPHONE`:

```text
POST /stegos-bootstrap/portable-workercoordinator/ecosystem-chat
```

StegOS does not own canonical WorkerCoordinator authority, and the source merge did not mint a claim/fence.

## Authority boundary

The static package grants no authority by existing. Only `workercoordinator/portable_checkout.js` may atomically mint the claim/fence after validating the package and current portable state. StegOS persists and executes the exact portable algorithm on the physical device but does not own global WorkerCoordinator authority.

The package or StegOS source projection does not prove:
- current iPhone portable-state presence;
- claim/fence issuance;
- local model execution;
- TVC route admission;
- LLM-adapter execution;
- measured usage;
- Master Records reconstruction;
- product activation.

Current parent package remains:

```text
state: HANDOFF_READY
claim_id: null
worker_id: null
runtime_execution_observed: false
activation_effect: false
```

## README impact

README change is **not required for this reconciliation-only update**. The package itself still uses the existing documented portable WorkerCoordinator contract, and the material downstream interface/behavior change was documented in the StegOS README in PR #216. This update changes only cross-repository continuation status; it does not change checkout code, runtime semantics, authority, failure behavior, prerequisite meaning, or capability meaning in `.github`.

## Next required transition

The source-projection portion is complete. The next required transition is authentic same-device consumption:

```text
CURRENT_USER_IPHONE invokes released StegOS Ecosystem Chat interface
+ exact portable WorkerCoordinator checkout atomically issues fresh G25+ fence
+ existing service-worker local-model proof is observed
+ exact TVC route is admitted
+ exact LLM-adapter executes with measured usage
+ exact Master Records reconstructs the same execution
+ provider-usage reconstruction PASS
+ transition reconstruction PASS
+ same_execution=true
+ device journal replay PASS
+ authentic evidence returns to the canonical parent terminalizer
```

The historical G20 carrier receipt remains nonterminal evidence. It must not be promoted or rewritten because source projection completed.

No second user-operated machine, hosted inference provider, non-TV/TVC credential, GitHub runtime authority, or parallel WorkerCoordinator is an admissible substitute.
