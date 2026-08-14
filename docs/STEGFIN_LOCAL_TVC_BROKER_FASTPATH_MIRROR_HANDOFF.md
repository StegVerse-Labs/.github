# StegFin Local TVC Broker Fast-Path Mirror Handoff

## Authority

This scoped handoff is subordinate to `handoffs/STEGFIN-CONTINUITY-CARRIER-007.json` and `StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md`. It changes transport readiness only; it grants no credential, trade, signing, broadcast, provider-secret, or settlement authority.

```text
goal_id: STEGFIN-LOCAL-TVC-BROKER-FASTPATH-009
parent_goal: STEGFIN-BASE-ROUNDTRIP-001
repository: StegVerse-Labs/.github
branch: fix/stegfin-local-tvc-broker-fastpath
canonical_worker: workers/stegfin_continuity_carrier_worker_v3.py
adapter: process:stegfin-continuity-carrier-v1
credential_authority: TV/TVC
wallet_signing_authority: USER_ONLY
broadcast_authority: USER_ONLY
github_token_required: false
```

## Defect

The canonical continuity runner already accepts either an HTTPS TV/TVC broker endpoint or an absolute same-host Unix broker socket, but the registered worker required `TVC-CAPABILITY-RUNTIME-002` HTTPS primary-runtime readiness before it would even inspect the same-host socket. That made the HTTPS exposure path a universal hard dependency even when the canonical private TV/TVC broker was already locally available.

## Fix

`workers/stegfin_continuity_carrier_worker_v3.py` now selects a live absolute Unix socket only when it is an actual Unix socket. On that path it preserves the old worker's exact TVC source validation, bypasses only the HTTPS runtime-observer gate, and then executes the existing `run_continuity_pretrade.py` against the real socket. The continuity runner therefore performs the actual provider-operation attempt; a dead, invalid, or denying socket fails closed.

If no local Unix socket is available, v3 delegates unchanged to the existing v2 -> primary-runtime-observer path.

## Security boundary

```text
non-TV/TVC secret/token accepted: false
GitHub token allowlisted: false
provider API key exported: false
wallet key accepted: false
signing: USER_ONLY
broadcast: USER_ONLY
carrier grants execution authority: false
```

No synthetic HTTP probe receipt is persisted and no claim is made that `tvc.stegverse.org` is observable when the Unix fast path is used. The local transport readiness record is explicitly `READY_LOCAL_TV_TVC_UNIX_BROKER_BOUND` and has authority effect `TRANSPORT_READINESS_ONLY`.

## Validation

Required validation:

```text
python -m unittest -v tests.test_stegfin_continuity_local_broker_fastpath
complete deterministic repository suite
executable handoff validation
no-token workflow proof
```

## Collision state

At implementation start the registered continuity task was `HANDOFF_READY`, `claim_id=null`, and its worker was `AVAILABLE`; there was no active continuity execution claim. The implementation changes adapter/source behavior only and does not acquire the trade collision scope.

## Release condition

Merge only after repository validation passes. After merge, machine execution may use either:

```text
A) same-host canonical TV/TVC Unix broker socket
OR
B) existing HTTPS primary runtime + TVC-CAPABILITY-RUNTIME-002 READY receipt
```

Both paths converge on the same terminal predicate:

```text
WALLET_HANDOFF_READY
credential_authority=TV/TVC
non_tv_tvc_secret_or_token_used=false
provider_secret_exported=false
signed=false
broadcast=false
```
