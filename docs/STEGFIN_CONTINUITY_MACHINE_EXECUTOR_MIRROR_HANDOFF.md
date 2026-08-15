# StegFin Continuity Machine Executor Mirror Handoff

Updated: 2026-08-15T01:17:00-05:00

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
state: SOURCE_COMPLETE_VALIDATED_RELEASED_POST_SOVEREIGN_INTEGRATION_RELEASED
```

## Canonical ownership and released source

The canonical trade handoff permits `ANY_AUTHORIZED_STEGVERSE_CONTINUITY_EXECUTOR`, makes resident heartbeat execution preferred but not required, binds execution to `MACHINE_SCHEDULER_ONLY`, and requires the existing StegFin worker itself to acquire the collision-safe continuity claim through `scripts/acquire_stegfin_continuity_claim.py`.

Released executor surfaces:

```text
scripts/run_stegfin_continuity_machine_executor.py
scripts/install_stegfin_continuity_machine_service.py
control/stegfin-continuity-machine-executor.json
data/stegfin-continuity-machine-executor/task-state.json
tests/test_stegfin_continuity_machine_executor.py
receipts/stegfin-continuity-machine-executor/source-validation-20260814.json
```

The dedicated executor validation workflow was intentionally removed under `G17-WORKFLOW-SURFACE-MINIMIZATION`. Continuing validation is owned by stable `.github/workflows/heartbeat-worker-project.yml`, which covers `scripts/**`, `tests/**`, `control/**`, `docs/**`, and `workers/**` and uses no GitHub credential-token authority.

Historical executor validation:

```text
run/job: 31850156719 / 94924299352
focused tests: 8/8 PASS
hosted execution fail-closed: PASS
rootless service materialization: PASS_NON_AUTHORIZING
```

## Machine contract

The executor is a one-shot local host adapter, not a heartbeat and not an authority source. It:

- rejects hosted GitHub/CI/Render/Vercel/Cloudflare execution;
- requires a valid sovereign-node declaration with `declared=true`, `credential_authority=TV/TVC`, and `github_token_required=false`;
- requires the canonical trade handoff/registry to remain machine-ready and collision-free;
- invokes only `workers/stegfin_continuity_carrier_worker_v3.py`;
- does not invent a claim/fence; the existing worker remains the claim issuer;
- strips GitHub/provider/wallet credential-like environment variables;
- accepts trade completion only when the canonical worker transition is exactly `STEGFIN_CONTINUITY_WALLET_HANDOFF_READY` with TV/TVC authority, no non-TV/TVC secret/token, no provider-secret export, `signed=false`, and `broadcast=false`.

The native installer produces a rootless systemd-user service on Linux or LaunchAgent on macOS. It embeds no credential material, does not replace the heartbeat, and creates no execution authority.

## Sovereign post-bootstrap integration — COMPLETE VALIDATED RELEASED

Task: `SOVEREIGN-STEGFIN-POST-BOOTSTRAP-001`  
Issue: `StegVerse-Labs/.github#163`  
Merged PR: `StegVerse-Labs/.github#171`  
Merge commit: `069d5f3211d73d987a6cf22be1db2b4519963d71`  
Claim: `control/session-implementation-claim-2026-08-15-sovereign-stegfin-post-bootstrap.json`  
Claim state: `COMPLETE_VALIDATED_RELEASED`

The former requirement that an executor host be independently pre-declared is superseded as an initiation prerequisite. The released sovereign self-bootstrap (`scripts/bootstrap_sovereign_runtime.py`, issue #160 / PR #162) can derive the non-authorizing local declaration, materialize/start native heartbeat supervision, and produce the canonical nine-predicate activation proof without requiring a resident heartbeat to pre-exist.

Released bridge:

```text
scripts/activate_stegfin_after_sovereign_bootstrap.py
```

It requires BOTH:

1. canonical sovereign `activation.latest.json` with `all_predicates_pass=true` and all nine predicates true;
2. a node declaration preserving `credential_authority=TV/TVC`, `github_token_required=false`, no third-party runtime requirement, and `RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY`.

Only then may it invoke:

```text
python scripts/install_stegfin_continuity_machine_service.py --root <local-StegVerse-Labs-.github-root>
```

The bridge accepts COMPLETE only when the executor activation receipt proves the rootless service active with:

```text
credential_authority=TV/TVC
github_token_runtime_authority=false
non_tv_tvc_secret_or_token_embedded=false
wallet_signing_authority=USER_ONLY
broadcast_authority=USER_ONLY
execution_authority_created=false
```

Its own receipt fixes:

```text
credential_requirement=NONE
provider_contacted=false
wallet_contacted=false
signed=false
broadcast=false
wallet_handoff_ready_claimed=false
```

The bridge therefore activates an already-released machine executor service; it does not execute the trade, acquire the continuity claim, choose credentials, contact provider/wallet, sign, broadcast, settle, or widen authority.

## Post-bootstrap validation evidence

Stable validation surface:

```text
.github/workflows/heartbeat-worker-project.yml
```

PR merge-ref evidence:

```text
run/job: 31868898830 / 94974292287
new integration tests: 5/5 PASS
compile: PASS
canonical JSON: PASS
executable handoffs: PASS
GitHub credential token present: false
```

Exact merged-main evidence:

```text
commit: 069d5f3211d73d987a6cf22be1db2b4519963d71
run/job: 31868980702 / 94974495941
new integration tests: 5/5 PASS
compile: PASS
canonical JSON: PASS_175
executable handoffs: PASS count=26 live_lanes=22
GitHub credential token present: false
```

The aggregate stable workflow remains red only because the immediately preceding main baseline already contains the same unrelated defects. Baseline run/job `31868785931 / 94973992395` fails on:

- `SHWP-ADMISSIBLE-SOURCE-GENERATION-CAPABILITY-001` retrospective phase/task-relationship mismatch;
- `control/session-goal-inventory-2026-08-14-admissible-existence-core-local-runtime-v5.json` schema/test drift (`shared_directives`, goal `origin`, `collision_boundaries`, and a legacy test still expecting v4).

No #163 surface introduced either failure class. This handoff therefore records the bounded post-bootstrap integration as validated while not falsely reporting the entire repository suite green.

## Collision exclusions

Absolute exclusions remain:

- no G18 heartbeat state, claim, fence, epoch, lease or worker mutation;
- no alternate StegFin continuity claim issuer;
- no alternate TV/TVC provider broker, credential, route, vault or runtime authority;
- no provider-secret input/export;
- no GitHub-token runtime authority;
- no wallet contact/sign/broadcast from the integration;
- no claim that service activation equals `WALLET_HANDOFF_READY`;
- no live provider operation from hosted validation/chat.

## Machine-owned continuation

The complete source chain is now:

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

No third-party host or pre-existing resident heartbeat is required to initiate the local chain.

Machine-observable trade completion remains exclusively:

```text
WALLET_HANDOFF_READY
credential_authority=TV/TVC
non_tv_tvc_secret_or_token_used=false
provider_secret_exported=false
signed=false
broadcast=false
```

Repository source completion is not live host activation and is not trade completion. The remaining live facts are owned by `SHWP-DURABLE-RUNTIME-ACTIVATION` G18 plus the canonical StegFin machine executor/worker and TV/TVC runtime authority. A genuine local nine-predicate proof releases the post-bootstrap bridge; only the canonical StegFin worker may then produce `WALLET_HANDOFF_READY` or an exact fail-closed receipt.

## Session consolidation / archive dependency

This handoff contains all #163 implementation, validation, authority-boundary, collision, and continuation state needed without this chat. The #163 session claim is released. The remaining product activation work is machine-owned and does not require a new chat-owned implementation claim unless a machine-observable failure reveals a new unclaimed source gap.

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```text
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.d/stegfin-continuity-carrier-007.json
collision_scope: STEGFIN-CONTINUITY-MACHINE-EXECUTOR-008 source and native service activation chain
release_condition: none; hosted/chat/manual execution cannot substitute for sovereign host execution
next_executable_action: NONE_MANUAL_EXECUTION_PROHIBITED
```

### WORKER-OWNED / DO NOT COMPETE

```text
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.d/stegfin-continuity-carrier-007.json
collision_scope: canonical StegFin continuity claim, Inventory N, provider pretrade preparation, and WALLET_HANDOFF_READY receipt
release_condition: canonical worker emits WALLET_HANDOFF_READY or exact fail-closed terminal receipt
next_executable_action: released sovereign bootstrap and post-bootstrap bridge activate the registered executor; the existing StegFin worker then self-acquires its collision-safe claim
```

### ESCALATED / AUTHORITY-OWNED

```text
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.d/stegfin-continuity-carrier-007.json
collision_scope: TV/TVC provider credential/route/vault/runtime authority and USER_ONLY wallet signing/broadcast
release_condition: required TV/TVC runtime predicate or USER_ONLY wallet action is independently evidenced by its canonical owner
next_executable_action: TV/TVC performs only provider/runtime operations it authorizes; USER_ONLY retains signing and broadcast
```

### COMPLETED / SUPERSEDED

```text
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.d/stegfin-continuity-carrier-007.json
collision_scope: executor source, installer, pre-heartbeat sovereign bootstrap, post-bootstrap bridge, and obsolete pre-declared-node initiation prerequisite
release_condition: source surfaces are COMPLETE_VALIDATED_RELEASED and obsolete initiation prerequisite is superseded by the released bootstrap chain
next_executable_action: NONE_SOURCE_REIMPLEMENTATION; observe the machine-owned live chain instead
```
