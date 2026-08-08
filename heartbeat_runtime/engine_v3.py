from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json
import math

from .engine_v2 import HeartbeatRuntime as HeartbeatRuntimeV2, WorkerResponse
from .org_assertions import issue_claim_assertions


class HeartbeatRuntime(HeartbeatRuntimeV2):
    """Single StegVerse heartbeat runtime with organization assertion issuance.

    This is the sole epoch-owning runtime. Organization claim assertions,
    worker transition timing, response-loss detection, authority expiry, renewal,
    and worker-registry evaluation are all measured on this same heartbeat
    sequence. No second worker heartbeat or scheduler clock exists here.
    """

    def _scope_sha256(self, handoff: dict[str, Any]) -> str:
        execution = handoff.get("execution") or {}
        value = {
            "required_capabilities": execution.get("required_capabilities") or [],
            "allowed_paths": execution.get("allowed_paths") or [],
            "allowed_services": execution.get("allowed_services") or [],
            "allowed_contracts": execution.get("allowed_contracts") or [],
            "allowed_release_surfaces": execution.get("allowed_release_surfaces") or [],
            "allowed_workflows": execution.get("allowed_workflows") or [],
        }
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    def _apply_admitted_renewal(
        self,
        task: dict[str, Any],
        handoff: dict[str, Any],
        epoch: int,
        events: list[dict[str, Any]],
    ) -> bool:
        renewal_ref = task.get("renewal_ref")
        if not renewal_ref:
            return False
        path = self.root / renewal_ref
        if not path.exists():
            self._event(events, epoch, "authorization_renewal_rejected", task_id=task["task_id"], reason="RENEWAL_RECORD_MISSING", renewal_ref=renewal_ref)
            return False
        try:
            renewal = self._load(path)
        except Exception:
            self._event(events, epoch, "authorization_renewal_rejected", task_id=task["task_id"], reason="RENEWAL_RECORD_INVALID", renewal_ref=renewal_ref)
            return False

        timing = task.get("heartbeat_timing") or {}
        expiry = timing.get("expiry_epoch")
        fence = timing.get("fencing_token")
        authority = handoff.get("authority") or {}
        valid = all([
            renewal.get("schema") == "stegverse.worker-renewal-admission/v0.1",
            renewal.get("status") == "ADMITTED",
            renewal.get("heartbeat_grants_renewal") is False,
            renewal.get("task_id") == task.get("task_id"),
            renewal.get("claim_id") == task.get("claim_id"),
            renewal.get("fencing_token") == fence,
            renewal.get("prior_expiry_epoch") == expiry,
            isinstance(renewal.get("additional_beats"), int) and renewal.get("additional_beats", 0) > 0,
            renewal.get("scope_sha256") == self._scope_sha256(handoff),
            renewal.get("authority_source") == authority.get("authority_source"),
            renewal.get("policy_version") == authority.get("policy_version"),
            isinstance(expiry, int) and epoch <= expiry,
        ])
        if not valid:
            self._event(events, epoch, "authorization_renewal_rejected", task_id=task["task_id"], reason="RENEWAL_BINDING_MISMATCH", renewal_ref=renewal_ref)
            return False

        additional = int(renewal["additional_beats"])
        timing["expiry_epoch"] = int(expiry) + additional
        timing["renewal_count"] = int(timing.get("renewal_count", 0)) + 1
        task["heartbeat_timing"] = timing
        task["renewal_ref"] = None
        if renewal_ref not in task.setdefault("evidence_refs", []):
            task["evidence_refs"].append(renewal_ref)
        self._event(
            events,
            epoch,
            "authorization_renewed",
            task_id=task["task_id"],
            claim_id=task.get("claim_id"),
            fencing_token=fence,
            renewal_ref=renewal_ref,
            prior_expiry_epoch=expiry,
            new_expiry_epoch=timing["expiry_epoch"],
            heartbeat_granted_renewal=False,
        )
        return True

    def _admit_orphan_recovery(
        self,
        registry: dict[str, Any],
        parent: dict[str, Any],
        epoch: int,
        events: list[dict[str, Any]],
    ) -> str:
        task_id = f"RECOVER-{parent['task_id']}-ORPHAN-HB{epoch}"
        existing = next((item for item in registry.get("tasks", []) if item.get("task_id") == task_id), None)
        if existing:
            return task_id

        parent_handoff = self._handoff(parent)
        handoff_ref = f"handoffs/generated/{task_id}.json"
        generated = {
            "schema": "stegverse.executable-handoff/v0.1",
            "handoff_id": f"HANDOFF-{task_id}",
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "state": "HANDOFF_READY",
            "goal": {
                "goal_id": task_id,
                "objective": "Reconstruct and recover work after the prior worker stopped returning expected transition information to the single StegVerse heartbeat.",
                "success_predicates": [
                    "Prior lifecycle is reconstructed from durable checkpoint and evidence",
                    "Old worker instance authority remains ended",
                    "Any successor acquisition uses a higher fencing generation"
                ],
                "failure_predicates": [
                    "Missing response is treated as a second heartbeat clock",
                    "Old claim or fence is reused",
                    "Successor acquires authority without reconstruction"
                ],
                "expires_at": None,
                "authority_ceiling": list((parent_handoff.get("goal") or {}).get("authority_ceiling") or [])
            },
            "task": {
                "task_id": task_id,
                "repository": (parent_handoff.get("task") or {}).get("repository", "StegVerse-Labs/.github"),
                "source_refs": [parent["handoff_ref"], parent.get("last_checkpoint_ref") or parent["task_id"]],
                "dependencies": [],
                "parent_task_id": parent["task_id"],
                "derivation_reason": "Expected worker response threshold exceeded on the common heartbeat sequence.",
                "priority": "critical"
            },
            "authority": {
                "authority_source": (parent_handoff.get("authority") or {}).get("authority_source", "StegVerse-Labs/.github#12 orphan recovery policy"),
                "heartbeat_grants_execution_authority": False,
                "policy_version": (parent_handoff.get("authority") or {}).get("policy_version", "shwp-single-hb-v0.2")
            },
            "execution": dict(parent_handoff.get("execution") or {}),
            "activation": {
                "carrier": "heartbeat",
                "executor_binding": "UNBOUND",
                "recheck_trigger": "each heartbeat after reconstruction and separate authorization are durable",
                "checkout_policy": "fenced_atomic_checkout"
            },
            "continuity": {
                "checkpoint_ref": parent.get("last_checkpoint_ref"),
                "handoff_destination": "control/worker-registry.json",
                "master_records_required": True,
                "status_projection": "control/worker-status.json"
            },
            "completion": {
                "next_authorized_action": "Create a PASS reconstruction proof from the last valid checkpoint plus Master Records evidence, then separately authorize successor acquisition.",
                "terminal_when": [
                    "Reconstruction proof is durable",
                    "Successor claim uses a higher fence or work is safely terminated"
                ]
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
            "renewal_ref": None,
            "cost_basis_ref": parent.get("cost_basis_ref"),
            "external_entity_job_ref": parent.get("external_entity_job_ref"),
            "last_checkpoint_ref": parent.get("last_checkpoint_ref"),
            "block_ref": None,
            "archive_eligible": False,
            "archive_reason_codes": ["ORPHAN_RECOVERY_REQUIRED", "SUCCESSOR_RECONSTRUCTION_REQUIRED", "EXECUTOR_NOT_BOUND"],
            "evidence_refs": [parent["task_id"], f"heartbeat-epoch:{epoch}", "WORKER_RESPONSE_THRESHOLD_EXCEEDED"]
        })
        self._event(events, epoch, "orphan_recovery_task_admitted", task_id=task_id, parent_task_id=parent["task_id"])
        return task_id

    def _observe_missing_response(
        self,
        registry: dict[str, Any],
        task: dict[str, Any],
        epoch: int,
        events: list[dict[str, Any]],
        reason: str,
    ) -> None:
        timing = task.get("heartbeat_timing") or {}
        last_response = int(timing.get("last_response_epoch", timing.get("start_epoch", epoch)))
        delta = max(0, epoch - last_response)
        threshold = max(1, int(timing.get("max_missing_response_beats", 1)))
        self._event(
            events,
            epoch,
            "worker_response_missing",
            task_id=task["task_id"],
            worker_id=task.get("worker_id"),
            delta_hb_since_response=delta,
            threshold_beats=threshold,
            reason=reason,
        )
        worker = next((item for item in registry.get("workers", []) if item.get("worker_id") == task.get("worker_id")), None)
        if worker is not None and worker.get("status") != "DISABLED":
            worker["status"] = "DEGRADED"
        if delta < threshold:
            task["archive_reason_codes"] = sorted(set(task.get("archive_reason_codes", []) + ["WORKER_RESPONSE_MISSING_OBSERVED"]))
            return

        recovery_id = self._admit_orphan_recovery(registry, task, epoch, events)
        old_claim = task.get("claim_id")
        old_worker_instance = task.get("worker_instance_id")
        old_fence = timing.get("fencing_token")
        self._release_worker(registry, task)
        task["state"] = "BLOCKED"
        task["block_ref"] = f"handoffs/generated/{recovery_id}.json"
        task["archive_eligible"] = False
        task["archive_reason_codes"] = ["WORKER_ORPHANED", "OLD_AUTHORITY_RELEASED", "RECOVERY_RECONSTRUCTION_REQUIRED"]
        self._event(
            events,
            epoch,
            "worker_orphaned",
            task_id=task["task_id"],
            recovery_task_id=recovery_id,
            released_claim_id=old_claim,
            released_worker_instance_id=old_worker_instance,
            last_valid_fencing_token=old_fence,
        )

    def _invoke(self, registry: dict[str, Any], task: dict[str, Any], epoch: int, cost_log: dict[str, Any], events: list[dict[str, Any]]) -> None:
        handoff = self._handoff(task)
        self._apply_admitted_renewal(task, handoff, epoch, events)
        timing = task.get("heartbeat_timing") or {}
        expiry_epoch = timing.get("expiry_epoch")
        if expiry_epoch is not None and epoch >= int(expiry_epoch):
            # Authority expiry has priority at its admitted epoch. This is still
            # measured on the same heartbeat sequence as response timing.
            super()._invoke(registry, task, epoch, cost_log, events)
            return

        worker = next((item for item in registry.get("workers", []) if item.get("worker_id") == task.get("worker_id")), None)
        adapter_ref = worker.get("adapter_ref") if worker else None
        adapter = self.adapters.get(adapter_ref) if adapter_ref else None
        if adapter is None:
            self._observe_missing_response(registry, task, epoch, events, "EXECUTOR_RESPONSE_UNAVAILABLE")
            return
        try:
            super()._invoke(registry, task, epoch, cost_log, events)
        except Exception as exc:
            self._observe_missing_response(registry, task, epoch, events, f"EXECUTOR_RESPONSE_ERROR:{type(exc).__name__}")
            return

        # A valid response on this same heartbeat clears degraded observation;
        # it never changes authority expiry unless an admitted renewal above did.
        current_timing = task.get("heartbeat_timing") or {}
        if current_timing.get("last_response_epoch") == epoch:
            task["archive_reason_codes"] = [
                code for code in task.get("archive_reason_codes", [])
                if code != "WORKER_RESPONSE_MISSING_OBSERVED"
            ]
            current_worker = next((item for item in registry.get("workers", []) if item.get("worker_id") == task.get("worker_id")), None)
            if current_worker is not None and current_worker.get("status") == "DEGRADED":
                current_worker["status"] = "BUSY"

    def _activate_one(self, registry: dict[str, Any], epoch: int, cost_log: dict[str, Any], events: list[dict[str, Any]]) -> bool:
        activated = super()._activate_one(registry, epoch, cost_log, events)
        if not activated:
            return False
        # Response-loss tolerance and authority expiry are distinct HB-relative
        # thresholds on the same epoch sequence. Response loss is intentionally
        # earlier so orphan recovery can occur before authority expiry.
        for task in registry.get("tasks", []):
            timing = task.get("heartbeat_timing") or {}
            if timing.get("start_epoch") != epoch:
                continue
            expiry = timing.get("expiry_epoch")
            if not isinstance(expiry, int):
                continue
            authority_budget = max(1, expiry - epoch)
            timing["max_missing_response_beats"] = max(1, min(3, int(math.ceil(authority_budget / 2))))
            timing.setdefault("renewal_count", 0)
            task["heartbeat_timing"] = timing
        return True

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
