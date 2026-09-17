# ERL Household Economic Conditions — BEA Readiness Reconciliation

Updated: 2026-09-17

## Identity

- Goal Task ID: `ERL-HOUSEHOLD-ECONOMIC-CONDITIONS-SITE-001`
- Canonical handoff: `docs/ERL_HOUSEHOLD_ECONOMIC_CONDITIONS_SITE_MIRROR_HANDOFF.md`
- Reconciliation base: `.github` main `8f8b87bb26159e6d0eeefa68bd6a9c3e4f1827a6`
- Supersedes stale reconciliation PR: `.github#2045`
- Site public activation: `FALSE / NOT AUTHORIZED`

## Canonical BEA capability

TVC PR `#442` merged from exact head `65963e90af099171945e63d7d167773d034f5bd1` as `257184d8f40d51ab20e5e75ba4708d676222d78f` after all returned exact-head workflows succeeded. It materializes provider `bea` as a TV/TVC-only read-only NIPA provider profile using secret reference `vault://tvc/providers/bea/api-key`, dataset `NIPA`, table `T20600`, and exact admitted lines `27`, `29`, `35`, `37`.

stegfin-governance PR `#110` merged from exact head `077d7365ba84689f499f7814c5a59607869fec4f` as `d92debb563009e9f33c4a14e6472709b38111d25` after all returned exact-head workflows succeeded. It extends the existing TV/TVC hidden-TTY -> inherited-FD -> protected tmpfs ingress path for provider `bea` and adds `scripts/check_tvc_bea_credential_readiness.py`.

The readiness observer checks only regular-file type, expected owner `10001:10001`, mode `0400`, and nonzero size. It explicitly does not read, return, log, or hash credential bytes and does not contact BEA.

## Runtime observation attempted

The current session queried the available remote execution connector and observed zero connected devices. Repository-accessible retained evidence was also searched for an authentic `stegverse.tvc.bea-credential-readiness/v1` receipt and none was observed.

This does not prove credential absence. Current authentic state is:

```text
BEA_PROVIDER_PROFILE = MATERIALIZED
BEA_SECRET_INGRESS_PATH = MATERIALIZED
BEA_AUTHENTIC_RESIDENT_CREDENTIAL_READINESS = UNKNOWN / NOT OBSERVED
BEA_API_EXECUTION = NOT PERFORMED
BEA_RESULT_ADMITTED_TO_ERL = false
SITE_PUBLIC_ACTIVATION = false
```

No second user-operated device is required or permitted. No credential value may be requested in chat, GitHub, argv, environment variables, logs, receipts, or artifacts.

## BEA execution gate

Only an authentic resident readiness result with `decision=READY` satisfies the credential-custody predicate. Source existence, CI, merge state, path conventions, or the existence of the metadata observer cannot satisfy it.

If authentic readiness becomes observable:

1. issue the existing bounded single-use TVC BEA read-only lease;
2. call only BEA `NIPA` / `T20600` lines `27`, `29`, `35`, `37`;
3. retain raw response bytes, SHA-256, acquisition timestamp, and source vintage;
4. normalize DPI, PCE, saving-rate, and real-DPI observations as candidate evidence only;
5. do not infer household net take-home resources, necessary-consumption satisfaction, discretionary residual, distributional welfare, or unmet need solely from those aggregates;
6. keep `finding_authority=false` and `public_activation_authorized=false`.

If authentic readiness is not observed, BEA remains `UNKNOWN / BLOCKED_ON_RUNTIME_PREDICATE` and no BEA values are fabricated.

## Household-state boundary retained

The state remains partial. Previously admitted required-cost and delinquency evidence remains only partial. Net disposable/take-home resources, complete required-cost burden, necessary consumption, discretionary residual, unsupported saving/dissaving, new borrowing, complete delinquency/arrears household interpretation, and unmet/foregone consumption remain `UNKNOWN` unless exact governed evidence supports them.

Observed debt stock is not new borrowing. Aggregate delinquency flow is not by itself distributional household stress. Aggregate PCE is not proof of need satisfaction. Gross real earnings are not take-home resources.

## Next authentic transition

`OBSERVE_BEA_RESIDENT_CREDENTIAL_READINESS` through the first authorized same-device or admitted ephemeral resident execution surface. Only `READY` permits `EXECUTE_BEA_READONLY_IF_READY`. Site binding remains separately gated on authentic governed ERL output and served-body proof.
