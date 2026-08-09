from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import hashlib
import json

from .engine_v8 import HeartbeatRuntime as HeartbeatRuntimeV8, WorkerResponse
from .org_assertions import issue_claim_assertions


class HeartbeatRuntime(HeartbeatRuntimeV8):
    """Single-heartbeat runtime with cycle-bound worker coordination subsignals.

    The heartbeat is the high-frequency carrier. Worker authority is still
    established by admitted task/claim/fence state. The worker-coordination
    subsignal carries the already-admitted worker lease on every heartbeat
    cycle; the lease lifetime is measured in heartbeat cycles, never in wall
    clock time and never by a low-frequency scheduler.
    """

    WORKER_COORDINATION_SUBSIGNAL = "worker_coordination"

    @property
    def subsignal_path(self):
        return self.root / "control" / "heartbeat-subsignals.json"

    @property
    def master_records_projection_path(self):
        return self.root / "control" / "heartbeat-master-records-projection.json"

    def _coordination_lease(self, task: dict[str, Any], epoch: int) -> dict[str, Any] | None:
        timing = task.get("heartbeat_timing") or {}
        start = timing.get("start_epoch")
        end = timing.get("expiry_epoch")
        if not all(isinstance(value, int) for value in (start, end)):
            return None
        assigned = max(0, end - start)
        return {
            "task_id": task.get("task_id"),
            "goal_id": task.get("goal_id"),
            "worker_id": task.get("worker_id"),
            "worker_instance_id": task.get("worker_instance_id"),
            "claim_id": task.get("claim_id"),
            "fencing_token": timing.get("fencing_token"),
            "lease_start_cycle": start,
            "lease_end_cycle_exclusive": end,
            "assigned_cycles": assigned,
            "remaining_cycles": max(0, end - epoch),
            "expiry_basis": timing.get("expiry_basis"),
            "current_transition": timing.get("current_transition"),
            "task_state": task.get("state"),
            "handoff_ref": task.get("handoff_ref"),
            "lease_clock": "canonical_heartbeat_cycle",
            "wall_clock_expiry_authority": False,
        }

    def _worker_coordination_subsignal(self, registry: dict[str, Any], epoch: int) -> dict[str, Any]:
        leases: list[dict[str, Any]] = []
        for task in sorted(registry.get("tasks", []), key=lambda item: str(item.get("task_id", ""))):
            if not task.get("worker_id") or not task.get("claim_id"):
                continue
            if task.get("state") not in self.WORKER_OWNED and task.get("state") != "BLOCKED":
                continue
            lease = self._coordination_lease(task, epoch)
            if lease is not None:
                leases.append(lease)
        return {
            "kind": "worker_coordination",
            "state": "ACTIVE" if leases else "IDLE",
            "carrier": "single_stegverse_heartbeat",
            "carrier_epoch": epoch,
            "carrier_cycle_unit": "heartbeat_cycle",
            "worker_lease_unit": "heartbeat_cycle",
            "worker_lease_source": "admitted_task_cost_basis_and_runtime_window",
            "worker_lease_is_heartbeat_lifetime": False,
            "wall_clock_expiry_authority": False,
            "active_leases": leases,
            "worker_registry_ref": "control/worker-registry.json",
            "master_records_projection": {
                "required": True,
                "latest_projection_ref": "control/heartbeat-master-records-projection.json",
                "event_log_ref": "events/heartbeat-runtime.jsonl",
                "destination": "master-records/orchestration",
                "authority_effect": False,
            },
            "authority_effect": False,
        }

    def _coordination_digest(self, subsignal: dict[str, Any]) -> str:
        payload = json.dumps(subsignal, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _carry_subsignals(
        self,
        heartbeat: dict[str, Any],
        registry: dict[str, Any],
        epoch: int,
        events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        data = self._load(self.subsignal_path) if self.subsignal_path.exists() else {
            "schema": "stegverse.heartbeat-subsignals/v1",
            "generation": 0,
            "subsignals": {},
        }
        coordination = self._worker_coordination_subsignal(registry, epoch)
        digest = self._coordination_digest(coordination)
        data.setdefault("subsignals", {})[self.WORKER_COORDINATION_SUBSIGNAL] = coordination
        data["generation"] = int(data.get("generation", 0)) + 1

        heartbeat["subsignals"] = {
            self.WORKER_COORDINATION_SUBSIGNAL: coordination,
            "registry_generation": data["generation"],
            "worker_coordination_sha256": digest,
        }
        projection = {
            "schema": "stegverse.heartbeat-master-records-projection/v1",
            "heartbeat_epoch": epoch,
            "heartbeat_generation": heartbeat.get("generation"),
            "worker_coordination_sha256": digest,
            "worker_coordination": coordination,
            "source_refs": [
                "control/heartbeat-state.json",
                "control/heartbeat-subsignals.json",
                "control/worker-registry.json",
                "events/heartbeat-runtime.jsonl",
            ],
            "destination": "master-records/orchestration",
            "recording_effect": "custody_and_reconstruction_only",
            "execution_authority": False,
        }
        if self._persist:
            self._atomic_write(self.subsignal_path, data)
            self._atomic_write(self.master_records_projection_path, projection)
        self._event(
            events,
            epoch,
            "worker_coordination_subsignal_carried",
            active_lease_count=len(coordination["active_leases"]),
            worker_coordination_sha256=digest,
            master_records_projection_ref="control/heartbeat-master-records-projection.json",
            wall_clock_expiry_authority=False,
            authority_effect=False,
        )
        return coordination

    def cycle(self, write: bool = True) -> dict[str, Any]:
        self._persist = write
        self._acquire()
        try:
            heartbeat = self._load(self.hb_path)
            registry = self._load(self.registry_path)
            cost_log = self._load(self.cost_log_path) if self.cost_log_path.exists() else {
                "schema": "stegverse.worker-cost-observation-log/v0.1",
                "generation": 0,
                "records": [],
            }

            epoch = int(heartbeat.get("epoch", 0)) + 1
            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            heartbeat["epoch"] = epoch
            heartbeat["generation"] = int(heartbeat.get("generation", 0)) + 1
            heartbeat["last_cycle_at"] = now

            issued = issue_claim_assertions(self.root, epoch, now, write=write)
            heartbeat["last_issued_at"] = now
            heartbeat["expected_returns"] = len(issued)
            heartbeat["issued"] = issued

            events: list[dict[str, Any]] = []
            self._event(events, epoch, "organization_assertions_issued", issued_count=len(issued), issued_refs=issued)

            for task in list(registry.get("tasks", [])):
                if task.get("state") in self.WORKER_OWNED and task.get("worker_id"):
                    self._invoke(registry, task, epoch, cost_log, events)
                elif task.get("state") == "BLOCKED" and task.get("worker_id"):
                    self._invoke(registry, task, epoch, cost_log, events)

            activated = self._activate_one(registry, epoch, cost_log, events)
            if not activated:
                self._event(events, epoch, "no_worker_initiated", reason="NO_ELIGIBLE_ADMISSIBLE_RESOLVED_WORK")

            coordination = self._carry_subsignals(heartbeat, registry, epoch, events)
            registry["updated_at"] = now
            result = {
                "schema": "stegverse.heartbeat-cycle-result/v0.9",
                "epoch": epoch,
                "organization_assertions": issued,
                "activated": activated,
                "subsignals": {self.WORKER_COORDINATION_SUBSIGNAL: coordination},
                "registry_generation": registry.get("generation", 0),
                "authority_effect": "none_beyond_existing_admitted_task_authority",
            }
            if write:
                self._atomic_write(self.hb_path, heartbeat)
                self._atomic_write(self.registry_path, registry)
                self._atomic_write(self.cost_log_path, cost_log)
                self.event_path.parent.mkdir(parents=True, exist_ok=True)
                with self.event_path.open("a", encoding="utf-8") as stream:
                    for event in events:
                        stream.write(json.dumps(event, sort_keys=True) + "\n")
            return result
        finally:
            self._release_lock()
            self._persist = True


__all__ = ["HeartbeatRuntime", "WorkerResponse"]
