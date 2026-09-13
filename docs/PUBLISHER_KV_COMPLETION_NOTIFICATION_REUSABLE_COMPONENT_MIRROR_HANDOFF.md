# Publisher -> KV -> GitHub Completion Notification reusable component

Component: `RTC-PUBLISHER-KV-COMPLETION-NOTIFY-012`
Reusable Task: `RT-PUBLISHER-KV-COMPLETION-NOTIFY-001`
Family: `release_propagation`

## Purpose

Provide one reusable terminal component for Goal Tasks whose finished Publisher documentation must be placed into KV and whose validated completion must then generate a GitHub notification event capable of producing the user's normal GitHub notification email.

The component is ordered and fail-closed:

`Publisher finished artifacts -> Interlock/InTr-admitted KV write -> KV readback/file manifest/link -> GitHub completion notification request`

The GitHub notification may not be requested before a successful retained KV publication receipt exists.

## Notification body

The completion notification body contains:

### Task Block
- Goal Task ID
- Handoff Task ID
- COSV ID
- STATUS

### Files added to KV
Exact file/object names from the retained KV publication manifest.

### KV Link
The stable KV reference/link returned from the successful KV publication step.

GitHub email delivery is downstream of the GitHub notification event and remains subject to the user's GitHub notification settings. The reusable component does not send mail directly and does not make GitHub Actions a runtime authority.

## Authority separation

- Publisher: finished documentation rendering only.
- Interlock/InTr: KV state-transition admission.
- KV/SKAP Vault: sole user-verification authority.
- TV/TVC: GitHub provider credential/mutation authority.
- Master Records: observed-reality custody/reconstruction.
- Task Registry: coordination only.
- GitHub Actions: validation/evidence transport only.

No second user-operated device and no device-local user verification are introduced.

## Evidence predicates

Completion of an invocation requires all of:

- `PUBLISHER_FINAL_ARTIFACT_SET_HASH_BOUND`
- `KV_WRITE_INTR_ADMISSION_RECEIPT`
- `KV_FILE_WRITE_READBACK_VERIFIED`
- `KV_PUBLICATION_RECEIPT_RETAINED`
- `KV_FILE_MANIFEST_RETAINED`
- `KV_LINK_RETAINED`
- `GITHUB_COMPLETION_NOTIFICATION_PROVIDER_RECEIPT`

Source construction or CI does not satisfy any authentic runtime/provider predicate.
