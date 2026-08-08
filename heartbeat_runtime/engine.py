from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
import json
import math
import os
import shutil
import tempfile


@dataclass(frozen=True)
class WorkerResponse:
    state: str
    transition_id: str
    transition_sequence: int
    expected_next_transition: str | None = None
    expected_next_earliest_epoch: int | None = None
    expected_next_latest_epoch: int | None = None
    checkpoint_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()
    cost_observation: dict[str, Any] | None = None


Adapter = Callable[[dict[str, Any], dict[str, Any], int], WorkerResponse]


class HeartbeatRuntime:
    """One StegVerse heartbeat that coordinates registry, workers, and continuity.

    This engine is host/provider agnostic. A host only needs to keep the process
    running; cadence, registry evaluation, worker invocation, relative timing,
    fencing, and recovery admission happen inside this function.
    """

    ACTIVE = {"CLAIMED", "ACTIVE", "BLOCKED", "EXPIRING", "HANDOFF_WRITING"}
    RESPONSE_STATES = {"ACTIVE", "BLOCKED", "HANDOFF_READY", "COMPLETED", "FAILED_RETRYABLE", "FAILED_TERMINAL"}
    PRIORITY = {"security": 0, "release": 1, "critical": 2, "elevated": 3, "normal": 4}

    def __init__(self, root: str | Path, adapters: dict[str, Adapter] | None = None):
        self.root = Path(root)
        self.adapters = adapters or {}
        self.hb_path = self.root / "control" / "heartbeat-state.json"
        self.registry_path = self.root / "control" / "worker-registry.json"
        self.cost_log_path = self.root / "control" / "worker-cost-observations.json"
        self.event_path = self.root / "events" / "heartbeat-runtime.jsonl"
        self.lock_path = self.root / "control" / ".heartbeat-runtime.lock"

    def _load(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _atomic_write(self, path: Path, value: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as f:
            json.dump(value, f, indent=2, sort_keys=True)
            f.write("\n")
            temp_name = f.name
        os.replace(temp_name, path)

    def _lock(self) -> None:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.lock_path.mkdir()
        except FileExistsError as exc:
            raise RuntimeError("heartbeat cycle already owns the atomic registry lock") from exc

    def _unlock(self) -> None:
        shutil.rmtree(self.lock_path, ignore_errors=True)

    def _event(self, events: list[dict[str, Any]], epoch: int, kind: str, **fields: Any) -> None:
        events.append({"schema": "stegverse.heartbeat-runtime-event/v0.1", "epoch": epoch, "event_type": kind, **fields})

    def _handoff(self, task: dict[str, Any]) -> dict[str, Any]:
        return self._load(self.root / task["handoff_ref"])

    def _dependencies_complete(self, task: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> bool:
        handoff = self._handoff(task)
        return all(by_id.get(dep, {}).get("state") == "COMPLETED" for dep in handoff.get("task", {}).get("dependencies", []))

    def _worker_for_task(self, task: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any] | None:
        handoff = self._handoff(task)
        required = set(handoff.get("execution", {}).get("required_capabilities", []))
        for worker in sorted(registry.get("workers", []), key=lambda x: x["worker_id"]):
            if worker.get("status") != "AVAILABLE":
                continue
            adapter_ref = worker.get("adapter_ref")
            if not adapter_ref or adapter_ref not in self.adapters:
                continue
            if required.issubset(set(worker.get("capabilities", []))):
                return worker
        return None

    def _expiry_budget(self, task: dict[str, Any]) -> tuple[int | None, str]:
        ref = task.get("cost_basis_ref")
        if not ref:
            return None, "NONE"
        path = self.root / ref
        if not path.exists():
            return None, "NONE"
        record = self._load(path)
        hb = record.get("hb_estimate", {})
        candidate = hb.get("expiry_candidate_beats")
        confidence = hb.get("confidence")
        if candidate is None or confidence in {None, "NONE"}:
            return None, "NONE"
        beats = max(1, int(math.ceil(float(candidate))))
        return beats, "TASK_CLASS_COST_BASIS"

    def _record_cost(self, log: dict[str, Any], task: dict[str, Any], epoch: int, response: WorkerResponse) -> None:
        if not response.cost_observation:
            return
        log["generation"] = int(log.get("generation", 0)) + 1
        log.setdefault("records", []).append({
            "schema": "stegverse.worker-cost-observation/v0.1",
            "heartbeat_epoch": epoch,
            "task_id": task["task_id"],
            "goal_id": task.get("goal_id"),
            "worker_id": task.get("worker_id"),
            "external_entity_job_ref": task.get("external_entity_job_ref"),
            "transition_id": response.transition_id,
            "transition_sequence": response.transition_sequence,
            "cost": response.cost_observation,
        })

    def _has_master_records_final(self, task: dict[str, Any]) -> bool:
        markers = ("final-worker-report", "task_completed", "claim_released", "finalization")
        for ref in task.get("evidence_refs", []):
            low = str(ref).lower()
            if "master-records:" in low and any(marker in low for marker in markers):
                return True
        return False

    def _admit_recovery(self, registry: dict[str, Any], parent: dict[str, Any], epoch: int, events: list[dict[str, Any]]) -> None:
        task_id = f"RECOVER-{parent['task_id']}-HB{epoch}"
        if any(t.get("task_id") == task_id for t in registry.get("tasks", [])):
            return
        path = self.root / "handoffs" / "generated" / f"{task_id}.json"
        handoff_ref = str(path.relative_to(self.root))
        parent_handoff = self._handoff(parent)
        generated = {
            "schema": "stegverse.executable-handoff/v0.1",
            "handoff_id": f"HANDOFF-{task_id}",
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "state": "HANDOFF_READY",
            "goal": {
                "goal_id": task_id,
                "objective": "Reconcile a worker lifecycle whose known heartbeat-relative expiry lacks the required Master Records final worker report.",
                "success_predicates": ["Lifecycle evidence is reconciled", "Failure cause is identified", "Any remediation is sandbox-tested before executable admission"],
                "failure_predicates": ["Missing finalization is silently treated as completion", "Expired worker authority is restored without a new admitted claim"],
                "expires_at": None,
                "authority_ceiling": ["control_plane_reconciliation", "sandbox_validation", "no_parent_execution_authority_restore"]
            },
            "task": {
                "task_id": task_id,
                "repository": "StegVerse-Labs/.github",
                "source_refs": [parent["handoff_ref"], parent.get("last_checkpoint_ref") or parent["task_id"]],
                "dependencies": [],
                "parent_task_id": parent["task_id"],
                "derivation_reason": "Known HB-relative expiry reached without required Master Records final worker report.",
                "priority": "critical"
            },
            "authority": {
                "authority_source": "StegVerse-Labs/.github#12 lifecycle reconciliation policy",
                "heartbeat_grants_execution_authority": False,
                "policy_version": parent_handoff.get("authority", {}).get("policy_version", "shwp-single-hb-v0.2")
            },
            "execution": {
                "required_capabilities": ["lifecycle_reconciliation", "sandbox_validation"],
                "allowed_paths": ["StegVerse-Labs/.github"],
                "allowed_services": ["github"],
                "max_actions": 50,
                "max_retries": 3,
                "external_cost_ceiling_usd": 0
            },
            "activation": {
                "carrier": "heartbeat",
                "executor_binding": "UNBOUND",
                "recheck_trigger": "each heartbeat while HANDOFF_READY and unclaimed",
                "checkout_policy": "fenced_atomic_checkout"
            },
            "continuity": {
                "checkpoint_ref": parent.get("last_checkpoint_ref"),
                "handoff_destination": "StegVerse-Labs/.github/control/worker-registry.json",
                "master_records_required": True,
                "status_projection": "StegVerse-Labs/.github/control/worker-status.json"
            },
            "completion": {
                "next_authorized_action": "Investigate the missing finalization, sandbox-test candidate remediation if required, and admit only a validated remediation task.",
                "terminal_when": ["Reconciliation result is durable", "Validated remediation is completed or separately admitted", "Parent lifecycle is reconstructable"]
            },
            "block": None
        }
        self._atomic_write(path, generated)
        registry.setdefault("tasks", []).append({
            "task_id": task_id,
            "goal_id": task_id,
            "state": "HANDOFF_READY",
            "handoff_ref": handoff_ref,
            "executor_binding": "UNBOUND",
            "worker_id": None,
            "worker_instance_id": None,
            "claim_id": None,
            "lease": None,
            "heartbeat_timing": None,
            "cost_basis_ref": None,
            "external_entity_job_ref": None,
            "last_checkpoint_ref": parent.get("last_checkpoint_ref"),
            "block_ref": None,
            "archive_eligible": False,
            "archive_reason_codes": ["RECOVERY_RECONCILIATION_REQUIRED", "EXECUTOR_NOT_BOUND"],
            "evidence_refs": [parent["task_id"], f"heartbeat-epoch:{epoch}", "MASTER_RECORDS_FINAL_WORKER_REPORT_MISSING"]
        })
        self._event(events, epoch, "recovery_task_admitted", task_id=task_id, parent_task_id=parent["task_id"])

    def _release_worker(self, registry: dict[str, Any], task: dict[str, Any]) -> None:
        wid = task.get("worker_id")
        if wid:
            for worker in registry.get("workers", []):
                if worker.get("worker_id") == wid and worker.get("status") != "DISABLED":
                    worker["status"] = "AVAILABLE"
        task["worker_id"] = None
        task["worker_instance_id"] = None
        task["claim_id"] = None
        task["executor_binding"] = "UNBOUND"

    def _invoke(self, registry: dict[str, Any], task: dict[str, Any], epoch: int, cost_log: dict[str, Any], events: list[dict[str, Any]]) -> None:
        timing = task.get("heartbeat_timing") or {}
        expiry = timing.get("expiry_epoch")
        if expiry is not None and epoch >= int(expiry):
            task["state"] = "EXPIRING"
            self._event(events, epoch, "worker_expiry_reached", task_id=task["task_id"], worker_id=task.get("worker_id"))
            if not self._has_master_records_final(task):
                self._admit_recovery(registry, task, epoch, events)
            self._release_worker(registry, task)
            task["state"] = "HANDOFF_READY"
            task["heartbeat_timing"] = None
            task["archive_eligible"] = False
            task["archive_reason_codes"] = ["KNOWN_EXPIRY_REACHED", "REQUIRES_RECONCILIATION"]
            return

        worker = next((w for w in registry.get("workers", []) if w.get("worker_id") == task.get("worker_id")), None)
        adapter_ref = worker and worker.get("adapter_ref")
        adapter = self.adapters.get(adapter_ref) if adapter_ref else None
        if adapter is None:
            self._event(events, epoch, "worker_response_missing", task_id=task["task_id"], worker_id=task.get("worker_id"))
            return

        response = adapter(task, self._handoff(task), epoch)
        if response.state not in self.RESPONSE_STATES:
            raise ValueError(f"unsupported worker response state: {response.state}")
        previous = timing.get("current_transition")
        timing["last_response_epoch"] = epoch
        if response.transition_id != previous:
            timing["last_transition_epoch"] = epoch
        timing["current_transition"] = response.transition_id
        timing["transition_sequence"] = response.transition_sequence
        timing["expected_next_transition"] = response.expected_next_transition
        timing["expected_next_earliest_epoch"] = response.expected_next_earliest_epoch
        timing["expected_next_latest_epoch"] = response.expected_next_latest_epoch
        task["heartbeat_timing"] = timing
        if response.checkpoint_ref:
            task["last_checkpoint_ref"] = response.checkpoint_ref
        task.setdefault("evidence_refs", []).extend(x for x in response.evidence_refs if x not in task.get("evidence_refs", []))
        self._record_cost(cost_log, task, epoch, response)
        self._event(events, epoch, "worker_response", task_id=task["task_id"], worker_id=task.get("worker_id"), transition_id=response.transition_id, transition_sequence=response.transition_sequence, response_state=response.state)

        if response.state == "COMPLETED":
            task["state"] = "COMPLETED"
            task["archive_eligible"] = True
            task["archive_reason_codes"] = []
            self._release_worker(registry, task)
        elif response.state == "HANDOFF_READY":
            task["state"] = "HANDOFF_READY"
            task["archive_eligible"] = False
            self._release_worker(registry, task)
            task["heartbeat_timing"] = None
        else:
            task["state"] = response.state

    def _activate_one(self, registry: dict[str, Any], epoch: int, cost_log: dict[str, Any], events: list[dict[str, Any]]) -> bool:
        by_id = {t["task_id"]: t for t in registry.get("tasks", [])}
        ready = [t for t in registry.get("tasks", []) if t.get("state") == "HANDOFF_READY" and self._dependencies_complete(t, by_id)]
        ready.sort(key=lambda t: (self.PRIORITY.get(self._handoff(t).get("task", {}).get("priority", "normal"), 4), t["task_id"]))
        for task in ready:
            budget, basis = self._expiry_budget(task)
            if budget is None:
                task["archive_reason_codes"] = sorted(set(task.get("archive_reason_codes", []) + ["EXPIRY_BASIS_UNAVAILABLE"]))
                self._event(events, epoch, "activation_deferred", task_id=task["task_id"], reason="EXPIRY_BASIS_UNAVAILABLE")
                continue
            worker = self._worker_for_task(task, registry)
            if worker is None:
                task["archive_reason_codes"] = sorted(set(task.get("archive_reason_codes", []) + ["EXECUTOR_NOT_RESOLVED"]))
                self._event(events, epoch, "activation_deferred", task_id=task["task_id"], reason="EXECUTOR_NOT_RESOLVED")
                continue
            generation = int(registry.get("generation", 0)) + 1
            registry["generation"] = generation
            claim_id = f"SHWP-{task['task_id']}-G{generation}"
            task["state"] = "ACTIVE"
            task["executor_binding"] = "BOUND"
            task["worker_id"] = worker["worker_id"]
            task["worker_instance_id"] = f"{worker['worker_id']}-HB{epoch}-G{generation}"
            task["claim_id"] = claim_id
            task["archive_eligible"] = False
            task["archive_reason_codes"] = []
            task["heartbeat_timing"] = {
                "start_epoch": epoch,
                "last_response_epoch": epoch,
                "last_transition_epoch": epoch,
                "current_transition": "ACTIVATED",
                "transition_sequence": 0,
                "expected_next_transition": None,
                "expected_next_earliest_epoch": None,
                "expected_next_latest_epoch": None,
                "max_missing_response_beats": max(1, min(10, budget)),
                "expiry_epoch": epoch + budget,
                "expiry_basis": basis,
                "fencing_token": generation
            }
            worker["status"] = "BUSY"
            worker["last_seen_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            self._event(events, epoch, "worker_activated", task_id=task["task_id"], worker_id=worker["worker_id"], claim_id=claim_id, fencing_token=generation, expiry_epoch=epoch + budget, expiry_basis=basis)
            self._invoke(registry, task, epoch, cost_log, events)
            return True
        return False

    def cycle(self, write: bool = True) -> dict[str, Any]:
        self._lock()
        try:
            hb = self._load(self.hb_path)
            registry = self._load(self.registry_path)
            cost_log = self._load(self.cost_log_path) if self.cost_log_path.exists() else {"schema": "stegverse.worker-cost-observation-log/v0.1", "generation": 0, "records": []}
            epoch = int(hb.get("epoch", 0)) + 1
            hb["epoch"] = epoch
            hb["generation"] = int(hb.get("generation", 0)) + 1
            hb["last_cycle_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            events: list[dict[str, Any]] = []

            # Active workers answer this same heartbeat before new work is selected.
            for task in list(registry.get("tasks", [])):
                if task.get("state") in self.ACTIVE and task.get("worker_id"):
                    self._invoke(registry, task, epoch, cost_log, events)

            activated = self._activate_one(registry, epoch, cost_log, events)
            if not activated:
                self._event(events, epoch, "no_worker_initiated", reason="NO_ELIGIBLE_ADMISSIBLE_RESOLVED_WORK")

            registry["updated_at"] = hb["last_cycle_at"]
            result = {
                "schema": "stegverse.heartbeat-cycle-result/v0.1",
                "epoch": epoch,
                "activated": activated,
                "events": events,
                "registry_generation": registry.get("generation", 0),
                "authority_effect": "none_beyond_existing_admitted_task_authority"
            }
            if write:
                self._atomic_write(self.hb_path, hb)
                self._atomic_write(self.registry_path, registry)
                self._atomic_write(self.cost_log_path, cost_log)
                self.event_path.parent.mkdir(parents=True, exist_ok=True)
                with self.event_path.open("a", encoding="utf-8") as stream:
                    for event in events:
                        stream.write(json.dumps(event, sort_keys=True) + "\n")
            return result
        finally:
            self._unlock()
