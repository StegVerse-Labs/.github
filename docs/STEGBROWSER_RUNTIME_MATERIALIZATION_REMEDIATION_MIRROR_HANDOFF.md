# StegBrowser Runtime Materialization Remediation Mirror Handoff

Updated: 2026-09-14

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- Parent/remediates: `STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001`
- Shared runtime-evidence owner: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
- Issue: `StegVerse-Labs/.github#1866`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / NATIVE RESIDENT EVIDENCE PATH RECONCILED / AUTHENTIC RESIDENT HEALER RECEIPT PENDING`
- External/second user-operated device required: `false`

## Current truth

The source-side packet/retention repairs remain merged and validated, but source state does not prove runtime execution.

- `StegVerse-Healer#81` added the task-bound non-authorizing `resident_custody_root_observation` packet surface.
- `StegVerse-Healer#82` repaired resident-root bootstrap circularity through the existing local source-refresh path.
- `StegVerse-Healer#83` retained the canonical packet at `receipts/sovereign-host/stegbrowser-resident-custody-root-observation.latest.json` under the observed resident root or existing materialization target.
- `.github#1841` repaired autonomous evidence continuation from the admitted ephemeral StegOS execution back into the existing resident runtime.
- `.github#1852` merged the non-authorizing exact resident receipt verifier from exact head `a6d0d6e33520a81b261018f36bb78ff5568d7fed` after Organization Control `34873353094`, Deterministic Repository Suite `34873352920`, and Heartbeat `34873352943` succeeded.
- `.github#1884` merged the latest source-side classification without creating a second export mechanism.

`scripts/consume_healer_sovereign_scheduler_request.py` writes:

```text
receipts/sovereign-host/healer-sovereign-scheduler-request-consumption.latest.json
```

and embeds:

```text
execution_result.resident_custody_root_observation_retention
```

including packet path, SHA-256, retained root, retained-root source, and packet state.

## Correct execution/evidence model

This task does **not** use or require an external desktop/device connector. External connector inventory is outside the production architecture for this Goal.

The correct StegVerse-native chain is:

```text
existing resident cycle
-> standing Healer resident carrier
-> neutral reusable scheduler
-> RT-STEGBROWSER-RUNTIME-CONSUMPTION-001
-> admitted ephemeral StegOS / Canonical Work
-> authentic execution receipts retained into the existing resident runtime
-> StegVerse-native resident custody surface
-> merged non-authorizing receipt verifier
-> bind retained-root pointer and exact receipt hashes
-> Master Records reconstruction where required
```

PR #1812 already established that zero remote-device discovery is not a blocker and selected `ADMITTED-EPHEMERAL-STEGOS-NODE` for the runtime-consumption path. PR #1841 then repaired the autonomous ephemeral-to-resident evidence retention seam. Therefore asking whether an external connector has a connected device is neither necessary nor relevant to this task.

## Canonical device / node invariant

KV/SKAP Vault is the sole user-verification authority. Eligible StegOS devices are interchangeable execution/transport nodes. Physical-device identity, named-handset completion gates, device attestation as user verification, and connector inventory as task state are prohibited.

Historical device-specific observations remain provenance only.

## Reconciled adjacent receipt-transport state

`STEG-BROWSER-RESIDENT-RECEIPT-TRANSPORT-001` was stale: it still described `.github#1852` as an open verifier requiring rebase. That was false. The canonical record and handoff now record #1852 as merged/validated and identify the first unresolved predicate as:

```text
AUTHENTIC_STEGVERSE_NATIVE_RESIDENT_RECEIPT_SURFACE_OBSERVED
```

The verifier is ready. The missing input is authentic resident output, not a missing inspection tool.

## Current exact defect

```text
AUTHENTIC_STEGVERSE_NATIVE_RESIDENT_HEALER_CARRIER_RECEIPT_NOT_YET_OBSERVED
```

This is narrower and more accurate than the earlier `NOT_GITHUB_VISIBLE` wording. GitHub visibility is not the runtime predicate. The runtime predicate is whether the existing resident cycle has authentically produced and retained the required receipt under StegVerse-native custody.

## Existing authorized output access path

```text
<resident-root>/receipts/sovereign-host/healer-sovereign-scheduler-request-consumption.latest.json
  -> execution_result
  -> resident_custody_root_observation_retention
  -> packet_ref / packet_relative_path / packet_sha256 / retained_under_root / retained_under_root_source / packet_state
```

Canonical retained packet:

```text
<resident-root>/receipts/sovereign-host/stegbrowser-resident-custody-root-observation.latest.json
```

## Exact next required execution

Do not perform device discovery and do not invoke an external connector.

Advance only through the existing StegVerse-native path:

1. allow/observe the existing resident cycle consuming the standing Healer scheduler request;
2. observe `healer-sovereign-scheduler-request-consumption.latest.json` in the retained resident custody surface;
3. read `execution_result.resident_custody_root_observation_retention` and bind the exact packet path/hash/root/root-source/state;
4. if packet state proves one authentic governed resident root, run the already-merged `scripts/check_stegbrowser_runtime_consumption_receipts.py --runtime-root <authentic-root>` exactly once as a non-authorizing classifier;
5. bind any `VALID_BINDABLE` receipt hashes/outcomes into canonical task evidence;
6. only after authentic retained runtime evidence exists, enter the global measurement child and freeze/execute its single measurement-only convergence pass.

If the authentic resident receipt is missing or invalid, remediate only the exact StegVerse-native producer/retention/custody defect revealed by that observation. Do not create a second scheduler, dispatcher, transport, runtime, credential route, evidence owner, or device-dependent path.

## Authority invariants

- Task Registry: coordination only.
- KV/SKAP Vault: sole user-verification authority.
- StegOS devices: interchangeable transport/execution nodes.
- Healer carrier / neutral reusable scheduler: scheduling and invocation transport only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed transition authority.
- TV/TVC: credential/provider authority where applicable.
- Master Records: observed-reality/reconstruction authority.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.
- External connectors: `NONE_NOT_APPLICABLE` for this Goal.

## Current state

`ACTIVE / CHECKED_OUT / NATIVE_RECEIPT_VERIFIER_MERGED / EXTERNAL_CONNECTOR_NOT_APPLICABLE / PHYSICAL_DEVICE_INVENTORY_NOT_APPLICABLE / AUTHENTIC_RESIDENT_HEALER_RECEIPT_NOT_YET_OBSERVED / RESIDENT_ROOT_NOT_AUTHENTICALLY_OBSERVED / RECEIPT_REACHABILITY_NOT_CLASSIFIED / RUNTIME_CONSUMPTION_NOT_CLAIMED`

## Manual work

None.
