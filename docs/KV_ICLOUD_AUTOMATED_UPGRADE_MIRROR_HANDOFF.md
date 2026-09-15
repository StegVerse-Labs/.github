# Automated iCloud KnowledgeVault Upgrade Coordination Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Goal Task ID: `KV-ICLOUD-AUTOMATED-UPGRADE-001`  
COSV profile: `task.v1`  
COSV: `40000100100000`  
Coordination state: `ACTIVE`  
Runtime phase: `STEGOS_CURRENT_IPHONE_INFRASTRUCTURE_INSTALL_PENDING`  
Canonical task record: `data/canonical-task-records/KV-ICLOUD-AUTOMATED-UPGRADE-001.json`  
Canonical task vector: `control/task-vectors/KV-ICLOUD-AUTOMATED-UPGRADE-001.json`  
Resident-health source: `StegVerse-Labs/Site/docs/STEGOS_RESIDENT_HEALTH_REPAIR_MIRROR_HANDOFF.md`  
Upgrade implementation handoff: `StegVerse-Labs/continuity-vault-kit/KV_ICLOUD_AUTOMATED_UPGRADE_MIRROR_HANDOFF.md`  
Optional MyKV management surface: `StegVerse-Labs/Site/docs/MYKV_IOS_INSTALLABLE_SURFACE_MIRROR_HANDOFF.md`

## Canonical architecture

The current iPhone is first equipped with a minimal resident **StegOS/Node infrastructure**, not with a KnowledgeVault instance merely because a management page was installed.

Canonical sequence:

1. install/activate the minimal resident StegOS/Node substrate on the current iPhone;
2. preserve or establish device Node/continuity state and the Interlock/InTr-governed storage transition path;
3. keep that small StegOS/Node resident after KV installation as the device-local diagnostic, recovery, and governed repair substrate;
4. let the owner choose the KnowledgeVault storage host independently of KV identity;
5. install or adopt the KV on that selected host;
6. connect and verify the resulting KV through the governed device path;
7. use MyKV as an owner-facing management surface over the verified relationship.

Storage host classes include iCloud Drive, Google Drive, other admitted providers/endpoints, and the device itself. Device hosting is one selectable KV host, not the definition of StegOS or MyKV.

## Resident StegOS diagnostic and repair source status

The shared resident-health source is now merged and validated in Site:

- implementation PR `StegVerse-Labs/Site#1351` merged as `3c78c5da968ae746ddaedfe6c68c3a148fc56f0c`;
- README and focused handoff reconciliation PR `Site#1352` merged as `2665945feb599b3067804bdb57abb831f94af09f`;
- claim-only terminalization PR `Site#1353` merged as `de85b7a9746c73fe40a9d736c06b061333fffcfd`.

`assets/stegos-resident-health.js` is loaded by both the StegOS bootstrap loader and the shared Node-continuity loader used by MyKV. It automatically performs a read-only visit-time diagnostic and reports resident install health, Node state, device-continuity visibility, schema compatibility, service-worker freshness, governed transition-surface availability, and only already-visible KV relationship state.

The diagnostic does not issue DEVICE_KV materialization/query operations or provider operations merely to enrich health state. Repair is owner-invoked and bounded to the device-side StegOS installation. A valid existing Node must be preserved; changing that identity fails closed. The repair source has no KV create, replace, renumber, migrate, or rehost path. If MyKV cannot perform the StegOS-side repair directly, it hands the owner to the same-origin StegOS bootstrap route rather than minting replacement state.

Source validation and merge establish this source contract only. They do not prove public propagation, physical current-iPhone installation, service-worker persistence, current Node health, repair execution, or KV host selection.

## Existing adjacent truth

The rollback-safe automated legacy-KV upgrade executor remains merged and validated in `StegVerse-Labs/continuity-vault-kit` PR #216 at merge commit `4c426925a354a5f2d71b8becd92896917247e74f`. It remains available when an existing KV specifically needs bounded upgrade/repackaging.

The standalone MyKV web surface remains an optional owner-management UI. It is not the KV, the KV storage host, or the required StegOS substrate.

The pending Google Drive KV #2 request `SITE-CLOUD-KV-4347408852127319cbda574f02e03edb` remains unchanged.

## Authority and identity boundaries

- StegOS infrastructure is the device/runtime substrate.
- The minimal resident StegOS/Node persists after KV installation and is responsible for device health/recovery, not owner-data hosting unless the device is separately selected as the KV host.
- KnowledgeVault identity is separate from the selected storage endpoint.
- Installing or repairing StegOS does not itself create a device-hosted KV.
- MyKV does not mint KV identity, storage authority, Node authority, provider authority, or Interlock/InTr admission.
- Interlock/InTr governs state-changing install/connect/verify/repair transitions.
- Existing KV instances must not be silently replaced when infrastructure is installed, diagnosed, repaired, or updated.
- No second user-operated device is required.

## Remaining completion predicates

Only runtime/deployment predicates remain for this phase:

1. independently verify public propagation of the merged StegOS bootstrap loader, resident-health client, and manifest at `stegverse.org`;
2. install the minimal resident StegOS/Node surface on the current iPhone;
3. observe resident health and verify valid Node/continuity is reused or, only when genuinely absent, establish the device Node once;
4. verify the governed storage-admission path;
5. present owner-selectable KV host options, including iCloud Drive and device-local hosting where supported;
6. install or adopt the target KV on the selected host without changing identity merely because storage differs;
7. connect/verify the KV through DEVICE_KV / Interlock/InTr and retain receipts;
8. confirm subsequent StegOS and MyKV visits continue to report resident-device health without silently changing Node or KV identity;
9. use bounded resident repair only if health requires it;
10. reconcile canonical state only from authentic runtime evidence.

The next owner-facing action is the one iPhone Home Screen installation sequence only after public propagation of the merged source is independently verified.
