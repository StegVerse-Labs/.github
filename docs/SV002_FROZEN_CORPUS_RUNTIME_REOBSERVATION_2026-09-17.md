# SV002 Frozen Corpus Runtime Re-observation — 2026-09-17

Goal Task ID: `SHWP-SV002-FROZEN-CORPUS-MATERIALIZATION-001`
COSV: `50000000107001`
Tracking issue: `#2064`

## Re-observation result

The authorized direct resident-device surface was queried again during this continuation and returned no online device. A direct read-only command probe against the command-capable resident connector also failed with `No devices available`; therefore no authentic resident filesystem or process evidence was available from that surface during this invocation.

No new authentic repository-retained evidence was found for:

- `SERVICE_INSTALLED_VERIFIED` from the existing TVC private-source resident service path;
- private-source `resident-state.json` proving resident service/watcher state and credential presence without disclosure;
- materialization/execution receipts for the four staged SV002 frozen-source requests;
- any TT/RTG/GTG/AE receipt satisfying `authorized_exact_sha == observed_exact_sha == requested exact_sha`.

## Relevant source repairs landed after prior handoff

The current `.github` main contains two machine-remediable runtime-source repairs that were not present when the previous SV002 handoff was written:

1. preclaim fragment-policy reconciliation at commit `491947e94a4463d7fed07c84372e261bd492d03f` with regression coverage at `dbf35f095e770203fb274ab27f1984a397544b7e`;
2. exact-selector dispatch fail-closed semantics at commit `24ad1e4f290980f7aaa7a7c24e18db6ce504b3c8` with regression coverage at `069014cab0e88b84dac0ca8f045b9b1c4a3a5ce4`.

The fleet reconciliation at `b944e48b639f937510678496fe509f3cc7d022f5` explicitly states these repairs do not establish an admitted local execution opportunity and do not prove TVC resident service/credential/request consumption.

These source fixes are therefore reusable prerequisites only. They do not satisfy this Goal's frozen-corpus materialization predicates.

## Existing callable paths checked

The resident dispatcher already registers `tvc_broker_validation`, but that consumer is scoped to TVC repository-broker validation and its private-source bootstrap deliberately records `systemd_service_start_requested_by_consumer=false`. It is not the `RT-TVC-PRIMARY-RUNTIME-BINDING-001 -> TVC-PRIMARY-RUNTIME-ACTIVATION-DELIVERY-006 -> TVC-RESIDENT-SERVICE-SELF-HEAL-001` activation path required by this Goal and must not be substituted for it.

The required activation chain remains:

```text
RT-TVC-PRIMARY-RUNTIME-BINDING-001
-> TVC-PRIMARY-RUNTIME-BINDER-005
-> TVC-PRIMARY-RUNTIME-ACTIVATION-DELIVERY-006
-> tvc.primary_runtime_binder.activate
-> existing singleton scripts/tvc_resident_service_self_heal.py --watch
-> existing TVC private-source watcher
-> consume the four already-staged immutable TT/RTG/GTG/AE requests
```

## Current blocker

`EXISTING_EVENT_EPHEMERAL_TVC_RUNTIME_INVOCATION_SURFACE_NOT_CURRENTLY_OBSERVED`

No new selector, worker, host, scheduler, source-read implementation, GitHub credential path, or second user-operated device was created or authorized.

## Required next evidence

1. authentic service installation receipt with state `SERVICE_INSTALLED_VERIFIED`;
2. authentic resident-state receipt from the same TVC private-source service path;
3. credential presence observed without credential disclosure;
4. four one-to-one materialization receipts for the staged TT/RTG/GTG/AE requests;
5. each receipt proves `authorized_exact_sha == observed_exact_sha == requested exact_sha`;
6. only then run the unchanged SV002 native resource-bundle builder and reuse the previously proven native/export/egress/Master-Records/origin-return chain.

Authority effect: `NONE_OBSERVATION_ONLY`.
