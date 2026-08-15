# StegFin Continuity Machine Executor Mirror Handoff

Updated: 2026-08-15T01:23:00-05:00

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
state: SOURCE_COMPLETE_VALIDATED_RELEASED_POST_BOOTSTRAP_PROVENANCE_HARDENING_ACTIVE
```

## Canonical ownership

This handoff owns the non-heartbeat machine executor, native rootless delivery, and bounded sovereign post-bootstrap activation bridge. It does not own the StegFin continuity claim algorithm, TV/TVC transport/credential/vault authority, G18 heartbeat authority, provider operation authority, wallet signing, broadcast, settlement, or `WALLET_HANDOFF_READY` disposition.

The canonical trade handoff permits `ANY_AUTHORIZED_STEGVERSE_CONTINUITY_EXECUTOR`, makes resident heartbeat execution preferred but not required, binds live trade execution to machine scheduling, and requires the existing StegFin worker itself to acquire the collision-safe continuity claim through `scripts/acquire_stegfin_continuity_claim.py`.

## Released machine executor source

```text
scripts/run_stegfin_continuity_machine_executor.py
scripts/install_stegfin_continuity_machine_service.py
control/stegfin-continuity-machine-executor.json
data/stegfin-continuity-machine-executor/task-state.json
tests/test_stegfin_continuity_machine_executor.py
receipts/stegfin-continuity-machine-executor/source-validation-20260814.json
```

Historical focused validation:

```text
run/job: 31850156719 / 94924299352
focused tests: 8/8 PASS
hosted execution fail-closed: PASS
rootless service materialization: PASS_NON_AUTHORIZING
```

The dedicated executor validation workflow was intentionally removed under `G17-WORKFLOW-SURFACE-MINIMIZATION`; continuing repository validation uses stable `.github/workflows/heartbeat-worker-project.yml` and the organization control-plane validators.

## Machine contract

The executor is a one-shot local host adapter, not a heartbeat and not an authority source. It:

- rejects hosted GitHub/CI/Render/Vercel/Cloudflare execution;
- requires a valid local sovereign-node declaration with `credential_authority=TV/TVC` and `github_token_required=false`;
- requires the canonical trade handoff/registry to remain machine-ready and collision-free;
- invokes only `workers/stegfin_continuity_carrier_worker_v3.py`;
- does not invent a claim/fence; the existing worker remains the continuity-claim issuer;
- strips GitHub/provider/wallet credential-like environment variables;
- accepts trade completion only when the canonical transition is exactly `STEGFIN_CONTINUITY_WALLET_HANDOFF_READY` and durable evidence proves TV/TVC authority, no non-TV/TVC secret/token, no provider-secret export, `signed=false`, and `broadcast=false`.

The native installer produces a rootless systemd-user service on Linux or LaunchAgent on macOS. It embeds no credential material, does not replace the heartbeat, and creates no execution authority.

## Sovereign self-bootstrap and post-bootstrap integration

The former initiation prerequisite requiring a pre-existing declared node is superseded. Released `scripts/bootstrap_sovereign_runtime.py` can, from canonical local source on a non-hosted machine:

```text
prove local source/state eligibility
-> derive non-authorizing node declaration
-> install/start native sovereign heartbeat service
-> run canonical activation verifier
-> emit ~/.stegverse/heartbeat/bootstrap.latest.json
-> emit ~/.stegverse/heartbeat/activation.latest.json with nine predicates
```

Issue #160 is CLOSED_COMPLETED for this bootstrap source. Issue #163 / PR #171 merged the first post-bootstrap StegFin integration at `069d5f3211d73d987a6cf22be1db2b4519963d71`.

The first bridge correctly preserved credential and wallet boundaries, but subsequent validation found a provenance gap: it accepted caller-supplied proof/node JSON by shape. That was insufficient because a boolean-complete but noncanonical proof could masquerade as sovereign bootstrap evidence.

## Canonical bootstrap-provenance hardening — ACTIVE

Task: `STEGFIN-POST-BOOTSTRAP-PROVENANCE-172`  
Issue: `StegVerse-Labs/.github#172`  
PR: `StegVerse-Labs/.github#173`  
Branch: `fix/stegfin-post-bootstrap-provenance-172`  
Claim: `control/session-implementation-claim-2026-08-15-stegfin-post-bootstrap-provenance-172.json`

The bounded correction requires all of the following before the post-bootstrap adapter may invoke the already-released executor-service installer:

```text
activation proof schema = stegverse.sovereign-runtime-activation-proof/v1
all nine activation predicates = true
bootstrap receipt schema = stegverse.sovereign-runtime-self-bootstrap-receipt/v1
bootstrap state = COMPLETE
bootstrap reason = SOVEREIGN_RUNTIME_SELF_BOOTSTRAP_VERIFIED
bootstrap credential_requirement = NONE
bootstrap credential_authority = TV/TVC
bootstrap github_token_required = false
bootstrap proof_path == exact activation proof consumed
bootstrap node_declaration_ref == exact node declaration consumed
bootstrap source_root == exact local StegVerse-Labs/.github root
proof.detail.runtime_root == bootstrap runtime_root
node credential_authority = TV/TVC
node github_token_required = false
node authority_effect = RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY
```

Forged proof schema, mismatched proof/bootstrap, mismatched node declaration, wrong source/runtime root, and non-complete bootstrap receipt all fail closed before installer invocation.

The adapter still fixes these non-authorizing invariants in its receipt:

```text
credential_requirement=NONE
credential_authority=TV/TVC
github_token_runtime_authority=NONE
non_tv_tvc_secret_or_token_used=false
provider_contacted=false
wallet_contacted=false
signed=false
broadcast=false
wallet_handoff_ready_claimed=false
```

Even a successful post-bootstrap adapter proves only that the released native executor service is active. It cannot claim trade readiness.

## Canonical live continuation

```text
canonical local source
-> sovereign self-bootstrap
-> exact canonical bootstrap + nine-predicate activation proof
-> provenance-bound post-bootstrap bridge
-> native rootless StegFin executor service active
-> released one-shot executor
-> canonical StegFin worker self-acquires claim
-> actual same-host TV/TVC Unix broker OR HTTPS path after TVC-CAPABILITY-RUNTIME-002 READY
-> fresh complete Inventory N
-> exact 12.50 USDC -> WETH governed preparation
-> quote/allowance/gas/simulation
-> WALLET_HANDOFF_READY OR exact fail-closed receipt
-> STOP
-> USER_ONLY wallet review/sign/broadcast
```

Machine-observable trade completion remains exclusively:

```text
WALLET_HANDOFF_READY
credential_authority=TV/TVC
non_tv_tvc_secret_or_token_used=false
provider_secret_exported=false
signed=false
broadcast=false
```

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```yaml
- task_id: STEGFIN-POST-BOOTSTRAP-PROVENANCE-172
  execution_owner: current bounded validation/integration session
  claim_state: CLAIMED_FOR_IMPLEMENTATION_AND_VALIDATION
  worker_registry_ref: control/session-implementation-claim-2026-08-15-stegfin-post-bootstrap-provenance-172.json
  manual_execution_allowed: true
  collision_scope: post-bootstrap proof/bootstrap/node provenance validation, deterministic tests, and this handoff only
  release_condition: PR #173 merged after owned validation passes and exact merged-main validation confirms provenance checks; claim then released
  next_executable_action: validate PR #173, repair only owned provenance surfaces, merge when current-head gates pass, and record merged-main evidence
```

### WORKER-OWNED / DO NOT COMPETE

```yaml
- task_id: STEGFIN-CONTINUITY-CARRIER-007
  execution_owner: stegfin-continuity-carrier-worker
  claim_state: MACHINE_CLAIM_ON_EXECUTION
  worker_registry_ref: handoffs/STEGFIN-CONTINUITY-CARRIER-007.json
  manual_execution_allowed: false
  collision_scope: continuity claim acquisition, Inventory N, TV/TVC transport selection, provider pretrade preparation, and WALLET_HANDOFF_READY/fail-closed receipt
  release_condition: terminal wallet-handoff-ready or fail-closed receipt persisted and canonical claim released
  next_executable_action: authorized native executor invokes the existing worker after local service activation; no chat/session substitutes
```

### ESCALATED / AUTHORITY-OWNED

```yaml
- task_id: TVC-PROVIDER-AND-RUNTIME-AUTHORITY
  execution_owner: StegVerse-Labs/TV + StegVerse-Labs/TVC
  claim_state: AUTHORITY_OWNED_WITH_EXISTING_HTTPS_VALIDATION_CLAIM
  worker_registry_ref: StegVerse-Labs/TVC/tasks/TVC-CAPABILITY-RUNTIME-002.json
  manual_execution_allowed: false
  collision_scope: credential/provider/vault/route authority, protected values, HTTPS primary-runtime activation and observation
  release_condition: applicable TV/TVC runtime/route evidence reaches its canonical release predicate, or the StegFin worker independently observes the admitted same-host Unix broker path
  next_executable_action: TV/TVC continues its existing authority-owned lanes without session-created credentials or tokens
```

### COMPLETED / SUPERSEDED

```yaml
- task_id: SOVEREIGN-STEGFIN-POST-BOOTSTRAP-001
  execution_owner: StegVerse-Labs/.github source integration
  claim_state: COMPLETE_VALIDATED_RELEASED_WITH_PROVENANCE_FOLLOWUP
  worker_registry_ref: StegVerse-Labs/.github#163 / PR #171
  manual_execution_allowed: false
  collision_scope: released initial post-bootstrap integration source; superseded only where #172 tightens provenance acceptance
  release_condition: source merged; provenance acceptance now governed by #172
  next_executable_action: none outside #172 bounded hardening
```

## Archive dependency

Repository source completion is not native host activation and is not trade completion. This handoff is sufficient for continuation without chat history only after the active #172 source claim is released. The wider session remains non-archive-ready while current v5 goals remain active and `WALLET_HANDOFF_READY` has not been observed.
