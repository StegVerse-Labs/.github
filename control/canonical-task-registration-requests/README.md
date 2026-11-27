# Canonical task registration requests

One `stegverse.canonical-task-registration-request/v1` manifest per proposed Goal Task
(`<request_id>.json`). The manifest is the only input: the record, the Registry row
(row == record), the generation bump and the COSV vector and index entry are derived
from it by `scripts/canonical_task_registration_transition.py` and verified by
`.github/workflows/canonical-task-registration-transition.yml`.
Contract: `contracts/canonical-task-registration-transition.v1.json`.
A manifest proposes; it is not admission and grants no claim, fence or execution authority.


## Input-only preflight

Run `python scripts/registration_input_preflight.py control/canonical-task-registration-requests/<request>.json` before submitting a request. This reads and validates inputs only; it never registers a Goal or derives/applies canonical state. `input_status=VALID` is not ALLOW or proof of registration. Construct new seals with `scripts/goal_scope_seal.py::make_sealed_scope`, supplying the actual record and an explicit testable finish point. Never recompute an existing digest merely to hide scope/record divergence. Full registration still uses the existing authorized fresh-base transition and independent canonical readback. See `docs/REGISTRATION_INPUT_PREFLIGHT_MIRROR_HANDOFF.md`.
