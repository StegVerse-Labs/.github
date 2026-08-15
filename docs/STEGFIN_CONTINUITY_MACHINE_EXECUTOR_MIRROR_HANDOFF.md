# StegFin Continuity Machine Executor Mirror Handoff

Updated: 2026-08-15T01:08:00-05:00

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
state: SOURCE_COMPLETE_VALIDATED_RELEASED_POST_SOVEREIGN_INTEGRATION_PENDING_VALIDATION
```

## Canonical ownership

The canonical trade handoff permits `ANY_AUTHORIZED_STEGVERSE_CONTINUITY_EXECUTOR`, makes resident heartbeat execution preferred but not required, binds execution to `MACHINE_SCHEDULER_ONLY`, and requires the existing worker itself to acquire the collision-safe continuity claim through `scripts/acquire_stegfin_continuity_claim.py`.

This handoff owns only the non-heartbeat machine executor, native rootless delivery, and the bounded post-sovereign activation integration. It does not own the StegFin continuity claim algorithm, TV/TVC transport/credential/vault authority, G18 heartbeat authority, provider operation authority, wallet signing, broadcast, or settlement.

## Released machine executor source

```text
scripts/run_stegfin_continuity_machine_executor.py
scripts/install_stegfin_continuity_machine_service.py
control/stegfin-continuity-machine-executor.json
data/stegfin-continuity-machine-executor/task-state.json
tests/test_stegfin_continuity_machine_executor.py
.github/workflows/stegfin-continuity-machine-executor.yml
receipts/stegfin-continuity-machine-executor/source-validation-20260814.json
```

Focused source evidence:

```text
workflow: StegFin Continuity Machine Executor - Validation Only / No GitHub Token Authority
run: 31850156719
job: 94924299352
conclusion: SUCCESS
focused tests: 8/8 PASS
hosted execution fail-closed: PASS
rootless service materialization: PASS_NON_AUTHORIZING
```

Source claim:

```text
control/session-implementation-claim-2026-08-14-stegfin-continuity-machine-executor.json
state: COMPLETE_VALIDATED_RELEASED_TO_AUTHORIZED_STEGVERSE_NODE_AND_CANONICAL_STEGFIN_WORKER
released_at: 2026-08-14T18:28:00-05:00
```

## Machine contract

The executor is a one-shot local host adapter, not a heartbeat and not an authority source. It:

- rejects GitHub Actions, CI, Render, Vercel and Cloudflare-hosted execution;
- requires a valid local sovereign-node declaration with `declared=true`, `credential_authority=TV/TVC`, and `github_token_required=false`;
- requires the canonical trade handoff/registry to remain machine-ready and collision-free;
- invokes only `workers/stegfin_continuity_carrier_worker_v3.py`;
- passes no carrier-invented claim or fence; the existing worker remains the continuity-claim issuer;
- strips GitHub/provider/wallet credential-like environment variables and forwards only bounded non-secret location/transport values;
- accepts worker completion only when the canonical transition is exactly `STEGFIN_CONTINUITY_WALLET_HANDOFF_READY` and durable evidence independently proves TV/TVC authority, no non-TV/TVC secret/token, no provider-secret export, `signed=false`, and `broadcast=false`.

The native installer produces a rootless systemd-user service on Linux or LaunchAgent on macOS. It embeds no credential material, does not replace the heartbeat, and creates no execution authority.

## Sovereign post-bootstrap integration — ACTIVE IMPLEMENTATION

Task: `SOVEREIGN-STEGFIN-POST-BOOTSTRAP-001`  
Issue: `StegVerse-Labs/.github#163`  
Branch: `feat/sovereign-stegfin-post-bootstrap-001-v2`  
Claim: `control/session-implementation-claim-2026-08-14-sovereign-stegfin-post-bootstrap.json`

The earlier instruction to start the executor only on an **already-declared** local node is superseded as an initiation prerequisite. The released sovereign self-bootstrap (`scripts/bootstrap_sovereign_runtime.py`, issue #160 / PR #162) can derive the non-authorizing node declaration, materialize/start native heartbeat supervision, and produce the canonical nine-predicate proof without requiring a resident heartbeat to pre-exist.

The post-bootstrap integration surface is:

```text
scripts/activate_stegfin_after_sovereign_bootstrap.py
```

It may invoke the existing StegFin service installer only after BOTH of these local facts are established:

1. `~/.stegverse/heartbeat/activation.latest.json` (or explicitly supplied proof path) reports `all_predicates_pass=true` and all nine sovereign predicates true;
2. the local node declaration preserves `credential_authority=TV/TVC`, `github_token_required=false`, no third-party runtime requirement, and `RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY`.

It then invokes only:

```text
python scripts/install_stegfin_continuity_machine_service.py --root <local-StegVerse-Labs-.github-root>
```

The integration succeeds only when the executor activation receipt reports the native service active while retaining:

```text
credential_authority=TV/TVC
github_token_runtime_authority=false
non_tv_tvc_secret_or_token_embedded=false
wallet_signing_authority=USER_ONLY
broadcast_authority=USER_ONLY
execution_authority_created=false
```

The integration itself explicitly records and preserves:

```text
credential_requirement=NONE
provider_contacted=false
wallet_contacted=false
signed=false
broadcast=false
wallet_handoff_ready_claimed=false
```

It is therefore an activation bridge, not a trade executor and not an authority source.

## Collision exclusions

Absolute exclusions for the executor and post-bootstrap integration:

- no heartbeat state, G18 claim, fence, epoch, lease or worker mutation;
- no alternate StegFin continuity claim issuer;
- no alternate TV/TVC provider broker, credential, route, vault or runtime authority;
- no provider-secret input/export;
- no GitHub-token runtime authority;
- no wallet contact/sign/broadcast from integration code;
- no claim that service activation equals `WALLET_HANDOFF_READY`;
- no live-provider operation from hosted validation or chat.

## Validation

Released executor validation remains authoritative for its bounded source package:

```text
run/job: 31850156719 / 94924299352 — SUCCESS
focused tests: 8/8 PASS
```

Post-sovereign integration validation target:

```text
python -m py_compile scripts/activate_stegfin_after_sovereign_bootstrap.py
python -m unittest tests.test_activate_stegfin_after_sovereign_bootstrap -v
workflow: Sovereign StegFin Post-Bootstrap Validation
```

Hosted validation must prove GitHub itself fails closed before native service activation and creates no production authority.

## Activation boundary

Repository source completion is not host activation and is not trade completion.

After the post-bootstrap integration source is released, the local machine-owned path is:

```text
canonical local source
  -> scripts/bootstrap_sovereign_runtime.py
  -> nine-predicate sovereign activation.latest.json PASS
  -> scripts/activate_stegfin_after_sovereign_bootstrap.py
  -> native rootless StegFin executor service active
  -> released executor
  -> canonical StegFin worker self-acquires claim
  -> canonical TV/TVC transport selection
  -> bounded pretrade preparation
  -> WALLET_HANDOFF_READY OR exact fail-closed receipt
  -> USER_ONLY wallet action boundary
```

No third-party host or pre-existing resident heartbeat is required to initiate this local chain.

Machine-observable trade completion remains exclusively:

```text
WALLET_HANDOFF_READY
credential_authority=TV/TVC
non_tv_tvc_secret_or_token_used=false
provider_secret_exported=false
signed=false
broadcast=false
```

Until that canonical worker receipt exists, `G08-STEGFIN-TRADE-READY` remains active and this handoff must not claim governed trade activation.

## Next action

Validate issue #163 on its rebased PR head, merge only if the dedicated tokenless gate passes, then observe exact merged-main validation and release the finite integration claim. Live `WALLET_HANDOFF_READY` remains owned by the canonical machine executor/worker and TV/TVC runtime authority.
