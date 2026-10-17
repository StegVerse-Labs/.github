"""Organization-ledger component (RTC-EVIDENCE-CUSTODY-004 profile): component-layout tests. Stdlib only.

Every test runs the component as a consumer would: the module is loaded from
org-kernel/organization-ledger/, the kernel is the sibling org-kernel/kernel.py,
and the working directory is a consumer checkout whose contracts were generated
from a parameter file (the formalism-tests pilot). No network, no clock, no
external machine.
"""
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

COMPONENT = Path(__file__).resolve().parents[1]
ORG_KERNEL = COMPONENT.parent / "kernel.py"
PILOT = {
    "schema": "stegverse.organization-ledger-parameters/v1",
    "organization": "formalism-tests",
    "designation_source": "StegVerse-org/.github#163 (H29 pilot adoption comment, to be cited once posted)",
    "propagation_target": "master-records/.github",
    "consumes": ["stegverse.repo-transition-receipt/v1"],
    "organization_record_service_declared": False,
    "genesis_mode": "SELF_CLOSURE_OPENS_CHAIN",
    "owning_existing_goal": "StegVerse-org/.github#162",
}
GOAL = PILOT["owning_existing_goal"]
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")
LOCATION_VARIABLES = {"STEGVERSE_REPO_LEDGER_ROOT", "STEGVERSE_ORG_LEDGER_ROOT", "STEGVERSE_REPO_LEDGER_HOME"}
A, B = "sha256:" + "a" * 64, "sha256:" + "b" * 64
EPOCH = 4200

PRELUDE = r'''
import importlib.util, json, sys
from pathlib import Path
C = Path(sys.argv[1])
def load(name):
    s = importlib.util.spec_from_file_location(name.replace(".py", ""), C / name)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def refusal(fn):
    try:
        return {"returned": fn()}
    except SystemExit as exc:
        return {"refused": getattr(exc, "refusal", None), "code": str(exc.code)}
'''


class Consumer:
    """A consumer checkout: committed parameter file and the contracts generated from it."""

    def __init__(self, params=PILOT):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "consumer"
        self.ledgers = Path(self.tmp.name) / "ledgers"
        tl = self.root / ".stegverse/transition-ledger"
        tl.mkdir(parents=True)
        (tl / "organization-ledger.parameters.json").write_text(json.dumps(params, indent=2) + "\n")
        out = subprocess.run([sys.executable, str(COMPONENT / "generate_ledger_contracts.py"),
                              str(tl / "organization-ledger.parameters.json"), "--out-dir", str(tl)],
                             capture_output=True, text=True)
        assert out.returncode == 0, out.stdout + out.stderr
        self.contract = json.loads((tl / "contract.json").read_text())
        self.env = dict(os.environ, STEGVERSE_REPO_LEDGER_ROOT=str(self.ledgers / "repo"),
                        STEGVERSE_ORG_LEDGER_ROOT=str(self.ledgers / "org"))

    def py(self, body):
        out = subprocess.run([sys.executable, "-c", PRELUDE + body, str(COMPONENT)], cwd=self.root,
                             env=self.env, capture_output=True, text=True)
        assert out.returncode == 0, out.stderr[-2000:]
        return json.loads(out.stdout.splitlines()[-1])

    def cli(self, script, *args):
        return subprocess.run([sys.executable, str(COMPONENT / script), *args], cwd=self.root,
                              env=self.env, capture_output=True, text=True)

    def written(self, level):
        base = self.ledgers / level
        return sorted(str(p.relative_to(base)) for p in base.rglob("*.json")) if base.exists() else []

    def close(self):
        self.tmp.cleanup()


def repo_receipt_snippet(transition_id="t-1"):
    return ('body = {"schema": "stegverse.repo-transition-receipt/v1", "repository": "formalism-tests/.github", '
            '"transition_id": "%s"}\n' % transition_id +
            'agg = load("aggregate_repo_transition.py")\n'
            'src = {**body, "receipt_sha256": agg.sha(body)}\n')


class SuppliedEpochRule(unittest.TestCase):
    """P1-FC-4 and the shared InTr rule: supplied, digits, >= 32, no clock anywhere."""

    def setUp(self):
        self.c = Consumer()
        self.addCleanup(self.c.close)

    def assertSixFieldRefusal(self, refusal, code):
        self.assertIsInstance(refusal, dict)
        for field in SIX:
            self.assertTrue(refusal.get(field), field)
        self.assertEqual(refusal["failure_code"], code)
        self.assertEqual(refusal["disposition"], "FAIL_CLOSED")
        self.assertIs(refusal["consequence_committed"], False)
        self.assertEqual(refusal["owning_existing_goal"], GOAL)

    def test_repo_receipt_refuses_without_supplied_epoch(self):
        out = self.c.cli("emit.py", "--transition-id", "t-1", "--transition-class", "TEST",
                         "--predecessor-state-sha256", A, "--successor-state-sha256", B)
        self.assertNotEqual(out.returncode, 0)
        refusal = json.loads(out.stdout.splitlines()[-1])
        self.assertSixFieldRefusal(refusal, "HB_EPOCH_NOT_SUPPLIED")
        self.assertEqual(refusal["failed_predicate"], "HB_EPOCH_IS_SUPPLIED_BY_THE_MANIFEST_OR_DISPATCH")
        self.assertEqual(refusal["retry_entrypoint"], "org-kernel/organization-ledger/emit.py::append")
        self.assertEqual(self.c.written("repo"), [], "nothing is written on refusal")

    def test_org_receipt_refuses_without_supplied_epoch(self):
        r = self.c.py(repo_receipt_snippet() + 'print(json.dumps(refusal(lambda: agg.append(src, "REPO_STATE_PROPAGATION", agg.GENESIS, "%s", {}, "NONE"))))' % B)
        self.assertSixFieldRefusal(r["refused"], "HB_EPOCH_NOT_SUPPLIED")
        self.assertEqual(r["code"], "HB_EPOCH_NOT_SUPPLIED")
        self.assertEqual(self.c.written("org"), [])

    def test_propagation_refuses_without_supplied_epoch(self):
        self.c.cli("emit.py", "--transition-id", "t-1", "--transition-class", "TEST",
                   "--predecessor-state-sha256", A, "--successor-state-sha256", B, "--hb-epoch", str(EPOCH))
        r = self.c.py('p = load("propagate_repository_receipts.py")\n'
                      'print(json.dumps(refusal(lambda: p.propagate("formalism-tests/.github", repository_root=Path(%r)))))'
                      % str(self.c.ledgers / "repo"))
        self.assertSixFieldRefusal(r["refused"], "HB_EPOCH_NOT_SUPPLIED")
        self.assertEqual(self.c.written("org"), [])

    def test_malformed_epochs_are_refused_as_invalid(self):
        for bad in ("31", "abc", "4.2", "-40", "+33", " 33", "33 ", "3_3", "\u0663\u0663", 31, True, 4.2, [64]):
            r = self.c.py('common = load("ledger_common.py")\n'
                          'print(json.dumps(refusal(lambda: common.require_supplied_epoch(%r, "x"))))' % (bad,))
            self.assertEqual(r["refused"]["failure_code"], "HB_EPOCH_INVALID", bad)
            self.assertEqual(r["refused"]["failed_predicate"], "HB_EPOCH_IS_AN_INTEGER_AT_OR_AFTER_THE_HB32_ANCHOR")
        for absent in (None, ""):
            r = self.c.py('common = load("ledger_common.py")\n'
                          'print(json.dumps(refusal(lambda: common.require_supplied_epoch(%r, "x"))))' % (absent,))
            self.assertEqual(r["refused"]["failure_code"], "HB_EPOCH_NOT_SUPPLIED")
        for good, value in (("32", 32), (32, 32), ("417798851", 417798851)):
            r = self.c.py('common = load("ledger_common.py")\n'
                          'print(json.dumps(refusal(lambda: common.require_supplied_epoch(%r, "x"))))' % (good,))
            self.assertEqual(r["returned"], value)

    def test_cli_invalid_epoch_is_refused_and_writes_nothing(self):
        out = self.c.cli("emit.py", "--transition-id", "t-1", "--transition-class", "TEST",
                         "--predecessor-state-sha256", A, "--successor-state-sha256", B, "--hb-epoch", "31")
        self.assertNotEqual(out.returncode, 0)
        self.assertSixFieldRefusal(json.loads(out.stdout.splitlines()[-1]), "HB_EPOCH_INVALID")
        self.assertEqual(self.c.written("repo"), [])

    def test_supplied_epoch_receipt_is_heartbeat_derived_not_clock_derived(self):
        out = self.c.cli("emit.py", "--transition-id", "t-1", "--transition-class", "TEST",
                         "--predecessor-state-sha256", A, "--successor-state-sha256", B, "--hb-epoch", str(EPOCH))
        self.assertEqual(out.returncode, 0, out.stderr)
        receipt = json.loads(out.stdout.splitlines()[-1])
        self.assertEqual(receipt["repository"], "formalism-tests/.github")
        self.assertEqual(receipt["hb_reference"]["epoch"], EPOCH)
        self.assertIs(receipt["hb_reference"]["derived_from_clock"], False)
        self.assertNotIn("sampled_unix_ns", receipt["hb_reference"])
        self.assertNotIn("observed_at", receipt)

    def test_no_component_module_reads_a_clock(self):
        for path in sorted(COMPONENT.glob("*.py")):
            text = path.read_text()
            self.assertNotRegex(text, r"\bimport time\b|\bfrom time\b|\btime\.time|time_ns|datetime", path.name)
            for call in re.findall(r"hb_reference\(([^)]*)\)", text):
                self.assertIn("epoch", call, path.name + ": hb_reference without a supplied epoch")


class CliEpochIsAsciiDigits(unittest.TestCase):
    """TVC#517 require_hb_epoch parity: the CLIs take --hb-epoch as text, so argparse's int()
    (which accepts '+33', ' 33', '3_3') never decides it; the shared rule does."""

    REFUSED = ("+33", " 33", "3_3", "31", "33 ", "\u0663\u0663")
    ACCEPTED = (("32", 32), ("33", 33))

    def setUp(self):
        self.c = Consumer()
        self.addCleanup(self.c.close)

    def emit(self, epoch):
        return self.c.cli("emit.py", "--transition-id", "t-1", "--transition-class", "TEST",
                          "--predecessor-state-sha256", A, "--successor-state-sha256", B, "--hb-epoch=" + epoch)

    def aggregate(self, epoch):
        body = {"schema": "stegverse.repo-transition-receipt/v1", "repository": "formalism-tests/.github", "transition_id": "t-1"}
        r = self.c.py('agg = load("aggregate_repo_transition.py")\nprint(json.dumps({**%r, "receipt_sha256": agg.sha(%r)}))' % (body, body))
        path = self.c.root / "repo-receipt.json"
        path.write_text(json.dumps(r))
        return self.c.cli("aggregate_repo_transition.py", "--repo-receipt", str(path),
                          "--predecessor-org-state-sha256", "GENESIS", "--successor-org-state-sha256", B, "--hb-epoch=" + epoch)

    def propagate(self, epoch):
        return self.c.cli("propagate_repository_receipts.py", "--repository", "formalism-tests/.github",
                          "--repository-ledger-root", str(self.c.ledgers / "repo"), "--hb-epoch=" + epoch)

    def assertRefused(self, out, level, epoch):
        self.assertNotEqual(out.returncode, 0, epoch)
        refusal = json.loads(out.stdout.splitlines()[-1])
        self.assertEqual(refusal["failure_code"], "HB_EPOCH_INVALID", (level, epoch))
        for field in SIX:
            self.assertTrue(refusal.get(field), field)
        self.assertEqual([p for p in self.c.written(level) if "receipts/" in p], [], (level, epoch))

    def test_emit_cli_refuses_non_ascii_digit_epochs(self):
        for epoch in self.REFUSED:
            self.assertRefused(self.emit(epoch), "repo", epoch)

    def test_aggregate_cli_refuses_non_ascii_digit_epochs(self):
        for epoch in self.REFUSED:
            self.assertRefused(self.aggregate(epoch), "org", epoch)

    def test_propagate_cli_refuses_non_ascii_digit_epochs(self):
        self.assertEqual(self.emit("4200").returncode, 0)
        for epoch in self.REFUSED:
            self.assertRefused(self.propagate(epoch), "org", epoch)

    def test_clis_accept_ascii_digit_epochs_at_and_after_the_anchor(self):
        for epoch, value in self.ACCEPTED:
            c = Consumer()
            self.addCleanup(c.close)
            self.c = c
            out = self.emit(epoch)
            self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
            self.assertEqual(json.loads(out.stdout.splitlines()[-1])["hb_reference"]["epoch"], value)
            out = self.propagate(epoch)
            self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
            org = [json.loads((c.ledgers / "org" / p).read_text()) for p in c.written("org") if p.startswith("receipts/")]
            self.assertEqual([r["hb_reference"]["epoch"] for r in org], [value])
        c = Consumer()
        self.addCleanup(c.close)
        self.c = c
        out = self.aggregate("32")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertEqual(json.loads(out.stdout.splitlines()[-1])["hb_reference"]["epoch"], 32)


class SixFieldRefusals(unittest.TestCase):
    """P1-FC-5: every non-ALLOW carries the six fields; the goal is the consumer's parameter."""

    def setUp(self):
        self.c = Consumer()
        self.addCleanup(self.c.close)

    def test_aggregator_bare_refusal_carries_six_fields(self):
        r = self.c.py('body = {"schema": "stegverse.repo-transition-receipt/v1", "repository": "Other-Org/x", "transition_id": "t"}\n'
                      'agg = load("aggregate_repo_transition.py")\n'
                      'src = {**body, "receipt_sha256": agg.sha(body)}\n'
                      'print(json.dumps(refusal(lambda: agg.append(src, "REPO_STATE_PROPAGATION", agg.GENESIS, "%s", {}, "NONE", hb_epoch=%d))))' % (B, EPOCH))
        refusal = r["refused"]
        for field in SIX:
            self.assertTrue(refusal.get(field), field)
        self.assertEqual(refusal["failure_code"], "REPO_OUTSIDE_ORGANIZATION")
        self.assertEqual(refusal["owning_existing_goal"], GOAL)
        self.assertEqual(refusal["retry_entrypoint"], "org-kernel/organization-ledger/aggregate_repo_transition.py::append")
        self.assertEqual(r["code"], "repo outside organization", "the SystemExit message is unchanged")

    def test_every_refusal_site_is_six_field(self):
        """No bare `raise SystemExit("...")` remains in any component writer (the CLI exit code excepted)."""
        for name in ("emit.py", "aggregate_repo_transition.py", "propagate_repository_receipts.py"):
            tree = ast.parse((COMPONENT / name).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call) \
                        and getattr(node.exc.func, "id", None) == "SystemExit":
                    arg = node.exc.args[0] if node.exc.args else None
                    self.assertFalse(isinstance(arg, (ast.Constant, ast.JoinedStr, ast.BinOp))
                                     and not (isinstance(arg, ast.Constant) and isinstance(arg.value, int)),
                                     "%s:%d bare SystemExit" % (name, node.lineno))

    def test_genesis_opens_then_from_head_follows_and_second_genesis_is_denied(self):
        r = self.c.py(repo_receipt_snippet("t-1") +
                      'g = agg.append(src, "REPO_STATE_PROPAGATION", agg.GENESIS, "%s", {}, "NONE", hb_epoch=%d)\n' % (B, EPOCH) +
                      'b2 = {**body, "transition_id": "t-2"}; s2 = {**b2, "receipt_sha256": agg.sha(b2)}\n'
                      'f = agg.append(s2, "REPO_STATE_PROPAGATION", agg.FROM_HEAD, "%s", {}, "NONE", hb_epoch=%d)\n' % (A, EPOCH + 1) +
                      'b3 = {**body, "transition_id": "t-3"}; s3 = {**b3, "receipt_sha256": agg.sha(b3)}\n'
                      'd = refusal(lambda: agg.append(s3, "REPO_STATE_PROPAGATION", agg.GENESIS, "%s", {}, "NONE", hb_epoch=%d))\n' % (B, EPOCH + 2) +
                      'print(json.dumps({"g": g, "f": f, "d": d}))')
        self.assertIs(r["g"]["chain_genesis"], True)
        self.assertIsNone(r["g"]["previous_receipt_sha256"])
        self.assertEqual(r["f"]["previous_receipt_sha256"], r["g"]["receipt_sha256"])
        self.assertEqual(r["d"]["refused"]["disposition"], "DENY")
        self.assertEqual(r["d"]["refused"]["failure_code"], "ORG_LEDGER_GENESIS_ON_NON_EMPTY_LEDGER")
        for field in SIX:
            self.assertTrue(r["d"]["refused"].get(field), field)
        self.assertEqual(len([p for p in self.c.written("org") if p.startswith("receipts/")]), 2)

    def test_from_head_on_empty_ledger_fails_closed(self):
        r = self.c.py(repo_receipt_snippet() + 'print(json.dumps(refusal(lambda: agg.append(src, "REPO_STATE_PROPAGATION", agg.FROM_HEAD, "%s", {}, "NONE", hb_epoch=%d))))' % (B, EPOCH))
        self.assertEqual(r["refused"]["failure_code"], "ORG_LEDGER_GENESIS_NOT_DECLARED")
        self.assertEqual(r["refused"]["disposition"], "FAIL_CLOSED")


class ComponentLayout(unittest.TestCase):
    def setUp(self):
        self.c = Consumer()
        self.addCleanup(self.c.close)

    def test_siblings_and_kernel_resolve_inside_the_component(self):
        r = self.c.py('common = load("ledger_common.py")\nroot = common.consumer_root(None)\n'
                      'print(json.dumps({"kernel": str(common.kernel_path(root)), "store": str(common.sibling("ledger_store.py", C, root)),'
                      '"emit": str(common.sibling("emit.py", C, root)), "root": str(root), "entry": common.entrypoint(str(C / "emit.py"), "append")}))')
        self.assertEqual(Path(r["kernel"]), ORG_KERNEL)
        self.assertEqual(Path(r["store"]), COMPONENT / "ledger_store.py")
        self.assertEqual(Path(r["emit"]), COMPONENT / "emit.py")
        self.assertEqual(Path(r["root"]), self.c.root.resolve())
        self.assertEqual(r["entry"], "org-kernel/organization-ledger/emit.py::append")

    def test_no_new_environment_variable_is_read(self):
        """Only the ledger locations are read by name, as the governed-ingress census requires."""
        for path in sorted(COMPONENT.glob("*.py")):
            text = path.read_text()
            for name in re.findall(r"(?:getenv|environ\.get|environ\[)\(?\s*['\"]([A-Z_]+)['\"]", text):
                self.assertIn(name, LOCATION_VARIABLES, path.name)
            for const in re.findall(r"getenv\(([A-Z_]+)\)", text):
                value = re.search(const + r'\s*=\s*"([A-Z_]+)"', text)
                self.assertIn(value.group(1) if value else const, LOCATION_VARIABLES, path.name)

    def test_contracts_come_from_the_consumer_not_the_component(self):
        self.assertFalse((COMPONENT / ".stegverse").exists())
        out = self.c.cli("emit.py", "--transition-id", "t-1", "--transition-class", "TEST",
                         "--predecessor-state-sha256", A, "--successor-state-sha256", B, "--hb-epoch", str(EPOCH))
        self.assertEqual(json.loads(out.stdout.splitlines()[-1])["repository"], self.c.contract["repository"])


class GeneratorAndManifest(unittest.TestCase):
    def test_generator_check_accepts_generated_and_refuses_edited_contracts(self):
        c = Consumer()
        self.addCleanup(c.close)
        tl = c.root / ".stegverse/transition-ledger"
        args = [sys.executable, str(COMPONENT / "generate_ledger_contracts.py"), str(tl / "organization-ledger.parameters.json"), "--out-dir", str(tl), "--check"]
        self.assertEqual(subprocess.run(args, capture_output=True).returncode, 0)
        (tl / "contract.json").write_text((tl / "contract.json").read_text().replace("formalism-tests/.github", "formalism-tests/other"))
        out = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(out.returncode, 1)
        refusal = json.loads(out.stdout.splitlines()[-1])
        self.assertEqual(refusal["failure_code"], "CONTRACT_NOT_GENERATED_FROM_PARAMETERS")
        for field in SIX:
            self.assertTrue(refusal.get(field), field)

    def test_component_manifest_matches_every_module_and_refuses_an_edit(self):
        manifest = COMPONENT / "component-manifest.json"
        args = [sys.executable, str(COMPONENT / "verify_component_manifest.py"), "--root", str(COMPONENT), "--manifest", str(manifest)]
        out = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout)
        listed = set(json.loads(manifest.read_text())["modules"])
        self.assertTrue({p.name for p in COMPONENT.glob("*.py")} <= listed)
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "c"
            shutil.copytree(COMPONENT, copy, ignore=shutil.ignore_patterns("__pycache__", "tests"))
            (copy / "emit.py").write_text((copy / "emit.py").read_text() + "\n# local edit\n")
            out = subprocess.run([sys.executable, str(copy / "verify_component_manifest.py"), "--root", str(copy), "--manifest", str(copy / "component-manifest.json")], capture_output=True, text=True)
            self.assertEqual(out.returncode, 1)
            self.assertEqual(json.loads(out.stdout)["failure_code"], "COMPONENT_DIGEST_MISMATCH")


class ReadbackAcceptsBothCommunicationIdForms(unittest.TestCase):
    """Steering (c): the 7 existing closures keep intr-selfclose-<Org>-20261017; new orgs use -HB<epoch>."""

    def test_legacy_dated_and_new_hb_forms_both_read_back(self):
        c = Consumer()
        self.addCleanup(c.close)
        r = c.py(repo_receipt_snippet("closure-1") +
                 'agg.append(src, "REPO_STATE_PROPAGATION", agg.GENESIS, "%s", {"communication_id": "intr-selfclose-formalism-tests-20261017"}, "NONE", hb_epoch=%d)\n' % (B, EPOCH) +
                 'b2 = {**body, "transition_id": "closure-2"}; s2 = {**b2, "receipt_sha256": agg.sha(b2)}\n'
                 'agg.append(s2, "REPO_STATE_PROPAGATION", agg.FROM_HEAD, "%s", {"communication_id": "intr-selfclose-formalism-tests-HB%d"}, "NONE", hb_epoch=%d)\n' % (A, EPOCH + 1, EPOCH + 1) +
                 'rb = load("organization_ledger_readback.py")\n'
                 'print(json.dumps(rb.readback(%r)))' % str(c.ledgers / "org"))
        self.assertEqual(r["disposition"], "ALLOW")
        self.assertEqual(r["chain_length"], 2)
        self.assertTrue(r["every_receipt_verifies_against_its_body"])


def _load_readback():
    import importlib.util
    spec = importlib.util.spec_from_file_location("readback_under_test", COMPONENT / "organization_ledger_readback.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RB = _load_readback()
LEDGER_REF = "refs/stegverse/organization-ledger"
SEGMENT_SIX = {
    "failure_code": "SOURCE_RECEIPT_RETAINED_AND_VERIFIES",
    "failed_predicate": "EVERY_ORGANIZATION_RECEIPT_RETAINS_AND_VERIFIES_ITS_SOURCE_RECEIPT",
    "required_evidence_or_repair": "forward retention; legacy receipts are never re-minted",
    "retry_entrypoint": "org-kernel/organization-ledger/organization_ledger_readback.py::main",
    "owning_existing_goal": GOAL,
    "next_attempt": "receipts appended after retention began are retained and checked",
}


class GitLedger:
    """A git organization ledger built receipt by receipt; one commit per append. No writer, no clock."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "ledger"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("checkout", "-q", "--orphan", "ledger")
        self.head, self.commits, self.n = None, [], 0

    def git(self, *args):
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@invalid", GIT_COMMITTER_NAME="t",
                   GIT_COMMITTER_EMAIL="t@invalid", GIT_AUTHOR_DATE="2026-10-17T00:00:00Z",
                   GIT_COMMITTER_DATE="2026-10-17T00:00:00Z")
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True,
                              text=True, env=env).stdout.strip()

    def _write(self, key, doc):
        path = self.repo / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")

    def append(self, kind, previous="HEAD", tamper=False):
        """kind: legacy (names repo_receipt_sha256 only), retained, or unretained (names a source it does not keep)."""
        self.n += 1
        source_body = {"schema": "stegverse.repo-transition-receipt/v1", "transition_id": "t-%d" % self.n}
        source = {**source_body, "receipt_sha256": RB.sha(source_body)}
        body = {"schema": "stegverse.organization-transition-receipt/v1", "organization": "formalism-tests",
                "source_transition_id": "t-%d" % self.n,
                "previous_receipt_sha256": self.head if previous == "HEAD" else previous}
        if kind == "legacy":
            body["repo_receipt_sha256"] = source["receipt_sha256"]
        else:
            body["source_transition_sha256"] = source["receipt_sha256"]
            body["repo_receipt_sha256"] = source["receipt_sha256"]
            if kind == "retained":
                self._write("source-receipts/" + source["receipt_sha256"].split(":")[1] + ".json", source)
        receipt = {**body, "receipt_sha256": RB.sha(body)}
        if tamper:
            receipt["source_transition_id"] = "rewritten"
        self._write("receipts/" + receipt["receipt_sha256"].split(":")[1] + ".json", receipt)
        self._write("HEAD.json", {"receipt_sha256": receipt["receipt_sha256"]})
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "append %d" % self.n)
        self.git("update-ref", LEDGER_REF, "HEAD")
        self.head = receipt["receipt_sha256"]
        self.commits.append(self.git("rev-parse", "HEAD"))
        return receipt["receipt_sha256"]

    @property
    def location(self):
        return "git+%s#%s" % (self.repo, LEDGER_REF)

    def close(self):
        self.tmp.cleanup()


def declaration(_receipts, _tip, **override):
    segment = {"receipts": list(_receipts), "waived_predicate": RB.WAIVABLE_PREDICATE, "six_fields": dict(SEGMENT_SIX),
               "ledger_tip_commit": _tip, "re_minted": False, "reported_as_source_retained": False}
    segment.update(override)
    segment["declaration_sha256"] = RB.declaration_digest(segment)
    return {"source_receipt_retention": {"prefix": "source-receipts/", "receipt_field": "source_transition_sha256",
                                         "legacy_pre_retention_segment": segment}}


class LegacySegmentReadback(unittest.TestCase):
    """G4/H45: a declared pre-retention prefix is named as FAIL_CLOSED, never ALLOW, never re-minted."""

    def ledger(self, *kinds):
        g = GitLedger()
        self.addCleanup(g.close)
        digests = [g.append(k) for k in kinds]
        return g, digests

    def refused(self, g, contract, code, predicate=None):
        with self.assertRaises(RB.ReadbackRefused) as caught:
            RB.readback(g.location, org_contract=contract)
        self.assertEqual(getattr(caught.exception, "failure_code", "ORGANIZATION_LEDGER_READBACK_FAILED"), code,
                         caught.exception.detail)
        if predicate:
            self.assertEqual(caught.exception.failed_predicate, predicate)
        return caught.exception

    def test_without_a_declaration_the_readback_is_unchanged(self):
        g, (legacy, _) = self.ledger("legacy", "retained")
        exc = self.refused(g, None, "ORGANIZATION_LEDGER_READBACK_FAILED", "SOURCE_RECEIPT_RETAINED_AND_VERIFIES")
        self.assertEqual(exc.detail, "None")
        self.assertEqual(RB.readback(self.ledger("retained", "retained")[0].location)["disposition"], "ALLOW")
        g2, _ = self.ledger("retained")
        self.assertEqual(RB.readback(g2.location, org_contract={"organization": "x"})["disposition"], "ALLOW")

    def test_declared_prefix_is_fail_closed_naming_exactly_it_and_the_rest_is_verified(self):
        g, (legacy, retained) = self.ledger("legacy", "retained")
        r = RB.readback(g.location, org_contract=declaration([legacy], g.commits[0]))
        self.assertEqual(r["disposition"], "FAIL_CLOSED")
        self.assertNotIn("ALLOW", r["disposition"])
        self.assertEqual(r["failure_code"], "DECLARED_LEGACY_SEGMENT_NOT_SOURCE_RETAINED")
        self.assertEqual(r["failed_predicate"], "SOURCE_RECEIPT_RETAINED_AND_VERIFIES")
        for field in SIX:
            self.assertTrue(r.get(field), field)
        self.assertFalse(r["every_source_receipt_retained_and_verifies"])
        self.assertTrue(r["every_receipt_verifies_against_its_body"])
        self.assertTrue(r["every_chain_link_verified"])
        seg = r["legacy_segment"]
        self.assertEqual(seg["receipts"], [legacy])
        self.assertEqual(seg["fully_verified_receipts"], [retained])
        self.assertEqual([f["receipt_sha256"] for f in seg["findings"]], [legacy])
        finding = seg["findings"][0]
        self.assertEqual(finding["disposition"], "FAIL_CLOSED")
        for field in SIX:
            self.assertEqual(finding[field], SEGMENT_SIX[field])
        self.assertFalse(finding["source_receipt_retained"])
        self.assertFalse(seg["re_minted"])
        self.assertIn(legacy, r["required_evidence_or_repair"])
        self.assertEqual(r["chain_length"], 2)

    def test_the_cli_exits_nonzero_with_six_fields_and_writes_nothing(self):
        g, (legacy, _) = self.ledger("legacy", "retained")
        before = g.git("rev-parse", LEDGER_REF)
        contract = Path(g.tmp.name) / "org-contract.json"
        contract.write_text(json.dumps(declaration([legacy], g.commits[0])))
        out = subprocess.run([sys.executable, str(COMPONENT / "organization_ledger_readback.py"), "--location", g.location,
                              "--org-contract", str(contract)], capture_output=True, text=True, cwd=g.tmp.name)
        self.assertEqual(out.returncode, 1)
        r = json.loads(out.stdout)
        self.assertEqual(r["failure_code"], "DECLARED_LEGACY_SEGMENT_NOT_SOURCE_RETAINED")
        self.assertEqual(g.git("rev-parse", LEDGER_REF), before)
        self.assertEqual(g.git("status", "--porcelain"), "")

    def test_redelivery_lookup_uses_the_verified_chain_of_a_declared_legacy_ledger(self):
        g, (legacy, retained) = self.ledger("legacy", "retained")
        self.assertIsNone(RB.recorded_for(g.location, "0" * 64, declaration([legacy], g.commits[0])))
        with self.assertRaises(RB.ReadbackRefused):
            RB.recorded_for(g.location, "0" * 64)

    def test_an_undeclared_failure_after_the_segment_is_refused(self):
        g, (legacy, _, unretained) = self.ledger("legacy", "retained", "unretained")
        exc = self.refused(g, declaration([legacy], g.commits[0]), "UNDECLARED_SOURCE_RECEIPT_RETENTION_FAILURE",
                           "SOURCE_RECEIPT_RETAINED_AND_VERIFIES")
        self.assertIn(unretained, exc.detail)
        self.assertNotIn(legacy, exc.detail)

    def test_a_declared_receipt_not_in_the_chain_is_refused(self):
        g, (legacy, _) = self.ledger("legacy", "retained")
        self.refused(g, declaration([legacy, "sha256:" + "c" * 64], g.commits[0]),
                     "LEGACY_SEGMENT_NAMES_A_RECEIPT_NOT_IN_THE_CHAIN")

    def test_a_declaration_may_never_waive_self_hash_or_linkage(self):
        g, (legacy, _) = self.ledger("legacy", "retained")
        for waived in ("ORGANIZATION_RECEIPT_VERIFIES_AGAINST_ITS_BODY", "ORGANIZATION_LEDGER_CHAIN_IS_COMPLETE",
                       ["SOURCE_RECEIPT_RETAINED_AND_VERIFIES", "CHAIN_LINKAGE"]):
            self.refused(g, declaration([legacy], g.commits[0], waived_predicate=waived),
                         "LEGACY_SEGMENT_WAIVES_SELF_HASH_OR_LINKAGE")
        self.refused(g, declaration([legacy], g.commits[0], waived_predicate="RECEIPT_IS_BOUND_TO_THE_SUBMITTED_MANIFEST"),
                     "LEGACY_SEGMENT_WAIVES_A_NON_WAIVABLE_PREDICATE")

    def test_declared_receipts_must_still_self_hash_and_link(self):
        g = GitLedger()
        self.addCleanup(g.close)
        legacy = g.append("legacy", tamper=True)
        g.append("retained")
        self.refused(g, declaration([legacy], g.commits[0]), "ORGANIZATION_LEDGER_READBACK_FAILED",
                     "ORGANIZATION_RECEIPT_VERIFIES_AGAINST_ITS_BODY")
        g2 = GitLedger()
        self.addCleanup(g2.close)
        legacy2 = g2.append("legacy")
        g2.append("retained", previous="sha256:" + "d" * 64)
        self.refused(g2, declaration([legacy2], g2.commits[0]), "ORGANIZATION_LEDGER_READBACK_FAILED",
                     "ORGANIZATION_LEDGER_CHAIN_IS_COMPLETE")

    def test_a_segment_that_is_not_a_contiguous_prefix_is_refused(self):
        g, (first, second, _) = self.ledger("legacy", "legacy", "retained")
        self.refused(g, declaration([second], g.commits[1]), "LEGACY_SEGMENT_NOT_A_CONTIGUOUS_PREFIX")
        self.refused(g, declaration([second, first], g.commits[1]), "LEGACY_SEGMENT_NOT_A_CONTIGUOUS_PREFIX")
        r = RB.readback(g.location, org_contract=declaration([first, second], g.commits[1]))
        self.assertEqual(r["legacy_segment"]["receipts"], [first, second])

    def test_a_segment_overlapping_retention_is_refused(self):
        g, (legacy, retained) = self.ledger("legacy", "retained")
        self.refused(g, declaration([legacy, retained], g.commits[1]), "LEGACY_SEGMENT_OVERLAPS_RETENTION")
        g2, (a, b, _) = self.ledger("legacy", "legacy", "retained")
        # ends before its own ledger commit: the second legacy receipt would be undeclared history
        self.refused(g2, declaration([a], g2.commits[1]), "LEGACY_SEGMENT_OVERLAPS_RETENTION")
        self.refused(g2, declaration([a, b], g2.commits[2]), "LEGACY_SEGMENT_OVERLAPS_RETENTION")

    def test_the_declaration_is_digest_and_ledger_bound(self):
        g, (legacy, _) = self.ledger("legacy", "retained")
        edited = declaration([legacy], g.commits[0])
        edited["source_receipt_retention"]["legacy_pre_retention_segment"]["six_fields"]["next_attempt"] = "edited"
        self.refused(g, edited, "LEGACY_SEGMENT_DECLARATION_DIGEST_MISMATCH")
        self.refused(g, declaration([legacy], "e" * 40), "LEGACY_SEGMENT_TIP_COMMIT_NOT_ON_THE_LEDGER_REF")
        posix = Path(g.tmp.name) / "posix"
        shutil.copytree(g.repo, posix, ignore=shutil.ignore_patterns(".git"))
        with self.assertRaises(RB.ReadbackRefused) as caught:
            RB.readback(str(posix), org_contract=declaration([legacy], g.commits[0]))
        self.assertEqual(caught.exception.failure_code, "LEGACY_SEGMENT_TIP_COMMIT_UNVERIFIABLE")

    def test_an_incomplete_or_malformed_declaration_is_refused(self):
        g, (legacy, _) = self.ledger("legacy", "retained")
        pr9_shape = {"source_receipt_retention": {"legacy_pre_retention_segment": {
            "receipts": [legacy], "ledger_tip_commit": g.commits[0], "re_minted": False,
            "reported_as_source_retained": False}}}
        exc = self.refused(g, pr9_shape, "LEGACY_SEGMENT_DECLARATION_INCOMPLETE")
        self.assertIn("six_fields", exc.detail)
        for override in ({"re_minted": True}, {"reported_as_source_retained": True},
                         {"six_fields": {k: v for k, v in SEGMENT_SIX.items() if k != "next_attempt"}},
                         {"receipts": []}, {"receipts": [legacy, legacy]}, {"ledger_tip_commit": "HEAD"}):
            self.refused(g, declaration([legacy], g.commits[0], **override), "LEGACY_SEGMENT_DECLARATION_INVALID")

    def test_generator_carries_a_valid_declaration_and_refuses_an_invalid_one(self):
        segment = declaration(["sha256:" + "a" * 64], "f" * 40)["source_receipt_retention"]
        c = Consumer(dict(PILOT, source_receipt_retention=segment))
        self.addCleanup(c.close)
        tl = c.root / ".stegverse/transition-ledger"
        self.assertEqual(json.loads((tl / "org-contract.json").read_text())["source_receipt_retention"], segment)
        args = [sys.executable, str(COMPONENT / "generate_ledger_contracts.py"), str(tl / "organization-ledger.parameters.json"), "--out-dir", str(tl), "--check"]
        self.assertEqual(subprocess.run(args, capture_output=True).returncode, 0)
        bad = json.loads(json.dumps(segment))
        bad["legacy_pre_retention_segment"]["waived_predicate"] = "ORGANIZATION_RECEIPT_VERIFIES_AGAINST_ITS_BODY"
        (tl / "bad.json").write_text(json.dumps(dict(PILOT, source_receipt_retention=bad)))
        out = subprocess.run([sys.executable, str(COMPONENT / "generate_ledger_contracts.py"), str(tl / "bad.json"),
                              "--out-dir", str(Path(c.tmp.name) / "unused")], capture_output=True, text=True)
        self.assertEqual(out.returncode, 1)
        refusal = json.loads(out.stdout.splitlines()[-1])
        self.assertEqual(refusal["failure_code"], "LEGACY_SEGMENT_WAIVES_SELF_HASH_OR_LINKAGE")
        for field in SIX:
            self.assertTrue(refusal.get(field), field)
        self.assertFalse((Path(c.tmp.name) / "unused").exists())


SV011_SEGMENT_ACA5AFD = {
    "receipts": ["sha256:3db9008d0326bdfa687796308fd61dc16e11e299e1c3762e03e577cd1f23fe51"],
    "ledger_tip_commit": "2cc58cec07117909750a760933641725b86a204b",
    "verified_by": "repo_receipt_sha256 names a receipt on the repository-ledger/SV-011/.github chain that verifies against its body",
    "re_minted": False, "reported_as_source_retained": False,
    "waived_predicate": "SOURCE_RECEIPT_RETAINED_AND_VERIFIES",
    "six_fields": {
        "failure_code": "SOURCE_RECEIPT_RETAINED_AND_VERIFIES",
        "failed_predicate": "EVERY_ORGANIZATION_RECEIPT_RETAINS_AND_VERIFIES_ITS_SOURCE_RECEIPT (SV-011/.github ledger, receipt sha256:3db9008d\u2026 at tip 2cc58cec; source_transition_sha256 absent, no source-receipts/)",
        "required_evidence_or_repair": "forward retention (each new org receipt names source_transition_sha256 and retains its repository receipt under source-receipts/), plus an explicit legacy-segment rule for 3db9008d in the shared readback component (H28 C6); never re-mint",
        "retry_entrypoint": "SV-011/.github resident-runtime/organization_ledger_readback.py::main; StegVerse-Labs/.github data/reusable-task-components/ (readback component)",
        "owning_existing_goal": "SV011-TT-CAPABILITY-MAP-OBSERVATION-001 (#167 lane B, #68)",
        "next_attempt": "after the component readback carries the legacy-segment rule, read the ref back with it; receipts appended after PR #9 merges are retained"},
    "declaration_sha256": "sha256:36c43b78e2c820d5448d7edb7f4bf7222d22faf9a91925ad18e3e50a54267375",
}


class DeclarationDigestCanonicalization(unittest.TestCase):
    """The declaration digest is pinned: UTF-8, sort_keys, (',', ':'), ensure_ascii=False -- the receipt form."""

    @staticmethod
    def explicit(value, ensure_ascii=False):
        import hashlib
        text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=ensure_ascii)
        return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()

    def test_pinned_form_is_declared_and_is_the_receipt_form(self):
        self.assertEqual(RB.CANONICAL_JSON, {"encoding": "utf-8", "sort_keys": True,
                                             "separators": [",", ":"], "ensure_ascii": False})
        body = {"z": "\u2026", "a": {"\u00e9": [1, "\U0001f512"]}}
        self.assertEqual(RB.sha(body), self.explicit(body))
        agg = Consumer()
        self.addCleanup(agg.close)
        writer = agg.py('agg = load("aggregate_repo_transition.py")\nprint(json.dumps(agg.sha(%r)))' % (body,))
        self.assertEqual(writer, RB.sha(body))
        receipt = {**body, "receipt_sha256": RB.sha(body)}
        self.assertTrue(RB.self_verifies(receipt))

    def test_non_ascii_member_digest_is_ensure_ascii_false(self):
        g = GitLedger()
        self.addCleanup(g.close)
        legacy = g.append("legacy")
        g.append("retained")
        six = dict(SEGMENT_SIX, failed_predicate="EVERY_RECEIPT_RETAINS_ITS_SOURCE (receipt " + legacy[:15] + "\u2026, caf\u00e9 \U0001f512)")
        contract = declaration([legacy], g.commits[0], six_fields=six)
        segment = contract["source_receipt_retention"]["legacy_pre_retention_segment"]
        unsigned = {k: v for k, v in segment.items() if k != "declaration_sha256"}
        self.assertEqual(segment["declaration_sha256"], self.explicit(unsigned))
        self.assertNotEqual(self.explicit(unsigned), self.explicit(unsigned, ensure_ascii=True))
        r = RB.readback(g.location, org_contract=contract)
        self.assertEqual(r["failure_code"], "DECLARED_LEGACY_SEGMENT_NOT_SOURCE_RETAINED")
        self.assertEqual(r["legacy_segment"]["declaration_digest_canonicalization"], RB.CANONICAL_JSON)
        self.assertEqual(r["legacy_segment"]["findings"][0]["failed_predicate"], six["failed_predicate"])
        ascii_signed = json.loads(json.dumps(contract))
        ascii_signed["source_receipt_retention"]["legacy_pre_retention_segment"]["declaration_sha256"] = \
            self.explicit(unsigned, ensure_ascii=True)
        with self.assertRaises(RB.ReadbackRefused) as caught:
            RB.readback(g.location, org_contract=ascii_signed)
        self.assertEqual(caught.exception.failure_code, "LEGACY_SEGMENT_DECLARATION_DIGEST_MISMATCH")

    def test_sv011_aca5afd_declaration_digest_cross_checks(self):
        segment = dict(SV011_SEGMENT_ACA5AFD)
        self.assertEqual(RB.declaration_digest(segment), segment["declaration_sha256"])
        self.assertIs(RB.validate_legacy_segment(segment), segment)
        unsigned = {k: v for k, v in segment.items() if k != "declaration_sha256"}
        self.assertEqual(self.explicit(unsigned, ensure_ascii=True),
                         "sha256:ecf4aabe417364bb5768b0870fe8a0c61fadd8bf77a3c86b65480673c8608cec")


if __name__ == "__main__":
    unittest.main()
