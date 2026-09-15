# Automated iCloud KnowledgeVault Upgrade Coordination Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Goal Task ID: `KV-ICLOUD-AUTOMATED-UPGRADE-001`  
COSV profile: `task.v1`  
COSV: `40000100100000`  
Coordination state: `ACTIVE`  
Runtime phase: `MYKV_CURRENT_IPHONE_UNIFIED_INSTALL_PENDING`  
Canonical task record: `data/canonical-task-records/KV-ICLOUD-AUTOMATED-UPGRADE-001.json`  
Canonical task vector: `control/task-vectors/KV-ICLOUD-AUTOMATED-UPGRADE-001.json`  
MyKV unified install source: `StegVerse-Labs/Site/docs/MYKV_IOS_INSTALLABLE_SURFACE_MIRROR_HANDOFF.md`  
Resident-health source: `StegVerse-Labs/Site/docs/STEGOS_RESIDENT_HEALTH_REPAIR_MIRROR_HANDOFF.md`  
Upgrade implementation handoff: `StegVerse-Labs/continuity-vault-kit/KV_ICLOUD_AUTOMATED_UPGRADE_MIRROR_HANDOFF.md`

## Canonical architecture

**MyKV is the sole owner-facing installation and management surface.** The owner does not separately visit or install a StegOS site.

Canonical sequence:

1. install MyKV once on the current iPhone;
2. on first standalone launch, MyKV automatically loads the existing StegOS bootstrap implementation, device-local continuity/autostart layer, canonical Node-continuity implementation, and resident-health client on the same StegVerse-controlled origin;
3. MyKV establishes or reuses the valid resident StegOS/Node substrate and runs the canonical resident-health diagnostic;
4. if device-side repair is required, MyKV performs only bounded resident-substrate repair and fails closed if valid Node identity or already-visible KV relationship state changes;
5. only after resident health is acceptable does MyKV expose owner-selectable KnowledgeVault storage hosts;
6. the owner selects iCloud Drive, Google Drive, device-local storage, or another admitted endpoint independently of KV identity;
7. the KV is installed/adopted and then connected/verified through the governed DEVICE_KV / Interlock/InTr path;
8. MyKV remains the owner-facing management surface while the small resident StegOS/Node remains underneath it as device/runtime substrate.

StegOS is therefore still required infrastructure, but it is an implementation component of the MyKV install/launch flow rather than a second owner-facing installation destination.

## Unified MyKV install source status

The unified install contract is merged and validated in Site:

- implementation PR `StegVerse-Labs/Site#1355` merged as `0d5df579e98ae44ad2f4358dd89efaae5d9809ed`;
- final README-inclusive implementation head `2aae799336464b290b230074992b2bf3899523d2` passed all 13 observed exact-head workflows;
- post-merge handoff reconciliation PR `Site#1356` merged as `78c6a6f77fbfa1b89a2d9ec8d5e9aa28ed9ef5d3`;
- claim-only terminalization PR `Site#1357` merged as `1942f3c7cd03b1007d7a0df1e5f4635cc4616f64`.

`my-kv-install.html` is the single install shell. In normal browser mode it remains non-installing. In standalone/Home Screen mode it invokes the shared resident-health client, runs bounded repair when required, and enters canonical MyKV only after `HEALTHY` resident readback with a valid registered Node.

`assets/stegverse-node-continuity.js` loads the existing StegOS schema/bootstrap/device-continuity layers before Node continuity and resident health, so normal MyKV installation does not require a separate StegOS bootstrap visit.

`cloud-kv-peers.html` keeps owner-selectable storage-host panels hidden until the same resident-health contract reports a healthy resident substrate and registered Node.

## Resident StegOS diagnostic and repair boundary

The resident StegOS/Node remains intentionally small. It is not a second KV and does not duplicate owner data. It provides the minimum same-device substrate needed for Node/continuity, diagnostic health, service-worker/runtime recovery, and governed transition availability.

Health checks are observational and non-authorizing. Bounded repair may refresh/register the same-origin StegOS service-worker shell and establish a device Node only when no valid Node exists. Existing valid Node identity and already-visible KV relationship state must survive repair or the flow fails closed.

Resident repair has no authority to create, replace, renumber, migrate, rehost, connect, synchronize, or expose a KnowledgeVault merely to repair device infrastructure.

## Existing adjacent truth

The rollback-safe automated legacy-KV upgrade executor remains merged and validated in `StegVerse-Labs/continuity-vault-kit` PR #216 at merge commit `4c426925a354a5f2d71b8becd92896917247e74f`. It remains available only when an existing KV specifically needs bounded upgrade/repackaging.

The pending Google Drive KV #2 request `SITE-CLOUD-KV-4347408852127319cbda574f02e03edb` remains unchanged. The unified MyKV install must not re-emit, regenerate, rename, reauthorize, or replace it.

## Authority and identity boundaries

- MyKV is the sole owner-facing install and management surface.
- MyKV is not the KnowledgeVault and is not its storage host.
- StegOS remains the resident device/runtime substrate under MyKV.
- No separate owner-facing StegOS installation is required.
- KnowledgeVault identity remains separate from the selected storage endpoint.
- Installing or repairing the MyKV resident substrate does not itself create a device-hosted or cloud-hosted KV.
- Interlock/InTr remains the authority boundary for state-changing KV install/connect/verify transitions and governed repair transitions where applicable.
- Existing valid Node and KV identities must not be silently replaced.
- No second user-operated device is required.

## Remaining completion predicates

Only deployment/runtime predicates remain for this phase:

1. independently verify public propagation of the merged MyKV install surface and its unified resident-substrate loader on the actual StegVerse-controlled origin;
2. install MyKV once on the current iPhone;
3. launch MyKV and observe the first consolidated resident-health / Node-continuity result;
4. verify a valid existing Node is reused or, only when genuinely absent, established once;
5. run bounded resident repair only if the health result requires it;
6. expose storage-host choices only after resident substrate health is acceptable;
7. select the KV storage host independently of KV identity;
8. install/adopt and connect/verify the KV through DEVICE_KV / Interlock/InTr with authentic receipts;
9. reconcile canonical state only from authentic runtime evidence.

The next owner-facing action, once public MyKV propagation is independently verified, is **one MyKV installation**. There is no separate owner-facing StegOS installation or multi-site bootstrap test.
