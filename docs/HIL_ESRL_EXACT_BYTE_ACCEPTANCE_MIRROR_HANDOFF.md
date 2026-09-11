# HIL ESRL Exact-Byte Acceptance Mirror Handoff

Updated: 2026-09-11  
Repository: `StegVerse-Labs/.github`  
Parent goal: `SHWP-HIL-SOVEREIGN-RECEIVER-001`  
Canonical parent handoff: `docs/HIL_RESIDENT_SESSION_MANIFOLD_ACTIVATION_MIRROR_HANDOFF.md`

## Current state

The exact user-exported standalone-Safari ESRL `LEASE_OPEN` artifact has been received and preserved byte-for-byte. Its SHA256 is `a6756c54da15f09cd6a3dbb201375891803f6589fd644db4c545be39ebe41b92`; the uploaded source and repository-preserved file share Git blob SHA-1 `64477f85c954d8428bece619c311cd97afb7734a`, confirming exact-byte identity.

Canonical ESRL intake is accepted and the only lawful bookkeeping transition is now prepared and applied in this change:

```text
50000000103000 -> 50000000102000
remove AUTHENTIC_ESRL_HIL_LEASE_OPEN_NOT_YET_OBSERVED
retain POST_RESTART_EXACT_BYTE_PROOF_NOT_YET_PRESERVED
retain TVC_HIL_LIFECYCLE_HANDOFF_NOT_YET_PROVEN
```

Parent worker state remains `HANDOFF_READY`; `archive_eligible=false`, `activated=false`, and `propagated=false` remain unchanged.

## Evidence

- `evidence/physical/hil-esrl-lease-open-a6756c54da15f09cd6a3dbb201375891803f6589fd644db4c545be39ebe41b92.json`
- `receipts/sovereign-host/hil-browser-esrl-evidence-intake.latest.json`
- `receipts/sovereign-host/hil-esrl-acceptance-reconciliation-proposal.latest.json`
- `receipts/sovereign-host/hil-esrl-exact-byte-staging-manifest.latest.json`
- `docs/HIL_ESRL_EXACT_BYTE_ACCEPTANCE_RESULT_20260911.md`

## Next stage

Continue at `HIL_RECEIVER_READY_AND_CUSTODY`, then preserve post-restart exact-byte reconstruction proof, then prove TVC HIL lifecycle handoff. Do not rerun G25 or mint a replacement claim/fence.

## README maintenance

README was re-reviewed. This is a task-specific evidence/state reconciliation and does not change the documented repository or public runtime interface. No README update is required.
