# Crypto Live Auto Canonical Work Mirror Handoff

Updated: 2026-09-09
Repository: `StegVerse-Labs/.github`
Task Registry ID: `CRYPTO-LIVE-AUTO-001`
COSV task vector: `50000000106000`
Source task owner: `StegVerse-Labs/crypto-bot`
Related goals: `CRYPTO-MONEY-MANAGER-001`, `CRYPTO-LIVE-AUTO-001`
Adjacent governed owners: `StegVerse-Labs/TVC#119`, `StegVerse-Labs/stegfin-governance#84`
Status: `RESIDENT_INGRESS_SOURCE_REPAIRS_MERGED / AUTHENTIC_INGRESS_PENDING`

## Current canonical identity

- task id: `CRYPTO-LIVE-AUTO-001`
- profile: `task.v1`
- COSV vector: `50000000106000`
- lifecycle: `MACHINE_OWNED`
- canonical coordination state: `PROPOSED`
- next canonical transition: `INGRESS_ADMITTED`
- required runtime environment: `CURRENT_USER_IPHONE_AND_SOVEREIGN_RESIDENT`

## Completed remediation

### PR #1263 — resident request/task self-materialization

Merged at `8efdad0ac689dbd3692b6dac8e014f4c87bd5c9c` after organization-control, Heartbeat Worker Project, and deterministic repository-suite validations all passed.

It repaired:

- permanent `NO_REQUEST` caused by checking resident request presence before local source materialization;
- stale preserved resident monolithic registry that predates `CRYPTO-LIVE-AUTO-001` by allowing exact task-specific fallback-shard materialization from already-local canonical source without replacing resident registry state.

Focused regression coverage: `tests/test_crypto_live_auto_resident_ingress_repair.py`.

### PR #1271 — portable exact-selector addressability

Merged at `5d2a65279af3ad8f15e986943adc3038ee532548`.

Exact-head validation evidence:

- Deterministic Repository Suite `34357571372` — SUCCESS;
- Cross-Framework Current-Basis Resident Request Validation `34357571329` — SUCCESS;
- Heartbeat Worker Project `34357571320` — SUCCESS;
- Validate organization control plane `34357571323` — SUCCESS.

This repair added `canonical_work_coordination` to `scripts/refresh_and_dispatch_resident_requests.py` so the already-local portable refresh/dispatch bridge can target the same Canonical Work consumer already registered by `scripts/dispatch_resident_execution_requests.py`.

Focused regression coverage: `tests/test_crypto_live_auto_portable_dispatch_selector.py`.

The historical portable default remains unchanged and exact one-consumer selection remains enforced.

README was reviewed after both repairs. Existing generalized Canonical Work ingress, resident dispatch, and portable local-source refresh documentation remains accurate; no duplicate CryptoBot-specific section is required.

## Existing runtime path

The rootless resident source-refresh watcher already watches `control/resident-execution-request.d` and performs a generic resident request dispatch after local source refresh. The portable bridge now additionally supports exact targeted selection of `canonical_work_coordination`.

Canonical chain remains:

`canonical task ingress -> Master Records reconciliation -> WorkerCoordinator admission/claim/fence -> TVC current-iPhone/SKAP/provider evidence -> StegFin #84 bounded decision -> first max-$10 ETH-USD LIMIT/GTC post_only proof -> reconciliation -> next authenticated snapshot -> second bounded cycle -> repeat-loop proof`

## Required authentic evidence

The exact runtime artifact still required is:

`receipts/sovereign-host/canonical-work-crypto-live-auto-request-consumption.latest.json`

Current GitHub registry dependency `DEP-CRYPTO-CANONICAL-WORK-INGRESS` remains `UNRESOLVED`, and no authentic copy of that receipt is currently present in canonical source evidence.

No merge, CI result, source request, COSV pointer, hosted workflow, or test receipt may substitute for this resident artifact.

## Exact next action

On an already-running sovereign resident after the merged source reaches the already-local canonical source projection:

1. refresh resident static source from that already-local canonical source;
2. dispatch exactly `canonical_work_coordination` or allow the existing source-refresh watcher to perform its generic request visit;
3. require `receipts/sovereign-host/canonical-work-crypto-live-auto-request-consumption.latest.json` with completed Canonical Work ingress evidence;
4. reconcile the resulting event into Master Records;
5. only then advance WorkerCoordinator admission and the TVC/SKAP + StegFin bounded-live stages.

## Current completion boundary

All currently identified GitHub/source-level resident-ingress defects for CryptoBot have been repaired, validated, and merged. Authentic sovereign resident consumption is still not observed. Master Records reconciliation, WorkerCoordinator admission, current-iPhone TVC/SKAP Coinbase evidence, StegFin bounded approval, first bounded live order, fill/fee reconciliation, next authenticated portfolio snapshot, and second-cycle proof remain outstanding.
