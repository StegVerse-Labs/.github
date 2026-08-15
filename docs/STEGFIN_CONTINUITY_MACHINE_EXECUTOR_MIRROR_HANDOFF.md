# StegFin Continuity Machine Executor Mirror Handoff

Updated: 2026-08-15T01:12:00-05:00

```text
goal_id: STEGFIN-CONTINUITY-MACHINE-EXECUTOR-008
originating_session_goal: G08-STEGFIN-TRADE-READY
repository: StegVerse-Labs/.github
branch: main
canonical_trade_handoff: handoffs/STEGFIN-CONTINUITY-CARRIER-007.json
canonical_worker: workers/stegfin_continuity_carrier_worker_v3.py
credential_authority: TV/TVC
github_token_runtime_authority: NONE
wallet_signing_authority: USER_ONLY
broadcast_authority: USER_ONLY
state: SOURCE_COMPLETE_VALIDATED_RELEASED_HOST_INSTALLATION_PENDING
```

## Gap closed

The canonical trade handoff permits `ANY_AUTHORIZED_STEGVERSE_CONTINUITY_EXECUTOR`, makes the resident heartbeat optional, binds execution to `MACHINE_SCHEDULER_ONLY`, and requires the existing worker itself to acquire the canonical collision-safe continuity claim through `scripts/acquire_stegfin_continuity_claim.py`.

Before this task, the repository had the worker, process-adapter fragment and resident-heartbeat adapter machinery but no task-specific non-heartbeat machine executor or rootless host-start delivery surface for this HANDOFF_READY continuity task. The generic heartbeat `ProcessWorkerAdapter` requires a pre-existing claim/fence and therefore could not lawfully be repurposed as the non-heartbeat carrier because the trade handoff explicitly forbids a carrier from inventing its own claim/fence.

That source gap is now closed without changing the canonical claim issuer, StegFin worker, TV/TVC broker/runtime authority, heartbeat state, or wallet authority.

## Released implementation

```text
scripts/run_stegfin_continuity_machine_executor.py
scripts/install_stegfin_continuity_machine_service.py
control/stegfin-continuity-machine-executor.json
data/stegfin-continuity-machine-executor/task-state.json
tests/test_stegfin_continuity_machine_executor.py
receipts/stegfin-continuity-machine-executor/source-validation-20260814.json
```

The formerly dedicated `.github/workflows/stegfin-continuity-machine-executor.yml` validation workflow is no longer an active source surface. It was removed under `G17-WORKFLOW-SURFACE-MINIMIZATION` after confirming that the stable `.github/workflows/heartbeat-worker-project.yml` already triggers on the executor's `scripts/**`, `tests/**`, `control/**`, `docs/**`, and `workers/**` surfaces and runs the complete deterministic repository test suite. The focused workflow's successful historical receipt remains evidence; capability validation was consolidated rather than dropped.

Key commits:

```text
handoff claim: 7681c23499f221d614cbfe519d68fbf4f70e83ed
executor: cb9123f6632899f738f897e6c6d2ab9e1e2c3fdc
rootless installer: 09e66212d8625b55d2f5800abe4edc398a06e4d4
installer hardening: 95dc1d269268d292c3ddc370ecf82c2faafeaf88
policy: a9f14edd749701a2542e1dffb1255fc4fa041c33
task-state initial: 63735646c2f84dad35dcc3bf70f094cbc0c7b0e4
tests: 2de66dee6473c71bed5783d7b7857af7f6bda179
focused workflow validation: b0d03891817b5ca764f097f1ae70e604eb192146
source validation receipt: cbaa3255fef7761d270029cde9b8aa8a7ea729a9
released task-state: 659b12303e349928a435b5648db9deb2efcf96de
workflow-minimization claim: d5f409a579ed5a461ed2aab364adcc2236277969
dedicated workflow elimination: f98e25c585602b28199cdd41e9add95dd3fc1d9e
```

## Machine contract

The executor is a one-shot local host adapter, not a heartbeat and not an authority source. It:

- rejects GitHub Actions, CI, Render, Vercel and Cloudflare-hosted execution;
- requires an existing `/etc/stegverse/node.json` or `~/.stegverse/node.json` sovereign-node declaration with `declared=true`, `credential_authority=TV/TVC`, and `github_token_required=false`;
- requires the canonical handoff to remain machine-only and the canonical registry task to remain `HANDOFF_READY` with no existing claim and the worker `AVAILABLE`;
- invokes only `workers/stegfin_continuity_carrier_worker_v3.py`;
- passes `claim_id=null` and no heartbeat timing/fence to the child, so the executor does not invent a claim/fence; the existing worker remains the canonical continuity-claim issuer;
- strips GitHub/provider/wallet/cloud credential-like environment variables and forwards only bounded non-secret source-location/transport values;
- accepts COMPLETE only when the worker transition is exactly `STEGFIN_CONTINUITY_WALLET_HANDOFF_READY` and the durable receipt independently proves TV/TVC authority, no non-TV/TVC secret/token, no provider-secret export, `signed=false`, and `broadcast=false`;
- writes a non-secret executor receipt under `receipts/stegfin-continuity-machine-executor/`.

The native delivery installer produces a rootless systemd-user service on Linux or LaunchAgent on macOS. It is `oneshot`, retries only non-successful executions, embeds no credential material, does not replace the heartbeat, and creates no execution authority. Hosted activation is explicitly refused.

## Validation evidence

Focused validation completed before workflow consolidation:

```text
workflow: StegFin Continuity Machine Executor - Validation Only / No GitHub Token Authority
run: 31850156719
job: 94924299352
conclusion: SUCCESS
focused tests: 8/8 PASS
compile: PASS
hosted execution fail-closed: PASS
rootless service materialization: PASS_NON_AUTHORIZING
workflow non-authorizing proof: PASS
GITHUB_TOKEN/GH_TOKEN/GITHUB_PAT present in validation process: false
```

Stable validation surface after consolidation:

```text
.github/workflows/heartbeat-worker-project.yml
trigger coverage: scripts/** tests/** control/** docs/** workers/**
validation coverage: python -m unittest discover -v tests
credential-token process authority: NONE
production/runtime authority: NONE
```

The earlier broader Heartbeat Worker Project run `31850078913`, job `94924085568`, executed all eight executor tests successfully while an unrelated Admissible-Existence source-generation retrospective binding failed. That concurrent AE binding was later reconciled by its own owner. The focused validation remains retained historical evidence and the stable repository-wide suite now owns continuing regression validation.

Receipt:

```text
receipts/stegfin-continuity-machine-executor/source-validation-20260814.json
```

## Claim disposition

```text
source_claim_ref: control/session-implementation-claim-2026-08-14-stegfin-continuity-machine-executor.json
source_claim_state: COMPLETE_VALIDATED_RELEASED
workflow_minimization_claim_ref: control/session-integration-claim-2026-08-15-stegfin-workflow-minimization.json
workflow_minimization_role: CONSOLIDATE_INTO_STABLE_DISPATCHER
```

Collision exclusions remain absolute:

- no heartbeat state, claim, fence or lease mutation;
- no alternate StegFin continuity claim issuer;
- no alternate TV/TVC provider broker, credential path or runtime observer;
- no provider secret input/export;
- no GitHub token runtime authority;
- no wallet contact/sign/broadcast;
- no live provider operation from hosted validation or chat.

## Activation boundary still open

**Repository source completion is not host activation and is not trade completion.** No available connector in this chat is the declared sovereign/local StegVerse host, so the native service was not installed or started from chat. Render and GitHub Actions are not substitutes.

Exact next authority-owned action on an already-declared authorized non-hosted StegVerse node with locally materialized canonical source:

```text
python scripts/install_stegfin_continuity_machine_service.py --root <local-StegVerse-Labs-.github-root>
```

The resulting native service invokes the released executor. The executor invokes the existing worker. The worker self-acquires the canonical collision-safe continuity claim, selects a real same-host TV/TVC Unix broker when present or the existing HTTPS READY path otherwise, performs only bounded pretrade preparation, and stops at USER_ONLY wallet action.

Machine-observable completion remains:

```text
WALLET_HANDOFF_READY
credential_authority=TV/TVC
non_tv_tvc_secret_or_token_used=false
provider_secret_exported=false
signed=false
broadcast=false
```

Until a native service activation receipt and terminal/fail-closed worker receipt exist, `G08-STEGFIN-TRADE-READY` remains active and this handoff must not claim governed activation.
