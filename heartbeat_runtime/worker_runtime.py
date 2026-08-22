"""Worker lifecycle coordinator separated from the heartbeat carrier.

The heartbeat provides a reference frame only. This coordinator owns worker
lifecycle under already-admitted task authority and never increments or writes
the heartbeat carrier state. Independently admitted HANDOFF_READY tasks do not
need a heartbeat-emitted event before lawful task-control acquisition.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

from state_language import preclaim_revalidate

from .engine_v11 import HeartbeatRuntime as LegacyWorkerCoordinator, WorkerResponse
from .process_adapter import ProcessWorkerAdapter
from .assignment_timer import (
    AssignmentTimer,
    TRIGGER_SCHEMA,
    bind_assignment_from_trigger,
    independent_task_control_packet,
)


class WorkerCoordinator(LegacyWorkerCoordinator):
    """Control-plane worker runtime synchronized to, but not controlled by, HB.

    Carrier packets remain a compatibility observation path. A HANDOFF_READY task
    that is explicitly admitted under INDEPENDENT_TASK_CONTROL can instead enter
    the same worker-selection, fencing, timer, and Master Records custody path
    directly. The observed carrier epoch is context only and grants no execution,
    claim, fence, timer, route, credential, or lifecycle authority.
    """

    def __init__(self, root: str | Path, adapters: dict | None = None):
        super().__init__(root, adapters=adapters)
        self.lock_path = self.root / "control" / ".worker-runtime.lock"
        self.carrier_state_path = self.root / "control" / "heartbeat-carrier-runtime-state.json"
        self.worker_runtime_state_path = self.root / "control" / "worker-runtime-state.json"
        self.worker_event_path = self.root / "events" / "worker-runtime.jsonl"
        self.assignment_record_path = self.root / "events" / "master-records-worker-assignment.jsonl"
        self.carrier_event_path = self.root / "events" / "heartbeat-runtime.jsonl"

    def _carrier_reference(self) -> tuple[int, int]:
        if not self.carrier_state_path.exists():
            raise RuntimeError("separated heartbeat carrier state is required before worker coordination")
        value = self._load(self.carrier_state_path)
        if value.get("schema") != "stegverse.heartbeat-carrier-runtime-state/v1":
            raise RuntimeError("worker coordinator requires separated heartbeat carrier schema")
        epoch = value.get("epoch")
        generation = value.get("generation")
        if not isinstance(epoch, int) or not isinstance(generation, int):
            raise RuntimeError("carrier reference is incomplete")
        return epoch, generation

    def _load_runtime_state(self) -> dict[str, Any]:
        if self.worker_runtime_state_path.exists():
            value = self._load(self.worker_runtime_state_path)
            if value.get("schema") != "stegverse.worker-runtime-state/v1":
                raise RuntimeError("unsupported worker runtime state schema")
            return value
        return {
            "schema": "stegverse.worker-runtime-state/v1",
            "runtime_tick": 0,
            "last_observed_carrier_epoch": None,
            "last_observed_carrier_generation": None,
            "seen_assignment_packet_ids": [],
            "carrier_controls_timer": False,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
        }

    def _trigger_packets(self, seen: set[str], carrier_epoch: int) -> list[dict[str, Any]]:
        if not self.carrier_event_path.exists():
            return []
        packets: list[dict[str, Any]] = []
        with self.carrier_event_path.open("r", encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("event_type") != "worker_assignment_trigger_carried":
                    continue
                packet = event.get("packet") or {}
                packet_id = packet.get("packet_id")
                if packet.get("schema") != TRIGGER_SCHEMA or not isinstance(packet_id, str):
                    continue
                if packet_id in seen:
                    continue
                packet_epoch = packet.get("carrier_epoch")
                if not isinstance(packet_epoch, int) or packet_epoch > carrier_epoch:
                    continue
                packets.append(packet)
        packets.sort(key=lambda item: (int(item.get("carrier_epoch", 0)), str(item.get("task_id", "")), str(item.get("packet_id", ""))))
        return packets

    def _timer_from_task(self, task: dict[str, Any], carrier_epoch: int) -> AssignmentTimer | None:
        value = task.get("assignment_timer")
        if isinstance(value, dict) and value.get("schema") == "stegverse.worker-assignment-timer/v1":
            return AssignmentTimer(
                task_id=str(value["task_id"]),
                worker_id=str(value["worker_id"]),
                worker_instance_id=str(value["worker_instance_id"]),
                claim_id=str(value["claim_id"]),
                fencing_token=int(value["fencing_token"]),
                allocated_hb_units=int(value["allocated_hb_units"]),
                remaining_hb_units=int(value["remaining_hb_units"]),
                cost_basis_ref=value.get("cost_basis_ref"),
                expiry_basis=str(value.get("expiry_basis") or "TASK_CLASS_COST_BASIS"),
                runtime_tick=int(value.get("runtime_tick", 0)),
            )

        timing = task.get("heartbeat_timing") or {}
        required = (
            task.get("task_id"), task.get("worker_id"), task.get("worker_instance_id"),
            task.get("claim_id"), timing.get("fencing_token"), timing.get("start_epoch"), timing.get("expiry_epoch"),
        )
        if not all(value is not None for value in required):
            return None
        start = int(timing["start_epoch"])
        end = int(timing["expiry_epoch"])
        allocated = max(1, end - start)
        remaining = max(0, end - int(carrier_epoch))
        timer = AssignmentTimer(
            task_id=str(task["task_id"]),
            worker_id=str(task["worker_id"]),
            worker_instance_id=str(task["worker_instance_id"]),
            claim_id=str(task["claim_id"]),
            fencing_token=int(timing["fencing_token"]),
            allocated_hb_units=allocated,
            remaining_hb_units=remaining,
            cost_basis_ref=task.get("cost_basis_ref"),
            expiry_basis="MIGRATED_TASK_CLASS_COST_BASIS",
        )
        migrated = timer.as_dict()
        migrated["migrated_from_legacy_heartbeat_timing"] = True
        migrated["legacy_start_epoch"] = start
        migrated["legacy_expiry_epoch"] = end
        task["assignment_timer"] = migrated
        timing["expiry_epoch"] = None
        timing["expiry_basis"] = "WORKER_RUNTIME_ASSIGNMENT_TIMER"
        task["heartbeat_timing"] = timing
        return timer

    def _append_assignment_record(self, record: dict[str, Any]) -> None:
        if not self._persist:
            return
        self.assignment_record_path.parent.mkdir(parents=True, exist_ok=True)
        with self.assignment_record_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")

    def _semantic_state_preclaim(self, task: dict[str, Any]) -> tuple[bool, str]:
        """Revalidate only tasks explicitly bound to a local canonical state vector.

        Legacy tasks remain unaffected until their registry projection includes
        `source_state_vector_ref`. A bound reference must stay inside this repository
        root and the vector hash must still equal the task's `source_state_hash`.
        """
        state_ref = task.get("source_state_vector_ref")
        if state_ref is None:
            return True, "SEMANTIC_STATE_BINDING_NOT_PRESENT"
        if not isinstance(state_ref, str) or not state_ref.strip():
            return False, "TASK_SOURCE_STATE_VECTOR_REF_INVALID"
        candidate = (self.root / state_ref).resolve()
        try:
            candidate.relative_to(self.root.resolve())
        except ValueError:
            return False, "TASK_SOURCE_STATE_VECTOR_REF_OUTSIDE_ROOT"
        if not candidate.is_file():
            return False, "TASK_SOURCE_STATE_VECTOR_MISSING"
        try:
            canonical_state = self._load(candidate)
        except Exception:
            return False, "TASK_SOURCE_STATE_VECTOR_UNREADABLE"
        return preclaim_revalidate(task, canonical_state)

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
        if task is None or task.get("state") != "HANDOFF_READY" or task.get("worker_id") or task.get("claim_id"):
            self._event(events, carrier_epoch, "assignment_trigger_stale", task_id=task_id, packet_id=trigger.get("packet_id"), authority_effect=False)
            return False

        state_current, state_reason = self._semantic_state_preclaim(task)
        if not state_current:
            task["reconciliation_disposition"] = "ESCALATION_REQUIRED"
            task["reconciliation_reason"] = state_reason
            task["archive_reason_codes"] = sorted(set(task.get("archive_reason_codes", []) + [state_reason]))
            self._event(
                events,
                carrier_epoch,
                "worker_preclaim_state_revalidation_deferred",
                task_id=task_id,
                packet_id=trigger.get("packet_id"),
                reason=state_reason,
                source_state_hash=task.get("source_state_hash"),
                source_state_vector_ref=task.get("source_state_vector_ref"),
                authority_effect=False,
            )
            return False
        if task.get("source_state_vector_ref"):
            self._event(
                events,
                carrier_epoch,
                "worker_preclaim_state_revalidation_passed",
                task_id=task_id,
                packet_id=trigger.get("packet_id"),
                source_state_hash=task.get("source_state_hash"),
                source_state_vector_ref=task.get("source_state_vector_ref"),
                authority_effect=False,
            )

        source = str(trigger.get("source") or "HEARTBEAT_CARRIER_OBSERVATION")
        independent = source == "INDEPENDENT_TASK_CONTROL"
        admission = task.get("admission") or {}
        if independent:
            if (
                admission.get("authority_domain") != "INDEPENDENT_TASK_CONTROL"
                or admission.get("claim_state") != "AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM"
                or admission.get("heartbeat_grants_execution_authority") is not False
                or admission.get("fresh_fence_required") is not True
            ):
                self._event(events, carrier_epoch, "independent_assignment_deferred", task_id=task_id, packet_id=trigger.get("packet_id"), reason="INDEPENDENT_TASK_CONTROL_ADMISSION_INVALID", authority_effect=False)
                return False

        by_id = {item["task_id"]: item for item in registry.get("tasks", []) if item.get("task_id")}
        if not self._dependencies_complete(task, by_id):
            self._event(events, carrier_epoch, "assignment_trigger_deferred", task_id=task_id, packet_id=trigger.get("packet_id"), reason="DEPENDENCIES_INCOMPLETE", authority_effect=False)
            return False

        handoff = self._handoff(task)
        self._activation_request(registry, task, handoff, carrier_epoch, events)
        if not self._execution_authorized(handoff):
            task["archive_reason_codes"] = sorted(set(task.get("archive_reason_codes", []) + ["EXECUTION_AUTHORIZATION_REQUIRED"]))
            self._event(events, carrier_epoch, "assignment_trigger_deferred", task_id=task_id, packet_id=trigger.get("packet_id"), reason="EXECUTION_AUTHORIZATION_REQUIRED", authority_effect=False)
            return False

        reconstructed, reconstruction_reason, proof = self._successor_reconstruction(registry, handoff)
        if not reconstructed:
            task["archive_reason_codes"] = sorted(set(task.get("archive_reason_codes", []) + [str(reconstruction_reason)]))
            self._event(events, carrier_epoch, "assignment_trigger_deferred", task_id=task_id, packet_id=trigger.get("packet_id"), reason=reconstruction_reason, authority_effect=False)
            return False
        if proof is not None:
            self._event(events, carrier_epoch, "successor_reconstruction_accepted", task_id=task_id, parent_task_id=handoff["task"]["parent_task_id"], reconstruction_ref=handoff["continuity"]["reconstruction_ref"], last_valid_fencing_token=proof["last_valid_fencing_token"], checkpoint_ref=proof["checkpoint_ref"], authority_effect=False)

        budget, expiry_basis = self._expiry_budget(task)
        if budget is None:
            task["archive_reason_codes"] = sorted(set(task.get("archive_reason_codes", []) + ["EXPIRY_BASIS_UNAVAILABLE"]))
            self._event(events, carrier_epoch, "assignment_trigger_deferred", task_id=task_id, packet_id=trigger.get("packet_id"), reason="EXPIRY_BASIS_UNAVAILABLE", authority_effect=False)
            return False
        worker = self._worker_for(task, registry)
        if worker is None:
            task["archive_reason_codes"] = sorted(set(task.get("archive_reason_codes", []) + ["EXECUTOR_NOT_RESOLVED"]))
            self._event(events, carrier_epoch, "assignment_trigger_deferred", task_id=task_id, packet_id=trigger.get("packet_id"), reason="EXECUTOR_NOT_RESOLVED", authority_effect=False)
            return False

        generation = int(registry.get("generation", 0)) + 1
        minimum_fence = admission.get("minimum_fencing_token_exclusive") if independent else None
        if independent and isinstance(minimum_fence, int) and generation <= minimum_fence:
            generation = minimum_fence + 1
        registry["generation"] = generation
        claim_id = f"SHWP-{task_id}-G{generation}"
        worker_instance_id = f"{worker['worker_id']}-HB{carrier_epoch}-G{generation}"
        timer, record = bind_assignment_from_trigger(
            trigger=trigger,
            worker_id=str(worker["worker_id"]),
            worker_instance_id=worker_instance_id,
            claim_id=claim_id,
            fencing_token=generation,
            allocated_hb_units=int(budget),
            expiry_basis=expiry_basis,
        )
        task.update({
            "state": "ACTIVE",
            "executor_binding": "BOUND",
            "worker_id": worker["worker_id"],
            "worker_instance_id": worker_instance_id,
            "claim_id": claim_id,
            "archive_eligible": False,
            "archive_reason_codes": [],
            "block_ref": None,
            "assignment_timer": timer.as_dict(),
            "heartbeat_timing": {
                "start_epoch": carrier_epoch,
                "last_response_epoch": carrier_epoch,
                "last_transition_epoch": carrier_epoch,
                "current_transition": "ACTIVATED",
                "transition_sequence": 0,
                "expected_next_transition": None,
                "expected_next_earliest_epoch": None,
                "expected_next_latest_epoch": None,
                "max_missing_response_beats": max(1, min(10, int(budget))),
                "expiry_epoch": None,
                "expiry_basis": "WORKER_RUNTIME_ASSIGNMENT_TIMER",
                "fencing_token": generation,
            },
        })
        worker["status"] = "BUSY"
        worker["last_seen_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        if independent:
            record["source_admission_ref"] = admission.get("authority_source")
            record["source_carrier_event_ref"] = None
        else:
            record["source_carrier_event_ref"] = f"events/heartbeat-runtime.jsonl#packet_id={trigger.get('packet_id')}"
        record["worker_runtime_event_ref"] = f"events/worker-runtime.jsonl#claim_id={claim_id}"
        record["terminal_destination"] = "master-records/orchestration"
        self._append_assignment_record(record)
        evidence_ref = f"events/master-records-worker-assignment.jsonl#packet_id={trigger.get('packet_id')}"
        if evidence_ref not in task.setdefault("evidence_refs", []):
            task["evidence_refs"].append(evidence_ref)
        event_type = "worker_assignment_bound_from_independent_task_control" if independent else "worker_assignment_bound_from_carrier_packet"
        self._event(
            events,
            carrier_epoch,
            event_type,
            task_id=task_id,
            worker_id=worker["worker_id"],
            claim_id=claim_id,
            fencing_token=generation,
            packet_id=trigger.get("packet_id"),
            assignment_timer_units=budget,
            master_records_binding_ref=evidence_ref,
            independent_task_control=independent,
            carrier_granted_authority=False,
            authority_effect=False,
        )
        self._invoke(registry, task, carrier_epoch, cost_log, events)
        return True

    def _activate_independently_admitted_tasks(
        self,
        registry: dict[str, Any],
        carrier_epoch: int,
        cost_log: dict[str, Any],
        events: list[dict[str, Any]],
    ) -> int:
        activated = 0
        candidates = sorted(registry.get("tasks", []), key=lambda item: str(item.get("task_id", "")))
        for task in candidates:
            admission = task.get("admission") or {}
            if (
                task.get("state") != "HANDOFF_READY"
                or task.get("worker_id")
                or task.get("claim_id")
                or admission.get("authority_domain") != "INDEPENDENT_TASK_CONTROL"
                or admission.get("claim_state") != "AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM"
            ):
                continue
            packet = independent_task_control_packet(carrier_epoch=carrier_epoch, task=task)
            if self._activate_from_trigger(registry, packet, carrier_epoch, cost_log, events):
                activated += 1
        return activated

    def _tick_active_timer(self, task: dict[str, Any], carrier_epoch: int, registry: dict[str, Any], cost_log: dict[str, Any], events: list[dict[str, Any]]) -> None:
        timer = self._timer_from_task(task, carrier_epoch)
        if timer is None:
            self._event(events, carrier_epoch, "worker_timer_missing", task_id=task.get("task_id"), worker_id=task.get("worker_id"), authority_effect=False)
            return
        if timer.expired:
            self._event(events, carrier_epoch, "worker_assignment_timer_expired", task_id=task.get("task_id"), worker_id=task.get("worker_id"), claim_id=task.get("claim_id"), fencing_token=timer.fencing_token, runtime_tick=timer.runtime_tick, carrier_controls_timer=False)
            self._expire(registry, task, carrier_epoch, events)
            task["assignment_timer"] = None
            return

        self._invoke(registry, task, carrier_epoch, cost_log, events)
        if task.get("state") in self.WORKER_OWNED | {"BLOCKED"} and task.get("worker_id"):
            advanced = timer.tick()
            task["assignment_timer"] = advanced.as_dict()
            if advanced.expired:
                self._event(events, carrier_epoch, "worker_assignment_timer_reached_zero", task_id=task.get("task_id"), worker_id=task.get("worker_id"), claim_id=task.get("claim_id"), fencing_token=advanced.fencing_token, runtime_tick=advanced.runtime_tick, carrier_controls_timer=False, expiry_on_next_worker_cycle=True)

    def cycle(self, write: bool = True) -> dict[str, Any]:
        self._persist = write
        self._acquire()
        try:
            carrier_epoch, carrier_generation = self._carrier_reference()
            registry = self._load(self.registry_path)
            registry_fragments_applied = self._apply_registry_fragments(registry)
            cost_log = self._load(self.cost_log_path) if self.cost_log_path.exists() else {
                "schema": "stegverse.worker-cost-observation-log/v0.1",
                "generation": 0,
                "records": [],
            }
            state = self._load_runtime_state()
            state["runtime_tick"] = int(state.get("runtime_tick", 0)) + 1
            state["last_observed_carrier_epoch"] = carrier_epoch
            state["last_observed_carrier_generation"] = carrier_generation
            state["carrier_controls_timer"] = False
            seen = set(str(item) for item in state.get("seen_assignment_packet_ids", []))
            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            events: list[dict[str, Any]] = []

            if registry_fragments_applied:
                self._event(events, carrier_epoch, "worker_registry_fragments_applied", fragment_refs=registry_fragments_applied, fragment_count=len(registry_fragments_applied), authority_effect=False, github_token_required=False)
            reconciled = self._reconcile_orphan_recovery_quarantines(registry, carrier_epoch, events)

            for task in list(registry.get("tasks", [])):
                if task.get("state") in self.WORKER_OWNED | {"BLOCKED"} and task.get("worker_id"):
                    self._tick_active_timer(task, carrier_epoch, registry, cost_log, events)

            independent_activated = self._activate_independently_admitted_tasks(registry, carrier_epoch, cost_log, events)

            carrier_activated = 0
            packets = self._trigger_packets(seen, carrier_epoch)
            for packet in packets:
                packet_id = str(packet["packet_id"])
                if self._activate_from_trigger(registry, packet, carrier_epoch, cost_log, events):
                    carrier_activated += 1
                seen.add(packet_id)

            state["seen_assignment_packet_ids"] = sorted(seen)[-4096:]
            state["last_cycle_at"] = now
            registry["updated_at"] = now
            result = {
                "schema": "stegverse.worker-runtime-cycle-result/v1",
                "worker_runtime_tick": state["runtime_tick"],
                "observed_carrier_epoch": carrier_epoch,
                "observed_carrier_generation": carrier_generation,
                "carrier_epoch_advanced_by_worker_runtime": False,
                "assignment_packets_observed": len(packets),
                "independent_task_control_activations": independent_activated,
                "carrier_packet_activations": carrier_activated,
                "workers_activated": independent_activated + carrier_activated,
                "registry_generation": registry.get("generation", 0),
                "registry_fragments_applied": registry_fragments_applied,
                "orphan_recoveries_reconciled": reconciled,
                "events": events,
                "credential_authority": "TV/TVC",
                "github_token_runtime_authority": "NONE",
                "heartbeat_event_required_for_independent_task_control": False,
                "authority_effect": "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY",
            }
            if write:
                self._atomic_write(self.registry_path, registry)
                self._atomic_write(self.cost_log_path, cost_log)
                self._atomic_write(self.worker_runtime_state_path, state)
                self.worker_event_path.parent.mkdir(parents=True, exist_ok=True)
                with self.worker_event_path.open("a", encoding="utf-8") as stream:
                    for event in events:
                        stream.write(json.dumps(event, sort_keys=True) + "\n")
            return result
        finally:
            self._release_lock()
            self._persist = True


__all__ = ["WorkerCoordinator", "WorkerResponse", "ProcessWorkerAdapter"]
