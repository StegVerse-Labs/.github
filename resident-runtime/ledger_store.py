#!/usr/bin/env python3
"""Storage for an append-only organization ledger, addressed rather than located.

The ledger's own model is already substrate-neutral: receipts are content
addressed and hash linked, and the chain is verified by recomputing digests.
What bound it to one machine was its storage, not its model -- a POSIX
filesystem under a home directory, a `fcntl` advisory lock as the whole
concurrency model, same-filesystem atomic rename for durability, and
directory enumeration as the integrity check. None of those survive a move to
ephemeral nodes that share no filesystem.

This module is the seam. The ledger addresses documents by key; a store maps
keys onto whatever substrate it has. `PosixLedgerStore` keeps today's exact
behaviour, so the filesystem remains a first-class implementation rather than
a legacy path, and a key-value store is a sibling rather than a rewrite.

Keys are `HEAD`, `receipts/<hex>` and `source-receipts/<hex>`. Nothing here
grants authority.

`GitLedgerStore` is the durable sibling on the canonical Git substrate: keys
are files on one dedicated ledger ref, and an append is one commit published
by a kernel-local ref compare-and-swap. A remote is never read or written
inside a transition; it is reached only by the explicit `materialize` (before
invocation) and `propagate` (after a completed local append) steps. Git is
transport and custody only, never admission or authority.

Packet release and batch custody add `BATCH_HEAD.json` and `batches/<hex>`.
On a store without a local lock, one Organization transition -- a released
batch, its BATCH_HEAD, any establishment receipt, the work receipt and HEAD --
is staged by `StagedLedgerTransaction` over one pinned snapshot and published
as one commit, so a lost race publishes none of it.
"""
from __future__ import annotations

import fcntl
import json
import os
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

HEAD_KEY = "HEAD.json"
RECEIPT_PREFIX = "receipts/"
SOURCE_PREFIX = "source-receipts/"


def receipt_key(digest):
    """Address a receipt by its own digest, so the key carries the content.

    The key keeps the `.json` suffix a filesystem store would give the file
    anyway, so a POSIX store's paths are unchanged by this indirection and an
    existing ledger root stays readable.
    """
    return RECEIPT_PREFIX + digest.split(":", 1)[1] + ".json"


def source_key(digest):
    """Address an exact retained source transition receipt by its source digest."""
    return SOURCE_PREFIX + digest.split(":", 1)[1] + ".json"


class PosixLedgerStore:
    """A ledger store on one POSIX filesystem.

    Durability is same-directory atomic replacement plus an fsync of the file
    and its directory. Appenders are serialized by an advisory lock, which
    holds only within one kernel -- two nodes on separate filesystems would
    each take "the lock" and both append. A networked store implements
    `exclusive` as a no-op and serializes through `compare_and_swap` instead.
    """

    kind = "POSIX_FILESYSTEM"

    def __init__(self, root):
        self.root = Path(root)
        self._lock_path = self.root / ".append.lock"
        self._held = 0

    def _path(self, key):
        return self.root / key

    def initialize(self):
        (self.root / RECEIPT_PREFIX.rstrip("/")).mkdir(parents=True, exist_ok=True)

    def locator(self, key):
        """How this substrate names the key, for a reader outside the ledger."""
        return str(self._path(key))

    def exists(self, key):
        return self._path(key).is_file()

    def get(self, key):
        path = self._path(key)
        if not path.is_file():
            return None
        return json.loads(path.read_text())

    def put(self, key, value):
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(prefix=".org-append-", suffix=".tmp", dir=str(path.parent))
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(json.dumps(value, indent=2, sort_keys=True).encode() + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, path)
            self._sync_directory(path.parent)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)

    def list_prefix(self, prefix):
        directory = self._path(prefix.rstrip("/"))
        if not directory.is_dir():
            return set()
        return {prefix + item.name for item in directory.glob("*.json")}

    @contextmanager
    def exclusive(self):
        """Serialize appenders, re-entrantly within one store instance.

        `flock` is held per open file description, so a second acquisition
        from the same process would block on the first forever. Callers nest
        legitimately -- compare_and_swap serializes internally and may be
        invoked from inside an append -- so re-entry is counted rather than
        re-locked.
        """
        if self._held:
            self._held += 1
            try:
                yield self
            finally:
                self._held -= 1
            return
        self.root.mkdir(parents=True, exist_ok=True)
        with self._lock_path.open("a+b") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            self._held = 1
            try:
                yield self
            finally:
                self._held = 0

    @contextmanager
    def assume_exclusive(self):
        """Enter `exclusive` for a caller that already holds this root's append lock.

        A second `flock` from a new open file description would block on the
        caller's own lock, so the held lock is counted rather than re-taken.
        """
        self._held += 1
        try:
            yield self
        finally:
            self._held -= 1

    def compare_and_swap(self, key, expected, value):
        """Publish `value` at `key` only if it still holds `expected`.

        Serialization a networked store gets natively. Here it is the advisory
        lock again, so the guarantee is the same one `exclusive` gives and no
        stronger.
        """
        with self.exclusive():
            if self.get(key) != expected:
                return False
            self.put(key, value)
            return True


    def append_transaction(self, receipt_key_name, receipt, expected_head, new_head, immutable=None):
        """Atomically publish a receipt and HEAD if HEAD still equals expected_head.

        This is the substrate portability contract. A lost comparison writes
        nothing, so a competing writer cannot leave an orphan receipt. A
        network/KV sibling implements this with its native transaction/CAS;
        POSIX uses its local lock only inside the storage primitive.

        `immutable` maps further content-addressed keys (the exact source
        transition receipt under `source-receipts/`) to their documents. They
        are inside the same boundary: every collision is checked before any
        write, so a refused or lost append writes none of them, and HEAD is
        written last, so a document is published only once HEAD names its
        receipt.
        """
        documents = dict(immutable or {})
        documents[receipt_key_name] = receipt
        with self.exclusive():
            if self.get(HEAD_KEY) != expected_head:
                return False
            missing = []
            for key, value in documents.items():
                existing = self.get(key)
                if existing is not None and existing != value:
                    raise ValueError("ledger_receipt_collision")
                if existing is None:
                    missing.append(key)
            for key in missing:
                self.put(key, documents[key])
            self.put(HEAD_KEY, new_head)
            return True

    @staticmethod
    def _sync_directory(directory):
        fd = os.open(str(directory), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


LEDGER_REF_PREFIX = "refs/heads/organization-ledger/"
PRIVATE_CUSTODY = "PRIVATE"
PAYLOAD_CLASSIFICATION = "ORGANIZATION_LEDGER_PRIVATE_EVIDENCE"
CAS_PREDICATE = "ORGANIZATION_LEDGER_REF_COMPARE_AND_SWAP"
APPEND_RETRY_ENTRYPOINT = "resident-runtime/aggregate_repo_transition.py::aggregate_transition"
PROPAGATION_RETRY_ENTRYPOINT = "resident-runtime/ledger_store.py::GitLedgerStore.propagate"
MATERIALIZATION_RETRY_ENTRYPOINT = "resident-runtime/ledger_store.py::GitLedgerStore.materialize"
FORK_PREDICATE = "ORGANIZATION_LEDGER_FORK_DETECTED"


class LedgerStoreRefused(ValueError):
    """A typed FAIL_CLOSED from the store: nothing was published, nothing was decided.

    A store refusal is never DENY: it says the substrate did not carry the
    transaction, not that the transition was wrong. It names its retry
    entrypoint and never waits or loops.
    """

    def __init__(self, failed_predicate, required_evidence_or_repair, *, detail=""):
        super().__init__(failed_predicate + (": " + detail if detail else ""))
        self.failed_predicate = failed_predicate
        self.required_evidence_or_repair = required_evidence_or_repair
        self.detail = detail
        self.retry_entrypoint = APPEND_RETRY_ENTRYPOINT

    def refusal(self):
        refusal = {
            "schema": "stegverse.organization-ledger-append-refusal/v1",
            "disposition": "FAIL_CLOSED",
            "failed_predicate": self.failed_predicate,
            "required_evidence_or_repair": self.required_evidence_or_repair,
            "retry_entrypoint": self.retry_entrypoint,
            "consequence_committed": False,
            "authority_effect": "NONE_REFUSAL_ONLY",
        }
        if self.detail:
            refusal["detail"] = self.detail
        return refusal


def lost_race(detail=""):
    """The refusal an appender gets when the ledger ref moved under it."""
    return LedgerStoreRefused(
        CAS_PREDICATE,
        "re-read the Organization ledger ref and attempt the append again from its current HEAD",
        detail=detail,
    )


class GitLedgerStore:
    """A ledger store on one dedicated ref of a Git repository.

    Keys are files in the tree of `ref` in `git_dir`, the authoritative local
    ledger. Reads come from the committed local ref only, never a working tree
    and never a remote. An append is one commit holding the receipt, any
    immutable documents and HEAD, built on the expected parent and published by
    the kernel-local compare-and-swap `git update-ref <ref> <new> <old>`. A
    lost race publishes nothing and is a typed FAIL_CLOSED; the store never
    waits or retries.

    A `remote` is custody transport only and never a transition predicate (F75-01):
    no remote CAS gates an append, so completion never awaits another
    machine. `materialize` seeds the local ref from the remote before
    invocation; `propagate` pushes a completed local append afterwards, fast
    forward only, and returns a typed non-gating disposition. Neither is
    invoked by a transition; if propagation is not admitted it is not invoked.

    Every ledger payload is classified ORGANIZATION_LEDGER_PRIVATE_EVIDENCE: a
    retained source receipt carries its inline evidence bytes. An append is
    refused unless the materializer declares the repository an authorized
    private custody surface (`custody="PRIVATE"`); nothing is redacted and
    nothing is published to a surface not declared private. Git hosting and
    credentials are transport and custody only, never admission or authority.
    """

    kind = "GIT_REF"

    def __init__(self, git_dir, ref, *, remote=None, custody=None):
        if not isinstance(ref, str) or not ref.startswith(LEDGER_REF_PREFIX) or ref == LEDGER_REF_PREFIX:
            raise LedgerStoreRefused(
                "ORGANIZATION_LEDGER_REF_INVALID",
                "supply a dedicated Organization ledger ref under " + LEDGER_REF_PREFIX,
                detail=str(ref),
            )
        self.git_dir = Path(git_dir).expanduser().resolve()
        self.ref = ref
        self.remote = remote or None
        self.custody = custody
        self._held = 0
        self._pinned = None
        if self._git("check-ref-format", ref, check=False).returncode != 0:
            raise LedgerStoreRefused("ORGANIZATION_LEDGER_REF_INVALID",
                                     "supply a well-formed Git ref name", detail=ref)

    def _git(self, *args, data=None, env=None, check=True):
        environment = dict(os.environ)
        # A missing credential is a refusal, not a prompt to wait on.
        environment["GIT_TERMINAL_PROMPT"] = "0"
        environment.update(env or {})
        result = subprocess.run(
            ["git", "--git-dir", str(self.git_dir), *args],
            input=data, capture_output=True, env=environment,
        )
        if check and result.returncode != 0:
            raise LedgerStoreRefused(
                "ORGANIZATION_LEDGER_GIT_OPERATION_FAILED",
                "supply a readable Organization ledger repository and ref",
                detail=" ".join(args[:1]) + ": " + result.stderr.decode(errors="replace").strip(),
            )
        return result

    def initialize(self):
        if not self.git_dir.is_dir() or self._git("rev-parse", "--git-dir", check=False).returncode != 0:
            raise LedgerStoreRefused(
                "ORGANIZATION_LEDGER_GIT_REPOSITORY_UNAVAILABLE",
                "supply the Organization ledger Git repository as materialized for this execution",
                detail=str(self.git_dir),
            )

    def locator(self, key):
        """The key on the ledger ref; never a host path or a credentialed URL."""
        return self.ref + ":" + key

    def _tip(self):
        """The committed tip of the local ledger ref, or None before genesis."""
        self.initialize()
        found = self._git("rev-parse", "--verify", "-q", self.ref + "^{commit}", check=False)
        return found.stdout.decode().strip() if found.returncode == 0 else None

    # --- Custody transport: explicit steps outside every transition (F75-01) ---

    def _disposition(self, disposition, step, *, local_tip, remote_tip, failed_predicate=None,
                     required=None, retry=None, detail=""):
        result = {
            "schema": "stegverse.organization-ledger-" + step + "/v1",
            "disposition": disposition,
            "ref": self.ref,
            "local_tip": local_tip,
            "remote_tip": remote_tip,
            "authority_effect": "NONE_CUSTODY_TRANSPORT_ONLY",
        }
        if failed_predicate is not None:
            result.update(failed_predicate=failed_predicate, required_evidence_or_repair=required,
                          retry_entrypoint=retry)
        if detail:
            result["detail"] = detail
        return result

    def _remote_tip(self):
        """(True, tip-or-None) from the remote's ref, or (False, stderr) if unreachable."""
        listed = self._git("ls-remote", "--refs", self.remote, self.ref, check=False)
        if listed.returncode != 0:
            return False, listed.stderr.decode(errors="replace").strip()
        rows = [line.split("\t") for line in listed.stdout.decode().splitlines() if line.strip()]
        return True, next((oid for oid, name in rows if name == self.ref), None)

    def _has_commit(self, oid):
        return self._git("cat-file", "-e", oid + "^{commit}", check=False).returncode == 0

    def _is_ancestor(self, older, newer):
        return self._git("merge-base", "--is-ancestor", older, newer, check=False).returncode == 0

    def _fetch_objects(self, tip):
        """Bring the remote tip's objects in without moving any ref; True if present after."""
        if not self._has_commit(tip):
            self._git("fetch", "--no-tags", "--quiet", self.remote, self.ref, check=False)
        return self._has_commit(tip)

    def _unreachable(self, step, retry, local_tip, detail):
        return self._disposition(
            "FAIL_CLOSED", step, local_tip=local_tip, remote_tip=None,
            failed_predicate="ORGANIZATION_LEDGER_REMOTE_UNREACHABLE",
            required="supply a reachable Organization ledger remote and its transport credential, then "
                     "invoke the retry entrypoint", retry=retry, detail=detail)

    def _fork(self, step, retry, local_tip, remote_tip):
        return self._disposition(
            "FAIL_CLOSED", step, local_tip=local_tip, remote_tip=remote_tip,
            failed_predicate=FORK_PREDICATE,
            required="the local and remote Organization ledger refs diverged: two writers appended to "
                     "one ledger; neither is rewritten, resolve custody before retrying",
            retry=retry)

    def materialize(self):
        """Seed the local ledger ref from the remote, before any invocation.

        Never called by a transition. The local ref is created or fast-forwarded
        to the remote tip by the local compare-and-swap; a local ref ahead of the
        remote is left as is (awaiting `propagate`). A divergence is reported as
        a fork, an unreachable remote as FAIL_CLOSED; the local ref is unchanged
        in both and nothing waits or retries.
        """
        step, retry = "materialization", MATERIALIZATION_RETRY_ENTRYPOINT
        local = self._tip()
        if self.remote is None:
            return self._disposition("MATERIALIZED", step, local_tip=local, remote_tip=None)
        reached, remote = self._remote_tip()
        if not reached:
            return self._unreachable(step, retry, local, remote)
        if remote is None or remote == local:
            return self._disposition("MATERIALIZED", step, local_tip=local, remote_tip=remote)
        if not self._fetch_objects(remote):
            return self._unreachable(step, retry, local, "remote tip objects not fetched: " + remote)
        if local is not None and self._is_ancestor(remote, local):
            return self._disposition("MATERIALIZED", step, local_tip=local, remote_tip=remote)
        if local is not None and not self._is_ancestor(local, remote):
            return self._fork(step, retry, local, remote)
        moved = self._git("update-ref", self.ref, remote, local or "", check=False)
        if moved.returncode != 0:
            raise lost_race(moved.stderr.decode(errors="replace").strip())
        return self._disposition("MATERIALIZED", step, local_tip=remote, remote_tip=remote)

    def propagate(self):
        """Push the completed local ledger to the remote, fast-forward only.

        Invoked only after a completed local append, never inside one; the
        local append is authoritative and is neither undone nor blocked by any
        outcome here. The lease names the remote tip just observed, which must
        be an ancestor of the local tip, so the push never rewrites the remote.
        Returns PROPAGATED (also for an exact retry once the remote holds the
        local tip), FAIL_CLOSED with the propagate retry entrypoint for an
        unreachable or unconfirmed remote, or FAIL_CLOSED
        ORGANIZATION_LEDGER_FORK_DETECTED for a divergence -- detected, not
        prevented. It never waits or retries.
        """
        self.require_private_custody()
        step, retry = "propagation", PROPAGATION_RETRY_ENTRYPOINT
        local = self._tip()
        if self.remote is None:
            return self._disposition(
                "FAIL_CLOSED", step, local_tip=local, remote_tip=None,
                failed_predicate="ORGANIZATION_LEDGER_REMOTE_NOT_SUPPLIED",
                required="supply the Organization ledger remote this materialization propagates to",
                retry=retry)
        reached, remote = self._remote_tip()
        if not reached:
            return self._unreachable(step, retry, local, remote)
        if remote == local:
            return self._disposition("PROPAGATED", step, local_tip=local, remote_tip=remote)
        if remote is not None:
            if not self._fetch_objects(remote):
                return self._unreachable(step, retry, local, "remote tip objects not fetched: " + remote)
            if local is not None and self._is_ancestor(local, remote):
                # The remote already holds every local commit; nothing to carry.
                return self._disposition("PROPAGATED", step, local_tip=local, remote_tip=remote)
            if local is None or not self._is_ancestor(remote, local):
                return self._fork(step, retry, local, remote)
        if local is None:
            return self._disposition("PROPAGATED", step, local_tip=None, remote_tip=None)
        pushed = self._git(
            "push", "--porcelain", "--no-verify",
            "--force-with-lease=" + self.ref + ":" + (remote or ""),
            self.remote, local + ":" + self.ref, check=False,
        )
        if pushed.returncode != 0:
            return self._disposition(
                "FAIL_CLOSED", step, local_tip=local, remote_tip=remote,
                failed_predicate="ORGANIZATION_LEDGER_REMOTE_PUBLISH_UNCONFIRMED",
                required="invoke the retry entrypoint; it re-reads the remote ref and reports "
                         "PROPAGATED, a fork, or this refusal again",
                retry=retry, detail=(pushed.stdout + pushed.stderr).decode(errors="replace").strip())
        return self._disposition("PROPAGATED", step, local_tip=local, remote_tip=local)

    def _snapshot(self):
        return self._pinned[0] if self._pinned is not None else self._tip()

    def _read(self, tip, key):
        if tip is None:
            return None
        found = self._git("rev-parse", "--verify", "-q", tip + ":" + key, check=False)
        if found.returncode != 0:
            return None
        blob = found.stdout.decode().strip()
        return json.loads(self._git("cat-file", "blob", blob).stdout)

    def exists(self, key):
        return self.get(key) is not None

    def get(self, key):
        return self._read(self._snapshot(), key)

    def list_prefix(self, prefix):
        tip = self._snapshot()
        if tip is None:
            return set()
        listed = self._git("ls-tree", "--name-only", tip, "--", prefix.rstrip("/") + "/")
        return {name for name in listed.stdout.decode().splitlines()
                if name.startswith(prefix) and name.endswith(".json") and "/" not in name[len(prefix):]}

    @contextmanager
    def exclusive(self):
        """Pin one committed snapshot; the compare-and-swap at publish is the lock.

        Nothing is held against other appenders. Reads inside see one tip, and
        `append_transaction` publishes only if the ref is still that tip.
        """
        if self._held:
            self._held += 1
            try:
                yield self
            finally:
                self._held -= 1
            return
        self._pinned = (self._tip(),)
        self._held = 1
        try:
            yield self
        finally:
            self._held = 0
            self._pinned = None

    assume_exclusive = exclusive

    def compare_and_swap(self, key, expected, value):
        raise LedgerStoreRefused(
            "ORGANIZATION_LEDGER_SINGLE_KEY_WRITE_REFUSED",
            "publish through append_transaction, the only write this store performs",
        )

    def put(self, key, value):
        self.compare_and_swap(key, None, value)

    @staticmethod
    def _encode(value):
        return json.dumps(value, indent=2, sort_keys=True).encode() + b"\n"

    def append_transaction(self, receipt_key_name, receipt, expected_head, new_head, immutable=None):
        """Publish receipt, immutable documents and HEAD as one commit by ref CAS.

        Returns True when published. A HEAD that no longer equals
        `expected_head`, or a ref that moved before publication, raises the
        typed lost-race FAIL_CLOSED; nothing reaches the ref, so no orphan
        receipt is committed. A key already holding different content raises
        `ledger_receipt_collision` before anything is built.
        """
        self.require_private_custody()
        documents = dict(immutable or {})
        documents[receipt_key_name] = receipt
        with self.exclusive():
            if self._read(self._snapshot(), HEAD_KEY) != expected_head:
                raise lost_race("HEAD no longer equals the expected head")
            return self.publish(documents, {HEAD_KEY: new_head}, receipt_key_name)

    def require_private_custody(self):
        """Refuse before anything is built unless the surface is declared private custody."""
        if self.custody != PRIVATE_CUSTODY:
            raise LedgerStoreRefused(
                "ORGANIZATION_LEDGER_PRIVATE_CUSTODY_SURFACE_REQUIRED",
                "supply an Organization ledger repository the materializer declares an authorized "
                "private custody surface (custody PRIVATE); ledger payload is classified "
                + PAYLOAD_CLASSIFICATION + " and is not published elsewhere",
                detail=str(self.custody),
            )

    def publish(self, immutable, mutable, subject):
        """Publish documents as one commit on the pinned tip by ref compare-and-swap.

        `immutable` keys are content addressed: a key already holding different
        content raises `ledger_receipt_collision` before anything is built, and
        one holding the same content is not rewritten. `mutable` keys (HEAD,
        BATCH_HEAD) are replaced. The commit's parent is the snapshot every read
        inside `exclusive` saw, so a ref that moved since raises the typed lost
        race and nothing reaches it.
        """
        self.require_private_custody()
        with self.exclusive():
            parent = self._snapshot()
            missing = []
            for key, value in immutable.items():
                existing = self._read(parent, key)
                if existing is not None and existing != value:
                    raise ValueError("ledger_receipt_collision")
                if existing is None:
                    missing.append(key)
            entries = [(key, immutable[key]) for key in missing] + list(mutable.items())
            commit = self._commit(parent, entries, subject)
            self._publish(commit, parent)
            self._pinned = (commit,)
            return True

    def _commit(self, parent, entries, subject):
        with tempfile.TemporaryDirectory(prefix="org-ledger-index-") as scratch:
            index = {"GIT_INDEX_FILE": os.path.join(scratch, "index")}
            if parent is None:
                self._git("read-tree", "--empty", env=index)
            else:
                self._git("read-tree", parent, env=index)
            for key, value in entries:
                blob = self._git("hash-object", "-w", "--stdin", data=self._encode(value)).stdout.decode().strip()
                self._git("update-index", "--add", "--cacheinfo", "100644," + blob + "," + key, env=index)
            tree = self._git("write-tree", env=index).stdout.decode().strip()
        identity = {
            "GIT_AUTHOR_NAME": "stegverse-organization-ledger",
            "GIT_AUTHOR_EMAIL": "organization-ledger@stegverse.invalid",
            "GIT_COMMITTER_NAME": "stegverse-organization-ledger",
            "GIT_COMMITTER_EMAIL": "organization-ledger@stegverse.invalid",
        }
        args = ["commit-tree", tree, "-m", "organization ledger append " + subject]
        if parent is not None:
            args[2:2] = ["-p", parent]
        return self._git(*args, env=identity).stdout.decode().strip()

    def _publish(self, commit, parent):
        """Move the local ref from exactly `parent` to `commit`, or raise the lost race.

        Kernel-local only: the remote is never consulted here (see `propagate`).
        """
        moved = self._git("update-ref", self.ref, commit, parent or "", check=False)
        if moved.returncode != 0:
            raise lost_race(moved.stderr.decode(errors="replace").strip())


class StagedLedgerTransaction:
    """Every write of one Organization transition, staged over one pinned snapshot.

    Packet release and batch custody write a batch, BATCH_HEAD, possibly an
    establishment receipt, then the work receipt and HEAD. A store with a local
    lock writes them in order under that lock. A store without one (the Git
    ref) cannot hold a lock across them, so they are staged here: reads see the
    staged documents over the store's pinned snapshot, and `commit` publishes
    them all as one compare-and-swap from that snapshot. A lost race publishes
    none of them; a refusal or error before `commit` publishes nothing.

    Use only inside the store's own `exclusive`, which pins the snapshot.
    """

    def __init__(self, store):
        self.store = store
        self.kind = store.kind
        self._immutable = {}
        self._mutable = {}
        self._subjects = []

    def initialize(self):
        self.store.initialize()

    def locator(self, key):
        return self.store.locator(key)

    def get(self, key):
        if key in self._mutable:
            return self._mutable[key]
        if key in self._immutable:
            return self._immutable[key]
        return self.store.get(key)

    def exists(self, key):
        return self.get(key) is not None

    def list_prefix(self, prefix):
        staged = {key for key in [*self._immutable, *self._mutable]
                  if key.startswith(prefix) and key.endswith(".json") and "/" not in key[len(prefix):]}
        return self.store.list_prefix(prefix) | staged

    @contextmanager
    def exclusive(self):
        yield self

    assume_exclusive = exclusive

    def put(self, key, value):
        """Stage a replaceable document (HEAD, BATCH_HEAD)."""
        self._mutable[key] = value

    def put_immutable(self, key, value):
        """Stage a content-addressed document; different content at its key is a collision."""
        existing = self.get(key)
        if existing is not None and existing != value:
            raise ValueError("ledger_receipt_collision")
        if existing is None:
            self._immutable[key] = value

    def compare_and_swap(self, key, expected, value):
        if self.get(key) != expected:
            return False
        self.put(key, value)
        return True

    def append_transaction(self, receipt_key_name, receipt, expected_head, new_head, immutable=None):
        documents = dict(immutable or {})
        documents[receipt_key_name] = receipt
        if self.get(HEAD_KEY) != expected_head:
            return False
        for key, value in documents.items():
            existing = self.get(key)
            if existing is not None and existing != value:
                raise ValueError("ledger_receipt_collision")
        for key, value in documents.items():
            self.put_immutable(key, value)
        self.put(HEAD_KEY, new_head)
        self._subjects.append(receipt_key_name)
        return True

    def commit(self):
        """Publish everything staged as one commit; nothing staged publishes nothing."""
        if not self._immutable and not self._mutable:
            return False
        subject = " ".join(self._subjects) or " ".join(sorted(self._mutable))
        return self.store.publish(self._immutable, self._mutable, subject)
