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

1. install/activate a minimal resident StegOS/Node substrate on the current iPhone;
2. preserve or establish device Node/continuity state and the Interlock/InTr-governed storage transition path;
3. keep that small StegOS/Node resident after KV installation as the device-local diagnostic, recovery, and governed repair substrate;
4. let the owner choose the KnowledgeVault storage host independently of KV identity;
5. install or adopt the KV on that selected host;
6. connect and verify the resulting KV through the governed device path;
7. use MyKV as an owner-facing management surface over the verified relationship.

Storage host classes include cloud providers such as iCloud Drive and Google Drive, network/removable storage where supported, and the device itself. The iPhone can therefore host a KV, but device hosting is one selectable storage endpoint rather than the definition of MyKV or StegOS.

## Resident StegOS diagnostic and repair contract

The resident StegOS/Node is intentionally small. It is not a second KV and does not duplicate owner data. Its continuing device responsibility is to retain/recover the minimum local infrastructure needed to identify the device/Node, inspect continuity and runtime health, confirm governed transition surfaces, and prepare bounded repair of the device-side StegOS installation.

Every visit to StegOS.org or MyKV should perform or surface the same resident device health check. At minimum that health view should distinguish:

- resident StegOS/Node present vs missing;
- current Node identity/continuity reusable vs inconsistent;
- required local schema/runtime surfaces current vs stale/incomplete;
- service-worker/offline/bootstrap material current vs absent/stale where applicable;
- Interlock/InTr device-side transition path available vs unavailable;
- selected KV relationship known/verified vs not connected/unknown;
- repair recommended vs no repair required.

A repair action is a **device-install repair**, not a KV reinstall. It must preserve Node identity and retained continuity whenever valid, must not silently create/replace/renumber/rehost a KV, and must not alter the chosen KV storage provider merely to repair StegOS. State-changing repair remains governed and receipted; a page visit or health check alone grants no mutation authority.

## Current truth

The rollback-safe automated legacy-KV upgrade executor remains merged and validated in `StegVerse-Labs/continuity-vault-kit` PR #216 at merge commit `4c426925a354a5f2d71b8becd92896917247e74f`. It remains available when an existing KV needs bounded upgrade/repackaging; it has not read or mutated private iCloud bytes.

The standalone MyKV web surface merged through Site #1348 (`27622f03e7f2683ee6598c67e261f424052242bf`) with post-merge handoff reconciliation through Site #1349 (`7aa532e19c7b06bb60f9e9615adfd8c66947b303`). That source is retained as a useful optional owner-management UI. It must not be interpreted as the KV itself, as a KV storage host, or as the required StegOS installation substrate.

Existing Site source already contains substantial pieces of the intended resident infrastructure: `stegos-bootstrap/index.html` is an installable standalone StegOS web-app entry, `stegos-bootstrap/manifest.webmanifest` defines the standalone application identity, the bootstrap reads/reuses local Node state, and the service-worker/offline shell provides persistent same-device runtime material. Those pieces establish a strong starting point, but source presence alone does not yet prove the complete shared StegOS.org/MyKV diagnostic-and-repair contract described above.

No authentic current-iPhone StegOS infrastructure installation is claimed by this coordination update. No KV is created, replaced, renumbered, migrated, or rebound by source/CI/merge.

## Authority and identity boundaries

- StegOS infrastructure is the device/runtime substrate.
- The minimal resident StegOS/Node persists after KV installation and is responsible for device health/recovery, not owner-data hosting unless the device is separately selected as the KV host.
- KnowledgeVault identity is separate from the selected storage endpoint.
- A device may be selected as a storage endpoint, but installing or repairing the substrate does not itself create a device-hosted KV.
- MyKV is a management surface; it does not mint KV identity, storage authority, Node authority, provider authority, or Interlock/InTr admission.
- Interlock/InTr governs state-changing install/connect/verify/repair transitions.
- Existing KV instances must not be silently replaced when infrastructure is installed, diagnosed, repaired, or updated.
- The pending Google Drive KV #2 request `SITE-CLOUD-KV-4347408852127319cbda574f02e03edb` remains unchanged.
- No second user-operated device is required.

## Remaining completion predicates

The authentic runtime sequence is now:

1. verify the existing installable StegOS infrastructure surface for the current iPhone;
2. verify/complete the shared resident diagnostic contract used whenever StegOS.org or MyKV is visited;
3. verify/complete bounded repair capability for the device-side install without KV replacement or rehosting;
4. install the minimal resident StegOS/Node infrastructure without replacing any existing KV or valid device identity;
5. verify device Node/continuity, resident health, and the governed storage-admission path;
6. present owner-selectable KV host options, including iCloud Drive and device-local hosting where supported;
7. install or adopt the target KV on the selected host without changing its identity merely because its storage endpoint differs;
8. connect/verify the KV through DEVICE_KV / Interlock/InTr and retain receipts;
9. expose MyKV as a management UI over the verified KV while continuing to surface resident-device health on every visit;
10. use the merged rollback-safe legacy updater only when an existing KV specifically requires upgrade/repackaging;
11. reconcile canonical state only from authentic runtime evidence.

The next owner-facing action should therefore be **installation of the minimal resident StegOS/Node infrastructure on this iPhone once that install/diagnostic/repair surface is verified**, not installation of a KV merely to make MyKV usable and not mandatory transport of an iCloud archive.
