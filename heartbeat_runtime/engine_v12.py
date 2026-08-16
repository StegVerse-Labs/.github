from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import hashlib
import json

from .engine_v11 import HeartbeatRuntime as LegacyWorkerCoordinator, WorkerResponse
from .assignment_timer import assignment_trigger_packet


class HeartbeatRuntime(LegacyWorkerCoordinator):
    """Non-authorizing StegVerse carrier signal.

    v12 removes worker scheduling, claim issuance, invocation, lease expiry,
    orphan recovery, and task activation from the heartbeat cycle. The heartbeat
    only advances its own carrier state and projects observational packets.
    """

    def _carrier_worker_observation(self, registry: dict[str, Any], epoch: int) -> dict[str, Any]:
        observations: list[dict[str, Any]] = []
        triggers: list[dict[str, Any]] = []
        for task in sorted(registry.get("tasks", []), key=lambda item: str(item.get("task_id", ""))):
            if task.get("state") == "HANDOFF_READY" and not task.get("worker_id") and not task.get("claim_id"):
                triggers.append(assignment_trigger_packet(carrier_epoch=epoch, task=task))
            if not task.get("worker_id") and not task.get("claim_id"):
                continue
            timing = task.get("heartbeat_timing") or {}
            timer = task.get("assignment_timer") or {}
            observations.append({
                "task_id": task.get("task_id"),
                "goal_id": task.get("goal_id"),
                "worker_id": task.get("worker_id"),
                "worker_instance_id": task.get("worker_instance_id"),
                "claim_id": task.get("claim_id"),
                "fencing_token": timer.get("fencing_token", timing.get("fencing_token")),
                "task_state": task.get("state"),
                "handoff_ref": task.get("handoff_ref"),
                "observed_at_carrier_epoch": epoch,
                "assignment_timer_remaining_hb_units": timer.get("remaining_hb_units"),
                "lease_or_expiry_effect": "NONE",
                "authority_effect": False,
            })
        return {
            "kind": "worker_coordination_observation",
            "state": "OBSERVING" if observations or triggers else "IDLE",
            "carrier": "single_stegverse_heartbeat",
            "carrier_epoch": epoch,
            "observed_worker_state": observations,
            "unassigned_task_trigger_packets": triggers,
            "trigger_packet_semantics": "SINGLE_USE_TRANSPORT_ONLY",
            "worker_registry_ref": "control/worker-registry.json",
            "claim_authority": False,
            "lease_authority": False,
            "expiry_authority": False,
            "activation_authority": False,
            "execution_authority": False,
            "authority_effect": False,
        }

    def _carry_observations(self, heartbeat: dict[str, Any], registry: dict[str, Any], epoch: int, events: list[dict[str, Any]]) -> dict[str, Any]:
        data = self._load(self.subsignal_path) if self.subsignal_path.exists() else {
            "schema": "stegverse.heartbeat-subsignals/v1",
            "generation": 0,
            "subsignals": {},
        }
        observation = self._carrier_worker_observation(registry, epoch)
        payload = json.dumps(observation, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        data.setdefault("subsignals", {})[self.WORKER_COORDINATION_SUBSIGNAL] = observation
        data["generation"] = int(data.get("generation", 0)) + 1
        heartbeat["subsignals"] = {
            self.WORKER_COORDINATION_SUBSIGNAL: observation,
            "registry_generation": registry.get("generation", 0),
            "worker_coordination_sha256": digest,
        }
        projection = {
            "schema": "stegverse.heartbeat-master-records-projection/v2",
            "heartbeat_epoch": epoch,
            "heartbeat_generation": heartbeat.get("generation"),
            "worker_coordination_sha256": digest,
            "worker_coordination_observation": observation,
            "source_refs": [
                "control/heartbeat-state.json",
                "control/heartbeat-subsignals.json",
                "control/worker-registry.json",
                "events/heartbeat-runtime.jsonl",
            ],
            "destination": "master-records/orchestration",
            "recording_effect": "custody_and_reconstruction_only",
            "claim_authority": False,
            "lease_authority": False,
            "expiry_authority": False,
            "activation_authority": False,
            "execution_authority": False,
            "authority_effect": False,
        }
        if self._persist:
            self._atomic_write(self.subsignal_path, data)
            self._atomic_write(self.master_records_projection_path, projection)
        self._event(
            events,
            epoch,
            "worker_state_observation_carried",
            observed_worker_count=len(observation["observed_worker_state"]),
            assignment_trigger_count=len(observation["unassigned_task_trigger_packets"]),
            worker_coordination_sha256=digest,
            master_records_projection_ref="control/heartbeat-master-records-projection.json",
            authority_effect=False,
        )
        return observation

    def cycle(self, write: bool = True) -> dict[str, Any]:
        self._persist = write
        self._acquire()
        try:
            heartbeat = self._load(self.hb_path)
            registry = self._load(self.registry_path)
            epoch = int(heartbeat.get("epoch", 0)) + 1
            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            heartbeat["epoch"] = epoch
            heartbeat["generation"] = int(heartbeat.get("generation", 0)) + 1
            heartbeat["last_cycle_at"] = now
            heartbeat["last_issued_at"] = None
            heartbeat["expected_returns"] = 0
            heartbeat["issued"] = []
            events: list[dict[str, Any]] = []
            self._event(events, epoch, "heartbeat_carrier_advanced", authority_effect=False, claim_authority=False, lease_authority=False, expiry_authority=False, activation_authority=False, execution_authority=False)
            observation = self._carry_observations(heartbeat, registry, epoch, events)
            result = {
                "schema": "stegverse.heartbeat-carrier-cycle-result/v1",
                "epoch": epoch,
                "events": events,
                "subsignals": {self.WORKER_COORDINATION_SUBSIGNAL: observation},
                "registry_generation_observed": registry.get("generation", 0),
                "claims_issued": 0,
                "workers_invoked": 0,
                "tasks_activated": 0,
                "leases_expired": 0,
                "authority_effect": "NONE_CARRIER_ONLY",
            }
            if write:
                self._atomic_write(self.hb_path, heartbeat)
                self.event_path.parent.mkdir(parents=True, exist_ok=True)
                with self.event_path.open("a", encoding="utf-8") as stream:
                    for event in events:
                        stream.write(json.dumps(event, sort_keys=True) + "\n")
            return result
        finally:
            self._release_lock()
            self._persist = True


__all__ = ["HeartbeatRuntime", "WorkerResponse"]
