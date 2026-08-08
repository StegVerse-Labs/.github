from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import json

from .engine_v2 import HeartbeatRuntime as HeartbeatRuntimeV2, WorkerResponse
from .org_assertions import issue_claim_assertions


class HeartbeatRuntime(HeartbeatRuntimeV2):
    """Single StegVerse heartbeat runtime with organization assertion issuance.

    This is the sole epoch-owning runtime. Organization claim assertions and
    worker registry evaluation are performed inside the same heartbeat cycle.
    """

    def cycle(self, write: bool = True) -> dict[str, Any]:
        self._persist = write
        self._acquire()
        try:
            heartbeat = self._load(self.hb_path)
            registry = self._load(self.registry_path)
            cost_log = self._load(self.cost_log_path) if self.cost_log_path.exists() else {
                "schema": "stegverse.worker-cost-observation-log/v0.1",
                "generation": 0,
                "records": []
            }

            epoch = int(heartbeat.get("epoch", 0)) + 1
            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            heartbeat["epoch"] = epoch
            heartbeat["generation"] = int(heartbeat.get("generation", 0)) + 1
            heartbeat["last_cycle_at"] = now

            # Organization assertions and worker lifecycle share this one epoch.
            issued = issue_claim_assertions(self.root, epoch, now, write=write)
            heartbeat["last_issued_at"] = now
            heartbeat["expected_returns"] = len(issued)
            heartbeat["issued"] = issued

            events: list[dict[str, Any]] = []
            self._event(events, epoch, "organization_assertions_issued", issued_count=len(issued), issued_refs=issued)

            # Every currently owned worker answers the same heartbeat first.
            for task in list(registry.get("tasks", [])):
                if task.get("state") in self.WORKER_OWNED and task.get("worker_id"):
                    self._invoke(registry, task, epoch, cost_log, events)
                elif task.get("state") == "BLOCKED" and task.get("worker_id"):
                    self._invoke(registry, task, epoch, cost_log, events)

            activated = self._activate_one(registry, epoch, cost_log, events)
            if not activated:
                self._event(events, epoch, "no_worker_initiated", reason="NO_ELIGIBLE_ADMISSIBLE_RESOLVED_WORK")

            registry["updated_at"] = now
            result = {
                "schema": "stegverse.heartbeat-cycle-result/v0.3",
                "epoch": epoch,
                "organization_assertions": issued,
                "activated": activated,
                "events": events,
                "registry_generation": registry.get("generation", 0),
                "authority_effect": "none_beyond_existing_admitted_task_authority"
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
