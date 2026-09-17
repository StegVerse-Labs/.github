# ERL Household Economic Conditions — BEA Readiness Reconciliation

Updated: 2026-09-17

## Identity

- Goal Task ID: `ERL-HOUSEHOLD-ECONOMIC-CONDITIONS-SITE-001`
- Canonical handoff: `docs/ERL_HOUSEHOLD_ECONOMIC_CONDITIONS_SITE_MIRROR_HANDOFF.md`
- Reconciliation base: `.github` main `365764f7653dca6745b287876f5dd5f76d057a54`
- Supersedes stale reconciliation PR: `.github#2045`
- COSV: not yet materialized
- Site public activation: `FALSE / NOT AUTHORIZED`

## Newly canonical source capability

TVC PR `#442` merged from exact head `65963e90af099171945e63d7d167773d034f5bd1` as `257184d8f40d51ab20e5e75ba4708d676222d78f` after all returned exact-head workflows succeeded. It materializes provider `bea` as a TV/TVC-only read-only NIPA provider profile using secret reference `vault://tvc/providers/bea/api-key`, dataset `NIPA`, table `T20600`, and exact admitted lines `27`, `29`, `35`, `37`. The profile does not create credential availability, finding authority, or public activation authority.

stegfin-governance PR `#110` merged from exact head `077d7365ba84689f499f7814c5a59607869fec4f` as `d92debb563009e9f33c4a14e6472709b38111d25` after all returned exact-head workflows succeeded. It extends the existing TV/TVC hidden-TTY -> inherited-FD -> protected tmpfs ingress path for provider `bea` and adds `scripts/check_tvc_bea_credential_readiness.py`.

The readiness observer is metadata-only. It checks regular-file type, expected owner `10001:10001`, mode `0400`, and nonzero size. It explicitly does not read, return, log, or hash credential bytes and does not contact BEA.

## Runtime observation attempt

The current session checked the available remote execution connector for an authorized device/runtime and observed zero connected devices. Repository-accessible evidence was also searched for an authentic `stegverse.tvc.bea-credential-readiness/v1` receipt and none was observed.

This does **not** establish credential absence. It establishes only:

```text
BEA_PROVIDER_PROFILE = MATERIALIZED
BEA_SECRET_INGRESS_PATH = MATERIALIZED
BEA_AUTHENTIC_RESIDENT_CREDENTIAL_READINESS = UNKNOWN / NOT OBSERVED
BEA_API_EXECUTION = NOT PERFORMED
BEA_RESULT_ADMITTED_TO_ERL = false
SITE_PUBLIC_ACTIVATION = false
```

No second user-operated device is required or permitted by this goal. No credential value should be requested in chat, GitHub, argv, environment variables, logs, receipts, or artifacts.

## BEA execution gate

Only an authentic resident readiness result with `decision=READY` may satisfy the credential-custody predicate. Source existence, CI, merge state, file-path conventions, or the existence of the metadata observer cannot satisfy it.

If authentic readiness becomes observable:

1. issue the existing bounded single-use TVC BEA read-only lease;
2. call only BEA `NIPA` / `T20600` lines `27`, `29`, `35`, `37`;
3. retain raw response bytes, SHA-256, acquisition timestamp, and source vintage;
4. normalize DPI, PCE, saving-rate, and real-DPI observations as candidate evidence only;
5. do not infer household net take-home resources, necessary consumption satisfaction, discretionary residual, distributional welfare, or unmet need solely from those aggregates;
6. keep `finding_authority=false` and `public_activation_authorized=false`.

If authentic readiness is not observed, BEA remains `UNKNOWN / BLOCKED_ON_RUNTIME_PREDICATE` and the household-state contract continues without fabricated BEA observations.

## Household-state boundary retained

The current evidence state remains partial. Required-cost burden and delinquency/arrears may carry only previously admitted partial evidence. Net disposable/take-home resources, complete required-cost burden, necessary consumption, discretionary residual, saving/dissaving where not authentically sourced, new borrowing, complete delinquency/arrears household interpretation, and unmet/foregone consumption remain `UNKNOWN` unless supported by exact governed evidence.

Observed debt stock is not new borrowing. Aggregate delinquency flow is not by itself distributional household stress. Aggregate PCE is not proof of need satisfaction. Gross real earnings are not take-home resources.

## Next authentic transition

`OBSERVE_BEA_RESIDENT_CREDENTIAL_READINESS` through the first authorized same-device or admitted ephemeral resident execution surface. Only `READY` permits `EXECUTE_BEA_READONLY_IF_READY`. Site binding remains separately gated on authentic governed ERL output and served-body proof.
