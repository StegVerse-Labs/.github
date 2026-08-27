from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json

from .engine_v8 import HeartbeatRuntime as HeartbeatRuntimeV8, WorkerResponse
from .org_assertions import issue_claim_assertions
from .orphan_recovery import reconcile_quarantined_orphan_recoveries


class HeartbeatRuntime(HeartbeatRuntimeV8):
    """Single-heartbeat runtime with cycle-bound worker coordination subsignals."""

    WORKER_COORDINATION_SUBSIGNAL = "worker_coordination"

    @property
    def subsignal_path(self):
        return self.root / "control" / "heartbeat-subsignals.json"

    @property
    def master_records_projection_path(self):
        return self.root / "control" / "heartbeat-master-records-projection.json"

    @property
    def registry_fragment_dir(self) -> Path:
        return self.root / "control" / "worker-registry.d"

    def _apply_registry_fragments(self, registry: dict[str, Any], task_id_filter: str | None = None) -> list[str]:
        """Admit repository-owned registry fragments without replacing runtime state.

        Fragments are append-only bootstrap declarations. Once a task/worker ID is
        present in the canonical registry, the live registry remains authoritative
        and the fragment cannot overwrite claim, fence, timing, status, or receipts.
        This lets bounded integrations install durable machine work without a
        GitHub-token-powered activation workflow or a giant whole-file registry edit.
        """
        if not self.registry_fragment_dir.is_dir():
            return []

        tasks = registry.setdefault("tasks", [])
        workers = registry.setdefault("workers", [])
        task_ids = {str(item.get("task_id")) for item in tasks if item.get("task_id")}
        worker_ids = {str(item.get("worker_id")) for item in workers if item.get("worker_id")}
        applied: list[str] = []

        for path in sorted(self.registry_fragment_dir.glob("*.json")):
            fragment = self._load(path)
            if task_id_filter is not None:
                declared_task_ids = {str(item.get("task_id")) for item in fragment.get("tasks", []) if isinstance(item, dict) and item.get("task_id")}
                if task_id_filter not in declared_task_ids:
                    continue
            if fragment.get("schema") != "stegverse.worker-registry-fragment/v0.1":
                raise RuntimeError(f"unsupported worker registry fragment schema: {path.name}")
            if fragment.get("authority_effect") != "NONE_REGISTRATION_ONLY":
                raise RuntimeError(f"worker registry fragment may not grant authority: {path.name}")
            if fragment.get("github_token_required") is not False:
                raise RuntimeError(f"worker registry fragment may not require GitHub token authority: {path.name}")

            changed = False
            for task in fragment.get("tasks", []):
                if not isinstance(task, dict):
                    raise RuntimeError(f"invalid task in registry fragment: {path.name}")
                task_id = task.get("task_id")
                if task_id_filter is not None and task_id != task_id_filter:
                    continue
                handoff_ref = task.get("handoff_ref")
                if not isinstance(task_id, str) or not task_id:
                    raise RuntimeError(f"registry fragment task_id missing: {path.name}")
                if not isinstance(handoff_ref, str) or not handoff_ref or not (self.root / handoff_ref).is_file():
                    raise RuntimeError(f"registry fragment handoff missing for {task_id}: {path.name}")
                if task_id not in task_ids:
                    tasks.append(dict(task))
                    task_ids.add(task_id)
                    changed = True

            for worker in fragment.get("workers", []):
                if not isinstance(worker, dict):
                    raise RuntimeError(f"invalid worker in registry fragment: {path.name}")
                worker_id = worker.get("worker_id")
                adapter_ref = worker.get("adapter_ref")
                if not isinstance(worker_id, str) or not worker_id:
                    raise RuntimeError(f"registry fragment worker_id missing: {path.name}")
                if not isinstance(adapter_ref, str) or not adapter_ref:
                    raise RuntimeError(f"registry fragment adapter_ref missing for {worker_id}: {path.name}")
                if worker_id not in worker_ids:
                    workers.append(dict(worker))
                    worker_ids.add(worker_id)
                    changed = True

            if changed:
                applied.append(str(path.relative_to(self.root)))

        if applied:
            registry["generation"] = int(registry.get("generation", 0)) + 1
        return applied

    def _coordination_lease(self, task: dict[str, Any], epoch: int) -> dict[str, Any] | None:
        timing = task.get("heartbeat_timing") or {}
        start = timing.get("start_epoch")
        end = timing.get("expiry_epoch")
        fence = timing.get("fencing_token")
        if not all(isinstance(value, int) for value in (start, end, fence)) or end <= start:
            return None
        return {
            "task_id": task.get("task_id"),
            "goal_id": task.get("goal_id"),
            "worker_id": task.get("worker_id"),
            "worker_instance_id": task.get("worker_instance_id"),
            "claim_id": task.get("claim_id"),
            "fencing_token": fence,
            "lease_start_cycle": start,
            "lease_end_cycle_exclusive": end,
            "assigned_cycles": end - start,
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

    def _carry_subsignals(self, heartbeat: dict[str, Any], registry: dict[str, Any], epoch: int, events: list[dict[str, Any]]) -> dict[str, Any]:
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

    def _reconcile_orphan_recovery_quarantines(self, registry: dict[str, Any], epoch: int, events: list[dict[str, Any]]) -> list[str]:
        def emit(event_epoch: int, event_type: str, **payload: Any) -> None:
            self._event(events, event_epoch, event_type, **payload)

        return reconcile_quarantined_orphan_recoveries(
            self.root,
            registry,
            epoch=epoch,
            event=emit,
        )

    def cycle(self, write: bool = True) -> dict[str, Any]:
        self._persist = write
        self._acquire()
        try:
            heartbeat = self._load(self.hb_path)
            registry = self._load(self.registry_path)
            registry_fragments_applied = self._apply_registry_fragments(registry)
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
            if registry_fragments_applied:
                self._event(
                    events,
                    epoch,
                    "worker_registry_fragments_applied",
                    fragment_refs=registry_fragments_applied,
                    fragment_count=len(registry_fragments_applied),
                    authority_effect=False,
                    github_token_required=False,
                )
            self._event(events, epoch, "organization_assertions_issued", issued_count=len(issued), issued_refs=issued)
            reconciled_recoveries = self._reconcile_orphan_recovery_quarantines(registry, epoch, events)
            for task in list(registry.get("tasks", [])):
                if task.get("state") in self.WORKER_OWNED and task.get("worker_id"):
                    self._invoke(registry, task, epoch, cost_log, events)
                elif task.get("state") == "BLOCKED" and task.get("worker_id"):
                    self._invoke(registry, task, epoch, cost_log, events)
            activated = self._activate_one(registry, epoch, cost_log, events)
            coordination = self._carry_subsignals(heartbeat, registry, epoch, events)
            if not activated:
                self._event(events, epoch, "no_worker_initiated", reason="NO_ELIGIBLE_ADMISSIBLE_RESOLVED_WORK")
            registry["updated_at"] = now
            result = {
                "schema": "stegverse.heartbeat-cycle-result/v0.9",
                "epoch": epoch,
                "organization_assertions": issued,
                "activated": activated,
                "events": events,
                "subsignals": {self.WORKER_COORDINATION_SUBSIGNAL: coordination},
                "registry_generation": registry.get("generation", 0),
                "registry_fragments_applied": registry_fragments_applied,
                "orphan_recoveries_reconciled": reconciled_recoveries,
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
