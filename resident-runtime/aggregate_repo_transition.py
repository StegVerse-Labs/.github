#!/usr/bin/env python3
import argparse,base64,fcntl,hashlib,importlib.util,io,json,os,re,shutil,subprocess,tarfile,tempfile
from datetime import datetime,timezone
from pathlib import Path,PurePosixPath

ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/".stegverse/transition-ledger/org-contract.json").read_text())
# The heartbeat is the ecosystem's time base and the kernel owns its derivation,
# loaded exactly as the repository ledger (.stegverse/transition-ledger/emit.py)
# loads it, so a repository receipt and the organization receipt consuming it
# cannot disagree about what an epoch is. `observed_at` stays as non-ordering
# provenance; ordering is the chain plus the heartbeat reference.
_kspec=importlib.util.spec_from_file_location("kernel",ROOT/"org-kernel/kernel.py")
kernel=importlib.util.module_from_spec(_kspec);_kspec.loader.exec_module(kernel)

# --- The Organization ledger locus -------------------------------------------
# The Organization ledger's durable locus is declared by the Organization
# manifest above as `organization_ledger_locus`: a repository, a ref in that
# repository and a path inside that ref. No machine chooses it. A local
# directory is only ever a non-authoritative cache of that locus -- the place
# the append below reads and writes files -- bound to exactly one declared
# locus by a stamp, so a directory already holding some other ledger is
# refused rather than silently adopted.
#
# An append through a bound cache is one Git commit on the declared ref:
#  1. read the ref's current commit (the expected head) and materialize the
#     declared path from it into the cache, discarding anything unpublished;
#  2. run the existing append against the cache, which links the new receipt
#     to the HEAD.json it found there;
#  3. write one commit whose parent is the expected head and whose tree carries
#     the receipt, any retained source receipt and the new HEAD.json together;
#  4. update the ref only if it still names the expected head
#     (`git push --force-with-lease=<ref>:<expected>`; the commit descends from
#     the expected head, so the update is a fast-forward and is never forced);
#  5. read the receipt back from the ref by its digest.
# A lost race re-reads the ref and repeats from (1), so the second writer
# re-links to the first writer's receipt and the chain never forks; an exact
# retry finds its receipt already recorded and publishes nothing. A push the
# ref refuses while it still names the expected head is not a race: it is a
# missing write permission or a repository protection, and the append fails
# closed naming that predicate. Nothing here weakens a protection, rewrites
# the chain or falls back to a host-local ledger.
#
# The remote is the declared repository's own address. How Git reaches that
# address (credentials, proxies, `url.<base>.insteadOf`) is Git's
# configuration, not a ledger location. Stdlib and the git CLI only.
LOCUS_KEY="organization_ledger_locus"
CACHE_VARIABLE="STEGVERSE_ORG_LEDGER_ROOT"
STAMP_NAME=".organization-ledger-locus.json"
GIT_DIR_NAME=".organization-ledger-locus.git"
STAMP_SCHEMA="stegverse.organization-ledger-locus-cache/v1"
MAX_ATTEMPTS=8
_SHA=re.compile(r"^[0-9a-f]{40}([0-9a-f]{24})?$")


class LocusFailClosed(ValueError):
    """An append or read through the declared locus that must fail closed."""

    def __init__(self, failed_predicate, detail, repair):
        super().__init__(failed_predicate+": "+detail)
        self.failed_predicate=failed_predicate
        self.detail=detail
        self.required_evidence_or_repair=repair


def _declared_locus(contract):
    """The locus the Organization manifest declares, validated; never derived from a host."""
    declared=contract.get(LOCUS_KEY)
    if not isinstance(declared,dict):
        raise LocusFailClosed("ORGANIZATION_LEDGER_LOCUS_DECLARED","org-contract.json declares no "+LOCUS_KEY,
                              "declare "+LOCUS_KEY+" (repository, ref, path) in .stegverse/transition-ledger/org-contract.json")
    repository,ref,path=declared.get("repository"),declared.get("ref"),declared.get("path")
    problems=[]
    # The lock is a ref in the same repository that carries the manifest, so the
    # repository's own permissions and protections govern every append.
    if repository!=str(contract.get("organization"))+"/.github":
        problems.append("repository must be the manifest's own repository "+str(contract.get("organization"))+"/.github")
    if not isinstance(ref,str) or not ref.startswith("refs/heads/") or subprocess.run(
            ["git","check-ref-format",ref],capture_output=True).returncode!=0:
        problems.append("ref must be a valid refs/heads/ ref")
    pure=PurePosixPath(path) if isinstance(path,str) and path else None
    if pure is None or pure.is_absolute() or str(pure)!=path or any(part in (".","..") or part.startswith(".") for part in pure.parts):
        problems.append("path must be a normalized relative path inside the ref")
    if problems:
        raise LocusFailClosed("ORGANIZATION_LEDGER_LOCUS_DECLARED","; ".join(problems),
                              "correct "+LOCUS_KEY+" in .stegverse/transition-ledger/org-contract.json")
    return {"repository":repository,"ref":ref,"path":path}


def remote_url(declared):
    """The declared repository's own address; transport rewriting is Git configuration."""
    return "https://github.com/"+declared["repository"]+".git"


def bound_locus(root):
    """The locus a cache directory is bound to, or None for a caller-held store."""
    stamp=Path(root)/STAMP_NAME
    if not stamp.is_file(): return None
    try: value=json.loads(stamp.read_text())
    except ValueError: value=None
    if not isinstance(value,dict) or value.get("schema")!=STAMP_SCHEMA or not isinstance(value.get("locus"),dict):
        raise LocusFailClosed("ORGANIZATION_LEDGER_CACHE_MATCHES_DECLARED_LOCUS","cache stamp unreadable: "+str(stamp),
                              "remove the cache directory; it is rebuilt from the declared locus")
    return value["locus"]


def bind_cache(root, declared, *, variable=CACHE_VARIABLE):
    """Bind a cache directory to the declared locus, or refuse one that names anything else.

    An empty directory is bound. A directory bound to another locus, or holding
    an unbound ledger, does not match the declared locus and fails closed: it
    is never adopted as the Organization ledger.
    """
    root=Path(root).expanduser().resolve()
    root.mkdir(mode=0o700,parents=True,exist_ok=True)
    current=bound_locus(root)
    if current is not None:
        if current!=declared:
            raise LocusFailClosed("ORGANIZATION_LEDGER_CACHE_MATCHES_DECLARED_LOCUS",
                                  variable+" cache is bound to "+json.dumps(current,sort_keys=True)
                                  +", not the declared "+json.dumps(declared,sort_keys=True),
                                  "unset "+variable+" or point it at a cache of the declared locus")
        return root
    if any(not entry.name.startswith(".") for entry in root.iterdir()):
        raise LocusFailClosed("ORGANIZATION_LEDGER_CACHE_MATCHES_DECLARED_LOCUS",
                              variable+" names a directory holding a ledger not bound to the declared locus: "+str(root),
                              "unset "+variable+" or point it at an empty directory; the declared locus is the ledger")
    stamp={"schema":STAMP_SCHEMA,"locus":dict(declared),"authority":"NONE_NON_AUTHORITATIVE_CACHE"}
    fd,name=tempfile.mkstemp(prefix=".locus-",dir=str(root))
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as stream:
            stream.write(json.dumps(stamp,indent=2,sort_keys=True)+"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name,root/STAMP_NAME)
    finally:
        if os.path.exists(name): os.unlink(name)
    return root


def ephemeral_cache(declared):
    """A fresh cache for an execution that supplied none; the locus, not the path, is the ledger."""
    return bind_cache(tempfile.mkdtemp(prefix="stegverse-org-ledger-cache-"),declared)


def _git_summary(result):
    """A refusal's own words, without anything that could carry a credential."""
    text=(result.stderr or b"").decode("utf-8","replace")+(result.stdout or b"").decode("utf-8","replace")
    text=re.sub(r"[a-z][a-z0-9+.-]*://[^\s]*","<url>",text)
    return " ".join(text.split())[-400:]


class GitLocus:
    """One cache of the declared locus and the Git operations that keep it honest."""

    def __init__(self, root, declared):
        self.root=Path(root)
        self.locus=dict(declared)
        self.url=remote_url(self.locus)
        self.git_dir=self.root/GIT_DIR_NAME
        self.prefix=self.locus["path"]

    def _git(self, *args, input=None, check=True, env=None):
        merged=dict(os.environ,GIT_TERMINAL_PROMPT="0",**(env or {}))
        result=subprocess.run(["git","--git-dir",str(self.git_dir),*args],input=input,capture_output=True,env=merged)
        if check and result.returncode!=0:
            raise LocusFailClosed("ORGANIZATION_LEDGER_GIT_OPERATION",args[0]+" failed: "+_git_summary(result),
                                  "repair the cache's git object store; the declared locus is unchanged")
        return result

    def remote_head(self):
        """The commit the declared ref names now, or None when the ref does not exist yet."""
        if not (self.git_dir/"HEAD").is_file():
            subprocess.run(["git","init","--bare","-q",str(self.git_dir)],check=True,capture_output=True)
        result=self._git("ls-remote","--refs",self.url,self.locus["ref"],check=False)
        if result.returncode!=0:
            raise LocusFailClosed("ORGANIZATION_LEDGER_REF_READABLE",
                                  "cannot read "+self.locus["ref"]+" in "+self.locus["repository"]+": "+_git_summary(result),
                                  "grant this execution read access to "+self.locus["repository"])
        for line in result.stdout.decode().splitlines():
            sha_,_,name=line.partition("\t")
            if name==self.locus["ref"] and _SHA.match(sha_): return sha_
        return None

    def fetch(self):
        """Fetch the declared ref; returns the commit fetched (the expected head) or None."""
        if self.remote_head() is None: return None
        result=self._git("fetch","--no-tags","--quiet",self.url,self.locus["ref"],check=False)
        if result.returncode!=0:
            raise LocusFailClosed("ORGANIZATION_LEDGER_REF_READABLE","cannot fetch "+self.locus["ref"]+": "+_git_summary(result),
                                  "grant this execution read access to "+self.locus["repository"])
        return self._git("rev-parse","FETCH_HEAD").stdout.decode().strip() or None

    def materialize(self, commit):
        """Make the cache hold exactly the declared path at `commit`; unpublished content is discarded."""
        for entry in self.root.iterdir():
            if entry.name.startswith("."): continue
            if entry.is_dir() and not entry.is_symlink(): shutil.rmtree(entry)
            else: entry.unlink()
        if commit is None or self._git("cat-file","-e",commit+":"+self.prefix,check=False).returncode!=0:
            return
        archive=self._git("archive","--format=tar",commit+":"+self.prefix).stdout
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            for member in tar.getmembers():
                parts=PurePosixPath(member.name).parts
                if member.name.startswith("/") or ".." in parts or not (member.isfile() or member.isdir()) \
                        or any(part.startswith(".") for part in parts):
                    raise LocusFailClosed("ORGANIZATION_LEDGER_REF_CONTENT_VALID",
                                          "declared path holds an entry the ledger never writes: "+member.name,
                                          "inspect "+self.locus["ref"]+":"+self.prefix)
                target=self.root.joinpath(*parts)
                if member.isdir():
                    target.mkdir(parents=True,exist_ok=True)
                    continue
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(tar.extractfile(member).read())

    def _published_files(self):
        files=[]
        for directory,names,filenames in os.walk(self.root):
            names[:]=sorted(name for name in names if not name.startswith("."))
            files.extend((Path(directory)/name).relative_to(self.root).as_posix()
                         for name in sorted(filenames) if not name.startswith("."))
        return files

    def tree(self, base):
        """The tree of `base` with the declared path replaced by the cache's ledger files."""
        index=self.git_dir/"locus-index"
        if index.exists(): index.unlink()
        env={"GIT_INDEX_FILE":str(index)}
        if base is None: self._git("read-tree","--empty",env=env)
        else:
            self._git("read-tree",base,env=env)
            self._git("rm","-r","--cached","--quiet","--ignore-unmatch","--",self.prefix,env=env)
        files=self._published_files()
        if files:
            paths="".join(str(self.root/name)+"\n" for name in files).encode()
            blobs=self._git("hash-object","-w","--no-filters","--stdin-paths",input=paths).stdout.decode().split()
            info="".join("100644 "+blob+"\t"+self.prefix+"/"+name+"\n" for blob,name in zip(blobs,files))
            self._git("update-index","--add","--index-info",input=info.encode(),env=env)
        tree=self._git("write-tree",env=env).stdout.decode().strip()
        index.unlink()
        return tree

    def commit(self, tree, parent, message):
        args=["commit-tree",tree,"-m",message]+(["-p",parent] if parent is not None else [])
        identity={"GIT_AUTHOR_NAME":"StegVerse Organization Ledger","GIT_AUTHOR_EMAIL":"organization-ledger@stegverse.invalid",
                  "GIT_COMMITTER_NAME":"StegVerse Organization Ledger","GIT_COMMITTER_EMAIL":"organization-ledger@stegverse.invalid"}
        return self._git(*args,env=identity).stdout.decode().strip()

    def compare_and_swap(self, commit, expected):
        """Move the declared ref to `commit` only if it still names `expected`."""
        lease="--force-with-lease="+self.locus["ref"]+":"+(expected or "")
        result=self._git("push","--porcelain","--quiet",lease,self.url,commit+":"+self.locus["ref"],check=False)
        return result.returncode==0,result

    def read_document(self, commit, key):
        result=self._git("cat-file","blob",commit+":"+self.prefix+"/"+key,check=False)
        if result.returncode!=0: return None
        try: return json.loads(result.stdout)
        except ValueError: return None

    def readback(self, commit, key, document):
        """The document, read from the declared ref by its content address, is exactly the one written."""
        tip=self.fetch()
        reachable=tip is not None and (tip==commit or self._git("merge-base","--is-ancestor",commit,tip,check=False).returncode==0)
        if not reachable or self.read_document(tip,key)!=document:
            raise LocusFailClosed("ORGANIZATION_LEDGER_RECEIPT_READBACK",
                                  key+" is not readable from "+self.locus["ref"],
                                  "inspect "+self.locus["ref"]+"; the chain is never rewritten to repair it")


def locus_sync(root):
    """Refresh a bound cache from the declared ref; a no-op for a caller-held store."""
    declared=bound_locus(root)
    if declared is not None:
        git=GitLocus(root,declared)
        git.materialize(git.fetch())
    return root


# Caches whose mutation is running inside locus_append, which publishes it.
_PUBLISHING=set()


def _receipt_published(record):
    return "receipts/"+record["receipt_sha256"].split(":",1)[1]+".json",record


def locus_append(root, operation, *, published=_receipt_published, attempts=MAX_ATTEMPTS):
    """Run one ledger `operation` against a bound cache and publish it under expected-head CAS.

    `operation` is the existing append (or batch closure); it reads and writes
    the cache only. `published(result)` names the content-addressed document,
    relative to the declared path, that must then be readable from the ref.
    The caller holds the cache's local lock, which serializes this host only;
    the ref comparison is the Organization ledger lock.
    """
    git=GitLocus(root,bound_locus(root))
    for _ in range(attempts):
        expected=git.fetch()
        git.materialize(expected)
        _PUBLISHING.add(str(git.root))
        try: result=operation()
        finally: _PUBLISHING.discard(str(git.root))
        key,document=published(result)
        tree=git.tree(expected)
        if expected is not None and tree==git._git("rev-parse",expected+"^{tree}").stdout.decode().strip():
            # An exact retry: the document is already on the ref and nothing new was written.
            git.readback(expected,key,document)
            return result
        commit=git.commit(tree,expected,"organization ledger append "+key)
        swapped,refused=git.compare_and_swap(commit,expected)
        if swapped:
            git.readback(commit,key,document)
            return result
        if git.remote_head()==expected:
            raise LocusFailClosed("ORGANIZATION_LEDGER_REF_WRITE_AUTHORIZED",
                                  git.locus["ref"]+" refused an update from its expected head: "+_git_summary(refused),
                                  "grant this execution contents write on "+git.locus["repository"]+" for "
                                  +git.locus["ref"]+" without weakening its protections")
        # Lost the race: another writer moved the ref. Re-read it and re-link.
    raise LocusFailClosed("ORGANIZATION_LEDGER_REF_CONTENTION","the ref moved on each of "+str(attempts)+" attempts",
                          "retry the same append; an exact retry returns the recorded receipt")


def canon(v): return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def sha(v): return "sha256:"+hashlib.sha256(canon(v)).hexdigest()
class LedgerLocationRequired(ValueError):
    """No ledger root was supplied; nothing is appended and nothing is derived."""

    failed_predicate="LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER"

    def __init__(self, variable):
        super().__init__("ledger_location_required_from_materializer: "+variable)
        self.variable=variable

class LedgerLocusFailClosed(LedgerLocationRequired):
    """The declared ledger locus could not be resolved, cached, read or appended."""

    def __init__(self, exc):
        ValueError.__init__(self, str(exc))
        self.variable=CACHE_VARIABLE
        self.failed_predicate=exc.failed_predicate
        self.detail=exc.detail
        self.required_evidence_or_repair=exc.required_evidence_or_repair

def location_refusal(exc):
    """The append attempt's own disposition when no ledger root was supplied."""
    return {
        "schema":"stegverse.organization-ledger-append-refusal/v1",
        "organization":C["organization"],
        "disposition":"FAIL_CLOSED",
        "failed_predicate":exc.failed_predicate,
        "required_evidence_or_repair":getattr(exc,"required_evidence_or_repair",None) or "supply the organization ledger root as "+exc.variable,
        "retry_entrypoint":"resident-runtime/aggregate_repo_transition.py::aggregate_transition",
        "consequence_committed":False,
        "authority_effect":"NONE_REFUSAL_ONLY",
    }

def declared_locus():
    """The Organization ledger locus the Organization manifest declares."""
    try: return _declared_locus(C)
    except LocusFailClosed as exc: raise LedgerLocusFailClosed(exc) from None

def ledger_root():
    """A cache of the Organization ledger, refreshed from its declared locus.

    The ledger is the organization's runtime reality and its locus is declared
    by the Organization manifest (org-contract.json `organization_ledger_locus`):
    a repository, a ref and a path. No machine chooses it. The directory
    returned is only a non-authoritative cache of that locus. STEGVERSE_ORG_LEDGER_ROOT,
    when set, names that cache and must be bound to the declared locus -- a
    directory bound to another locus or holding an unbound ledger fails closed;
    unset, a fresh cache is made. Appends through a bound cache are published
    to the declared ref by expected-head compare-and-swap.
    """
    declared=declared_locus()
    try:
        o=os.getenv(CACHE_VARIABLE)
        root=bind_cache(o,declared) if o else ephemeral_cache(declared)
        with (root/".append.lock").open("a+b") as lock:
            fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
            try: locus_sync(root)
            finally: fcntl.flock(lock.fileno(),fcntl.LOCK_UN)
        return root
    except LocusFailClosed as exc: raise LedgerLocusFailClosed(exc) from None
def load(p): return json.loads(Path(p).read_text())

def verify_required_evidence(receipt):
    """Require exact inline canonical evidence bytes for organization-local replay."""
    manifest=receipt.get("required_evidence_manifest")
    if not isinstance(manifest,list): raise ValueError("canonical required evidence manifest missing")
    seen=set()
    for item in manifest:
        if not isinstance(item,dict): raise ValueError("canonical evidence entry invalid")
        for key in ("evidence_id","evidence_type","origin_transition_id","encoding","sha256","content"):
            if key not in item: raise ValueError("canonical evidence field missing: "+key)
        identity=item["evidence_id"]
        if not isinstance(identity,str) or not identity or identity in seen:
            raise ValueError("canonical evidence identity invalid")
        seen.add(identity)
        if not isinstance(item["evidence_type"],str) or not item["evidence_type"] or item["origin_transition_id"]!=receipt.get("transition_id"):
            raise ValueError("canonical evidence transition binding invalid")
        encoding=item["encoding"]
        content=item["content"]
        if encoding=="canonical-json": raw=canon(content)
        elif encoding=="utf-8" and isinstance(content,str): raw=content.encode("utf-8")
        elif encoding=="base64" and isinstance(content,str):
            try: raw=base64.b64decode(content.encode("ascii"),validate=True)
            except (ValueError,UnicodeError) as exc: raise ValueError("canonical evidence base64 invalid") from exc
        else: raise ValueError("canonical evidence encoding invalid")
        digest=item["sha256"]
        if not isinstance(digest,str) or len(digest)!=64 or hashlib.sha256(raw).hexdigest()!=digest:
            raise ValueError("canonical required evidence digest mismatch")


def retain_source(root, receipt, verified):
    """Keep immutable exact source bytes under the existing private org ledger root."""
    digest=verified["source_transition_sha256"]
    if not isinstance(digest,str) or len(digest)!=71 or not digest.startswith("sha256:"):
        raise ValueError("organization source hash invalid")
    directory=root/"source-receipts"
    directory.mkdir(mode=0o700,parents=True,exist_ok=True)
    path=directory/(digest[7:]+".json")
    if path.exists():
        stored=load(path)
        if stored!=receipt or verify_source(stored)["source_transition_sha256"]!=digest:
            raise ValueError("retained organization source receipt conflict")
        return path
    fd,name=tempfile.mkstemp(prefix=".source-",dir=str(directory))
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as stream:
            stream.write(json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            stored=load(path)
            if stored!=receipt: raise ValueError("retained organization source receipt conflict")
        else: os.replace(name,path)
    finally:
        if os.path.exists(name): os.unlink(name)
    return path


def verify_source(receipt):
    schema=receipt.get("schema")
    allowed=C.get("consumes")
    if isinstance(allowed,str): allowed=[allowed]
    if schema not in (allowed or []): raise ValueError("organization source receipt schema mismatch")
    if schema=="stegverse.repo-transition-receipt/v1":
        repository=str(receipt.get("repository",""))
        if not repository.startswith(C["organization"]+"/"): raise ValueError("repo outside organization")
        claimed=receipt.get("receipt_sha256"); body=dict(receipt); body.pop("receipt_sha256",None)
        if claimed!=sha(body): raise ValueError("repo receipt hash mismatch")
        return {
            "source_receipt_schema":schema,
            "source_transition_sha256":claimed,
            "source_transition_id":receipt["transition_id"],
            "source_repository":repository,
            "repo_receipt_sha256":claimed,
            "repo_transition_id":receipt["transition_id"],
            "canonical_state_transition_receipt_sha256":None,
            "subject_or_correlation_id":None,
        }
    verify_required_evidence(receipt)
    digest=sha(receipt)
    return {
        "source_receipt_schema":schema,
        "source_transition_sha256":digest,
        "source_transition_id":receipt["transition_id"],
        "source_repository":None,
        "repo_receipt_sha256":None,
        "repo_transition_id":None,
        "canonical_state_transition_receipt_sha256":digest,
        "subject_or_correlation_id":receipt.get("subject_or_correlation_id"),
    }

def _existing_exact_source(d, source, *, org_transition_class, predecessor_org_state_sha256, successor_org_state_sha256, boundary_evidence, authority_effect):
    """Reuse an immutable organization receipt for an exact already-recorded transition.

    The existing receipt directory is the only index; no new store or authority
    is introduced. A retry after an incomplete Master Records submission must
    not append a second organization transition for the same exact source.
    `hb_reference` and `observed_at` are deliberately not compared: a retry
    arrives at a later heartbeat, and that is not a different transition.
    """
    for path in sorted(d.glob("*.json")):
        row=load(path)
        if row.get("source_transition_sha256") != source["source_transition_sha256"]:
            continue
        if row.get("source_receipt_schema") != source["source_receipt_schema"]:
            raise ValueError("organization source digest/schema collision")
        body=dict(row)
        claimed=body.pop("receipt_sha256",None)
        if claimed != sha(body) or path.stem != claimed.split(":",1)[-1]:
            raise ValueError("existing organization receipt integrity invalid")
        if (
            row.get("source_transition_id") != source["source_transition_id"]
            or row.get("org_transition_class") != org_transition_class
            or row.get("authority_effect") != authority_effect
            or row.get("boundary_evidence") != dict(boundary_evidence or {})
            or (predecessor_org_state_sha256 is not None and row.get("predecessor_org_state_sha256") != predecessor_org_state_sha256)
            or (successor_org_state_sha256 is not None and row.get("successor_org_state_sha256") != successor_org_state_sha256)
        ):
            raise ValueError("existing organization source transition context conflict")
        return row
    return None

def _atomic_json(path, value):
    """Durably replace a JSON record while holding the organization append lock."""
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix=".append-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        directory_fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _packet_establishment_source(released_batch):
    """Deterministic source transition for a release-born packet establishment.

    The organization append owner performs this transition itself, so no
    external caller supplies its source receipt. It is derived from the exact
    released batch id, which makes an exact retry idempotent.
    """
    return {
        "schema": "stegverse.canonical-state-transition-receipt/v1",
        "transition_id": "ORG-RECEIPT-PACKET-ESTABLISHMENT:" + released_batch["batch_id"],
        "transition_sequence": 1,
        "subject_or_correlation_id": released_batch["batch_id"],
        "transition_outcome": "OBSERVED",
        "required_evidence_manifest": [
            {
                "evidence_id": "released_batch_commitment",
                "evidence_type": "ORGANIZATION_BATCH_COMMITMENT",
                "origin_transition_id": "ORG-RECEIPT-PACKET-ESTABLISHMENT:" + released_batch["batch_id"],
                "encoding": "canonical-json",
                "content": {
                    "batch_id": released_batch["batch_id"],
                    "last_org_receipt_sha256": released_batch["last_org_receipt_sha256"],
                    "closure_reason": released_batch["closure_reason"],
                },
                "sha256": hashlib.sha256(canon({
                    "batch_id": released_batch["batch_id"],
                    "last_org_receipt_sha256": released_batch["last_org_receipt_sha256"],
                    "closure_reason": released_batch["closure_reason"],
                })).hexdigest(),
            }
        ],
    }


def aggregate_transition(receipt, *, org_transition_class="ORGANIZATION_STATE_TRANSITION",
                         predecessor_org_state_sha256=None, successor_org_state_sha256=None,
                         boundary_evidence=None, authority_effect="NONE", parent_manifest=None,
                         establishes_packet=False, now_ns=None, ledger=None, hb_epoch=None):
    """Serialize appends; the governing parent manifest owns packet release.

    A manifested receipt packet's first receipt records its own establishment.
    `establishes_packet` marks the four-part WorkerCoordinator transition whose
    t(0) accounting opens the first packet; later packets are opened by the
    single transition that releases their predecessor.

    `ledger` is the organization ledger root when the caller holds it as
    supplied by its materializer (the kernel does); otherwise it is the one
    supplied to this execution. Either way it is supplied, never derived.

    `hb_epoch` is the carrier's heartbeat epoch. Supplied, every receipt this
    call writes carries that exact reference; absent, the reference is derived
    from the host clock and says so. An exact retry returns the original
    receipt whatever epoch it arrives at.
    """
    root = Path(ledger).expanduser().resolve() if ledger is not None else ledger_root()
    return publish_ledger_mutation(root, lambda: _append_locked(
        receipt, root=root, org_transition_class=org_transition_class,
        predecessor_org_state_sha256=predecessor_org_state_sha256,
        successor_org_state_sha256=successor_org_state_sha256,
        boundary_evidence=boundary_evidence, authority_effect=authority_effect,
        parent_manifest=parent_manifest, establishes_packet=establishes_packet,
        now_ns=now_ns, hb_epoch=hb_epoch))


def publish_ledger_mutation(root, operation, *, published=_receipt_published):
    """Run one ledger mutation against `root` under its lock, publishing it when `root` caches the declared locus.

    A root bound to the declared locus is a cache: the mutation is published to
    the declared ref by expected-head compare-and-swap or fails closed. An
    unbound root is a caller-held store (a temporary ledger, or a root a caller
    holds directly): written locally and never the Organization runtime reality.
    """
    root = Path(root).expanduser().resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (root / ".append.lock").open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            bound = bound_locus(root)
            if bound is None:
                return operation()
            if bound != declared_locus():
                raise LocusFailClosed(
                    "ORGANIZATION_LEDGER_CACHE_MATCHES_DECLARED_LOCUS",
                    "ledger cache is bound to " + json.dumps(bound, sort_keys=True),
                    "mutate the ledger through a cache of the declared locus")
            return locus_append(root, operation, published=published)
        except LocusFailClosed as exc:
            raise LedgerLocusFailClosed(exc) from None
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _append_locked(receipt, *, root, org_transition_class, predecessor_org_state_sha256,
                   successor_org_state_sha256, boundary_evidence, authority_effect,
                   parent_manifest, establishes_packet, now_ns, hb_epoch):
    """The append itself, against the ledger root its caller holds locked."""
    released = None
    effective_boundary_evidence = dict(boundary_evidence or {})
    if parent_manifest is not None:
        # The governing parent manifest owns packet release, authorized
        # once at establishment. A satisfied or expired prior packet is
        # released and carried through the existing canonical custody
        # client as a manifest-directed consequence. That custody result
        # is execution evidence only; it must never mint or replace the
        # parent manifest's governance disposition.
        import organization_batch_custody as batches
        # Establishment is declared by the manifest. A manifest without
        # one stays count-governed and unchanged, so manifests written
        # before packets had a t(0) remain valid.
        manifest_establishes = batches.manifest_declares_establishment(parent_manifest)
        if establishes_packet and not manifest_establishes:
            raise ValueError("t(0) establishment requires a manifest establishment declaration")
        if establishes_packet:
            effective_boundary_evidence[batches.ESTABLISHMENT_KEY] = batches.establishment_record(
                parent_manifest, kind="MANIFEST_ASSIGNMENT_T0"
            )
        released = batches.release_satisfied_packet_before_next_transition(
            parent_manifest, root=root, now_ns=now_ns
        )
        if released is not None:
            if establishes_packet:
                raise ValueError("t(0) establishment cannot also release a prior packet")
            release_execution_result = batches.submit_released_batch(root, released["batch_id"])
            if release_execution_result.get("state") not in {"COMPLETED", "FAILED"}:
                raise ValueError("released organization batch execution result invalid")
            if release_execution_result.get("governance_disposition") is not None:
                raise ValueError("released organization batch attempted governance escalation")
            carried = {
                "batch_id": released["batch_id"],
                "execution_result": release_execution_result["state"],
                "reason": release_execution_result.get("reason"),
                "authority_effect": release_execution_result.get("authority_effect"),
            }
            if manifest_establishes:
                # Release and successor establishment are one transition
                # and one receipt. It is member #1 of the packet it
                # opens, so the release has its own identity rather than
                # riding as an attribute of an unrelated work transition.
                _aggregate_transition_locked(
                    _packet_establishment_source(released), root=root,
                    org_transition_class="ORGANIZATION_RECEIPT_PACKET_ESTABLISHMENT",
                    boundary_evidence={
                        batches.ESTABLISHMENT_KEY: batches.establishment_record(
                            parent_manifest, kind="PRIOR_PACKET_RELEASE", released_batch=carried
                        ),
                        "parent_manifest_released_batch": carried,
                    },
                    authority_effect="NONE",
                    hb_epoch=hb_epoch,
                )
            else:
                effective_boundary_evidence["parent_manifest_released_batch"] = carried
    record = _aggregate_transition_locked(
        receipt, root=root, org_transition_class=org_transition_class,
        predecessor_org_state_sha256=predecessor_org_state_sha256,
        successor_org_state_sha256=successor_org_state_sha256,
        boundary_evidence=effective_boundary_evidence, authority_effect=authority_effect,
        hb_epoch=hb_epoch,
    )
    if released is not None:
        state = batches.open_packet_state(parent_manifest, root=root, now_ns=now_ns)
        if state["receipt_count"] != (2 if manifest_establishes else 1):
            raise ValueError("successor organization receipt packet did not initialize correctly")
    return record


def _aggregate_transition_locked(receipt, *, root=None, org_transition_class="ORGANIZATION_STATE_TRANSITION", predecessor_org_state_sha256=None, successor_org_state_sha256=None, boundary_evidence=None, authority_effect="NONE", hb_epoch=None):
    source=verify_source(receipt)
    root=root if root is not None else ledger_root()
    if str(Path(root).expanduser().resolve()) not in _PUBLISHING and bound_locus(root) is not None:
        # Written here, a cache of the declared locus would hold a receipt the
        # ref never received: it would appear appended and be discarded.
        raise LedgerLocusFailClosed(LocusFailClosed(
            "ORGANIZATION_LEDGER_APPENDED_UNDER_LOCUS_CAS",
            "a cache of the declared locus is appended only through aggregate_transition",
            "append through aggregate_transition, which publishes under the declared ref's compare-and-swap"))
    d=root/"receipts"; d.mkdir(parents=True,exist_ok=True); h=root/"HEAD.json"
    existing=_existing_exact_source(
        d,source,org_transition_class=org_transition_class,
        predecessor_org_state_sha256=predecessor_org_state_sha256,
        successor_org_state_sha256=successor_org_state_sha256,
        boundary_evidence=boundary_evidence,authority_effect=authority_effect,
    )
    if existing is not None:
        retain_source(root,receipt,source)
        return existing
    retain_source(root,receipt,source)
    prev=load(h).get("receipt_sha256") if h.exists() else None
    predecessor=predecessor_org_state_sha256 or prev
    successor=successor_org_state_sha256 or source["source_transition_sha256"]
    body={
        "schema":"stegverse.organization-transition-receipt/v1",
        "organization":C["organization"],
        **source,
        "org_transition_class":org_transition_class,
        "predecessor_org_state_sha256":predecessor,
        "successor_org_state_sha256":successor,
        "boundary_evidence":dict(boundary_evidence or {}),
        "authority_effect":authority_effect,
        "hb_reference":kernel.hb_reference(epoch=hb_epoch) if hb_epoch is not None else kernel.hb_reference(),
        "observed_at":datetime.now(timezone.utc).isoformat(),
        "previous_receipt_sha256":prev,
    }
    digest=sha(body); record={**body,"receipt_sha256":digest}; fp=d/(digest.split(":",1)[1]+".json")
    if fp.exists() and load(fp)!=record: raise ValueError("org receipt collision")
    if not fp.exists(): _atomic_json(fp,record)
    # In a cache of the declared locus the receipt is named where it lives in the
    # declared ref, never by the cache's host path.
    bound=bound_locus(root)
    path=bound["path"]+"/receipts/"+fp.name if bound is not None else str(fp)
    _atomic_json(h,{"organization":C["organization"],"receipt_sha256":digest,"receipt_path":path})
    return record

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo-receipt")
    p.add_argument("--transition-receipt")
    p.add_argument("--org-transition-class",default=None)
    p.add_argument("--predecessor-org-state-sha256")
    p.add_argument("--successor-org-state-sha256")
    p.add_argument("--boundary-evidence-json",default="{}")
    p.add_argument("--authority-effect",default="NONE")
    p.add_argument("--parent-manifest")
    a=p.parse_args()
    source_path=a.transition_receipt or a.repo_receipt
    if not source_path: raise SystemExit("transition receipt required")
    receipt=load(source_path)
    default_class="REPO_STATE_PROPAGATION" if receipt.get("schema")=="stegverse.repo-transition-receipt/v1" else "ORGANIZATION_STATE_TRANSITION"
    try:
        record=aggregate_transition(
            receipt,
            org_transition_class=a.org_transition_class or default_class,
            predecessor_org_state_sha256=a.predecessor_org_state_sha256,
            successor_org_state_sha256=a.successor_org_state_sha256,
            boundary_evidence=json.loads(a.boundary_evidence_json),
            authority_effect=a.authority_effect,
            parent_manifest=load(a.parent_manifest) if a.parent_manifest else None,
        )
    except LedgerLocationRequired as exc:
        print(json.dumps(location_refusal(exc),sort_keys=True))
        raise SystemExit(1)
    except ValueError as exc:
        raise SystemExit(str(exc))
    print(json.dumps(record,sort_keys=True))

if __name__=="__main__": main()
