from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json

from .engine_v11 import HeartbeatRuntime as LegacyRuntimeBase, WorkerResponse
from .assignment_timer import assignment_trigger_packet

LEGACY_SCHEMA = "stegverse.org-heartbeat-state/v1"
CARRIER_STATE_SCHEMA = "stegverse.heartbeat-carrier-runtime-state/v1"
CARRIER_OBSERVATION_SCHEMA = "stegverse.heartbeat-carrier-observation/v1"
CONTROL_PLANE_SCHEMA = "stegverse.worker-control-plane-coordination/v1"
CUTOVER_LEGACY_EPOCH = 29


class HeartbeatRuntime(LegacyRuntimeBase):
    """Non-authorizing carrier with immutable HB29 -> separated-schema cutover.

    The class reuses only durable IO/locking/event helpers inherited from the
    compatibility runtime. It never calls the legacy worker-lifecycle cycle.
    Historical ``control/heartbeat-state.json`` remains immutable at HB29. The
    first persistent v12 cycle derives a new carrier state from that exact
    snapshot and emits HB30 in ``heartbeat-carrier-runtime-state.json``.

    Unassigned-task packets are carried as non-authorizing runtime events. They
    may be consumed by the separate worker coordinator, which must independently
    validate task authority, worker eligibility and the assignment timer. Claim,
    fence, lease and worker lifecycle state never become carrier authority.
    """

    def __init__(self, root: str | Path, adapters: dict | None = None):
        super().__init__(root, adapters=adapters)
        self.legacy_hb_path = self.root / "control" / "heartbeat-state.json"
        self.carrier_state_path = self.root / "control" / "heartbeat-carrier-runtime-state.json"
        self.carrier_observation_path = self.root / "control" / "heartbeat-carrier-observation.json"
        self.control_plane_path = self.root / "control" / "worker-control-plane-coordination.json"
        self.master_records_projection_path = self.root / "control" / "heartbeat-master-records-projection.json"
        self.cutover_receipt_path = self.root / "receipts" / "heartbeat-schema-cutover" / "HB29.json"
        self.hb_path = self.carrier_state_path if self.carrier_state_path.exists() else self.legacy_hb_path

    @staticmethod
    def _sha256_bytes(value: bytes) -> str:
        return hashlib.sha256(value).hexdigest()

    @staticmethod
    def _canonical_sha256(value: dict[str, Any]) -> str:
        payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _legacy_source(self) -> tuple[dict[str, Any], bytes, str]:
        raw = self.legacy_hb_path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
        if value.get("schema") != LEGACY_SCHEMA:
            raise RuntimeError("HB29 cutover requires canonical legacy heartbeat schema")
        if int(value.get("epoch", -1)) != CUTOVER_LEGACY_EPOCH:
            raise RuntimeError(
                f"HB29 cutover requires legacy epoch {CUTOVER_LEGACY_EPOCH}; observed {value.get('epoch')}"
            )
        return value, raw, self._sha256_bytes(raw)

    def _initial_carrier_state(self) -> dict[str, Any]:
        legacy, _raw, digest = self._legacy_source()
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

    def _load_carrier_state(self) -> tuple[dict[str, Any], bool]:
        if not self.carrier_state_path.exists():
            return self._initial_carrier_state(), True
        state = self._load(self.carrier_state_path)
        if state.get("schema") != CARRIER_STATE_SCHEMA:
            raise RuntimeError("unsupported separated heartbeat carrier runtime state")
        legacy, _raw, digest = self._legacy_source()
        cutover = state.get("legacy_cutover") or {}
        if cutover.get("legacy_state_sha256") != digest:
            raise RuntimeError("legacy HB29 changed after carrier cutover")
        if int(cutover.get("legacy_epoch", -1)) != CUTOVER_LEGACY_EPOCH:
            raise RuntimeError("separated carrier is not bound to canonical HB29")
        if int(legacy["epoch"]) != CUTOVER_LEGACY_EPOCH:
            raise RuntimeError("legacy heartbeat source advanced after cutover")
        return state, False

    def _active_control_leases(self, registry: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        worker_owned = set(self.WORKER_OWNED) | {"BLOCKED"}
        for task in registry.get("tasks", []):
            if task.get("state") not in worker_owned:
                continue
            timing = task.get("heartbeat_timing") or {}
            timer = task.get("assignment_timer") or {}
            fence = timer.get("fencing_token", timing.get("fencing_token"))
            if not task.get("worker_id") or not task.get("claim_id") or not isinstance(fence, int):
                continue
            rows.append({
                "task_id": task.get("task_id"),
                "goal_id": task.get("goal_id"),
                "worker_id": task.get("worker_id"),
                "worker_instance_id": task.get("worker_instance_id"),
                "claim_id": task.get("claim_id"),
                "fencing_token": fence,
                "task_state": task.get("state"),
                "current_transition": timing.get("current_transition"),
                "assignment_timer_remaining_hb_units": timer.get("remaining_hb_units"),
                "expiry_basis": timer.get("expiry_basis", timing.get("expiry_basis")),
                "carrier_reference_unit": "heartbeat_reference",
                "heartbeat_grants_authority": False,
            })
        return sorted(rows, key=lambda row: (str(row["task_id"]), int(row["fencing_token"])))

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

    def _assignment_triggers(self, registry: dict[str, Any], epoch: int) -> list[dict[str, Any]]:
        triggers: list[dict[str, Any]] = []
        for task in sorted(registry.get("tasks", []), key=lambda item: str(item.get("task_id", ""))):
            if task.get("state") != "HANDOFF_READY":
                continue
            if task.get("worker_id") or task.get("claim_id"):
                continue
            triggers.append(assignment_trigger_packet(carrier_epoch=epoch, task=task))
        return triggers

    def _carrier_observation(self, state: dict[str, Any], control_hash: str, trigger_count: int) -> dict[str, Any]:
        epoch = int(state["epoch"])
        observations = [
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
                "source_ref": f"control/worker-control-plane-coordination.json#sha256={control_hash}",
                "authority_effect": "NONE",
            },
        ]
        if trigger_count:
            observations.append({
                "signal_id": "unassigned_worker_task_packet_presence",
                "kind": "SUBSYSTEM_SIGNAL_PRESENCE",
                "present": True,
                "source_ref": f"events/heartbeat-runtime.jsonl#heartbeat_epoch:{epoch}",
                "authority_effect": "NONE",
            })
        return {
            "schema": CARRIER_OBSERVATION_SCHEMA,
            "generation": int(state["generation"]),
            "carrier": {
                "role": "REGULATORY_CARRIER_REFERENCE_FRAME",
                "reference_frame": f"heartbeat_epoch:{epoch}",
                "frequency_rule": "GATE_PASSBAND_DERIVED",
                "authority_effect": "NONE",
            },
            "observations": observations,
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
            "generation": int(registry.get("generation", 0)),
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

    def _cutover_receipt(self, state: dict[str, Any], legacy_digest: str, control_hash: str) -> dict[str, Any]:
        base = {
            "schema": "stegverse.heartbeat-schema-cutover-receipt/v1",
            "state": "CLOSED_MIGRATED",
            "legacy_schema": LEGACY_SCHEMA,
            "legacy_epoch": CUTOVER_LEGACY_EPOCH,
            "legacy_state_ref": "control/heartbeat-state.json",
            "legacy_state_sha256": legacy_digest,
            "legacy_state_mutated": False,
            "new_carrier_schema": CARRIER_STATE_SCHEMA,
            "first_new_epoch": CUTOVER_LEGACY_EPOCH + 1,
            "observed_new_epoch": int(state["epoch"]),
            "new_carrier_state_ref": "control/heartbeat-carrier-runtime-state.json",
            "new_carrier_state_sha256": self._canonical_sha256(state),
            "carrier_observation_ref": "control/heartbeat-carrier-observation.json",
            "control_plane_ref": "control/worker-control-plane-coordination.json",
            "control_plane_sha256": control_hash,
            "worker_registry_ref": "control/worker-registry.json",
            "heartbeat_grants_execution_authority": False,
            "credential_authority": "TV/TVC",
            "non_tv_tvc_secret_or_token_used": False,
            "github_token_runtime_authority": "NONE",
            "render_production_runtime_used": False,
            "authority_effect": "NONE_CARRIER_ONLY",
            "recorded_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        }
        receipt = dict(base)
        receipt["receipt_sha256"] = self._canonical_sha256(base)
        return receipt

    def cycle(self, write: bool = True) -> dict[str, Any]:
        self._persist = write
        self._acquire()
        try:
            _legacy, legacy_raw_before, legacy_digest = self._legacy_source()
            state, first_cutover = self._load_carrier_state()
            registry = self._load(self.registry_path)
            epoch = int(state.get("epoch", CUTOVER_LEGACY_EPOCH)) + 1
            generation = int(state.get("generation", CUTOVER_LEGACY_EPOCH)) + 1
            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

            state["epoch"] = epoch
            state["generation"] = generation
            state["last_cycle_at"] = now
            state["reference_frame"] = f"heartbeat_epoch:{epoch}"
            state["activation_state"] = "ACTIVE"
            state["authority_effect"] = "NONE"
            state["legacy_cutover"]["closed"] = True

            control = self._control_plane_coordination(state, registry)
            control_hash = self._canonical_sha256(control)
            triggers = self._assignment_triggers(registry, epoch)
            observation = self._carrier_observation(state, control_hash, len(triggers))
            events: list[dict[str, Any]] = []
            self._event(
                events,
                epoch,
                "heartbeat_carrier_advanced",
                authority_effect=False,
                claim_authority=False,
                lease_authority=False,
                expiry_authority=False,
                activation_authority=False,
                execution_authority=False,
                carrier_schema=CARRIER_STATE_SCHEMA,
                legacy_hb29_immutable=True,
            )
            for trigger in triggers:
                events.append({
                    "schema": trigger["schema"],
                    "event_type": "worker_assignment_trigger_carried",
                    "epoch": epoch,
                    "packet": trigger,
                    "authority_effect": "NONE",
                    "execution_authority": False,
                })

            result = {
                "schema": "stegverse.heartbeat-carrier-cycle-result/v2",
                "runtime_schema": CARRIER_STATE_SCHEMA,
                "epoch": epoch,
                "generation": generation,
                "reference_frame": f"heartbeat_epoch:{epoch}",
                "legacy_hb29_cutover": "ACTIVATED" if write else "PREVIEW_ONLY",
                "legacy_hb29_was_first_cutover": first_cutover,
                "carrier_observation_ref": "control/heartbeat-carrier-observation.json",
                "control_plane_ref": "control/worker-control-plane-coordination.json",
                "assignment_trigger_packets": triggers,
                "registry_generation_observed": registry.get("generation", 0),
                "claims_issued": 0,
                "workers_invoked": 0,
                "tasks_activated": 0,
                "leases_expired": 0,
                "events": events,
                "authority_effect": "NONE_CARRIER_ONLY",
            }

            if write:
                if self._sha256_bytes(self.legacy_hb_path.read_bytes()) != legacy_digest:
                    raise RuntimeError("legacy HB29 changed during carrier cutover")
                self._atomic_write(self.carrier_state_path, state)
                self._atomic_write(self.control_plane_path, control)
                self._atomic_write(self.carrier_observation_path, observation)
                projection = {
                    "schema": "stegverse.heartbeat-master-records-projection/v3",
                    "heartbeat_epoch": epoch,
                    "heartbeat_generation": generation,
                    "carrier_state_ref": "control/heartbeat-carrier-runtime-state.json",
                    "carrier_state_sha256": self._canonical_sha256(state),
                    "carrier_observation_ref": "control/heartbeat-carrier-observation.json",
                    "carrier_observation_sha256": self._canonical_sha256(observation),
                    "worker_control_plane_ref": "control/worker-control-plane-coordination.json",
                    "worker_control_plane_sha256": control_hash,
                    "assignment_trigger_packet_ids": [item["packet_id"] for item in triggers],
                    "destination": "master-records/orchestration",
                    "recording_effect": "custody_and_reconstruction_only",
                    "authority_effect": False,
                }
                self._atomic_write(self.master_records_projection_path, projection)
                if first_cutover:
                    self._atomic_write(self.cutover_receipt_path, self._cutover_receipt(state, legacy_digest, control_hash))
                elif self.cutover_receipt_path.exists():
                    existing = self._load(self.cutover_receipt_path)
                    if existing.get("legacy_state_sha256") != legacy_digest or existing.get("first_new_epoch") != 30:
                        raise RuntimeError("existing HB29 cutover receipt is not bound to canonical legacy state")
                self.event_path.parent.mkdir(parents=True, exist_ok=True)
                with self.event_path.open("a", encoding="utf-8") as stream:
                    for event in events:
                        stream.write(json.dumps(event, sort_keys=True) + "\n")
                if self.legacy_hb_path.read_bytes() != legacy_raw_before:
                    raise RuntimeError("legacy HB29 was mutated by separated carrier")
                result["cutover_receipt_ref"] = "receipts/heartbeat-schema-cutover/HB29.json"
            return result
        finally:
            self._release_lock()
            self._persist = True


__all__ = ["HeartbeatRuntime", "WorkerResponse"]
