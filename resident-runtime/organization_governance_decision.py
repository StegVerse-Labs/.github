#!/usr/bin/env python3
"""Decide the governance requests another organization queued on its mesh, and answer on ours.

An emitting organization publishes its request frames on a git ref of its own
`.github` (its federation mesh). This organization does not wait for them to be
delivered: a materializer names that ref, and one execution

1. **materializes** the durable queue: the source ref, fetched anonymously into
   a temporary repository and archived into a mesh directory, overlaid with the
   frames this organization already published on its own
   `refs/stegverse/federation-mesh`. Frames are write-once and addressed by
   content, so the union is safe; a key that carries different content on the
   two sides is refused. A frame whose key or digests do not recompute is
   excluded and reported, never consumed;
2. **runs the cycle**: `org-kernel/kernel.py::consume_and_respond` over that
   directory, with node state and both ledgers at locations under the run's own
   temporary space. The organization ledger is opened by `organization_store()`
   exactly as `.stegverse/transition-ledger/org-contract.json` declares it --
   git, private custody, `propagate_target: null` -- so its receipts are real
   appends that, by that declaration, are published nowhere. A request this
   organization already answered on its own ref is passed as seen, so a replay
   decides nothing twice;
3. **publishes** every frame the cycle added onto this repository's own
   `refs/stegverse/federation-mesh`, as one fast-forward commit whose tree is
   the existing own tree plus the new frames. No other repository or ref is
   written. A lost race is refused, never forced;
4. **reads back** what it published from a fresh anonymous fetch and recovers
   each answer with the kernel.

Every refusal of this execution is a six-field FAIL_CLOSED and exits 1. A
FAIL_CLOSED governance *decision* is a decision, carried back like any other.

Nothing here grants authority.
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OWN_MESH_REF = "refs/stegverse/federation-mesh"
CANDIDATE_REF = "refs/stegverse/publish-candidate"
FRAME_PATH = re.compile(r"^frames\.d/[0-9a-f]{64}\.json$")
LEDGER_PERSISTENCE = "EXECUTION_SCOPED_PROPAGATE_TARGET_NULL"
REPORT_SCHEMA = "stegverse.organization-governance-decision-run/v1"
DECISION_AUTHORITY_PIN = "org-runtime/decision-authority.json"
EVALUATOR_NOT_PROVIDED = {
    "installed": False, "reason": "STEGCORE_READ_CREDENTIAL_NOT_PROVIDED",
    "owner_decision": ("provide a read-only STEGCORE_READ_TOKEN repository secret "
                       "(Contents: read on StegVerse-Labs/StegCore)")}


def _module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kernel = _module("org_governance_decision_kernel", "org-kernel/kernel.py")
binding = _module("mesh_source_binding", "resident-runtime/mesh_source_binding.py")
node_store = kernel.node_store_module


class Refusal(Exception):
    """A six-field FAIL_CLOSED of this execution itself."""

    def __init__(self, failure_code: str, failed_predicate: str, required: str):
        super().__init__(failure_code + ": " + failed_predicate)
        self.document = binding.fail_closed(failure_code, failed_predicate, required)


def own_organization() -> str:
    return kernel.load_registry(ROOT)["organization"]


def _git(*args: str, git_dir: Path | None = None, data: bytes | None = None,
         env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess:
    command = ["git"] + (["--git-dir", str(git_dir)] if git_dir is not None else []) + list(args)
    completed = subprocess.run(command, input=data, capture_output=True, env=env, check=False)
    if check and completed.returncode != 0:
        raise Refusal("ORGANIZATION_MESH_GIT_FAILED",
                      " ".join(args[:2]) + ":" + completed.stderr.decode(errors="replace").strip()[-300:],
                      "repair the local git materialization and re-run")
    return completed


def _init_bare(path: Path) -> Path:
    if not (path / "HEAD").is_file():
        path.mkdir(parents=True, exist_ok=True)
        _git("init", "-q", "--bare", str(path))
    return path


def _anonymous_tip(url: str, ref: str) -> str | None:
    """The ref's tip as an anonymous reader sees it; None when the ref is unpublished."""
    completed = binding.anonymous_git("ls-remote", "--refs", url, ref)
    if completed.returncode != 0:
        raise Refusal("MESH_SOURCE_NOT_ANONYMOUSLY_FETCHABLE",
                      "ls_remote_failed:" + url + ":" + (completed.stderr or "").strip()[-300:],
                      "make " + url + " readable without credentials")
    for line in completed.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == ref:
            return parts[0]
    return None


def _anonymous_fetch(url: str, ref: str, git_dir: Path) -> str:
    _init_bare(git_dir)
    completed = binding.anonymous_git("fetch", "-q", "--no-tags", url, "+" + ref + ":" + ref,
                                      git_dir=git_dir)
    if completed.returncode != 0:
        raise Refusal("MESH_SOURCE_NOT_ANONYMOUSLY_FETCHABLE",
                      "fetch_failed:" + url + "#" + ref + ":" + (completed.stderr or "").strip()[-300:],
                      "make " + url + "#" + ref + " fetchable without credentials")
    return _git("rev-parse", ref, git_dir=git_dir).stdout.decode().strip()


def archive_frames(git_dir: Path, tip: str) -> dict[str, bytes]:
    """Every frame in a commit's tree, by key, as `git archive` carries it."""
    raw = _git("archive", "--format=tar", tip, git_dir=git_dir).stdout
    frames: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
        for member in archive.getmembers():
            if member.isfile() and FRAME_PATH.match(member.name):
                frames[member.name] = archive.extractfile(member).read()
    return frames


def union_frames(source: dict[str, bytes], own: dict[str, bytes]) -> dict[str, bytes]:
    """The source queue plus this organization's own frames; a same-key difference is refused."""
    merged = dict(source)
    for key, raw in own.items():
        if key in merged and _parsed(merged[key]) != _parsed(raw):
            raise Refusal("ORGANIZATION_MESH_UNION_CONFLICT", "same_key_content_differs:" + key,
                          "a write-once frame key carries different content on the source and own "
                          "mesh refs; resolve which publisher is wrong before consuming either")
        merged.setdefault(key, raw)
    return merged


def _parsed(raw: bytes) -> Any:
    try:
        return json.loads(raw)
    except ValueError:
        return ("UNPARSEABLE", raw)


def verify_frame(key: str, raw: bytes) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None]:
    """(frame, packet, None) when the frame recomputes under its key, else (None, None, reason)."""
    try:
        frame = json.loads(raw)
    except ValueError:
        return None, None, "frame_not_json"
    if not isinstance(frame, dict):
        return None, None, "frame_not_object"
    try:
        packet = kernel.recover_packet(frame)
    except (ValueError, KeyError, TypeError) as exc:
        return None, None, "recover_packet_refused:" + str(exc)
    if node_store.frame_key(frame) != key:
        return None, None, "frame_key_mismatch"
    return frame, packet, None


def _frame_summary(key: str, frame: dict[str, Any]) -> dict[str, Any]:
    return {"key": key, "packet_id": frame.get("packet_id"), "frame_sha256": frame.get("frame_sha256"),
            "origin_org": frame.get("origin_org"), "destination_org": frame.get("destination_org")}


def materialize(*, source_url: str, source_ref: str, own_url: str, own_ref: str, work: Path,
                mesh: Path, emitting_organization: str) -> dict[str, Any]:
    """Build the durable queue in `mesh`: the source ref united with this organization's own ref."""
    work.mkdir(parents=True, exist_ok=True)
    if (mesh / "frames.d").exists() and any((mesh / "frames.d").iterdir()):
        raise Refusal("ORGANIZATION_MESH_DIRECTORY_NOT_EMPTY", "mesh_directory_not_empty:" + str(mesh),
                      "materialize into a fresh mesh directory")
    source_tip = _anonymous_fetch(source_url, source_ref, work / "source.git")
    source_frames = archive_frames(work / "source.git", source_tip)
    own_git = _init_bare(work / "own.git")
    own_tip = _anonymous_tip(own_url, own_ref)
    if own_tip:
        # The fetched tip, not the listed one: it is the parent a publish builds on.
        own_tip = _anonymous_fetch(own_url, own_ref, own_git)
    own_frames = archive_frames(own_git, own_tip) if own_tip else {}
    merged = union_frames(source_frames, own_frames)

    organization = own_organization()
    accepted: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    refused = []
    for key in sorted(merged):
        frame, packet, reason = verify_frame(key, merged[key])
        if reason is not None:
            refused.append({"key": key, "from": "own" if key in own_frames else "source", "reason": reason})
            continue
        accepted[key] = (frame, packet)
    (mesh / "frames.d").mkdir(parents=True, exist_ok=True)
    for key in accepted:
        (mesh / key).write_bytes(merged[key])

    # What this organization already answered: an ack it originated, carried on
    # its own ref, naming the request it answers and addressed to its origin.
    answered: dict[tuple[str, str], dict[str, Any]] = {}
    for key in own_frames:
        if key not in accepted:
            continue
        frame, packet = accepted[key]
        body = ((packet.get("payload") or {}).get("body") or {})
        if (packet.get("origin") or {}).get("org") == organization and isinstance(body.get("request_packet_id"), str):
            answered[(body["request_packet_id"], (packet.get("destination") or {}).get("org"))] = _frame_summary(key, frame)
    already = []
    for key, (frame, packet) in accepted.items():
        if frame.get("destination_org") != organization:
            continue
        answer = answered.get((frame.get("packet_id"), (packet.get("origin") or {}).get("org")))
        if answer is not None:
            already.append({"request": _frame_summary(key, frame), "answer": answer,
                            "frame_name": node_store.frame_name(key)})
    return {"schema": "stegverse.organization-governance-mesh-materialization/v1",
            "organization": organization, "emitting_organization": emitting_organization,
            "source": {"url": source_url, "ref": source_ref, "tip": source_tip,
                       "frame_keys": sorted(source_frames)},
            "own": {"url": own_url, "ref": own_ref, "tip": own_tip,
                    "frames": [_frame_summary(k, accepted[k][0]) for k in sorted(own_frames) if k in accepted]},
            "mesh_root": str(mesh), "frame_keys": sorted(accepted),
            "addressed_to_organization": sorted(k for k, (f, _) in accepted.items()
                                                if f.get("destination_org") == organization),
            "refused_frames": refused, "already_answered": already,
            "authority_effect": "NONE_MATERIALIZATION_ONLY"}


def _mesh_keys(mesh: Path) -> set[str]:
    directory = mesh / "frames.d"
    return {"frames.d/" + p.name for p in directory.glob("*.json")} if directory.is_dir() else set()


def _item(entry: dict[str, Any]) -> dict[str, Any]:
    result = entry.get("result") or {}
    execution = result.get("execution_result") or {}
    publication = entry.get("response_publication")
    published = None
    if publication:
        frame = publication["frame"]
        published = {**_frame_summary(node_store.frame_key(frame), frame),
                     "message_class": ((publication.get("packet") or {}).get("payload") or {}).get("message_class")}
    return {"frame_key": node_store.MESH_FRAME_PREFIX + node_store.frame_name(str(entry.get("path"))),
            "request_packet_id": (result.get("packet") or {}).get("packet_id") or result.get("packet_id"),
            "status": result.get("status"), "disposition": result.get("disposition"),
            "failed_predicate": result.get("failed_predicate"),
            "service_id": execution.get("service_id"),
            "application_result": execution.get("application_result"),
            "response_publication": published,
            "organization_record": entry.get("organization_record"),
            "seen_marker": entry.get("seen_marker")}


def run_cycle(*, mesh: Path, node_state: Path, repo_ledger: Path,
              materialization: dict[str, Any]) -> dict[str, Any]:
    """consume_and_respond over the materialized queue, with the declared organization store."""
    supplied = os.environ.get("STEGVERSE_REPO_LEDGER_ROOT")
    if not supplied or Path(supplied).resolve() != Path(repo_ledger).resolve():
        raise Refusal("ORGANIZATION_REPOSITORY_LEDGER_NOT_SUPPLIED",
                      "STEGVERSE_REPO_LEDGER_ROOT_must_equal_repo_ledger_root",
                      "set STEGVERSE_REPO_LEDGER_ROOT to the repository ledger root passed to the cycle")
    if not os.environ.get("STEGVERSE_ORG_LEDGER_GIT_DIR"):
        raise Refusal("ORGANIZATION_LEDGER_GIT_DIR_NOT_SUPPLIED", "STEGVERSE_ORG_LEDGER_GIT_DIR_absent",
                      "set STEGVERSE_ORG_LEDGER_GIT_DIR to a run-scoped bare repository")
    if os.environ.get("STEGVERSE_ORG_LEDGER_GIT_REMOTE"):
        raise Refusal("ORGANIZATION_LEDGER_REMOTE_FORBIDDEN", "STEGVERSE_ORG_LEDGER_GIT_REMOTE_set",
                      "propagate_target is null by approved declaration; set no remote")
    _init_bare(Path(os.environ["STEGVERSE_ORG_LEDGER_GIT_DIR"]))
    aggregate = _module("org_governance_decision_aggregate", "resident-runtime/aggregate_repo_transition.py")
    seen = {entry["frame_name"] for entry in materialization.get("already_answered") or []}
    before = _mesh_keys(mesh)
    try:
        store = aggregate.organization_store()
        results = kernel.consume_and_respond(ROOT, mesh_root=mesh, node_state_root=node_state,
                                             repo_ledger_root=repo_ledger, org_ledger_root=store, seen=seen)
    except (ValueError, KeyError, OSError) as exc:
        raise Refusal("ORGANIZATION_GOVERNANCE_CYCLE_REFUSED", type(exc).__name__ + ":" + str(exc)[:300],
                      "repair the named custody or ledger precondition and re-run")
    new_frames = []
    for key in sorted(_mesh_keys(mesh) - before):
        frame = json.loads((mesh / key).read_text(encoding="utf-8"))
        new_frames.append(_frame_summary(key, frame))
    return {"schema": "stegverse.organization-governance-cycle/v1",
            "organization": own_organization(),
            "organization_ledger": {"store": getattr(store, "kind", type(store).__name__),
                                    "ref": getattr(store, "ref", None),
                                    "custody": getattr(store, "custody", None),
                                    "remote": getattr(store, "remote", None)},
            "skipped_already_answered": sorted(seen), "items": [_item(entry) for entry in results],
            "new_frames": new_frames, "authority_effect": "NONE_EXECUTION_RECORD"}


def publish(*, mesh: Path, cycle: dict[str, Any], materialization: dict[str, Any], work: Path,
            own_ref: str, remote: str, push_repo: Path | None = None) -> dict[str, Any]:
    """One fast-forward commit of the cycle's new frames onto this organization's own mesh ref."""
    organization = own_organization()
    emitting = materialization["emitting_organization"]
    new = cycle.get("new_frames") or []
    own_tip = materialization["own"]["tip"]
    if not new:
        return {"published": False, "reason": "NO_NEW_FRAMES_PRODUCED", "ref": own_ref,
                "parent": own_tip, "commit": None, "frames": []}
    own_by_packet = {row["packet_id"]: row for row in materialization["own"]["frames"]}
    frames = []
    for row in new:
        raw = (mesh / row["key"]).read_bytes()
        frame, packet, reason = verify_frame(row["key"], raw)
        if reason is not None:
            raise Refusal("ORGANIZATION_ANSWER_FRAME_INVALID", row["key"] + ":" + reason,
                          "the cycle produced a frame that does not recompute; do not publish it")
        if (packet.get("origin") or {}).get("org") != organization:
            raise Refusal("ORGANIZATION_ANSWER_ORIGIN_MISMATCH", row["key"] + ":origin_not_" + organization,
                          "only frames this organization originates are published on its own ref")
        if frame.get("destination_org") != emitting:
            raise Refusal("ORGANIZATION_ANSWER_DESTINATION_MISMATCH",
                          row["key"] + ":destination_" + str(frame.get("destination_org")) + "_not_" + emitting,
                          "answer only the emitting organization named by mesh_root")
        prior = own_by_packet.get(frame["packet_id"])
        if prior is not None and prior["frame_sha256"] != frame["frame_sha256"]:
            raise Refusal("ORGANIZATION_ANSWER_CONFLICT", frame["packet_id"] + ":already_answered_differently",
                          "an answer with this packet_id is already published with different content")
        frames.append((row["key"], raw, _frame_summary(row["key"], frame)))

    own_git = _init_bare(work / "own.git")
    with tempfile.TemporaryDirectory() as scratch:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(scratch) / "index")}
        if own_tip:
            _git("read-tree", own_tip, git_dir=own_git, env=env)
        else:
            _git("read-tree", "--empty", git_dir=own_git, env=env)
        for key, raw, _ in frames:
            if _git("ls-files", "--", key, git_dir=own_git, env=env).stdout.strip():
                raise Refusal("ORGANIZATION_MESH_UNION_CONFLICT", "new_frame_key_already_on_own_ref:" + key,
                              "a frame this run produced is already on the own ref; nothing to publish")
            oid = _git("hash-object", "-w", "--stdin", git_dir=own_git, data=raw).stdout.decode().strip()
            _git("update-index", "--add", "--cacheinfo", "100644," + oid + "," + key, git_dir=own_git, env=env)
        tree = _git("write-tree", git_dir=own_git, env=env).stdout.decode().strip()
    message = (organization + " governance answers: " + str(len(frames)) + " frame(s) for "
               + emitting + "\n\nsource " + materialization["source"]["url"] + "#"
               + materialization["source"]["ref"] + " @ " + materialization["source"]["tip"] + "\n")
    parents = ["-p", own_tip] if own_tip else []
    commit = _git("commit-tree", "--no-gpg-sign", tree, *parents, "-m", message,
                  git_dir=own_git).stdout.decode().strip()
    _git("update-ref", CANDIDATE_REF, commit, git_dir=own_git)

    pusher = ["git", "-C", str(push_repo)] if push_repo is not None else ["git", "--git-dir", str(own_git)]
    if push_repo is not None:
        fetched = subprocess.run(pusher + ["fetch", "-q", "--no-tags", str(own_git), CANDIDATE_REF],
                                 capture_output=True, text=True, check=False)
        if fetched.returncode != 0:
            raise Refusal("ORGANIZATION_MESH_PUBLISH_FAILED", "candidate_fetch_failed:" + fetched.stderr.strip()[-300:],
                          "repair the publishing checkout and re-run")
    # No '+', no --force: a push that is not a fast-forward of what the remote
    # holds now is rejected by git, and that rejection is the lost race.
    pushed = subprocess.run(pusher + ["push", "--porcelain", remote, commit + ":" + own_ref],
                            capture_output=True, text=True, check=False)
    if pushed.returncode != 0:
        output = (pushed.stdout + pushed.stderr)
        if any(marker in output for marker in ("[rejected]", "non-fast-forward", "fetch first", "stale info")):
            raise Refusal("ORGANIZATION_MESH_PUBLISH_RACE",
                          own_ref + ":not_a_fast_forward_of_" + str(own_tip),
                          "another publisher moved " + own_ref + "; re-run to materialize from its new tip")
        raise Refusal("ORGANIZATION_MESH_PUBLISH_FAILED", own_ref + ":" + output.strip()[-300:],
                      "grant this run contents: write on its own repository and re-run")
    return {"published": True, "ref": own_ref, "parent": own_tip, "commit": commit, "tree": tree,
            "frames": [summary for _, _, summary in frames]}


def _recovered_answer(raw: bytes, key: str, expected: dict[str, Any] | None,
                      emitting: str) -> dict[str, Any]:
    frame, packet, reason = verify_frame(key, raw)
    if reason is not None:
        raise Refusal("ORGANIZATION_MESH_READBACK_MISMATCH", key + ":" + reason,
                      "the published frame does not recompute on a fresh fetch")
    if expected is not None and (frame["frame_sha256"] != expected["frame_sha256"]
                                 or frame["packet_id"] != expected["packet_id"]):
        raise Refusal("ORGANIZATION_MESH_READBACK_MISMATCH", key + ":frame_or_packet_id_differs",
                      "the published frame differs from what this run produced")
    if (packet.get("destination") or {}).get("org") != emitting:
        raise Refusal("ORGANIZATION_MESH_READBACK_MISMATCH", key + ":not_addressed_to_" + emitting,
                      "answers are addressed to the emitting organization")
    payload = packet.get("payload") or {}
    body = payload.get("body") or {}
    application = body.get("application_result") or {}
    return {**_frame_summary(key, frame), "recovered": True,
            "message_class": payload.get("message_class"),
            "destination": packet.get("destination"),
            "request_packet_id": body.get("request_packet_id"),
            "disposition": application.get("disposition"), "reason": application.get("reason"),
            "repository_receipt_sha256": application.get("repository_receipt_sha256"),
            "organization_receipt_sha256": application.get("organization_receipt_sha256")}


def read_back(*, own_url: str, own_ref: str, publication: dict[str, Any],
              materialization: dict[str, Any], work: Path) -> dict[str, Any]:
    """Every answer for this queue, from a fresh anonymous fetch of the own ref."""
    emitting = materialization["emitting_organization"]
    expected = {row["key"]: row for row in publication.get("frames") or []}
    for entry in materialization.get("already_answered") or []:
        expected.setdefault(entry["answer"]["key"], entry["answer"])
    if not expected:
        return {"tip": _anonymous_tip(own_url, own_ref), "answers": [], "verified": True,
                "note": "NO_ANSWER_FRAMES_TO_READ_BACK"}
    git_dir = work / "readback.git"
    if git_dir.exists():
        raise Refusal("ORGANIZATION_MESH_READBACK_NOT_FRESH", "readback_repository_exists:" + str(git_dir),
                      "read back into a fresh repository")
    tip = _anonymous_fetch(own_url, own_ref, git_dir)
    if publication.get("commit"):
        ancestor = _git("merge-base", "--is-ancestor", publication["commit"], tip, git_dir=git_dir, check=False)
        if ancestor.returncode != 0:
            raise Refusal("ORGANIZATION_MESH_READBACK_MISMATCH", own_ref + ":published_commit_not_reachable",
                          "the published commit is not on the fetched ref")
    answers = []
    for key in sorted(expected):
        shown = _git("cat-file", "blob", tip + ":" + key, git_dir=git_dir, check=False)
        if shown.returncode != 0:
            raise Refusal("ORGANIZATION_MESH_READBACK_MISMATCH", key + ":absent_on_fetched_ref",
                          "the published frame is not on the fetched ref")
        answers.append(_recovered_answer(shown.stdout, key, expected[key], emitting))
    return {"tip": tip, "answers": answers, "verified": True}


def decision_authority_pin(path: Path | None = None) -> dict[str, Any]:
    return json.loads((path or ROOT / DECISION_AUTHORITY_PIN).read_text(encoding="utf-8"))


def _requirement_name(spec: str) -> str:
    return re.split(r"[\s<>=!~;\[(]", spec.strip(), maxsplit=1)[0].lower().replace("_", "-")


def authority_requirements(source: Path, pin: dict[str, Any]) -> list[str]:
    """The pinned requirements, refused unless the checkout is the pinned commit and
    they pin exactly the dependencies its pyproject declares."""
    import tomllib
    head = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"], capture_output=True, text=True)
    if head.returncode != 0 or head.stdout.strip() != pin["commit"]:
        raise Refusal("DECISION_AUTHORITY_SOURCE_NOT_PINNED",
                      "head:" + (head.stdout.strip() or "unreadable") + "!=" + pin["commit"],
                      "check out " + pin["repository"] + " at the commit " + DECISION_AUTHORITY_PIN + " pins")
    project = tomllib.loads((source / "pyproject.toml").read_text(encoding="utf-8")).get("project") or {}
    declared = sorted(_requirement_name(spec) for spec in project.get("dependencies") or [])
    pinned = sorted(_requirement_name(spec) for spec in pin["requirements"])
    if project.get("name") != pin["package"] or declared != pinned or \
            not all(re.fullmatch(r"[A-Za-z0-9._-]+==[A-Za-z0-9.]+", spec) for spec in pin["requirements"]):
        raise Refusal("DECISION_AUTHORITY_REQUIREMENTS_NOT_PINNED",
                      "declared:" + ",".join(declared) + ";pinned:" + ",".join(pin["requirements"]),
                      "pin each dependency " + pin["repository"] + " declares, and no other, with ==")
    return list(pin["requirements"])


def evaluator_record(pin: dict[str, Any], *, installed: bool) -> dict[str, Any]:
    """Which evaluator this run's decisions were made by."""
    if not installed:
        return dict(EVALUATOR_NOT_PROVIDED)
    from importlib import metadata
    try:
        importlib.import_module(pin["decision_authority"].rsplit(".", 1)[0])
        version = metadata.version(pin["package"])
    except (ImportError, metadata.PackageNotFoundError) as exc:
        raise Refusal("DECISION_AUTHORITY_INSTALL_UNVERIFIED", pin["package"] + ":" + type(exc).__name__,
                      "the installed " + pin["repository"] + " must import and report its version") from exc
    return {"installed": True, "commit": pin["commit"], "version": version}


def build_report(evidence: Path, *, mesh_root: str) -> tuple[dict[str, Any], int]:
    def load(name: str) -> Any:
        path = evidence / name
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
    bound, materialized, cycle, published, readback = (
        load("binding.json"), load("materialization.json"), load("cycle.json"),
        load("publication.json"), load("readback.json"))
    evaluator = load("evaluator.json")
    installed = bool((evaluator or {}).get("installed"))
    failure = load("fail_closed.json")
    if failure is None and (bound or {}).get("disposition") == "FAIL_CLOSED":
        failure = bound
    items = (cycle or {}).get("items") or []
    crossing_fail_closed = [item for item in items
                            if item.get("status") == "REFUSED" and item.get("disposition") == "FAIL_CLOSED"]
    decisions = [{"request_packet_id": item.get("request_packet_id"),
                  "disposition": (item.get("application_result") or {}).get("disposition"),
                  "reason": (item.get("application_result") or {}).get("reason"),
                  "repository_receipt_sha256": (item.get("application_result") or {}).get("repository_receipt_sha256"),
                  "organization_receipt_sha256": (item.get("application_result") or {}).get("organization_receipt_sha256"),
                  "crossing_record": item.get("organization_record"),
                  "answer": item.get("response_publication")}
                 for item in items if item.get("application_result")]
    # A successful workflow is not a governance decision. If addressed requests
    # produced neither a decision nor an authenticated already-published answer,
    # fail closed instead of reporting COMPLETED with zero decision evidence.
    addressed = set((materialized or {}).get("addressed_to_organization") or [])
    answered_keys = {row.get("request", {}).get("key")
                     for row in (materialized or {}).get("already_answered") or []}
    decided_keys = {item.get("frame_key") for item in items
                    if (item.get("application_result") or {}).get("disposition")
                    in {"ALLOW", "DENY", "FAIL_CLOSED"}}
    pending = sorted(addressed - answered_keys - decided_keys)
    if failure is None and pending:
        failure = binding.fail_closed(
            "ORGANIZATION_GOVERNANCE_DECISION_MISSING",
            "addressed_frames_without_decision:" + ",".join(pending)[:500],
            "repair receiver dispatch or decision publication and rerun with authenticated evidence")
    # A local decision is not an authenticated return. Require the independently
    # fetched own-ref answer evidence before reporting a completed decision run.
    if failure is None and decisions and (readback or {}).get("verified") is not True:
        failure = binding.fail_closed(
            "ORGANIZATION_GOVERNANCE_READBACK_NOT_VERIFIED",
            "decision_exists_without_verified_fresh_ref_readback",
            "publish the decision answer on the authorized own mesh ref and verify by fresh fetch")
    if failure is None and crossing_fail_closed:
        failure = binding.fail_closed(
            "ORGANIZATION_CROSSING_FAIL_CLOSED",
            ";".join(str(item.get("frame_key")) + ":" + str(item.get("failed_predicate"))
                     for item in crossing_fail_closed)[:600],
            "repair the named crossing precondition; FAIL_CLOSED crossings are left unmarked and retried")
    report = {"schema": REPORT_SCHEMA, "organization": own_organization(), "mesh_root": mesh_root,
              "source_tip": ((materialized or {}).get("source") or {}).get("tip") or (bound or {}).get("source_tip"),
              "own_ref": OWN_MESH_REF,
              "own_tip_before": ((materialized or {}).get("own") or {}).get("tip"),
              "own_tip_after": (readback or {}).get("tip"),
              "refused_frames": (materialized or {}).get("refused_frames"),
              "already_answered": (materialized or {}).get("already_answered"),
              "decisions": decisions,
              "evaluator": evaluator,
              "decision_authority_installed": installed,
              "decision_authority_commit": evaluator["commit"] if installed else None,
              "published": published,
              "readback": readback,
              "ledger_persistence": LEDGER_PERSISTENCE,
              "ledger_persistence_note": ("the repository and organization receipts are real appends to "
                                          "run-scoped ledgers; by the approved declaration "
                                          "(organization_ledger.propagate_target null) they are published nowhere"),
              "organization_ledger": (cycle or {}).get("organization_ledger"),
              "workflow_disposition": "FAIL_CLOSED" if failure else "COMPLETED",
              "fail_closed": failure,
              "authority_effect": "NONE_REPORT_ONLY"}
    return report, 1 if failure else 0


def _write(path: Path, document: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--evidence", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    m = sub.add_parser("materialize")
    m.add_argument("--work", type=Path, required=True)
    m.add_argument("--mesh", type=Path, required=True)
    m.add_argument("--own-url", required=True)
    c = sub.add_parser("cycle")
    c.add_argument("--mesh", type=Path, required=True)
    c.add_argument("--node-state", type=Path, required=True)
    c.add_argument("--repo-ledger", type=Path, required=True)
    p = sub.add_parser("publish")
    p.add_argument("--mesh", type=Path, required=True)
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--remote", required=True)
    p.add_argument("--push-repo", type=Path)
    r = sub.add_parser("readback")
    r.add_argument("--work", type=Path, required=True)
    r.add_argument("--own-url", required=True)
    s = sub.add_parser("report")
    s.add_argument("--mesh-root", required=True)
    q = sub.add_parser("authority-requirements")
    q.add_argument("--source", type=Path, required=True)
    q.add_argument("--out", type=Path, required=True)
    e = sub.add_parser("evaluator")
    e.add_argument("--installed", action="store_true")
    args = parser.parse_args(argv)
    evidence = args.evidence
    try:
        if args.command == "authority-requirements":
            requirements = authority_requirements(args.source, decision_authority_pin())
            args.out.write_text("\n".join(requirements) + "\n", encoding="utf-8")
            print("\n".join(requirements))
            return 0
        if args.command == "evaluator":
            document = evaluator_record(decision_authority_pin(), installed=args.installed)
            name = "evaluator.json"
        elif args.command == "materialize":
            bound = _read(evidence / "binding.json")
            if bound.get("disposition") == "FAIL_CLOSED":
                raise Refusal(bound["failure_code"], bound["failed_predicate"], bound["required_evidence_or_repair"])
            document = materialize(source_url=bound["url"], source_ref=bound["ref"], own_url=args.own_url,
                                   own_ref=OWN_MESH_REF, work=args.work, mesh=args.mesh,
                                   emitting_organization=bound["emitting_organization"])
            name = "materialization.json"
        elif args.command == "cycle":
            document = run_cycle(mesh=args.mesh, node_state=args.node_state, repo_ledger=args.repo_ledger,
                                 materialization=_read(evidence / "materialization.json"))
            name = "cycle.json"
        elif args.command == "publish":
            document = publish(mesh=args.mesh, cycle=_read(evidence / "cycle.json"),
                               materialization=_read(evidence / "materialization.json"), work=args.work,
                               own_ref=OWN_MESH_REF, remote=args.remote, push_repo=args.push_repo)
            name = "publication.json"
        elif args.command == "readback":
            document = read_back(own_url=args.own_url, own_ref=OWN_MESH_REF,
                                 publication=_read(evidence / "publication.json"),
                                 materialization=_read(evidence / "materialization.json"), work=args.work)
            name = "readback.json"
        else:
            report, status = build_report(evidence, mesh_root=args.mesh_root)
            _write(evidence / "report.json", report)
            print(json.dumps(report, indent=2, sort_keys=True))
            return status
    except Refusal as exc:
        _write(evidence / "fail_closed.json", exc.document)
        print(json.dumps(exc.document, indent=2, sort_keys=True))
        return 1
    _write(evidence / name, document)
    print(json.dumps(document, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
