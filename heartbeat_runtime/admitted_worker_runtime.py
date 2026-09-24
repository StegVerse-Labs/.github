"""Canonical WorkerCoordinator wrapper with mandatory pre-initiation packet review."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .coordination_graph import review_coordination_preflight
from .coordination_ledger import load_composed_coordination_ledger
from .worker_runtime_legacy import WorkerCoordinator as LegacySeparatedWorkerCoordinator, ProcessWorkerAdapter
from .hil_legacy_registration_reconcile import reconcile_legacy_hil_registration, FRAGMENT as HIL_FRAGMENT
from .worker_task_admission import persist_admission_receipt, review_worker_task_admission
from .worker_assignment_functional_memory import (
    allow_manifest_context,
    bind_assignment_review,
    record_non_allow_functional_memory,
    reconstruct_prior_functional_memory,
)


class WorkerCoordinator(LegacySeparatedWorkerCoordinator):
    """Require fresh fail-closed coordination and task-admission review.

    Cross-task coordination is mandatory for autonomous augmentation. Neither
    coordination review nor task-admission review grants authority. Only passing
    reviews permit the existing separated WorkerCoordinator to continue into
    assignment/claim/fence/timer creation under authority it independently verifies.
    """

    def _apply_registry_fragments(
        self,
        registry: dict[str, Any],
        task_id_filter: str | None = None,
    ) -> list[str]:
        """Apply append-only fragments plus bounded preclaim static reconciliation.

        The inherited fragment loader never overwrites existing task/worker IDs.
        That protects live claims, fences, timing, leases, receipts, and worker
        lifecycle state. Before any claim exists, an unclaimed HANDOFF_READY task
        may reconcile only static declarations that would otherwise remain stale
        forever after source refresh:

        - authorized_policy_version, when fragment and canonical handoff agree;
        - an already-existing AVAILABLE worker's capabilities/profile, when the
          worker identity, adapter, executor type, and authority source are
          unchanged and the fragment satisfies the handoff's required capabilities.

        No new worker identity, assignment, claim, fence, timing, lease, credential,
        execution, transition, or custody authority is created here.
        """
        generation_before = int(registry.get("generation", 0))
        applied = super()._apply_registry_fragments(registry, task_id_filter=task_id_filter)
        legacy_hil_reconciled = (
            task_id_filter in (None, "SHWP-HIL-SOVEREIGN-RECEIVER-001")
            and reconcile_legacy_hil_registration(self.root, registry)
        )
        if legacy_hil_reconciled and HIL_FRAGMENT.as_posix() not in applied:
            applied.append(HIL_FRAGMENT.as_posix())
        tasks = {
            str(item.get("task_id")): item
            for item in registry.get("tasks", [])
            if isinstance(item, dict) and item.get("task_id")
        }
        workers = {
            str(item.get("worker_id")): item
            for item in registry.get("workers", [])
            if isinstance(item, dict) and item.get("worker_id")
        }
        reconciled = bool(legacy_hil_reconciled)

        if not self.registry_fragment_dir.is_dir():
            return applied

        for path in sorted(self.registry_fragment_dir.glob("*.json")):
            fragment_reconciled = False
            fragment = self._load(path)
            if fragment.get("schema") != "stegverse.worker-registry-fragment/v0.1":
                continue
            fragment_ref = str(path.relative_to(self.root))
            for declared in fragment.get("tasks", []):
                if not isinstance(declared, dict):
                    continue
                task_id = declared.get("task_id")
                if not isinstance(task_id, str) or not task_id:
                    continue
                if task_id_filter is not None and task_id != task_id_filter:
                    continue
                current = tasks.get(task_id)
                if not isinstance(current, dict):
                    continue

                # Never reconcile live or previously bound lifecycle state.
                if current.get("state") != "HANDOFF_READY":
                    continue
                if any(current.get(key) not in (None, "") for key in ("claim_id", "worker_id", "worker_instance_id")):
                    continue
                if current.get("heartbeat_timing") not in (None, {}):
                    continue
                if current.get("assignment_timer") not in (None, {}):
                    continue
                if current.get("lease") not in (None, {}):
                    continue

                current_handoff = current.get("handoff_ref")
                fragment_handoff = declared.get("handoff_ref")
                if not isinstance(current_handoff, str) or current_handoff != fragment_handoff:
                    continue
                handoff_path = self.root / current_handoff
                if not handoff_path.is_file():
                    raise RuntimeError(f"preclaim reconciliation handoff missing for {task_id}")
                handoff = self._load(handoff_path)

                fragment_policy = declared.get("authorized_policy_version")
                canonical_policy = str((handoff.get("authority") or {}).get("policy_version") or "")
                if not isinstance(fragment_policy, str) or not fragment_policy:
                    continue
                if not canonical_policy or fragment_policy != canonical_policy:
                    raise RuntimeError(f"preclaim policy reconciliation mismatch for {task_id}")
                if current.get("authorized_policy_version") != canonical_policy:
                    old_policy = current.get("authorized_policy_version")
                    current["authorized_policy_version"] = canonical_policy
                    current["preclaim_policy_reconciliation"] = {
                        "state": "RECONCILED_BEFORE_CLAIM",
                        "old_policy_version": old_policy,
                        "new_policy_version": canonical_policy,
                        "fragment_ref": fragment_ref,
                        "handoff_ref": current_handoff,
                        "claim_authority_effect": False,
                        "fence_authority_effect": False,
                        "execution_authority_effect": False,
                    }
                    reconciled = True
                    fragment_reconciled = True

                required = set((handoff.get("execution") or {}).get("required_capabilities") or [])
                for declared_worker in fragment.get("workers", []):
                    if not isinstance(declared_worker, dict):
                        continue
                    worker_id = declared_worker.get("worker_id")
                    if not isinstance(worker_id, str) or not worker_id:
                        continue
                    current_worker = workers.get(worker_id)
                    if not isinstance(current_worker, dict):
                        continue
                    if current_worker.get("status") != "AVAILABLE":
                        continue
                    if any(
                        current_worker.get(key) != declared_worker.get(key)
                        for key in ("adapter_ref", "executor_type", "authority_source")
                    ):
                        continue
                    declared_capabilities = set(declared_worker.get("capabilities") or [])
                    if not required.issubset(declared_capabilities):
                        continue
                    declared_profile = declared_worker.get("capability_profile_ref")
                    if not isinstance(declared_profile, str) or not declared_profile:
                        continue
                    old_capabilities = list(current_worker.get("capabilities") or [])
                    old_profile = current_worker.get("capability_profile_ref")
                    new_capabilities = list(declared_worker.get("capabilities") or [])
                    if old_capabilities == new_capabilities and old_profile == declared_profile:
                        continue
                    current_worker["capabilities"] = new_capabilities
                    current_worker["capability_profile_ref"] = declared_profile
                    current["preclaim_worker_registration_reconciliation"] = {
                        "state": "RECONCILED_BEFORE_CLAIM",
                        "worker_id": worker_id,
                        "old_capabilities": old_capabilities,
                        "new_capabilities": new_capabilities,
                        "old_capability_profile_ref": old_profile,
                        "new_capability_profile_ref": declared_profile,
                        "fragment_ref": fragment_ref,
                        "handoff_ref": current_handoff,
                        "worker_identity_changed": False,
                        "adapter_changed": False,
                        "authority_source_changed": False,
                        "claim_authority_effect": False,
                        "fence_authority_effect": False,
                        "execution_authority_effect": False,
                    }
                    reconciled = True
                    fragment_reconciled = True

                if fragment_reconciled and fragment_ref not in applied:
                    applied.append(fragment_ref)

        if reconciled and int(registry.get("generation", 0)) == generation_before:
            registry["generation"] = generation_before + 1
        return applied

    def _coordination_review(
        self,
        task: dict[str, Any],
        carrier_epoch: int,
        events: list[dict[str, Any]],
    ) -> bool:
        root = Path(self.root)
        ledger_path = root / "control" / "cross-task-coordination.json"
        ledger: dict[str, Any] | None = None
        if ledger_path.exists():
            try:
                ledger = load_composed_coordination_ledger(ledger_path)
            except Exception as exc:
                self._event(
                    events,
                    carrier_epoch,
                    "cross_task_coordination_blocked",
                    task_id=task.get("task_id"),
                    reason="COORDINATION_LEDGER_UNREADABLE",
                    detail=type(exc).__name__,
                    authority_effect=False,
                )
                return False

        ledger_task = None
        if ledger is not None:
            ledger_task = next(
                (item for item in ledger.get("tasks", []) if item.get("task_id") == task.get("task_id")),
                None,
            )
        autonomous = bool(task.get("autonomous_augmentation")) or bool(
            isinstance(ledger_task, dict) and ledger_task.get("autonomous_augmentation")
        )
        if not autonomous:
            return True

        if ledger is None:
            self._event(
                events,
                carrier_epoch,
                "cross_task_coordination_blocked",
                task_id=task.get("task_id"),
                reason="COORDINATION_LEDGER_REQUIRED_FOR_AUTONOMOUS_AUGMENTATION",
                authority_effect=False,
            )
            task["last_coordination_preflight"] = {
                "verdict": "BLOCK_COORDINATION",
                "reasons": ["COORDINATION_LEDGER_REQUIRED_FOR_AUTONOMOUS_AUGMENTATION"],
                "authority_effect": "NONE",
            }
            return False

        preflight = review_coordination_preflight(ledger=ledger, task=task)
        receipt_ref = None
        if self._persist:
            task_id = str(task.get("task_id") or "UNKNOWN").replace("/", "_")
            receipt = root / "receipts" / "cross-task-coordination" / f"{task_id}-hb{int(carrier_epoch):08d}.json"
            receipt.parent.mkdir(parents=True, exist_ok=True)
            receipt.write_text(json.dumps(preflight, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            receipt_ref = str(receipt.relative_to(root))

        self._event(
            events,
            carrier_epoch,
            "cross_task_coordination_reviewed",
            task_id=task.get("task_id"),
            verdict=preflight.get("verdict"),
            reasons=preflight.get("reasons"),
            collision_claims=[item.get("claim_id") for item in preflight.get("collisions", [])],
            newly_unblocked_tasks=preflight.get("newly_unblocked_tasks", []),
            coordination_receipt_ref=receipt_ref,
            authority_effect=False,
        )
        task["last_coordination_preflight"] = {
            "verdict": preflight.get("verdict"),
            "reasons": preflight.get("reasons"),
            "receipt_ref": receipt_ref,
            "authority_effect": "NONE",
        }
        if preflight.get("verdict") != "ADMIT_COORDINATION":
            task["reconciliation_disposition"] = "BLOCK_COORDINATION"
            task["reconciliation_reason"] = ",".join(preflight.get("reasons") or [])
            return False
        return True

    def _activate_from_trigger(
        self,
        registry: dict[str, Any],
        trigger: dict[str, Any],
        carrier_epoch: int,
        cost_log: dict[str, Any],
        events: list[dict[str, Any]],
    ) -> bool:
        task_id = trigger.get("task_id")
        task = next((item for item in registry.get("tasks", []) if item.get("task_id") == task_id), None)
        if task is None:
            self._event(events, carrier_epoch, "worker_task_admission_blocked", task_id=task_id, reason="TASK_NOT_FOUND", authority_effect=False)
            return False

        if not self._coordination_review(task, carrier_epoch, events):
            return False

        try:
            handoff = self._handoff(task)
        except Exception as exc:
            self._event(events, carrier_epoch, "worker_task_admission_blocked", task_id=task_id, reason="HANDOFF_UNREADABLE", detail=type(exc).__name__, authority_effect=False)
            return False

        state_current, _ = self._semantic_state_preclaim(task)
        by_id = {item["task_id"]: item for item in registry.get("tasks", []) if item.get("task_id")}
        dependencies_complete = self._dependencies_complete(task, by_id)
        execution_authorized = self._execution_authorized(handoff)
        worker_resolved = self._worker_for(task, registry) is not None
        source = str(trigger.get("source") or "HEARTBEAT_CARRIER_OBSERVATION")
        prior_memory, prior_memory_valid, prior_memory_reason = reconstruct_prior_functional_memory(task)
        if not prior_memory_valid:
            task["reconciliation_disposition"] = "FUNCTIONAL_MEMORY_RECONSTRUCTION_BOUNDARY"
            task["reconciliation_reason"] = str(prior_memory_reason or "FUNCTIONAL_MEMORY_RECONSTRUCTION_FAILED")
            self._event(
                events,
                carrier_epoch,
                "worker_assignment_functional_memory_reconstruction_blocked",
                task_id=task_id,
                packet_id=trigger.get("packet_id"),
                reason=task["reconciliation_reason"],
                successor_functional_memory_emitted=False,
                worker_materialized=False,
                claim_minted=False,
                fence_minted=False,
                authority_effect=False,
            )
            return False

        packet = review_worker_task_admission(
            root=Path(self.root),
            task=task,
            handoff=handoff,
            registry=registry,
            carrier_epoch=carrier_epoch,
            trigger_source=source,
            execution_authorized=execution_authorized,
            dependencies_complete=dependencies_complete,
            worker_resolved=worker_resolved,
            semantic_state_current=state_current,
        )
        packet = bind_assignment_review(
            root=Path(self.root),
            task=task,
            packet=packet,
            prior_memory=prior_memory,
            prior_memory_valid=prior_memory_valid,
            prior_memory_reason=prior_memory_reason,
        )
        receipt_ref = None
        if self._persist:
            receipt = persist_admission_receipt(Path(self.root), packet)
            receipt_ref = str(receipt.relative_to(Path(self.root)))
        verdict = packet["review"]["verdict"]
        self._event(
            events,
            carrier_epoch,
            "worker_task_admission_reviewed",
            task_id=task_id,
            packet_id=trigger.get("packet_id"),
            heartbeat_id=packet["heartbeat_id"],
            admission_packet_sha256=packet["packet_sha256"],
            admission_receipt_ref=receipt_ref,
            verdict=verdict,
            admissibility_resolution=packet["assignment_transition"]["admissibility_resolution"],
            reasons=packet["review"]["reasons"],
            functional_memory_consumed=packet["assignment_transition"]["prior_functional_memory_consumed"],
            authority_effect=False,
        )
        task["last_worker_task_admission"] = {
            "verdict": verdict,
            "packet_sha256": packet["packet_sha256"],
            "heartbeat_id": packet["heartbeat_id"],
            "receipt_ref": receipt_ref,
            "assignment_transition": packet["assignment_transition"],
            "authority_effect": "NONE",
        }
        if verdict != "ADMIT":
            memory = record_non_allow_functional_memory(task=task, trigger=trigger, packet=packet)
            task["reconciliation_disposition"] = verdict
            task["reconciliation_reason"] = ",".join(packet["review"]["reasons"])
            if memory.get("state") != "RECORDED":
                task["reconciliation_disposition"] = "MASTER_RECORDS_BOUNDARY"
                task["reconciliation_reason"] = str(memory.get("reason") or "FUNCTIONAL_MEMORY_MASTER_RECORDS_CUSTODY_INCOMPLETE")
                self._event(
                    events,
                    carrier_epoch,
                    "worker_assignment_functional_memory_blocked",
                    task_id=task_id,
                    packet_id=trigger.get("packet_id"),
                    verdict=verdict,
                    admissibility_resolution=packet["assignment_transition"]["admissibility_resolution"],
                    reason=task["reconciliation_reason"],
                    authority_effect=False,
                )
                return False
            task["functional_memory"] = memory
            self._event(
                events,
                carrier_epoch,
                "worker_assignment_functional_memory_recorded",
                task_id=task_id,
                packet_id=trigger.get("packet_id"),
                verdict=verdict,
                admissibility_resolution=memory.get("admissibility_resolution"),
                task_registry_generation=memory.get("task_registry_generation"),
                generation_bound_cosv_id=memory.get("generation_bound_cosv_id"),
                master_records_receipt_sha256=memory.get("receipt_sha256"),
                master_record_ref=memory.get("master_record_ref"),
                authority_effect=False,
            )
            return False

        trigger = dict(trigger)
        trigger["functional_memory_context"] = allow_manifest_context(packet, task)
        return super()._activate_from_trigger(registry, trigger, carrier_epoch, cost_log, events)


__all__ = ["WorkerCoordinator", "ProcessWorkerAdapter"]
