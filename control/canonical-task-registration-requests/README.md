# Canonical task registration requests

One `stegverse.canonical-task-registration-request/v1` manifest per proposed Goal Task
(`<request_id>.json`). The manifest is the only input: the record, the Registry row
(row == record), the generation bump and the COSV vector and index entry are derived
from it by `scripts/canonical_task_registration_transition.py` and verified by
`.github/workflows/canonical-task-registration-transition.yml`.
Contract: `contracts/canonical-task-registration-transition.v1.json`.
A manifest proposes; it is not admission and grants no claim, fence or execution authority.
