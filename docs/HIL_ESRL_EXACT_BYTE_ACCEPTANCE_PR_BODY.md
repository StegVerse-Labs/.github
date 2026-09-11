Goal: `SHWP-HIL-SOVEREIGN-RECEIVER-001`

This change consumes the exact downloaded physical ESRL `LEASE_OPEN` artifact from the retained G25 standalone-Safari context.

Exact-byte identity:
- source size: 2011 bytes
- source SHA256: a6756c54da15f09cd6a3dbb201375891803f6589fd644db4c545be39ebe41b92
- uploaded-source Git blob SHA-1: 64477f85c954d8428bece619c311cd97afb7734a
- preserved repository blob SHA-1: 64477f85c954d8428bece619c311cd97afb7734a

The artifact passes the merged canonical ESRL intake contract against the accepted G25 request-consumption receipt. This PR preserves the exact artifact, installs the ACCEPTED intake receipt, records the reconciliation proposal, reconciles task vector/worker registry from `50000000103000` to `50000000102000`, and removes only `AUTHENTIC_ESRL_HIL_LEASE_OPEN_NOT_YET_OBSERVED`.

Two blockers remain:
1. `POST_RESTART_EXACT_BYTE_PROOF_NOT_YET_PRESERVED`
2. `TVC_HIL_LIFECYCLE_HANDOFF_NOT_YET_PROVEN`

Next runtime stage is `HIL_RECEIVER_READY_AND_CUSTODY`.

No second claim/fence, no second machine, no runtime launch from GitHub, and no post-restart/TVC/broader lifecycle overclaim. README was re-reviewed; no change required.
