from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
import hashlib
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
    """Provider-agnostic single-heartbeat worker runtime.

    One heartbeat epoch is the common timing frame. The runtime evaluates
    HANDOFF/registry state, invokes active workers on that same heartbeat,
    performs fenced checkout, records cost observations, and creates recovery
    work when lifecycle evidence diverges. It never invents execution authority.
    """

    WORKER_OWNED = {"CLAIMED", "ACTIVE", "EXPIRING", "HANDOFF_WRITING"}
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
        self._persist = True

    def _load(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _atomic_write(self, path: Path, value: Any) -> None:
        if not self._persist:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            temp_name = stream.name
        os.replace(temp_name, path)

    def _acquire(self) -> None:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.lock_path.mkdir()
        except FileExistsError as exc:
            raise RuntimeError("heartbeat cycle already owns the atomic registry lock") from exc

    def _release_lock(self) -> None:
        shutil.rmtree(self.lock_path, ignore_errors=True)

    def _event(self, events: list[dict[str, Any]], epoch: int, event_type: str, **fields: Any) -> None:
        events.append({
            "schema": "stegverse.heartbeat-runtime-event/v0.2",
            "epoch": epoch,
            "event_type": event_type,
            **fields,
        })

    def _handoff(self, task: dict[str, Any]) -> dict[str, Any]:
        return self._load(self.root / task["handoff_ref"])

    def _handoff_hash(self, handoff: dict[str, Any]) -> str:
        payload = json.dumps(handoff, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _activation_request(self, registry: dict[str, Any], task: dict[str, Any], handoff: dict[str, Any], epoch: int, events: list[dict[str, Any]]) -> None:
        activation = handoff.get("activation", {})
        authority = handoff.get("authority", {})
        execution = handoff.get("execution", {})
        events.append({
            "schema": "stegverse.heartbeat-activation-request/v0.1",
            "event_type": "activation_requested",
            "epoch": epoch,
            "task_id": task["task_id"],
            "goal_id": task.get("goal_id") or handoff.get("goal", {}).get("goal_id"),
            "handoff_ref": task["handoff_ref"],
            "handoff_sha256": self._handoff_hash(handoff),
            "required_capabilities": list(execution.get("required_capabilities", [])),
            "current_fence_generation": int(registry.get("generation", 0)),
            "authority_source": authority.get("authority_source"),
            "authorization_ref": activation.get("authorization_ref"),
            "execution_authority": False,
        })

    def _execution_authorized(self, handoff: dict[str, Any]) -> bool:
        authority = handoff.get("authority", {})
        activation = handoff.get("activation", {})
        return (
            authority.get("heartbeat_grants_execution_authority") is False
            and activation.get("executor_binding") == "AUTHORIZED"
            and isinstance(activation.get("authorization_ref"), str)
            and bool(activation.get("authorization_ref"))
        )

    def _dependencies_complete(self, task: dict[str, Any], tasks: dict[str, dict[str, Any]]) -> bool:
        deps = self._handoff(task).get("task", {}).get("dependencies", [])
        return all(tasks.get(dep, {}).get("state") == "COMPLETED" for dep in deps)

    def _expiry_budget(self, task: dict[str, Any]) -> tuple[int | None, str]:
        ref = task.get("cost_basis_ref")
        if not ref:
            return None, "NONE"
        path = self.root / ref
        if not path.exists():
            return None, "NONE"
        record = self._load(path)
        estimate = record.get("hb_estimate", {})
        candidate = estimate.get("expiry_candidate_beats")
        confidence = estimate.get("confidence")
        if candidate is None or confidence in {None, "NONE"}:
            return None, "NONE"
        return max(1, int(math.ceil(float(candidate)))), "TASK_CLASS_COST_BASIS"

    def _worker_for(self, task: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any] | None:
        required = set(self._handoff(task).get("execution", {}).get("required_capabilities", []))
        for worker in sorted(registry.get("workers", []), key=lambda item: item["worker_id"]):
            adapter_ref = worker.get("adapter_ref")
            if worker.get("status") != "AVAILABLE" or not adapter_ref or adapter_ref not in self.adapters:
                continue
            if required.issubset(set(worker.get("capabilities", []))):
                return worker
        return None

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
        return any(
            "master-records:" in str(ref).lower()
            and any(marker in str(ref).lower() for marker in markers)
            for ref in task.get("evidence_refs", [])
        )

    def _release_worker(self, registry: dict[str, Any], task: dict[str, Any]) -> None:
        worker_id = task.get("worker_id")
        for worker in registry.get("workers", []):
            if worker.get("worker_id") == worker_id and worker.get("status") != "DISABLED":
                worker["status"] = "AVAILABLE"
        task["worker_id"] = None
        task["worker_instance_id"] = None
        task["claim_id"] = None
        task["executor_binding"] = "UNBOUND"

    def _admit_recovery(self, registry: dict[str, Any], parent: dict[str, Any], epoch: int, events: list[dict[str, Any]]) -> str:
        task_id = f"RECOVER-{parent['task_id']}-HB{epoch}"
        existing = next((task for task in registry.get("tasks", []) if task.get("task_id") == task_id), None)
        if existing:
            return task_id

        handoff_ref = f"handoffs/generated/{task_id}.json"
        parent_handoff = self._handoff(parent)
        generated = {
            "schema": "stegverse.executable-handoff/v0.1",
            "handoff_id": f"HANDOFF-{task_id}",
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "state": "HANDOFF_READY",
            "goal": {
                "goal_id": task_id,
                "objective": "Reconcile a worker lifecycle whose known heartbeat-relative expiry lacks the required Master Records final worker report.",
                "success_predicates": [
                    "Lifecycle evidence is reconciled",
                    "Failure cause is identified",
                    "Any remediation is sandbox-tested before executable admission"
                ],
                "failure_predicates": [
                    "Missing finalization is silently treated as completion",
                    "Expired worker authority is restored without a new admitted claim"
                ],
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
                "next_authorized_action": "Investigate missing finalization, sandbox-test candidate remediation if needed, and admit only validated remediation work.",
                "terminal_when": ["Reconciliation is durable", "Parent lifecycle is reconstructable", "Any remediation is separately admitted or complete"]
            },
            "block": None
        }
        self._atomic_write(self.root / handoff_ref, generated)
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
        return task_id

    def _expire(self, registry: dict[str, Any], task: dict[str, Any], epoch: int, events: list[dict[str, Any]]) -> None:
        self._event(events, epoch, "worker_expiry_reached", task_id=task["task_id"], worker_id=task.get("worker_id"))
        missing_final = not self._has_master_records_final(task)
        recovery_id = self._admit_recovery(registry, task, epoch, events) if missing_final else None
        self._release_worker(registry, task)
        task["heartbeat_timing"] = None
        task["archive_eligible"] = False
        if recovery_id:
            task["state"] = "BLOCKED"
            task["block_ref"] = f"handoffs/generated/{recovery_id}.json"
            task["archive_reason_codes"] = ["KNOWN_EXPIRY_REACHED", "MASTER_RECORDS_FINAL_WORKER_REPORT_MISSING", "RECOVERY_RECONCILIATION_REQUIRED"]
            self._event(events, epoch, "expired_parent_blocked_on_recovery", task_id=task["task_id"], recovery_task_id=recovery_id)
        else:
            task["state"] = "HANDOFF_READY"
            task["archive_reason_codes"] = ["KNOWN_EXPIRY_REACHED", "HANDOFF_REACQUISITION_REQUIRED"]

    def _invoke(self, registry: dict[str, Any], task: dict[str, Any], epoch: int, cost_log: dict[str, Any], events: list[dict[str, Any]]) -> None:
        timing = task.get("heartbeat_timing") or {}
        expiry_epoch = timing.get("expiry_epoch")
        if expiry_epoch is not None and epoch >= int(expiry_epoch):
            self._expire(registry, task, epoch, events)
            return

        worker = next((item for item in registry.get("workers", []) if item.get("worker_id") == task.get("worker_id")), None)
        adapter_ref = worker.get("adapter_ref") if worker else None
        adapter = self.adapters.get(adapter_ref) if adapter_ref else None
        if adapter is None:
            self._event(events, epoch, "worker_response_missing", task_id=task["task_id"], worker_id=task.get("worker_id"))
            return

        response = adapter(task, self._handoff(task), epoch)
        if response.state not in self.RESPONSE_STATES:
            raise ValueError(f"unsupported worker response state: {response.state}")

        previous_transition = timing.get("current_transition")
        timing["last_response_epoch"] = epoch
        if response.transition_id != previous_transition:
            timing["last_transition_epoch"] = epoch
        timing["current_transition"] = response.transition_id
        timing["transition_sequence"] = response.transition_sequence
        timing["expected_next_transition"] = response.expected_next_transition
        timing["expected_next_earliest_epoch"] = response.expected_next_earliest_epoch
        timing["expected_next_latest_epoch"] = response.expected_next_latest_epoch
        task["heartbeat_timing"] = timing
        if response.checkpoint_ref:
            task["last_checkpoint_ref"] = response.checkpoint_ref
        for ref in response.evidence_refs:
            if ref not in task.setdefault("evidence_refs", []):
                task["evidence_refs"].append(ref)
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
            task["heartbeat_timing"] = None
            self._release_worker(registry, task)
        else:
            task["state"] = response.state

    def _activate_one(self, registry: dict[str, Any], epoch: int, cost_log: dict[str, Any], events: list[dict[str, Any]]) -> bool:
        by_id = {task["task_id"]: task for task in registry.get("tasks", [])}
        ready = [
            task for task in registry.get("tasks", [])
            if task.get("state") == "HANDOFF_READY" and self._dependencies_complete(task, by_id)
        ]
        ready.sort(key=lambda task: (self.PRIORITY.get(self._handoff(task).get("task", {}).get("priority", "normal"), 4), task["task_id"]))

        for task in ready:
            handoff = self._handoff(task)
            self._activation_request(registry, task, handoff, epoch, events)
            if not self._execution_authorized(handoff):
                task["archive_reason_codes"] = sorted(set(task.get("archive_reason_codes", []) + ["EXECUTION_AUTHORIZATION_REQUIRED"]))
                self._event(events, epoch, "activation_deferred", task_id=task["task_id"], reason="EXECUTION_AUTHORIZATION_REQUIRED")
                continue

            budget, expiry_basis = self._expiry_budget(task)
            if budget is None:
                task["archive_reason_codes"] = sorted(set(task.get("archive_reason_codes", []) + ["EXPIRY_BASIS_UNAVAILABLE"]))
                self._event(events, epoch, "activation_deferred", task_id=task["task_id"], reason="EXPIRY_BASIS_UNAVAILABLE")
                continue
            worker = self._worker_for(task, registry)
            if worker is None:
                task["archive_reason_codes"] = sorted(set(task.get("archive_reason_codes", []) + ["EXECUTOR_NOT_RESOLVED"]))
                self._event(events, epoch, "activation_deferred", task_id=task["task_id"], reason="EXECUTOR_NOT_RESOLVED")
                continue

            generation = int(registry.get("generation", 0)) + 1
            registry["generation"] = generation
            claim_id = f"SHWP-{task['task_id']}-G{generation}"
            task.update({
                "state": "ACTIVE",
                "executor_binding": "BOUND",
                "worker_id": worker["worker_id"],
                "worker_instance_id": f"{worker['worker_id']}-HB{epoch}-G{generation}",
                "claim_id": claim_id,
                "archive_eligible": False,
                "archive_reason_codes": [],
                "block_ref": None,
                "heartbeat_timing": {
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
                    "expiry_basis": expiry_basis,
                    "fencing_token": generation
                }
            })
            worker["status"] = "BUSY"
            worker["last_seen_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            self._event(events, epoch, "worker_activated", task_id=task["task_id"], worker_id=worker["worker_id"], claim_id=claim_id, fencing_token=generation, authorization_ref=handoff["activation"]["authorization_ref"], expiry_epoch=epoch + budget, expiry_basis=expiry_basis)
            self._invoke(registry, task, epoch, cost_log, events)
            return True
        return False

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
            events: list[dict[str, Any]] = []

            # All currently active workers answer this same heartbeat first.
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
                "schema": "stegverse.heartbeat-cycle-result/v0.2",
                "epoch": epoch,
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
