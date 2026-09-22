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
import time

from .engine_v11 import HeartbeatRuntime as LegacyWorkerCoordinator, WorkerResponse
from .process_adapter import ProcessWorkerAdapter
from .independent_oscillator import current_reference
from workers.canonical_state_transition_custody import build_state_receipt, require_predecessor_master_records_closure, sha256_uri, submit_state_receipt
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


    def _custody_assignment_transition(
        self,
        *,
        task: dict[str, Any],
        trigger: dict[str, Any],
        record: dict[str, Any],
        claim_id: str,
        fencing_token: int,
        worker_instance_id: str,
    ) -> dict[str, Any]:
        transition_id = "WORKERCOORDINATOR_CLAIM_FENCE_BOUND"
        evidence_sha = sha256_uri(record).split(":", 1)[1]
        required_evidence = {
            "evidence_id": f"workercoordinator-assignment:{claim_id}",
            "evidence_type": "WORKERCOORDINATOR_CLAIM_FENCE_ASSIGNMENT",
            "origin_transition_id": transition_id,
            "encoding": "canonical-json",
            "sha256": evidence_sha,
            "content": dict(record),
        }
        functional_context = record.get("functional_memory_context") if isinstance(record.get("functional_memory_context"), dict) else {}
        predecessor_receipt_sha256 = functional_context.get("prior_functional_memory_receipt_sha256")
        prior_state_ref, predecessor_evidence = require_predecessor_master_records_closure(
            predecessor_receipt_sha256,
            successor_transition_id=transition_id,
        )
        receipt = build_state_receipt(
            transition_id=transition_id,
            transition_sequence=1,
            subject_or_correlation_id=str(task.get("task_id") or ""),
            transition_outcome="OBSERVED",
            prior_state_ref_or_hash=prior_state_ref,
            resulting_state_ref_or_hash=sha256_uri(record),
            governance_decision_ref_where_applicable=None,
            transition_evidence={
                "task_id": task.get("task_id"),
                "claim_id": claim_id,
                "fencing_token": fencing_token,
                "worker_instance_id": worker_instance_id,
                "packet_id": trigger.get("packet_id"),
                "trigger_source": trigger.get("source"),
                "workercoordinator_grants_transition_authority": False,
                "master_records_grants_claim_authority": False,
            },
            required_evidence_manifest=[*predecessor_evidence, required_evidence],
            proof_scope="WORKERCOORDINATOR_CLAIM_FENCE_ASSIGNMENT_ONLY",
            proof_ceiling="CLAIM_FENCE_OBSERVED_AND_MASTER_RECORDS_CUSTODY_ONLY",
        )
        result = submit_state_receipt(receipt)
        return {
            "state": result.get("state"),
            "reason": result.get("reason"),
            "transition_id": transition_id,
            "receipt_sha256": result.get("receipt_sha256"),
            "reconstructed_receipt_sha256": result.get("reconstructed_receipt_sha256"),
            "reconstruction_status": result.get("reconstruction_status"),
            "required_evidence_validation_status": result.get("required_evidence_validation_status"),
            "required_evidence_count": result.get("required_evidence_count"),
            "master_record_ref": result.get("master_record_ref"),
            "authority_effect": "NONE_CUSTODY_RECONSTRUCTION_ONLY",
        }

    def _atomic_constitutive_activation_required(self, handoff: dict[str, Any]) -> bool:
        activation = handoff.get("activation") if isinstance(handoff.get("activation"), dict) else {}
        return (
            activation.get("constitutive_transition") == "ACTIVATE_TASK_AND_CREATE_BIND_WORKER"
            and activation.get("project_active_only_after_master_records_closure") is True
        )

    @staticmethod
    def _master_records_transition_closed(row: Any, transition_id: str) -> bool:
        return (
            isinstance(row, dict)
            and row.get("transition_id") == transition_id
            and row.get("state") == "RECORDED"
            and row.get("reconstruction_status") == "PASS"
            and row.get("required_evidence_validation_status") == "PASS"
            and isinstance(row.get("receipt_sha256"), str)
            and row.get("receipt_sha256") == row.get("reconstructed_receipt_sha256")
        )

    def _admit_atomic_constitutive_activation(
        self,
        *,
        task: dict[str, Any],
        handoff: dict[str, Any],
        worker: dict[str, Any],
        claim_id: str,
        fencing_token: int,
        proposed_worker_instance_id: str,
        carrier_epoch: int,
    ) -> tuple[WorkerResponse, dict[str, Any]]:
        adapter_ref = worker.get("adapter_ref")
        adapter = self.adapters.get(adapter_ref) if isinstance(adapter_ref, str) else None
        if adapter is None:
            raise RuntimeError("atomic constitutive activation adapter unavailable")
        if task.get("state") != "HANDOFF_READY":
            raise RuntimeError("atomic constitutive activation requires HANDOFF_READY task")
        if any(task.get(name) not in (None, "") for name in ("claim_id", "worker_id", "worker_instance_id")):
            raise RuntimeError("atomic constitutive activation pre-state already exposes task-bound worker state")

        pending_task = dict(task)
        pending_task["claim_id"] = None
        pending_task["worker_id"] = None
        pending_task["worker_instance_id"] = None
        pending_task["pending_atomic_activation"] = {
            "claim_id": claim_id,
            "fencing_token": fencing_token,
            "worker_id": worker["worker_id"],
            "proposed_worker_instance_id": proposed_worker_instance_id,
        }
        response = adapter(pending_task, handoff, carrier_epoch)
        if response.state != "ACTIVE" or response.transition_id != "STEGAGENTS_ATOMIC_TASK_WORKER_ACTIVATION_ADMITTED":
            raise RuntimeError("atomic constitutive activation adapter did not return admitted transition")
        checkpoint_ref = response.checkpoint_ref
        if not isinstance(checkpoint_ref, str) or not checkpoint_ref:
            raise RuntimeError("atomic constitutive activation receipt missing")
        checkpoint = Path(checkpoint_ref)
        if not checkpoint.is_absolute():
            checkpoint = self.root / checkpoint
        if not checkpoint.is_file():
            raise RuntimeError("atomic constitutive activation receipt not retained")
        receipt = self._load(checkpoint)
        if receipt.get("state") != "AUTHENTIC_ATOMIC_TASK_WORKER_ACTIVATION_ADMITTED":
            raise RuntimeError("atomic constitutive activation receipt state mismatch")
        if receipt.get("task_id") != task.get("task_id"):
            raise RuntimeError("atomic constitutive activation receipt task mismatch")
        worker_claim = receipt.get("worker_claim") if isinstance(receipt.get("worker_claim"), dict) else {}
        if (
            worker_claim.get("claim_id") != claim_id
            or worker_claim.get("fencing_token") != fencing_token
            or worker_claim.get("worker_id") != worker.get("worker_id")
            or worker_claim.get("proposed_worker_instance_id") != proposed_worker_instance_id
        ):
            raise RuntimeError("atomic constitutive activation receipt pending claim mismatch")
        if not self._master_records_transition_closed(
            receipt.get("warrant_policy_master_records_transition"),
            "TV_TVC_WARRANT_POLICY_VERIFIED",
        ):
            raise RuntimeError("atomic constitutive activation TV/TVC closure incomplete")
        if not self._master_records_transition_closed(
            receipt.get("atomic_activation_master_records_transition"),
            "ACTIVATE_TASK_AND_CREATE_BIND_WORKER",
        ):
            raise RuntimeError("atomic constitutive activation Master Records closure incomplete")
        projection = receipt.get("activation_projection") if isinstance(receipt.get("activation_projection"), dict) else {}
        if (
            projection.get("task_pre_state") != "HANDOFF_READY"
            or projection.get("task_post_state") != "ACTIVE"
            or projection.get("worker_bound_task_id") != task.get("task_id")
            or projection.get("worker_instance_id") != proposed_worker_instance_id
            or projection.get("claim_id") != claim_id
            or projection.get("fencing_token") != fencing_token
            or projection.get("invocation_started") is not False
        ):
            raise RuntimeError("atomic constitutive activation projection mismatch")
        return response, receipt

    def _semantic_state_preclaim(self, task: dict[str, Any]) -> tuple[bool, str]:
        """Revalidate tasks bound to either semantic or operational state vectors.

        `source_state_vector_ref` predates COSV and historically pointed only to
        `stegverse.semantic-state-vector/v1`. COSV adoption also uses this provenance
        slot for local `task.v1` operational records. The schemas are intentionally
        distinct: semantic vectors retain hash-based reconciliation, while COSV task
        records require exact task identity/profile/vector parity with the embedded
        machine-readable projection. Unknown schemas fail closed.
        """
        state_ref = task.get("source_state_vector_ref")
        if state_ref is None:
            return True, "SEMANTIC_STATE_BINDING_NOT_PRESENT"
        if not isinstance(state_ref, str) or not state_ref.strip():
            return False, "TASK_SOURCE_STATE_VECTOR_REF_INVALID"
        state_path = state_ref.split("#", 1)[0]
        candidate = (self.root / state_path).resolve()
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

        if canonical_state.get("profile") == "task.v1" and canonical_state.get("level") == "task":
            machine = task.get("machine_readable_state")
            embedded = machine.get("cosv") if isinstance(machine, dict) else None
            vector = canonical_state.get("vector")
            identity = str(canonical_state.get("identity") or "")
            task_id = str(task.get("task_id") or "")
            if not isinstance(embedded, dict):
                return False, "TASK_OPERATIONAL_STATE_VECTOR_MISSING"
            checks = (
                identity.endswith(f":task:{task_id}"),
                embedded.get("profile") == "task.v1",
                embedded.get("notation") == "L R U I V G O C M T B E A P",
                embedded.get("width") == 14,
                embedded.get("vector_state") == "EMITTED",
                embedded.get("authority_effect") == "NONE",
                isinstance(vector, str) and len(vector) == 14 and vector.isdigit(),
                embedded.get("vector") == vector,
            )
            if not all(checks):
                return False, "TASK_OPERATIONAL_STATE_VECTOR_STALE_OR_INVALID"
            return True, "CURRENT_OPERATIONAL_STATE_VECTOR_CONFIRMED"

        if canonical_state.get("schema") == "stegverse.semantic-state-vector/v1":
            # Import lazily so carrier-only validation/deployment capsules that copy
            # only heartbeat_runtime remain independent of the optional package.
            from state_language import preclaim_revalidate
            try:
                return preclaim_revalidate(task, canonical_state)
            except (KeyError, TypeError, ValueError):
                return False, "TASK_SEMANTIC_STATE_VECTOR_INVALID"

        return False, "TASK_SOURCE_STATE_VECTOR_SCHEMA_UNSUPPORTED"

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

        previous_generation = int(registry.get("generation", 0))
        generation = previous_generation + 1
        minimum_fence = admission.get("minimum_fencing_token_exclusive") if independent else None
        if independent and isinstance(minimum_fence, int) and generation <= minimum_fence:
            generation = minimum_fence + 1
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
        if independent:
            record["source_admission_ref"] = admission.get("authority_source")
            record["source_carrier_event_ref"] = None
        else:
            record["source_carrier_event_ref"] = f"events/heartbeat-runtime.jsonl#packet_id={trigger.get('packet_id')}"
        record["worker_runtime_event_ref"] = f"events/worker-runtime.jsonl#claim_id={claim_id}"
        record["terminal_destination"] = "master-records/orchestration"

        purpose_graph_claim_bundle = None
        graph_contract = handoff.get("state_dependent_graph") if isinstance(handoff.get("state_dependent_graph"), dict) else None
        manifest_runtime_request_path = self.root / "runtime-state" / "sdk-manifest-state-transition" / f"{task_id}.latest.json"
        manifest_runtime_request_present = manifest_runtime_request_path.is_file()
        if manifest_runtime_request_present:
            record["manifest_state_transition_request_ref"] = str(manifest_runtime_request_path)
            record["manifest_state_transition_request_grants_authority"] = False
        if (
            task_id == "SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001"
            and isinstance(graph_contract, dict)
            and graph_contract.get("enabled") is True
            and not manifest_runtime_request_present
        ):
            labels = ("CASE_1", "CASE_2", "CASE_3", "TASK4_A", "TASK4_B", "TASK4_C")
            claims = []
            for label in labels:
                if label == "CASE_1":
                    child_claim_id = claim_id
                    child_instance_id = worker_instance_id
                else:
                    child_claim_id = f"SHWP-{task_id}-{label}-G{generation}"
                    child_instance_id = f"{worker['worker_id']}-HB{carrier_epoch}-{label}-G{generation}"
                claims.append({
                    "label": label,
                    "claim_id": child_claim_id,
                    "fencing_token": generation,
                    "worker_id": worker["worker_id"],
                    "worker_instance_id": child_instance_id,
                })
            purpose_graph_claim_bundle = {
                "schema": "stegverse.workercoordinator-purpose-bound-state-graph-claim-bundle/v1",
                "task_id": task_id,
                "cosv_task_vector": ((task.get("machine_readable_state") or {}).get("cosv") or {}).get("vector"),
                "group_claim_id": claim_id,
                "group_fencing_token": generation,
                "claims": claims,
                "case1_is_outer_assignment": True,
                "case2_case3_admission_requires_predecessor_master_records_closure": True,
                "task4_atomic_three_child_binding_required": True,
                "claim_authority": "WORKERCOORDINATOR",
                "authority_effect": "EXISTING_WORKERCOORDINATOR_CLAIM_AUTHORITY_ONLY",
            }
            record["purpose_bound_state_graph_claim_bundle"] = purpose_graph_claim_bundle

        assignment_custody = self._custody_assignment_transition(
            task=task,
            trigger=trigger,
            record=record,
            claim_id=claim_id,
            fencing_token=generation,
            worker_instance_id=worker_instance_id,
        )
        assignment_custody_complete = (
            assignment_custody.get("state") == "RECORDED"
            and assignment_custody.get("reconstruction_status") == "PASS"
            and assignment_custody.get("required_evidence_validation_status") == "PASS"
            and isinstance(assignment_custody.get("receipt_sha256"), str)
            and assignment_custody.get("receipt_sha256") == assignment_custody.get("reconstructed_receipt_sha256")
        )
        if not assignment_custody_complete:
            self._event(
                events,
                carrier_epoch,
                "worker_assignment_master_records_blocked",
                task_id=task_id,
                claim_id=claim_id,
                fencing_token=generation,
                packet_id=trigger.get("packet_id"),
                master_records_state=assignment_custody.get("state"),
                master_records_reason=assignment_custody.get("reason"),
                reconstruction_status=assignment_custody.get("reconstruction_status"),
                required_evidence_validation_status=assignment_custody.get("required_evidence_validation_status"),
                receipt_sha256=assignment_custody.get("receipt_sha256"),
                reconstructed_receipt_sha256=assignment_custody.get("reconstructed_receipt_sha256"),
                authority_effect=False,
            )
            task["reconciliation_disposition"] = "MASTER_RECORDS_BOUNDARY"
            task["reconciliation_reason"] = str(assignment_custody.get("reason") or "WORKER_ASSIGNMENT_MASTER_RECORDS_CUSTODY_INCOMPLETE")
            return False

        if task_id == "SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001":
            pending = {
                "schema": "stegverse.pending-atomic-task-worker-activation/v1",
                "claim_id": claim_id,
                "fencing_token": generation,
                "worker_id": worker["worker_id"],
                "proposed_worker_instance_id": worker_instance_id,
                "assignment_master_records_transition": dict(assignment_custody),
                "assignment_timer": timer.as_dict(),
                "authority_effect": "NONE_PENDING_COORDINATION_ONLY",
            }
            task["pending_atomic_activation"] = pending
            adapter_ref = worker.get("adapter_ref")
            adapter = self.adapters.get(adapter_ref) if adapter_ref else None
            if adapter is None:
                task.pop("pending_atomic_activation", None)
                self._event(events, carrier_epoch, "test3_atomic_activation_adapter_missing", task_id=task_id, authority_effect=False)
                return False

            activation_response = adapter(task, handoff, carrier_epoch)
            activation_ready = (
                activation_response.state == "ACTIVE"
                and activation_response.transition_id == "STEGAGENTS_ATOMIC_TASK_WORKER_ACTIVATION_ADMITTED"
                and isinstance(activation_response.checkpoint_ref, str)
                and bool(activation_response.checkpoint_ref)
            )
            if not activation_ready:
                task.pop("pending_atomic_activation", None)
                self._event(
                    events,
                    carrier_epoch,
                    "test3_atomic_activation_fail_closed",
                    task_id=task_id,
                    claim_id=claim_id,
                    fencing_token=generation,
                    transition_id=activation_response.transition_id,
                    response_state=activation_response.state,
                    authority_effect=False,
                )
                return False

            activation_path = Path(activation_response.checkpoint_ref)
            if not activation_path.is_absolute():
                activation_path = self.root / activation_path
            if not activation_path.is_file():
                task.pop("pending_atomic_activation", None)
                self._event(events, carrier_epoch, "test3_atomic_activation_receipt_missing", task_id=task_id, claim_id=claim_id, authority_effect=False)
                return False
            activation_receipt = self._load(activation_path)
            activation_result = activation_receipt.get("result") if isinstance(activation_receipt, dict) else None
            transition = activation_result.get("atomic_activation_master_records_transition") if isinstance(activation_result, dict) else None
            projection = activation_result.get("activation_projection") if isinstance(activation_result, dict) else None
            closure_complete = (
                activation_receipt.get("state") == "AUTHENTIC_ATOMIC_TASK_WORKER_ACTIVATION_ADMITTED"
                and isinstance(transition, dict)
                and transition.get("transition_id") == "ACTIVATE_TASK_AND_CREATE_BIND_WORKER"
                and transition.get("state") == "RECORDED"
                and transition.get("reconstruction_status") == "PASS"
                and transition.get("required_evidence_validation_status") == "PASS"
                and isinstance(transition.get("receipt_sha256"), str)
                and transition.get("receipt_sha256") == transition.get("reconstructed_receipt_sha256")
                and isinstance(projection, dict)
                and projection.get("task_pre_state") == "HANDOFF_READY"
                and projection.get("task_post_state") == "ACTIVE"
                and projection.get("worker_bound_task_id") == task_id
                and projection.get("worker_instance_id") == worker_instance_id
                and projection.get("claim_id") == claim_id
                and projection.get("fencing_token") == generation
                and projection.get("invocation_started") is False
            )
            if not closure_complete:
                task.pop("pending_atomic_activation", None)
                self._event(
                    events,
                    carrier_epoch,
                    "test3_atomic_activation_master_records_blocked",
                    task_id=task_id,
                    claim_id=claim_id,
                    fencing_token=generation,
                    authority_effect=False,
                )
                return False

            registry["generation"] = generation
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
                "atomic_activation_receipt_ref": activation_response.checkpoint_ref,
                "heartbeat_timing": {
                    "start_epoch": carrier_epoch,
                    "last_response_epoch": carrier_epoch,
                    "last_transition_epoch": carrier_epoch,
                    "current_transition": "ATOMIC_ACTIVATION_CLOSED",
                    "transition_sequence": 1,
                    "expected_next_transition": "STEGAGENTS_TASK_BOUND_WORKER_INVOCATION_READY",
                    "expected_next_earliest_epoch": None,
                    "expected_next_latest_epoch": None,
                    "max_missing_response_beats": max(1, min(10, int(budget))),
                    "expiry_epoch": None,
                    "expiry_basis": "WORKER_RUNTIME_ASSIGNMENT_TIMER",
                    "fencing_token": generation,
                },
            })
            task.pop("pending_atomic_activation", None)
            worker["status"] = "BUSY"
            worker["last_seen_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            record["canonical_master_records_transition"] = assignment_custody
            record["constitutive_activation_master_records_transition"] = dict(transition)
            self._append_assignment_record(record)
            for ref in activation_response.evidence_refs:
                if ref not in task.setdefault("evidence_refs", []):
                    task["evidence_refs"].append(ref)
            self._event(
                events,
                carrier_epoch,
                "test3_atomic_task_worker_binding_projected",
                task_id=task_id,
                worker_id=worker["worker_id"],
                worker_instance_id=worker_instance_id,
                claim_id=claim_id,
                fencing_token=generation,
                constitutive_transition_id=transition.get("transition_id"),
                constitutive_receipt_sha256=transition.get("receipt_sha256"),
                invocation_started=False,
                authority_effect=False,
            )
            self._invoke(registry, task, carrier_epoch, cost_log, events)
            return True

        if task_id == "SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001":
            adapter_ref = worker.get("adapter_ref")
            adapter = self.adapters.get(adapter_ref) if isinstance(adapter_ref, str) else None
            if adapter is None:
                self._event(events, carrier_epoch, "purpose_bound_post_claim_adapter_missing", task_id=task_id, authority_effect=False)
                return False

            provisional = dict(task)
            provisional.update({
                "state": "ACTIVE",
                "executor_binding": "BOUND",
                "worker_id": worker["worker_id"],
                "worker_instance_id": worker_instance_id,
                "claim_id": claim_id,
                "claim_fence_master_records_transition": dict(assignment_custody),
                "purpose_bound_state_graph_claim_bundle": purpose_graph_claim_bundle,
                "assignment_timer": timer.as_dict(),
                "heartbeat_timing": {
                    "start_epoch": carrier_epoch,
                    "last_response_epoch": carrier_epoch,
                    "last_transition_epoch": carrier_epoch,
                    "current_transition": "CLAIM_FENCE_CUSTODY_CLOSED_PENDING_GOVERNED_ACTIVATION",
                    "transition_sequence": 0,
                    "expected_next_transition": "TV_TVC_WARRANT_POLICY_VERIFIED",
                    "expected_next_earliest_epoch": None,
                    "expected_next_latest_epoch": None,
                    "max_missing_response_beats": max(1, min(10, int(budget))),
                    "expiry_epoch": None,
                    "expiry_basis": "WORKER_RUNTIME_ASSIGNMENT_TIMER",
                    "fencing_token": generation,
                },
            })
            response = adapter(provisional, handoff, carrier_epoch)
            if response.state != "COMPLETED" or not isinstance(response.checkpoint_ref, str) or not response.checkpoint_ref:
                self._event(
                    events,
                    carrier_epoch,
                    "purpose_bound_post_claim_governed_execution_fail_closed",
                    task_id=task_id,
                    claim_id=claim_id,
                    fencing_token=generation,
                    response_state=response.state,
                    transition_id=response.transition_id,
                    authority_effect=False,
                )
                return False

            checkpoint = Path(response.checkpoint_ref)
            if not checkpoint.is_absolute():
                checkpoint = self.root / checkpoint
            if not checkpoint.is_file():
                self._event(events, carrier_epoch, "purpose_bound_post_claim_receipt_missing", task_id=task_id, claim_id=claim_id, authority_effect=False)
                return False
            retained = self._load(checkpoint)
            records_only_closed = (
                retained.get("schema") == "stegverse.stegagents-purpose-bound-worker-runtime-receipt/v1"
                and retained.get("state") == "AUTHENTIC_PURPOSE_BOUND_WORKER_LIFECYCLE_OBSERVED"
                and retained.get("task_id") == task_id
                and retained.get("records_only") is True
                and retained.get("worker_live_after_close") is False
                and retained.get("continued_authority_after_retirement") is False
                and isinstance(retained.get("claim_fence_master_records_transition"), dict)
                and retained["claim_fence_master_records_transition"].get("receipt_sha256") == assignment_custody.get("receipt_sha256")
            )
            if not records_only_closed:
                self._event(
                    events,
                    carrier_epoch,
                    "purpose_bound_post_claim_records_only_closure_blocked",
                    task_id=task_id,
                    claim_id=claim_id,
                    fencing_token=generation,
                    authority_effect=False,
                )
                return False

            registry["generation"] = generation
            task.update({
                "state": "COMPLETED",
                "executor_binding": "UNBOUND",
                "worker_id": None,
                "worker_instance_id": None,
                "claim_id": None,
                "archive_eligible": True,
                "archive_reason_codes": [],
                "block_ref": None,
                "assignment_timer": None,
                "heartbeat_timing": None,
                "claim_fence_master_records_transition": dict(assignment_custody),
                "purpose_bound_state_graph_claim_bundle": purpose_graph_claim_bundle,
                "last_checkpoint_ref": response.checkpoint_ref,
            })
            record["canonical_master_records_transition"] = assignment_custody
            record["governed_records_only_receipt_ref"] = response.checkpoint_ref
            self._append_assignment_record(record)
            for ref in response.evidence_refs:
                if ref not in task.setdefault("evidence_refs", []):
                    task["evidence_refs"].append(ref)
            self._record_cost(cost_log, task, carrier_epoch, response)
            self._event(
                events,
                carrier_epoch,
                "purpose_bound_state_graph_completed_after_governed_activation",
                task_id=task_id,
                claim_id=claim_id,
                fencing_token=generation,
                claim_fence_receipt_sha256=assignment_custody.get("receipt_sha256"),
                records_only_receipt_ref=response.checkpoint_ref,
                task_active_projected_before_governed_activation=False,
                authority_effect=False,
            )
            return True

        if self._atomic_constitutive_activation_required(handoff):
            try:
                atomic_response, atomic_receipt = self._admit_atomic_constitutive_activation(
                    task=task,
                    handoff=handoff,
                    worker=worker,
                    claim_id=claim_id,
                    fencing_token=generation,
                    proposed_worker_instance_id=worker_instance_id,
                    carrier_epoch=carrier_epoch,
                )
            except Exception as exc:
                self._event(
                    events,
                    carrier_epoch,
                    "atomic_constitutive_activation_blocked",
                    task_id=task_id,
                    claim_id=claim_id,
                    fencing_token=generation,
                    reason=str(exc),
                    authority_effect=False,
                )
                task["reconciliation_disposition"] = "ATOMIC_CONSTITUTIVE_ACTIVATION_REQUIRED"
                task["reconciliation_reason"] = str(exc)
                return False

            registry["generation"] = generation
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
                "atomic_activation_receipt_ref": atomic_response.checkpoint_ref,
                "atomic_activation_transition_receipt_sha256": (
                    atomic_receipt.get("atomic_activation_master_records_transition") or {}
                ).get("receipt_sha256"),
                "heartbeat_timing": {
                    "start_epoch": carrier_epoch,
                    "last_response_epoch": carrier_epoch,
                    "last_transition_epoch": carrier_epoch,
                    "current_transition": atomic_response.transition_id,
                    "transition_sequence": atomic_response.transition_sequence,
                    "expected_next_transition": atomic_response.expected_next_transition,
                    "expected_next_earliest_epoch": atomic_response.expected_next_earliest_epoch,
                    "expected_next_latest_epoch": atomic_response.expected_next_latest_epoch,
                    "max_missing_response_beats": max(1, min(10, int(budget))),
                    "expiry_epoch": None,
                    "expiry_basis": "WORKER_RUNTIME_ASSIGNMENT_TIMER",
                    "fencing_token": generation,
                },
            })
            worker["status"] = "BUSY"
            worker["last_seen_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            record["canonical_master_records_transition"] = assignment_custody
            record["constitutive_activation_receipt_ref"] = atomic_response.checkpoint_ref
            record["constitutive_activation_transition_receipt_sha256"] = task["atomic_activation_transition_receipt_sha256"]
            self._append_assignment_record(record)
            assignment_evidence_ref = f"events/master-records-worker-assignment.jsonl#packet_id={trigger.get('packet_id')}"
            if assignment_evidence_ref not in task.setdefault("evidence_refs", []):
                task["evidence_refs"].append(assignment_evidence_ref)
            for ref in atomic_response.evidence_refs:
                if ref not in task.setdefault("evidence_refs", []):
                    task["evidence_refs"].append(ref)
            if atomic_response.checkpoint_ref:
                task["last_checkpoint_ref"] = atomic_response.checkpoint_ref
            self._record_cost(cost_log, task, carrier_epoch, atomic_response)
            self._event(
                events,
                carrier_epoch,
                "atomic_task_worker_activation_projected",
                task_id=task_id,
                worker_id=worker["worker_id"],
                worker_instance_id=worker_instance_id,
                claim_id=claim_id,
                fencing_token=generation,
                claim_fence_master_records_receipt_sha256=assignment_custody.get("receipt_sha256"),
                constitutive_transition_id="ACTIVATE_TASK_AND_CREATE_BIND_WORKER",
                constitutive_master_records_receipt_sha256=task["atomic_activation_transition_receipt_sha256"],
                activation_receipt_ref=atomic_response.checkpoint_ref,
                invocation_started=False,
                authority_effect=False,
            )
            return True

        registry["generation"] = generation
        task["claim_fence_master_records_transition"] = dict(assignment_custody)
        if purpose_graph_claim_bundle is not None:
            task["purpose_bound_state_graph_claim_bundle"] = purpose_graph_claim_bundle
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
        record["canonical_master_records_transition"] = assignment_custody
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
            master_records_transition_id=assignment_custody.get("transition_id"),
            master_records_receipt_sha256=assignment_custody.get("receipt_sha256"),
            master_records_reconstruction_status=assignment_custody.get("reconstruction_status"),
            master_records_required_evidence_validation_status=assignment_custody.get("required_evidence_validation_status"),
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
        target_task_id: str | None = None,
    ) -> int:
        activated = 0
        candidates = sorted(registry.get("tasks", []), key=lambda item: str(item.get("task_id", "")))
        for task in candidates:
            if target_task_id is not None and task.get("task_id") != target_task_id:
                continue
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

    def _invoke(self, registry: dict[str, Any], task: dict[str, Any], epoch: int, cost_log: dict[str, Any], events: list[dict[str, Any]]) -> None:
        super()._invoke(registry, task, epoch, cost_log, events)
        timing = task.get("heartbeat_timing") if isinstance(task.get("heartbeat_timing"), dict) else {}
        if timing.get("current_transition") == "STEGAGENTS_TASK_RESULT_READY_FOR_GOVERNED_CLOSE":
            task["test3_waiting_for_governed_close"] = True

    def _tick_active_timer(self, task: dict[str, Any], carrier_epoch: int, registry: dict[str, Any], cost_log: dict[str, Any], events: list[dict[str, Any]]) -> None:
        if task.get("test3_waiting_for_governed_close") is True:
            self._event(
                events,
                carrier_epoch,
                "test3_governed_close_invoked",
                task_id=task.get("task_id"),
                worker_id=task.get("worker_id"),
                claim_id=task.get("claim_id"),
                authority_effect=False,
            )
            self._invoke(registry, task, carrier_epoch, cost_log, events)
            if task.get("state") == "COMPLETED":
                task["test3_waiting_for_governed_close"] = False
            return
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

    def cycle(self, write: bool = True, *, target_task_id: str | None = None) -> dict[str, Any]:
        self._persist = write
        self._acquire()
        try:
            targeted = target_task_id is not None
            carrier_reference_observed = self.carrier_state_path.exists()
            if carrier_reference_observed:
                carrier_epoch, carrier_generation = self._carrier_reference()
                coordination_reference_source = "SEPARATED_HEARTBEAT_CARRIER"
            elif targeted:
                reference = current_reference(now_ns=time.time_ns())
                carrier_epoch = int(reference["epoch"])
                carrier_generation = int(reference["generation"])
                coordination_reference_source = "INDEPENDENT_OSCILLATOR_REFERENCE_ONLY"
            else:
                carrier_epoch, carrier_generation = self._carrier_reference()
                coordination_reference_source = "SEPARATED_HEARTBEAT_CARRIER"
            registry = self._load(self.registry_path)
            registry_fragments_applied = self._apply_registry_fragments(registry, task_id_filter=target_task_id)
            cost_log = self._load(self.cost_log_path) if self.cost_log_path.exists() else {
                "schema": "stegverse.worker-cost-observation-log/v0.1",
                "generation": 0,
                "records": [],
            }
            state = self._load_runtime_state()
            state["runtime_tick"] = int(state.get("runtime_tick", 0)) + 1
            if carrier_reference_observed:
                state["last_observed_carrier_epoch"] = carrier_epoch
                state["last_observed_carrier_generation"] = carrier_generation
            state["carrier_controls_timer"] = False
            seen = set(str(item) for item in state.get("seen_assignment_packet_ids", []))
            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            events: list[dict[str, Any]] = []

            if registry_fragments_applied:
                self._event(events, carrier_epoch, "worker_registry_fragments_applied", fragment_refs=registry_fragments_applied, fragment_count=len(registry_fragments_applied), authority_effect=False, github_token_required=False)
            reconciled = [] if targeted else self._reconcile_orphan_recovery_quarantines(registry, carrier_epoch, events)

            for task in list(registry.get("tasks", [])):
                if targeted and task.get("task_id") != target_task_id:
                    continue
                if task.get("state") in self.WORKER_OWNED | {"BLOCKED"} and task.get("worker_id"):
                    self._tick_active_timer(task, carrier_epoch, registry, cost_log, events)

            independent_activated = self._activate_independently_admitted_tasks(
                registry, carrier_epoch, cost_log, events, target_task_id=target_task_id
            )

            carrier_activated = 0
            packets = [] if targeted else self._trigger_packets(seen, carrier_epoch)
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
                "observed_carrier_epoch": carrier_epoch if carrier_reference_observed else None,
                "observed_carrier_generation": carrier_generation if carrier_reference_observed else None,
                "coordination_reference_epoch": carrier_epoch,
                "coordination_reference_generation": carrier_generation,
                "coordination_reference_source": coordination_reference_source,
                "carrier_reference_observed": carrier_reference_observed,
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
                "target_task_id": target_task_id,
                "targeted_independent_task_control": targeted,
                "unrelated_worker_execution_suppressed": targeted,
                "carrier_packet_execution_suppressed": targeted,
                "orphan_reconciliation_suppressed": targeted,
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
