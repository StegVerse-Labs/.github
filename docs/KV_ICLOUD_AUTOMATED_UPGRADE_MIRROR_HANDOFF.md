# Automated iCloud KnowledgeVault Upgrade Coordination Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Goal Task ID: `KV-ICLOUD-AUTOMATED-UPGRADE-001`  
COSV profile: `task.v1`  
COSV: `40000100100000`  
Coordination state: `ACTIVE`  
Runtime phase: `STEGOS_CURRENT_IPHONE_INFRASTRUCTURE_INSTALL_PENDING`  
Canonical task record: `data/canonical-task-records/KV-ICLOUD-AUTOMATED-UPGRADE-001.json`  
Canonical task vector: `control/task-vectors/KV-ICLOUD-AUTOMATED-UPGRADE-001.json`  
Upgrade implementation handoff: `StegVerse-Labs/continuity-vault-kit/KV_ICLOUD_AUTOMATED_UPGRADE_MIRROR_HANDOFF.md`  
Optional MyKV management surface: `StegVerse-Labs/Site/docs/MYKV_IOS_INSTALLABLE_SURFACE_MIRROR_HANDOFF.md`

## Canonical architecture

The current iPhone is first equipped with **StegOS infrastructure**, not with a KnowledgeVault instance merely because a management page was installed.

Canonical sequence:

1. install/activate the StegOS device substrate on the current iPhone;
2. preserve or establish the device Node/continuity surface and the Interlock/InTr-governed storage transition path;
3. let the owner choose the KnowledgeVault storage host independently of KV identity;
4. install or adopt the KV on that selected host;
5. connect and verify the resulting KV through the governed device path;
6. use MyKV as an owner-facing management surface after the substrate and KV binding exist.

Storage host classes include cloud providers such as iCloud Drive and Google Drive, network/removable storage where supported, and the device itself. The iPhone can therefore host a KV, but device hosting is one selectable storage endpoint rather than the definition of MyKV or StegOS.

## Current truth

The rollback-safe automated legacy-KV upgrade executor remains merged and validated in `StegVerse-Labs/continuity-vault-kit` PR #216 at merge commit `4c426925a354a5f2d71b8becd92896917247e74f`. It remains available when an existing KV needs bounded upgrade/repackaging; it has not read or mutated private iCloud bytes.

The standalone MyKV web surface merged through Site #1348 (`27622f03e7f2683ee6598c67e261f424052242bf`) with post-merge handoff reconciliation through Site #1349 (`7aa532e19c7b06bb60f9e9615adfd8c66947b303`). That source is retained as a useful optional owner-management UI. It must not be interpreted as the KV itself, as a KV storage host, or as the required StegOS installation substrate.

No authentic current-iPhone StegOS infrastructure installation is claimed by this coordination update. No KV is created, replaced, renumbered, migrated, or rebound by source/CI/merge.

## Authority and identity boundaries

- StegOS infrastructure is the device/runtime substrate.
- KnowledgeVault identity is separate from the selected storage endpoint.
- A device may be selected as a storage endpoint, but installing the substrate does not itself create a device-hosted KV.
- MyKV is a management surface; it does not mint KV identity, storage authority, Node authority, provider authority, or Interlock/InTr admission.
- Interlock/InTr governs state-changing install/connect/verify transitions.
- Existing KV instances must not be silently replaced when infrastructure is installed or updated.
- The pending Google Drive KV #2 request `SITE-CLOUD-KV-4347408852127319cbda574f02e03edb` remains unchanged.
- No second user-operated device is required.

## Remaining completion predicates

The authentic runtime sequence is now:

1. identify or complete the installable StegOS infrastructure surface for the current iPhone;
2. install that StegOS infrastructure without replacing any existing KV or device identity;
3. verify device Node/continuity and the governed storage-admission path;
4. present owner-selectable KV host options, including iCloud Drive and device-local hosting where supported;
5. install or adopt the target KV on the selected host without changing its identity merely because its storage endpoint differs;
6. connect/verify the KV through DEVICE_KV / Interlock/InTr and retain receipts;
7. expose MyKV as a management UI over the verified KV;
8. use the merged rollback-safe legacy updater only when an existing KV specifically requires upgrade/repackaging;
9. reconcile canonical state only from authentic runtime evidence.

The next owner-facing action should therefore be **installation of StegOS infrastructure on this iPhone once that install surface is verified**, not installation of a KV merely to make MyKV usable and not mandatory transport of an iCloud archive.
