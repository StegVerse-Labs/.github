from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from .engine_v11 import HeartbeatRuntime as HeartbeatRuntimeV11, WorkerResponse


LEGACY_SCHEMA = "stegverse.org-heartbeat-state/v1"
CARRIER_STATE_SCHEMA = "stegverse.heartbeat-carrier-runtime-state/v1"
CARRIER_OBSERVATION_SCHEMA = "stegverse.heartbeat-carrier-observation/v1"
CONTROL_PLANE_SCHEMA = "stegverse.worker-control-plane-coordination/v1"
CUTOVER_LEGACY_EPOCH = 29


class HeartbeatRuntime(HeartbeatRuntimeV11):
    """Separated heartbeat producer activated after immutable legacy HB29.

    The historical ``control/heartbeat-state.json`` is never written by this
    runtime. The first persistent v12 cycle derives a zero-authority carrier
    state from exact legacy HB29, advances that carrier to HB30, persists the
    worker/control-plane projection separately, and records a hash-bound cutover
    receipt. Existing task claims/fences remain in ``worker-registry.json`` and
    never become heartbeat-carrier fields.
    """

    def __init__(self, root: str | Path, adapters: dict | None = None):
        super().__init__(root, adapters=adapters)
        self.legacy_hb_path = self.root / "control" / "heartbeat-state.json"
        self.carrier_state_path = self.root / "control" / "heartbeat-carrier-runtime-state.json"
        self.carrier_observation_path = self.root / "control" / "heartbeat-carrier-observation.json"
        self.control_plane_path = self.root / "control" / "worker-control-plane-coordination.json"
        self.cutover_receipt_path = self.root / "receipts" / "heartbeat-schema-cutover" / "HB29.json"
        self.hb_path = self.carrier_state_path if self.carrier_state_path.exists() else self.legacy_hb_path

    @staticmethod
    def _sha256_bytes(value: bytes) -> str:
        return hashlib.sha256(value).hexdigest()

    @staticmethod
    def _canonical_sha256(value: dict[str, Any]) -> str:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _load_legacy_cutover_source(self) -> tuple[dict[str, Any], str]:
        raw = self.legacy_hb_path.read_bytes()
        legacy = json.loads(raw.decode("utf-8"))
        if legacy.get("schema") != LEGACY_SCHEMA:
            raise RuntimeError("HB29 cutover requires canonical legacy heartbeat schema")
        if int(legacy.get("epoch", -1)) != CUTOVER_LEGACY_EPOCH:
            raise RuntimeError(
                f"HB29 cutover requires legacy epoch {CUTOVER_LEGACY_EPOCH}; observed {legacy.get('epoch')}"
            )
        return legacy, self._sha256_bytes(raw)

    def _initial_carrier_state(self) -> dict[str, Any]:
        legacy, digest = self._load_legacy_cutover_source()
        generation = int(legacy.get("generation", CUTOVER_LEGACY_EPOCH) or 0)
        return {
            "schema": CARRIER_STATE_SCHEMA,
            "epoch": CUTOVER_LEGACY_EPOCH,
            "generation": generation,
            "last_cycle_at": legacy.get("last_cycle_at"),
            "role": "REGULATORY_CARRIER_REFERENCE_FRAME",
            "reference_frame": f"heartbeat_epoch:{CUTOVER_LEGACY_EPOCH}",
            "frequency_rule": "GATE_PASSBAND_DERIVED",
            "authority_effect": "NONE",
            "activation_state": "PREPARED",
            "legacy_cutover": {
                "legacy_schema": LEGACY_SCHEMA,
                "legacy_epoch": CUTOVER_LEGACY_EPOCH,
                "legacy_generation": generation,
                "legacy_state_sha256": digest,
                "source_ref": "control/heartbeat-state.json",
                "closed": False,
            },
        }

    def _ensure_persistent_carrier_state(self) -> bool:
        if self.carrier_state_path.exists():
            state = self._load(self.carrier_state_path)
            if state.get("schema") != CARRIER_STATE_SCHEMA:
                raise RuntimeError("unsupported separated heartbeat carrier runtime state")
            self.hb_path = self.carrier_state_path
            return False
        self._atomic_write(self.carrier_state_path, self._initial_carrier_state())
        self.hb_path = self.carrier_state_path
        return True

    def _active_control_leases(self, registry: dict[str, Any]) -> list[dict[str, Any]]:
        leases: list[dict[str, Any]] = []
        for task in registry.get("tasks", []):
            timing = task.get("heartbeat_timing") or {}
            if task.get("state") not in self.WORKER_OWNED | {"BLOCKED"}:
                continue
            if not task.get("worker_id") or not task.get("claim_id"):
                continue
            fence = timing.get("fencing_token")
            if not isinstance(fence, int):
                continue
            leases.append(
                {
                    "task_id": task["task_id"],
                    "goal_id": task.get("goal_id"),
                    "worker_id": task["worker_id"],
                    "worker_instance_id": task.get("worker_instance_id"),
                    "claim_id": task["claim_id"],
                    "fencing_token": fence,
                    "task_state": task.get("state"),
                    "current_transition": timing.get("current_transition"),
                    "expiry_basis": timing.get("expiry_basis"),
                    "lease_end_cycle_exclusive": timing.get("expiry_epoch"),
                    "carrier_reference_unit": "heartbeat_reference",
                    "heartbeat_grants_authority": False,
                }
            )
        return sorted(leases, key=lambda row: (row["task_id"], row["fencing_token"]))

    def _compatibility_subsignals(self) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        path = self.root / "control" / "heartbeat-subsignals.json"
        if not path.exists():
            return [], None
        value = self._load(path)
        subsignals = value.get("subsignals") or {}
        transport = [
            deepcopy(item)
            for _, item in sorted(subsignals.items())
            if isinstance(item, dict) and item.get("kind") == "transport_lease"
        ]
        federation = deepcopy(subsignals.get("organization_federation"))
        return transport, federation

    def _carrier_observation(self, state: dict[str, Any]) -> dict[str, Any]:
        epoch = int(state["epoch"])
        return {
            "schema": CARRIER_OBSERVATION_SCHEMA,
            "generation": int(state["generation"]),
            "carrier": {
                "role": "REGULATORY_CARRIER_REFERENCE_FRAME",
                "reference_frame": f"heartbeat_epoch:{epoch}",
                "frequency_rule": "GATE_PASSBAND_DERIVED",
                "authority_effect": "NONE",
            },
            "observations": [
                {
                    "signal_id": "carrier_continuity",
                    "kind": "CARRIER_CONTINUITY",
                    "present": True,
                    "source_ref": "control/heartbeat-carrier-runtime-state.json",
                    "authority_effect": "NONE",
                },
                {
                    "signal_id": "worker_control_plane_presence",
                    "kind": "SUBSYSTEM_SIGNAL_PRESENCE",
                    "present": True,
                    "source_ref": "control/worker-control-plane-coordination.json",
                    "authority_effect": "NONE",
                },
            ],
            "authority": {
                "heartbeat_grants_execution_authority": False,
                "credential_authority": "TV/TVC",
                "github_token_runtime_authority": False,
                "master_records_action_authority": False,
            },
        }

    def _control_plane_coordination(self, state: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
        leases = self._active_control_leases(registry)
        transport, federation = self._compatibility_subsignals()
        epoch = int(state["epoch"])
        return {
            "schema": CONTROL_PLANE_SCHEMA,
            "generation": int(state["generation"]),
            "observed_reference": {
                "carrier_generation": int(state["generation"]),
                "reference_frame": f"heartbeat_epoch:{epoch}",
                "heartbeat_is_authority": False,
            },
            "worker_coordination": {
                "state": "ACTIVE" if leases else "IDLE",
                "active_leases": leases,
                "worker_registry_ref": "control/worker-registry.json",
            },
            "transport_leases": transport,
            "organization_federation": federation,
            "enforcement_signal_refs": [],
            "authority": {
                "heartbeat_grants_execution_authority": False,
                "signal_grants_execution_authority": False,
                "master_records_action_authority": False,
                "credential_authority": "TV/TVC",
                "github_token_runtime_authority": False,
            },
        }

    def _finalize_cutover(self, state: dict[str, Any], registry: dict[str, Any]) -> None:
        legacy, legacy_digest = self._load_legacy_cutover_source()
        if state.get("legacy_cutover", {}).get("legacy_state_sha256") != legacy_digest:
            raise RuntimeError("legacy HB29 changed after cutover preparation")
        if int(state.get("epoch", -1)) < CUTOVER_LEGACY_EPOCH + 1:
            raise RuntimeError("separated producer did not advance beyond HB29")

        state["activation_state"] = "ACTIVE"
        state["reference_frame"] = f"heartbeat_epoch:{int(state['epoch'])}"
        state["legacy_cutover"]["closed"] = True
        self._atomic_write(self.carrier_state_path, state)
        self._atomic_write(self.carrier_observation_path, self._carrier_observation(state))
        self._atomic_write(self.control_plane_path, self._control_plane_coordination(state, registry))

        if self.cutover_receipt_path.exists():
            existing = self._load(self.cutover_receipt_path)
            if existing.get("legacy_state_sha256") != legacy_digest or existing.get("first_new_epoch") != 30:
                raise RuntimeError("existing HB29 cutover receipt does not bind canonical legacy state")
            return

        receipt_base: dict[str, Any] = {
            "schema": "stegverse.heartbeat-schema-cutover-receipt/v1",
            "state": "CLOSED_MIGRATED",
            "legacy_schema": LEGACY_SCHEMA,
            "legacy_epoch": CUTOVER_LEGACY_EPOCH,
            "legacy_state_ref": "control/heartbeat-state.json",
            "legacy_state_sha256": legacy_digest,
            "legacy_state_epoch_after_cutover": int(legacy["epoch"]),
            "legacy_state_mutated": False,
            "new_carrier_schema": CARRIER_STATE_SCHEMA,
            "carrier_observation_schema": CARRIER_OBSERVATION_SCHEMA,
            "control_plane_schema": CONTROL_PLANE_SCHEMA,
            "first_new_epoch": CUTOVER_LEGACY_EPOCH + 1,
            "observed_new_epoch": int(state["epoch"]),
            "new_carrier_state_ref": "control/heartbeat-carrier-runtime-state.json",
            "new_carrier_state_sha256": self._canonical_sha256(state),
            "carrier_observation_ref": "control/heartbeat-carrier-observation.json",
            "control_plane_ref": "control/worker-control-plane-coordination.json",
            "worker_registry_ref": "control/worker-registry.json",
            "active_control_claims_preserved_separately": len(self._active_control_leases(registry)),
            "heartbeat_grants_execution_authority": False,
            "credential_authority": "TV/TVC",
            "non_tv_tvc_secret_or_token_used": False,
            "github_token_runtime_authority": "NONE",
            "render_production_runtime_used": False,
            "authority_effect": "NONE_BEYOND_PREEXISTING_ADMITTED_CONTROL_PLANE_AUTHORITY",
            "recorded_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        }
        receipt = dict(receipt_base)
        receipt["receipt_sha256"] = self._canonical_sha256(receipt_base)
        self._atomic_write(self.cutover_receipt_path, receipt)

    def cycle(self, write: bool = True) -> dict[str, Any]:
        first_cutover = False
        if write:
            first_cutover = self._ensure_persistent_carrier_state()
        else:
            # A dry-run previews HB30 from immutable legacy HB29 without writing
            # the cutover state or receipt.
            if self.carrier_state_path.exists():
                self.hb_path = self.carrier_state_path
            else:
                self.hb_path = self.legacy_hb_path

        result = super().cycle(write=write)
        result["runtime_schema"] = CARRIER_STATE_SCHEMA
        result["legacy_hb29_cutover"] = "ACTIVATED" if write else "PREVIEW_ONLY"
        result["legacy_hb29_was_first_cutover"] = first_cutover

        if write:
            state = self._load(self.carrier_state_path)
            registry = self._load(self.registry_path)
            self._finalize_cutover(state, registry)
            result["carrier_observation_ref"] = "control/heartbeat-carrier-observation.json"
            result["control_plane_ref"] = "control/worker-control-plane-coordination.json"
            result["cutover_receipt_ref"] = "receipts/heartbeat-schema-cutover/HB29.json"
        return result


__all__ = ["HeartbeatRuntime", "WorkerResponse"]
