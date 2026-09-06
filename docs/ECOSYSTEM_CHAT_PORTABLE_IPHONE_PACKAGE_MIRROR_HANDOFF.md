# Ecosystem Chat Portable iPhone Package Mirror Handoff

Updated: 2026-09-05
Repository: `StegVerse-Labs/.github`
Architecture owner: `StegVerse-Labs/.github#201`
Parent task: `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`

## Goal

Bind the already-authorized clean Ecosystem Chat parent task to the existing canonical portable WorkerCoordinator checkout surface so `CURRENT_USER_IPHONE` can acquire a fresh parent claim/fence without another machine, another WorkerCoordinator, or browser-owned global authority.

## Canonical preflight

Resolved before mutation:
- `docs/ORG_MIRROR_HANDOFF.md`;
- `docs/ARCHIVE_GATE_PROGRESS_MIRROR_HANDOFF.md` and `control/archive-readiness.json`;
- `docs/ECOSYSTEM_CHAT_ORPHAN_RECOVERY_MIRROR_HANDOFF.md`;
- `handoffs/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json`;
- `control/worker-registry.json` and `control/worker-registry.d/ecosystem-chat-sovereign-inference-parent-001.json`;
- `control/task-vectors/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json`;
- `workercoordinator/portable_checkout.js` and `docs/WORKERCOORDINATOR_PORTABLE_IPHONE_EXECUTION_MIRROR_HANDOFF.md`;
- current same-device invariant `.github#201`;
- open PR collision search for Ecosystem Chat portable WorkerCoordinator work: none observed.

Recovery G22 is terminal and is not replayed. Parent authority remains a separately admitted fresh independent-task-control fence.

## Installed source slice

```text
control/portable-workercoordinator-packages/ecosystem-chat-sovereign-inference.json
tests/test_ecosystem_chat_portable_workercoordinator_package.py
docs/ECOSYSTEM_CHAT_PORTABLE_IPHONE_PACKAGE_MIRROR_HANDOFF.md
control/session-implementation-claim-2026-09-05-ecosystem-chat-portable-iphone-package.json
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

Observed portable lineage already contains an authentic canonical G23 and an authentic duplicate/non-custodial G24. Therefore a fresh/reset portable state must not begin from the historical registry generation 22 and reuse G23/G24.

This package sets:

```text
predecessor_generation_floor: 24
minimum_fencing_token_exclusive: 24
fresh/reset first possible Ecosystem Chat fence: G25
```

An existing persisted portable state with a higher generation remains monotonic and advances from that state. This does not promote G24 to custody-eligible status; it only prevents fence-number reuse.

## Authority boundary

The static package grants no authority by existing. Only `workercoordinator/portable_checkout.js` may atomically mint the claim/fence after validating the package and current portable state. StegOS may later project the exact package and provide atomic persistence/subordinate execution, but it does not own canonical WorkerCoordinator authority.

The package does not prove:
- current iPhone portable-state presence;
- package projection into StegOS;
- claim/fence issuance;
- local model execution;
- TVC route admission;
- LLM-adapter execution;
- measured usage;
- Master Records reconstruction;
- product activation.

## README impact preflight

`README.md` change is **not required for this upstream package-only slice**. Evidence-supported reason: the repository README already documents the generic sequential portable WorkerCoordinator contract, including one monotonic authority lineage, distinct-task checkout, no parallel issuance, TV/TVC authority, HB non-authority, and downstream same-device reuse. This change adds only a static task package bound to that existing documented interface; it does not change the checkout algorithm, runtime semantics, authority model, failure behavior, or user-visible execution surface.

The downstream StegOS composition/profile is a material functional change and must update the StegOS README in its own change set.

## Next required transition

After exact package validation and merge:

```text
project exact package into StegOS
+ project exact LLM-adapter web runtime
+ project exact Master Records web reconstruction runtime
+ register Ecosystem Chat external-resident profile
+ bind portable WorkerCoordinator checkout to same-device service-worker execution
+ validate source fail-closed behavior
+ physically consume on CURRENT_USER_IPHONE
+ observe fresh fence >24 and same-device proof chain
```

The thread is not archive-ready until that runtime continuation actually advances or the full goal completes.
