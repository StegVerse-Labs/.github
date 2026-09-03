from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import base64
import hashlib
import json
import os
import subprocess
import sys

from .engine_v9 import HeartbeatRuntime as HeartbeatRuntimeV9, WorkerResponse
from .blocker_policy import RESOLUTION_EVIDENCE_PREFIX


class HeartbeatRuntime(HeartbeatRuntimeV9):
    """Heartbeat runtime with fail-closed -> resolution-task continuation.

    A refused consequence stays refused. The governing goal does not become a
    passive BLOCKED worker task: the runtime derives a distinct registered
    resolution task. Repeated inability to resolve the same constraint advances
    through the resolution hierarchy until an eligible machine worker exists or
    an explicit HUMAN_AUTHORITY_REQUIRED boundary is reached.
    """

    RESOLUTION_LEVELS = (
        "WORKER",
        "REPOSITORY_OWNER",
        "COMPONENT_AUTHORITY",
        "ECOSYSTEM_GOVERNANCE",
        "HUMAN_AUTHORITY",
    )
    LEVEL_CAPABILITIES = {
        "REPOSITORY_OWNER": ["repository_resolution", "sandbox_validation"],
        "COMPONENT_AUTHORITY": ["component_resolution", "governance_validation"],
        "ECOSYSTEM_GOVERNANCE": ["ecosystem_resolution", "governance_validation"],
    }
    POLICY_REF = "control/blocker-resolution-policy.json"
    STEGINDEX_PREFLIGHT_SCRIPT = "scripts/run_stegindex_preflight.py"
    STEGINDEX_OPERATIONAL_PROOF_SCRIPT = "scripts/verify_stegindex_resident_operational_proof.py"

    def _decode_resolution_ref(self, ref: str) -> dict[str, Any] | None:
        if not isinstance(ref, str) or not ref.startswith(RESOLUTION_EVIDENCE_PREFIX):
            return None
        encoded = ref[len(RESOLUTION_EVIDENCE_PREFIX):]
        try:
            encoded += "=" * (-len(encoded) % 4)
            value = json.loads(base64.urlsafe_b64decode(encoded.encode("ascii")).decode("utf-8"))
        except Exception:
            return None
        return value if isinstance(value, dict) else None

    def _latest_resolution_contract(self, task: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
        for ref in reversed(task.get("evidence_refs", [])):
            contract = self._decode_resolution_ref(ref)
            if contract is not None:
                return ref, contract
        return None

    def _resolution_level(self, handoff: dict[str, Any]) -> str:
        for ref in handoff.get("task", {}).get("source_refs", []):
            if isinstance(ref, str) and ref.startswith("resolution-level:"):
                candidate = ref.split(":", 1)[1]
                if candidate in self.RESOLUTION_LEVELS:
                    return candidate
        return "WORKER"

    def _next_level(self, current: str) -> str:
        try:
            index = self.RESOLUTION_LEVELS.index(current)
        except ValueError:
            index = 0
        return self.RESOLUTION_LEVELS[min(index + 1, len(self.RESOLUTION_LEVELS) - 1)]

    def _target_level(self, parent_handoff: dict[str, Any], contract: dict[str, Any]) -> str:
        current = self._resolution_level(parent_handoff)
        depth = int(parent_handoff.get("task", {}).get("derivation_depth", 0))
        resolvable = bool(contract.get("resolvable_by_current_worker", True))

        # Once a derived resolution task itself reports the same class of
        # unsatisfied condition, that is evidence the assigned level did not
        # resolve it. A same-level retry is allowed only when the worker
        # explicitly proves that it selected a different workaround candidate.
        if depth > 0 and not (
            contract.get("same_level_retry_authorized") is True
            and contract.get("workaround_candidate_changed") is True
        ):
            resolvable = False

        requested = contract.get("escalation_target")
        if not resolvable:
            if isinstance(requested, str) and requested in self.RESOLUTION_LEVELS:
                requested_index = self.RESOLUTION_LEVELS.index(requested)
                current_index = self.RESOLUTION_LEVELS.index(current)
                if requested_index > current_index:
                    return requested
            return self._next_level(current)
        return current

    def _resolution_capabilities(
        self,
        parent_handoff: dict[str, Any],
        contract: dict[str, Any],
        target_level: str,
    ) -> list[str]:
        declared = contract.get("required_capabilities")
        if isinstance(declared, list):
            cleaned = [item for item in declared if isinstance(item, str) and item]
            if cleaned:
                return sorted(set(cleaned))
        if target_level == "WORKER":
            inherited = parent_handoff.get("execution", {}).get("required_capabilities", [])
            cleaned = [item for item in inherited if isinstance(item, str) and item]
            if cleaned:
                return sorted(set(cleaned))
        return list(self.LEVEL_CAPABILITIES.get(target_level, ["governance_resolution"]))

    def _write_resolution_cost_basis(self, task_id: str, source_refs: list[str]) -> str:
        ref = f"cost-basis/generated/{task_id}.json"
        record = {
            "schema": "stegverse.worker-runtime-cost-basis/v0.1",
            "task_class": "constraint_resolution",
            "sample_count": 0,
            "hb_estimate": {
                "expected_completion_beats": 1,
                "expected_idle_beats": 0,
                "expiry_candidate_beats": 64,
                "confidence": "LOW",
            },
            "cost_estimate": {
                "compute_units": 1,
                "token_units": 0,
                "storage_bytes": 65536,
                "network_bytes": 0,
                "operator_seconds": 0,
                "external_cost_usd": 0,
                "latency_ms": None,
                "failure_recovery_units": 1,
            },
            "evidence_refs": source_refs,
            "notes": [
                "Generated bounded cost basis for a goal-preserving constraint-resolution task.",
                "This record grants no product, policy, credential, route, or execution authority.",
            ],
        }
        self._atomic_write(self.root / ref, record)
        return ref

    def _refresh_stegindex_operational_proof(self) -> None:
        script = self.root / self.STEGINDEX_OPERATIONAL_PROOF_SCRIPT
        if not script.is_file():
            return
        subprocess.run(
            [sys.executable, str(script), "--runtime-root", str(self.root)],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
            env={"PATH": os.environ.get("PATH", "")},
        )

    def _run_stegindex_preflight(
        self,
        parent: dict[str, Any],
        contract: dict[str, Any],
        epoch: int,
    ) -> tuple[str, dict[str, Any]]:
        script = self.root / self.STEGINDEX_PREFLIGHT_SCRIPT
        query = str(
            contract.get("problem_statement")
            or contract.get("next_solution_action")
            or parent.get("goal_id")
            or parent.get("task_id")
            or "constraint resolution"
        ).strip()
        env = {"PATH": os.environ.get("PATH", "")}
        for name in ("STEGVERSE_STEGINDEX_SOURCE_ROOT", "STEGVERSE_REPO_ROOTS_JSON"):
            value = os.environ.get(name)
            if value:
                env[name] = value

        if not script.is_file():
            result: dict[str, Any] = {
                "schema": "stegverse.stegindex-preflight-result/v1",
                "query": query,
                "state": "PREFLIGHT_UNAVAILABLE",
                "problem_statement": "StegIndex preflight consumer is not materialized in the resident runtime source",
                "capabilities": [],
                "first_actionable_predicate": None,
                "machine_continuation_required": False,
                "generic_blocker_permitted": False,
                "source_unavailable_is_implementation_missing": False,
                "network_fetch_performed": False,
                "github_token_required": False,
                "authority_effect": "NONE_READ_RESOLVE_ONLY",
            }
        else:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--query",
                    query,
                    "--intent",
                    "DECLARE_BLOCKER",
                ],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
                env=env,
            )
            try:
                parsed = json.loads(completed.stdout)
                result = parsed if isinstance(parsed, dict) else {}
            except Exception:
                result = {}
            if not result:
                result = {
                    "schema": "stegverse.stegindex-preflight-result/v1",
                    "query": query,
                    "state": "PREFLIGHT_UNAVAILABLE",
                    "problem_statement": f"StegIndex preflight consumer exited {completed.returncode} without valid JSON",
                    "capabilities": [],
                    "first_actionable_predicate": None,
                    "machine_continuation_required": False,
                    "generic_blocker_permitted": False,
                    "source_unavailable_is_implementation_missing": False,
                    "network_fetch_performed": False,
                    "github_token_required": False,
                    "authority_effect": "NONE_READ_RESOLVE_ONLY",
                }

        stable = {
            "parent_task_id": parent.get("task_id"),
            "heartbeat_epoch": epoch,
            "query": query,
            "state": result.get("state"),
            "duplicate_implementation_guard": result.get("duplicate_implementation_guard"),
            "first_actionable_predicate": result.get("first_actionable_predicate"),
        }
        digest = hashlib.sha256(
            json.dumps(stable, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:16]
        safe_parent = str(parent.get("task_id") or "unknown").replace("/", "_")
        ref = f"receipts/stegindex-preflight/{safe_parent}-HB{epoch}-{digest}.json"
        receipt = {
            "schema": "stegverse.stegindex-resolution-admission-preflight/v1",
            "parent_task_id": parent.get("task_id"),
            "heartbeat_epoch": epoch,
            "resolution_contract": {
                "dependency_class": contract.get("dependency_class"),
                "problem_statement": contract.get("problem_statement"),
                "required_capabilities": contract.get("required_capabilities") or [],
            },
            "preflight": result,
            "network_fetch_performed": False,
            "credential_read_or_acquired": False,
            "github_token_required": False,
            "credential_authority": "TV/TVC",
            "authority_effect": "NONE_READ_RESOLVE_ONLY",
        }
        self._atomic_write(self.root / ref, receipt)
        self._refresh_stegindex_operational_proof()
        return ref, result

    def _admit_resolution_task(
        self,
        registry: dict[str, Any],
        parent: dict[str, Any],
        epoch: int,
        events: list[dict[str, Any]],
        resolution_ref: str,
        contract: dict[str, Any],
    ) -> str:
        parent_handoff = self._handoff(parent)
        preflight_ref, preflight = self._run_stegindex_preflight(parent, contract, epoch)
        target_level = self._target_level(parent_handoff, contract)
        stable = {
            "parent_task_id": parent.get("task_id"),
            "dependency_class": contract.get("dependency_class"),
            "problem_statement": contract.get("problem_statement"),
            "target_level": target_level,
        }
        digest = hashlib.sha256(
            json.dumps(stable, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:12]
        prefix = "ESCALATE" if target_level != self._resolution_level(parent_handoff) else "RESOLVE"
        task_id = f"{prefix}-{parent['task_id']}-{digest}"
        handoff_ref = f"handoffs/generated/{task_id}.json"
        existing = next((item for item in registry.get("tasks", []) if item.get("task_id") == task_id), None)
        if existing is not None:
            self._release_worker(registry, parent)
            parent["state"] = "ACTIVATION_PENDING"
            parent["heartbeat_timing"] = None
            parent["block_ref"] = handoff_ref
            parent["archive_eligible"] = False
            return task_id

        parent_task = parent_handoff.get("task", {})
        parent_goal = parent_handoff.get("goal", {})
        parent_execution = parent_handoff.get("execution", {})
        parent_authority = parent_handoff.get("authority", {})
        depth = int(parent_task.get("derivation_depth", 0)) + 1
        max_depth = max(depth + 1, int(parent_goal.get("max_successor_depth", 8)))
        source_refs = [parent["handoff_ref"], resolution_ref, preflight_ref, f"resolution-level:{target_level}"]
        completion_evidence = contract.get("completion_evidence")
        if not isinstance(completion_evidence, list) or not completion_evidence:
            completion_evidence = [
                "The originating unsatisfied predicate is corrected or a narrower admitted route satisfies the same governing goal."
            ]

        human = target_level == "HUMAN_AUTHORITY"
        state = "HUMAN_AUTHORITY_REQUIRED" if human else "HANDOFF_READY"
        capabilities = self._resolution_capabilities(parent_handoff, contract, target_level)
        allowed_paths = list(parent_execution.get("allowed_paths") or ["control/**", "handoffs/generated/**", "receipts/**"])
        allowed_services = list(parent_execution.get("allowed_services") or [])
        lineage = str(parent_task.get("canonical_lineage_key") or parent.get("goal_id") or parent["task_id"])
        generated = {
            "schema": "stegverse.executable-handoff/v0.1",
            "handoff_id": f"HANDOFF-{task_id}",
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "state": state,
            "goal": {
                "goal_id": str(parent.get("goal_id") or parent_goal.get("goal_id") or parent["task_id"]),
                "objective": f"Resolve the constraint preventing progress toward the originating goal: {contract.get('problem_statement')}",
                "success_predicates": [str(item) for item in completion_evidence],
                "failure_predicates": [
                    "The constraint is re-observed without a changed solution attempt.",
                    "A safety, policy, credential, route, or execution authority boundary is bypassed.",
                    "The originating goal is silently replaced by a weaker unrelated goal.",
                ],
                "expires_at": None,
                "authority_ceiling": list(parent_goal.get("authority_ceiling") or ["goal_preserving_resolution_only"]),
                "successor_policy": "SEPARATE_AUTHORIZATION_REQUIRED_FOR_EXPANSION",
                "max_successor_depth": max_depth,
            },
            "task": {
                "task_id": task_id,
                "repository": str(parent_task.get("repository") or "StegVerse-Labs/.github"),
                "source_refs": source_refs,
                "dependencies": [],
                "parent_task_id": None,
                "derivation_reason": f"{contract.get('trigger_type', 'BLOCKED_CONDITION')}:{contract.get('dependency_class')}:{contract.get('problem_statement')}",
                "canonical_owner_ref": f"resolution-level:{target_level}",
                "canonical_lineage_key": f"{lineage}/resolution/{digest}",
                "derivation_depth": depth,
                "priority": "critical",
            },
            "authority": {
                "authority_source": str(parent_authority.get("authority_source") or self.POLICY_REF),
                "heartbeat_grants_execution_authority": False,
                "policy_version": str(parent_authority.get("policy_version") or "active-resolution-escalation-v2"),
            },
            "execution": {
                "required_capabilities": capabilities,
                "allowed_paths": allowed_paths,
                "allowed_services": allowed_services,
                "max_actions": int(parent_execution.get("max_actions", 50)),
                "max_retries": int(parent_execution.get("max_retries", 2)),
                "external_cost_ceiling_usd": float(parent_execution.get("external_cost_ceiling_usd", 0)),
                "runtime_window_beats": int(parent_execution.get("runtime_window_beats", 64)),
                "rate_class": str(parent_execution.get("rate_class", "resolution")),
            },
            "activation": {
                "carrier": "heartbeat",
                "executor_binding": "UNBOUND" if human else "AUTHORIZED",
                **({} if human else {"authorization_ref": self.POLICY_REF}),
                "recheck_trigger": "each heartbeat until the resolution task is completed or escalated",
                "checkout_policy": "fenced_atomic_checkout",
            },
            "continuity": {
                "checkpoint_ref": parent.get("last_checkpoint_ref"),
                "handoff_destination": "control/worker-registry.json",
                "master_records_required": True,
                "status_projection": "control/worker-status.json",
            },
            "completion": {
                "next_authorized_action": str(contract.get("next_solution_action") or "Derive and execute an admitted solution that preserves the originating goal."),
                "terminal_when": [
                    "Resolution evidence satisfies the generated success predicates.",
                    "If this level cannot resolve the collision, a higher-level resolution task is registered before this task stops progressing.",
                ],
            },
            "block": None,
        }
        self._atomic_write(self.root / handoff_ref, generated)
        cost_ref = self._write_resolution_cost_basis(task_id, source_refs)
        registry.setdefault("tasks", []).append({
            "task_id": task_id,
            "goal_id": generated["goal"]["goal_id"],
            "state": state,
            "handoff_ref": handoff_ref,
            "executor_binding": "UNBOUND",
            "worker_id": None,
            "worker_instance_id": None,
            "claim_id": None,
            "lease": None,
            "heartbeat_timing": None,
            "resource_budget": None,
            "authorized_policy_version": None,
            "policy_rebind_ref": None,
            "transition_history": [],
            "renewal_ref": None,
            "cost_basis_ref": cost_ref,
            "external_entity_job_ref": None,
            "last_checkpoint_ref": parent.get("last_checkpoint_ref"),
            "block_ref": None,
            "archive_eligible": False,
            "archive_reason_codes": [
                "GOAL_PRESERVING_RESOLUTION_REQUIRED",
                f"RESOLUTION_LEVEL_{target_level}",
            ],
            "evidence_refs": [parent["task_id"], resolution_ref, preflight_ref, f"heartbeat-epoch:{epoch}"],
        })
        self._release_worker(registry, parent)
        parent["state"] = "ACTIVATION_PENDING"
        parent["heartbeat_timing"] = None
        parent["block_ref"] = handoff_ref
        parent["archive_eligible"] = False
        parent["archive_reason_codes"] = sorted(set(parent.get("archive_reason_codes", []) + [
            "RESOLUTION_TASK_REGISTERED",
            f"RESOLUTION_LEVEL_{target_level}",
        ]))
        self._event(
            events,
            epoch,
            "resolution_task_admitted",
            task_id=task_id,
            parent_task_id=parent["task_id"],
            resolution_level=target_level,
            dependency_class=contract.get("dependency_class"),
            trigger_type=contract.get("trigger_type"),
            stegindex_preflight_ref=preflight_ref,
            stegindex_preflight_state=preflight.get("state") or "RESOLVED",
            stegindex_duplicate_guard=preflight.get("duplicate_implementation_guard"),
            stegindex_machine_continuation_required=bool(preflight.get("machine_continuation_required")),
            stegindex_risk_transition_surfaces=list(
                (preflight.get("capability_risk") or {}).get("transition_surfaces") or []
            ),
            stegindex_risk_required_governance=list(
                (preflight.get("capability_risk") or {}).get("required_governance") or []
            ),
            stegindex_risk_authority_effect=(
                (preflight.get("capability_risk") or {}).get("authority_effect")
                or "NONE_INDEX_ONLY"
            ),
            authority_effect=False,
        )
        return task_id

    def _invoke(self, registry: dict[str, Any], task: dict[str, Any], epoch: int, cost_log: dict[str, Any], events: list[dict[str, Any]]) -> None:
        super()._invoke(registry, task, epoch, cost_log, events)
        if task.get("state") != "BLOCKED":
            return
        found = self._latest_resolution_contract(task)
        if found is None:
            raise RuntimeError(
                f"BLOCKED task {task.get('task_id')} lacks a machine-readable resolution contract; passive blocked state is prohibited"
            )
        resolution_ref, contract = found
        self._admit_resolution_task(registry, task, epoch, events, resolution_ref, contract)

    def _expire(self, registry: dict[str, Any], task: dict[str, Any], epoch: int, events: list[dict[str, Any]]) -> None:
        super()._expire(registry, task, epoch, events)
        # Legacy lifecycle recovery creates a distinct RECOVER-* task. The parent
        # therefore waits on active recovery work rather than remaining BLOCKED.
        if task.get("state") == "BLOCKED" and task.get("block_ref"):
            task["state"] = "ACTIVATION_PENDING"
            task["archive_reason_codes"] = sorted(set(task.get("archive_reason_codes", []) + ["RECOVERY_TASK_ACTIVE"]))
            self._event(
                events,
                epoch,
                "blocked_parent_normalized_to_active_recovery",
                task_id=task["task_id"],
                recovery_ref=task.get("block_ref"),
            )

    def _reconcile_resolved_parents(self, registry: dict[str, Any], epoch: int, events: list[dict[str, Any]]) -> None:
        by_handoff = {str(item.get("handoff_ref")): item for item in registry.get("tasks", [])}
        for parent in registry.get("tasks", []):
            if parent.get("state") != "ACTIVATION_PENDING" or not parent.get("block_ref"):
                continue
            child = by_handoff.get(str(parent.get("block_ref")))
            if child is None or child.get("state") != "COMPLETED":
                continue
            parent["state"] = "HANDOFF_READY"
            parent["block_ref"] = None
            parent["archive_reason_codes"] = [
                code for code in parent.get("archive_reason_codes", [])
                if not str(code).startswith("RESOLUTION_") and code != "RECOVERY_TASK_ACTIVE"
            ]
            self._event(
                events,
                epoch,
                "originating_goal_reactivated_after_resolution",
                task_id=parent["task_id"],
                completed_resolution_task_id=child["task_id"],
            )

    def _escalate_unassigned_resolution_tasks(self, registry: dict[str, Any], epoch: int, events: list[dict[str, Any]]) -> None:
        # A resolution task without any eligible worker is itself an authority /
        # capability collision. Escalate immediately rather than leaving a
        # HANDOFF_READY task to be rediscovered indefinitely.
        for _ in range(len(self.RESOLUTION_LEVELS)):
            changed = False
            for task in list(registry.get("tasks", [])):
                if task.get("state") != "HANDOFF_READY":
                    continue
                handoff = self._handoff(task)
                current = self._resolution_level(handoff)
                if current == "WORKER" and not any(
                    isinstance(ref, str) and ref.startswith(RESOLUTION_EVIDENCE_PREFIX)
                    for ref in handoff.get("task", {}).get("source_refs", [])
                ):
                    continue
                if self._worker_for(task, registry) is not None:
                    continue
                if current == "HUMAN_AUTHORITY":
                    task["state"] = "HUMAN_AUTHORITY_REQUIRED"
                    continue
                synthetic = {
                    "trigger_type": "EXECUTOR_UNRESOLVED",
                    "dependency_class": "CONSTRAINT_COLLISION",
                    "problem_statement": f"No admitted worker at resolution level {current} has the capabilities required by {task['task_id']}.",
                    "solution_required": True,
                    "workaround_candidates": ["escalate to the next resolution level"],
                    "next_solution_action": "Escalate without relaxing the originating goal or bypassing the unsatisfied constraint.",
                    "resolvable_by_current_worker": False,
                    "completion_evidence": ["An admitted higher-level worker or explicit human authority resolves the constraint collision."],
                }
                raw = json.dumps(synthetic, sort_keys=True, separators=(",", ":")).encode("utf-8")
                encoded = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
                synthetic_ref = RESOLUTION_EVIDENCE_PREFIX + encoded
                if synthetic_ref not in task.setdefault("evidence_refs", []):
                    task["evidence_refs"].append(synthetic_ref)
                self._admit_resolution_task(registry, task, epoch, events, synthetic_ref, synthetic)
                changed = True
            if not changed:
                break

    def _activate_one(self, registry: dict[str, Any], epoch: int, cost_log: dict[str, Any], events: list[dict[str, Any]]) -> bool:
        self._reconcile_resolved_parents(registry, epoch, events)
        self._escalate_unassigned_resolution_tasks(registry, epoch, events)
        return super()._activate_one(registry, epoch, cost_log, events)


__all__ = ["HeartbeatRuntime", "WorkerResponse"]
