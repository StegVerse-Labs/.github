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
        self.assertEqual(refusal["failed_predicate"], "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH")
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
            self.assertEqual(r["refused"]["failed_predicate"], "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH")
        # Shared rule (org-kernel/kernel.py::supplied_epoch_failure): only None is absent; "" is not ASCII [0-9]+.
        for absent, code in ((None, "HB_EPOCH_NOT_SUPPLIED"), ("", "HB_EPOCH_INVALID")):
            r = self.c.py('common = load("ledger_common.py")\n'
                          'print(json.dumps(refusal(lambda: common.require_supplied_epoch(%r, "x"))))' % (absent,))
            self.assertEqual(r["refused"]["failure_code"], code, absent)
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


NS = "repository-ledger/formalism-tests/.github"
REPO_CONTRACT = {"repository_ledger_location": {"namespace": NS}}


def rb(location, **kwargs):
    """The readback as the workflow calls it: with the contract's repository namespace."""
    kwargs.setdefault("repository_namespace", NS)
    kwargs.setdefault("repo_contract", REPO_CONTRACT)
    return RB.readback(location, **kwargs)


class LegacySegmentReadback(unittest.TestCase):
    """G4/H45: a declared pre-retention prefix is named as FAIL_CLOSED, never ALLOW, never re-minted."""

    def ledger(self, *kinds):
        g = GitLedger()
        self.addCleanup(g.close)
        digests = [g.append(k) for k in kinds]
        return g, digests

    def refused(self, g, contract, code, predicate=None):
        with self.assertRaises(RB.ReadbackRefused) as caught:
            rb(g.location, org_contract=contract)
        self.assertEqual(getattr(caught.exception, "failure_code", "ORGANIZATION_LEDGER_READBACK_FAILED"), code,
                         caught.exception.detail)
        if predicate:
            self.assertEqual(caught.exception.failed_predicate, predicate)
        return caught.exception

    def test_without_a_declaration_the_readback_is_unchanged(self):
        g, (legacy, _) = self.ledger("legacy", "retained")
        exc = self.refused(g, None, "ORGANIZATION_LEDGER_READBACK_FAILED", "SOURCE_RECEIPT_RETAINED_AND_VERIFIES")
        # Same disposition, code and predicate as before; the repair now names the receipt instead of 'None' (P1-FC-12).
        self.assertTrue(exc.detail.startswith("organization receipt " + legacy + " names no source receipt"))
        self.assertEqual(rb(self.ledger("retained", "retained")[0].location)["disposition"], "ALLOW")
        g2, _ = self.ledger("retained")
        self.assertEqual(rb(g2.location, org_contract={"organization": "x"})["disposition"], "ALLOW")

    def test_declared_prefix_is_fail_closed_naming_exactly_it_and_the_rest_is_verified(self):
        g, (legacy, retained) = self.ledger("legacy", "retained")
        r = rb(g.location, org_contract=declaration([legacy], g.commits[0]))
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
        tl = Path(g.tmp.name) / ".stegverse/transition-ledger"
        tl.mkdir(parents=True)
        (tl / "contract.json").write_text(json.dumps(REPO_CONTRACT))
        base = [sys.executable, str(COMPONENT / "organization_ledger_readback.py"), "--location", g.location,
                "--org-contract", str(contract)]
        out = subprocess.run(base + ["--repository-namespace", NS], capture_output=True, text=True, cwd=g.tmp.name)
        self.assertEqual(out.returncode, 1)
        r = json.loads(out.stdout)
        # past the namespace guard, the CLI walks the repository chain; this ledger has none, so that
        # refuses next (the full CLI path with a repository chain is the SV-011 parity harness)
        self.assertEqual(r["failed_predicate"], "REPOSITORY_LEDGER_HEAD_PRESENT")
        for args in ([], ["--repository-namespace", "repository-ledger/other/.github"]):
            out = subprocess.run(base + args, capture_output=True, text=True, cwd=g.tmp.name)
            self.assertEqual(out.returncode, 1)
            r = json.loads(out.stdout)
            self.assertEqual(r["failed_predicate"], "REPOSITORY_NAMESPACE_MATCHES_THE_CONTRACT")
            for field in SIX:
                self.assertTrue(r.get(field), field)
        self.assertEqual(g.git("rev-parse", LEDGER_REF), before)
        self.assertEqual(g.git("status", "--porcelain"), "")

    def test_redelivery_lookup_uses_the_verified_chain_of_a_declared_legacy_ledger(self):
        g, (legacy, retained) = self.ledger("legacy", "retained")
        self.assertIsNone(RB.recorded_for(g.location, "0" * 64, declaration([legacy], g.commits[0]), NS, REPO_CONTRACT))
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
        r = rb(g.location, org_contract=declaration([first, second], g.commits[1]))
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
            rb(str(posix), org_contract=declaration([legacy], g.commits[0]))
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
        r = rb(g.location, org_contract=contract)
        self.assertEqual(r["failure_code"], "DECLARED_LEGACY_SEGMENT_NOT_SOURCE_RETAINED")
        self.assertEqual(r["legacy_segment"]["declaration_digest_canonicalization"], RB.CANONICAL_JSON)
        self.assertEqual(r["legacy_segment"]["findings"][0]["failed_predicate"], six["failed_predicate"])
        ascii_signed = json.loads(json.dumps(contract))
        ascii_signed["source_receipt_retention"]["legacy_pre_retention_segment"]["declaration_sha256"] = \
            self.explicit(unsigned, ensure_ascii=True)
        with self.assertRaises(RB.ReadbackRefused) as caught:
            rb(g.location, org_contract=ascii_signed)
        self.assertEqual(caught.exception.failure_code, "LEGACY_SEGMENT_DECLARATION_DIGEST_MISMATCH")

    def test_sv011_aca5afd_declaration_digest_cross_checks(self):
        segment = dict(SV011_SEGMENT_ACA5AFD)
        self.assertEqual(RB.declaration_digest(segment), segment["declaration_sha256"])
        self.assertIs(RB.validate_legacy_segment(segment), segment)
        unsigned = {k: v for k, v in segment.items() if k != "declaration_sha256"}
        self.assertEqual(self.explicit(unsigned, ensure_ascii=True),
                         "sha256:ecf4aabe417364bb5768b0870fe8a0c61fadd8bf77a3c86b65480673c8608cec")


class NamespaceAndEmptyLedger(unittest.TestCase):
    """C6 fix (parity with SV-011 @8dcf892): a declared segment needs the contract's namespace; an empty ledger is HEAD_ABSENT."""

    def ledger(self, *kinds):
        g = GitLedger()
        self.addCleanup(g.close)
        return g, [g.append(k) for k in kinds]

    def test_a_declared_segment_requires_the_contract_namespace(self):
        g, (legacy, _) = self.ledger("legacy", "retained")
        contract = declaration([legacy], g.commits[0])
        for namespace, repo_contract in ((None, REPO_CONTRACT), ("", REPO_CONTRACT),
                                         ("repository-ledger/other/.github", REPO_CONTRACT), (NS, {}),
                                         (NS, {"repository_ledger_location": {"namespace": "repository-ledger/x/.github"}})):
            with self.assertRaises(RB.ReadbackRefused) as caught:
                RB.readback(g.location, org_contract=contract, repository_namespace=namespace, repo_contract=repo_contract)
            self.assertEqual(caught.exception.failed_predicate, "REPOSITORY_NAMESPACE_MATCHES_THE_CONTRACT")
            self.assertEqual(getattr(caught.exception, "failure_code", "ORGANIZATION_LEDGER_READBACK_FAILED"),
                             "ORGANIZATION_LEDGER_READBACK_FAILED")
        r = RB.readback(g.location, org_contract=contract, repository_namespace=NS, repo_contract=REPO_CONTRACT)
        self.assertEqual(r["failure_code"], "DECLARED_LEGACY_SEGMENT_NOT_SOURCE_RETAINED")
        with self.assertRaises(RB.ReadbackRefused) as caught:
            RB.recorded_for(g.location, "0" * 64, contract)
        self.assertEqual(caught.exception.failed_predicate, "REPOSITORY_NAMESPACE_MATCHES_THE_CONTRACT")

    def test_without_a_declaration_no_namespace_is_needed(self):
        g, _ = self.ledger("retained", "retained")
        self.assertEqual(RB.readback(g.location)["disposition"], "ALLOW")
        self.assertEqual(RB.readback(g.location, org_contract={"organization": "x"})["disposition"], "ALLOW")

    def test_an_empty_ledger_is_head_absent_with_the_head_present_predicate(self):
        g = GitLedger()
        self.addCleanup(g.close)
        (g.repo / "README").write_text("x")
        g.git("add", "-A")
        g.git("commit", "-q", "-m", "empty")
        g.git("update-ref", LEDGER_REF, "HEAD")
        posix = Path(g.tmp.name) / "posix-empty"
        posix.mkdir()
        for location in (g.location, str(posix)):
            with self.assertRaises(RB.ReadbackRefused) as caught:
                RB.readback(location)
            self.assertEqual(caught.exception.failure_code, "ORGANIZATION_LEDGER_HEAD_ABSENT")
            self.assertEqual(caught.exception.failed_predicate, "ORGANIZATION_LEDGER_HEAD_PRESENT")
            # recorded_for keys on the predicate: an empty ledger has recorded nothing
            self.assertIsNone(RB.recorded_for(location, "0" * 64))
        out = subprocess.run([sys.executable, str(COMPONENT / "organization_ledger_readback.py"), "--location", g.location],
                             capture_output=True, text=True, cwd=g.tmp.name)
        self.assertEqual(out.returncode, 1)
        r = json.loads(out.stdout)
        self.assertEqual((r["disposition"], r["failure_code"], r["failed_predicate"]),
                         ("FAIL_CLOSED", "ORGANIZATION_LEDGER_HEAD_ABSENT", "ORGANIZATION_LEDGER_HEAD_PRESENT"))
        for field in SIX:
            self.assertTrue(r.get(field), field)
        out = subprocess.run([sys.executable, str(COMPONENT / "organization_ledger_readback.py"), "--location", g.location,
                              "--recorded-for", "0" * 64], capture_output=True, text=True, cwd=g.tmp.name)
        self.assertEqual((out.returncode, out.stdout), (0, "\n"))



class PropagateAfterAppend(unittest.TestCase):
    """Item (5), INDEX H51: the existing propagate() runs after each append, through propagate_after_append.py."""
    REPO = "formalism-tests/.github"

    def setUp(self):
        self.c = Consumer()
        self.addCleanup(self.c.close)
        self.repo_root = self.c.ledgers / "repo"

    def emit(self, transition_id="t-1"):
        out = self.c.cli("emit.py", "--transition-id", transition_id, "--transition-class", "TEST",
                         "--predecessor-state-sha256", A, "--successor-state-sha256", B, "--hb-epoch", str(EPOCH))
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout.splitlines()[-1])

    def propagate(self, epoch=str(EPOCH)):
        args = ["--repository", self.REPO, "--repository-ledger-root", str(self.repo_root)]
        if epoch is not None:
            args.append("--hb-epoch=" + epoch)
        out = self.c.cli("propagate_after_append.py", *args)
        return out.returncode, json.loads(out.stdout.splitlines()[-1])

    def org_head(self):
        head = self.c.ledgers / "org" / "HEAD.json"
        return head.read_text() if head.exists() else None

    def assertSix(self, refusal, code):
        self.assertEqual(refusal["disposition"], "FAIL_CLOSED")
        self.assertEqual(refusal["failure_code"], code)
        for field in SIX:
            self.assertTrue(isinstance(refusal.get(field), str) and refusal[field].strip(), field)

    def test_plus_33_is_refused_before_propagation_is_reached(self):
        self.emit()
        for bad in ("+33", " 33", "3_3", "31"):
            code, out = self.propagate(bad)
            self.assertEqual(code, 1, bad)
            self.assertSix(out, "HB_EPOCH_INVALID")
            self.assertEqual(out["retry_entrypoint"], "org-kernel/organization-ledger/propagate_after_append.py::main")
            self.assertEqual(self.c.written("org"), [], bad)
        code, out = self.propagate(None)
        self.assertEqual((code, out["failure_code"]), (1, "HB_EPOCH_NOT_SUPPLIED"))
        # in-process: the propagation module is never loaded when the epoch is refused
        r = self.c.py('w = load("propagate_after_append.py")\nloaded = []\nreal = w._load\n'
                      'w._load = lambda name: (loaded.append(name), real(name))[1]\n'
                      'res = refusal(lambda: w.run(%r, Path(%r), "+33"))\n'
                      'print(json.dumps({"res": res, "loaded": loaded}))' % (self.REPO, str(self.repo_root)))
        self.assertEqual(r["res"]["refused"]["failure_code"], "HB_EPOCH_INVALID")
        self.assertEqual(r["loaded"], [], "propagate_repository_receipts must not be reached")

    def test_the_validated_epoch_is_handed_over_in_process_not_re_coerced(self):
        self.emit()
        r = self.c.py('w = load("propagate_after_append.py")\nseen = {}\nreal = w._load\n'
                      'def spy(name):\n    m = real(name)\n    orig = m.propagate\n'
                      '    m.propagate = lambda *a, **k: (seen.update(epoch=k["hb_epoch"], type=type(k["hb_epoch"]).__name__), orig(*a, **k))[1]\n'
                      '    return m\n'
                      'w._load = spy\nw.run(%r, Path(%r), "0033")\nprint(json.dumps(seen))' % (self.REPO, str(self.repo_root)))
        self.assertEqual(r, {"epoch": 33, "type": "int"})

    def test_an_orphan_repository_receipt_is_carried_once(self):
        receipt = self.emit()
        code, out = self.propagate()
        self.assertEqual(code, 0, out)
        self.assertEqual([p["repository_receipt_sha256"] for p in out["propagated"]], [receipt["receipt_sha256"]])
        before = self.c.written("org")
        code, again = self.propagate()
        self.assertEqual((code, again["propagated"], again["skipped"]), (0, [], [receipt["receipt_sha256"]]))
        self.assertEqual(self.c.written("org"), before, "a second run is a no-op")

    def test_after_a_normal_append_it_is_a_no_op(self):
        receipt = self.emit()
        self.c.py('agg = load("aggregate_repo_transition.py")\nsrc = json.loads(%r)\n'
                  'print(json.dumps(agg.append(src, "REPO_STATE_PROPAGATION", agg.GENESIS, src["receipt_sha256"], {}, "NONE", hb_epoch=%d)))'
                  % (json.dumps(receipt), EPOCH))
        before = self.c.written("org")
        code, out = self.propagate()
        self.assertEqual((code, out["propagated"], out["skipped"]), (0, [], [receipt["receipt_sha256"]]))
        self.assertEqual(self.c.written("org"), before)

    def test_a_refusal_is_printed_unchanged_and_the_appended_receipt_stands(self):
        receipt = self.emit()
        self.c.py('agg = load("aggregate_repo_transition.py")\nsrc = json.loads(%r)\n'
                  'print(json.dumps(agg.append(src, "REPO_STATE_PROPAGATION", agg.GENESIS, src["receipt_sha256"], {}, "NONE", hb_epoch=%d)))'
                  % (json.dumps(receipt), EPOCH))
        head, files = self.org_head(), self.c.written("org")
        path = self.repo_root / "receipts" / (receipt["receipt_sha256"].split(":", 1)[1] + ".json")
        tampered = json.loads(path.read_text()); tampered["transition_id"] = "edited"
        path.write_text(json.dumps(tampered))
        code, out = self.propagate()
        self.assertEqual(code, 1)
        self.assertSix(out, "REPOSITORY_LEDGER_RECEIPT_HASH_MISMATCH")
        self.assertEqual(out["schema"], "stegverse.organization-ledger-append-refusal/v1", "the LedgerRefusal, unchanged")
        self.assertEqual(out["retry_entrypoint"], "org-kernel/organization-ledger/propagate_repository_receipts.py::propagate")
        self.assertEqual((self.org_head(), self.c.written("org")), (head, files), "nothing rolled back, nothing added")

    def test_a_plain_systemexit_and_a_missing_location_get_six_fields(self):
        r = self.c.py('w = load("propagate_after_append.py")\nimport io, contextlib\n'
                      'def boom(*a): raise SystemExit("SOMETHING_REFUSED: plain message")\n'
                      'w.run = boom\nbuf = io.StringIO()\n'
                      'with contextlib.redirect_stdout(buf): code = w.main(["--repository", "x/y", "--repository-ledger-root", "/nonexistent"])\n'
                      'print(json.dumps({"code": code, "out": json.loads(buf.getvalue())}))')
        self.assertEqual(r["code"], 1)
        self.assertSix(r["out"], "SOMETHING_REFUSED")
        self.assertEqual(r["out"]["failed_predicate"], "REPOSITORY_RECEIPTS_PROPAGATE_AFTER_THE_APPEND")
        self.emit()
        env = {k: v for k, v in self.c.env.items() if k != "STEGVERSE_ORG_LEDGER_ROOT"}
        out = subprocess.run([sys.executable, str(COMPONENT / "propagate_after_append.py"), "--repository", self.REPO,
                              "--repository-ledger-root", str(self.repo_root), "--hb-epoch", str(EPOCH)],
                             cwd=self.c.root, env=env, capture_output=True, text=True)
        self.assertEqual(out.returncode, 1, out.stderr)
        self.assertSix(json.loads(out.stdout.splitlines()[-1]), "LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER")

    def test_the_workflow_propagates_after_each_append_and_fails_after_publish(self):
        wf = (COMPONENT.parents[1] / ".github/workflows/organization-ledger-transition-reusable.yml").read_text()
        self.assertEqual(wf.count('python "$COMPONENT/propagate_after_append.py"'), 2)
        self.assertLess(wf.index("organization_manifest_ingress.py\" \\"), wf.index('propagate_after_append.py"'))
        self.assertLess(wf.index("--self-close \\"), wf.rindex('propagate_after_append.py"'))
        self.assertNotIn('--out "$out/propagation.json" || true', wf)
        self.assertEqual(wf.count('--hb-epoch "$HB_EPOCH" --out "$out/propagation.json" || rc=$?'), 2)
        self.assertEqual(wf.count('echo "$rc" > "$out/propagation.exit"'), 2)
        gate = wf.index("Fail on a recorded propagation refusal")
        self.assertLess(wf.index("Publish the ledger ref (fast-forward only)"), gate)
        self.assertLess(wf.index("Read the organization and repository ledgers back from a fresh fetch"), gate)
        self.assertNotIn("type=int", (COMPONENT / "propagate_repository_receipts.py").read_text())


def _load_store():
    import importlib.util
    spec = importlib.util.spec_from_file_location("ledger_store_fc12", COMPONENT / "ledger_store.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REMOTE_LOCATORS = ("https://github.com/StegVerse-org/.github", "http://example.invalid/ledger",
                   "ssh://git@github.com/StegVerse-org/.github.git", "git://github.com/StegVerse-org/.github",
                   "file:///tmp/ledger", "git@github.com:StegVerse-org/.github.git", "github.com:StegVerse-org/.github",
                   "git+https://github.com/StegVerse-org/.github#refs/stegverse/organization-ledger",
                   "git+git@github.com:StegVerse-org/.github#refs/stegverse/organization-ledger",
                   "git+ssh://github.com/StegVerse-org/.github#refs/stegverse/organization-ledger:" + NS)
LOCATOR_GOAL = "StegVerse-org/.github#163"


class RemoteLocatorRefused(unittest.TestCase):
    """P1-FC-12: a remote locator is refused in six fields, never read as an empty local ledger."""

    def assert_six(self, refusal, retry):
        for field in SIX:
            self.assertTrue(refusal.get(field), field)
            self.assertNotEqual(str(refusal.get(field)).strip(), "None", field)
        self.assertEqual((refusal["disposition"], refusal["failure_code"], refusal["owning_existing_goal"]),
                         ("FAIL_CLOSED", "LEDGER_LOCATOR_INVALID", LOCATOR_GOAL))
        self.assertEqual(refusal["retry_entrypoint"], retry)

    def test_parse_locator_refuses_every_remote_form(self):
        store = _load_store()
        for locator in REMOTE_LOCATORS:
            with self.assertRaises(ValueError) as caught:   # still a ValueError, so existing callers catch it
                store.parse_locator(locator)
            self.assertIsInstance(caught.exception, store.LedgerLocatorInvalid)
            self.assertEqual(caught.exception.failure_code, "LEDGER_LOCATOR_INVALID")
            self.assert_six(caught.exception.refusal, "org-kernel/organization-ledger/ledger_store.py::parse_locator")
            with self.assertRaises(store.LedgerLocatorRefused):
                store.open_store(locator)

    def test_local_locators_are_unchanged(self):
        store = _load_store()
        with tempfile.TemporaryDirectory() as tmp:
            for locator in (tmp, tmp + "/a:b", "./relative", "relative/dir"):
                self.assertIsInstance(store.parse_locator(locator), Path)
            loc = store.parse_locator("git+" + tmp + "#" + LEDGER_REF + ":" + NS)
            self.assertEqual((loc.repository, loc.ref, loc.namespace), (Path(tmp).resolve(), LEDGER_REF, NS))
            self.assertEqual(store.parse_locator("git+./rel#" + LEDGER_REF).repository, Path("rel").resolve())

    def test_readback_cli_refuses_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            for locator in REMOTE_LOCATORS:
                out = subprocess.run([sys.executable, str(COMPONENT / "organization_ledger_readback.py"),
                                      "--location", locator], capture_output=True, text=True, cwd=tmp)
                self.assertEqual(out.returncode, 1, locator)
                r = json.loads(out.stdout)
                self.assert_six(r, "org-kernel/organization-ledger/organization_ledger_readback.py::main")
                self.assertEqual(r["failed_predicate"], "LEDGER_LOCATOR_NAMES_A_STORE_ON_THIS_NODE")
            self.assertEqual(os.listdir(tmp), [], "nothing is created for a remote locator")

    def test_writers_refuse_a_remote_ledger_root_in_six_fields(self):
        c = Consumer()
        self.addCleanup(c.close)
        c.env["STEGVERSE_ORG_LEDGER_ROOT"] = "https://github.com/StegVerse-org/.github"
        c.env["STEGVERSE_REPO_LEDGER_ROOT"] = "git+https://github.com/StegVerse-org/.github#refs/stegverse/repo"
        r = c.py(repo_receipt_snippet() + 'emit = load("emit.py")\n'
                 'print(json.dumps({"agg": refusal(lambda: agg.append(src, "REPO_STATE_PROPAGATION", agg.GENESIS, "%s", {}, "NONE", hb_epoch=%d)), '
                 '"emit": refusal(lambda: emit.lr())}))' % (B, EPOCH))
        self.assert_six(r["agg"]["refused"], "org-kernel/organization-ledger/aggregate_repo_transition.py::append")
        self.assertEqual(r["emit"]["refused"]["failure_code"], "LEDGER_LOCATOR_INVALID")
        self.assertEqual(r["emit"]["refused"]["owning_existing_goal"], LOCATOR_GOAL)
        self.assertEqual((c.written("org"), c.written("repo")), ([], []))
        self.assertFalse((c.root / "https:").exists())


class RequiredRepairIsNeverEmpty(unittest.TestCase):
    """No refusal the component emits has required_evidence_or_repair empty or 'None'."""

    def test_unretained_source_names_its_repair(self):
        g = GitLedger()
        self.addCleanup(g.close)
        legacy = g.append("legacy")
        with self.assertRaises(RB.ReadbackRefused) as caught:
            RB.readback(g.location)
        self.assertEqual(caught.exception.failed_predicate, "SOURCE_RECEIPT_RETAINED_AND_VERIFIES")
        self.assertIn(legacy, caught.exception.detail)
        out = subprocess.run([sys.executable, str(COMPONENT / "organization_ledger_readback.py"), "--location", g.location],
                             capture_output=True, text=True, cwd=g.tmp.name)
        r = json.loads(out.stdout)
        self.assertEqual((out.returncode, r["disposition"]), (1, "FAIL_CLOSED"))
        self.assertNotIn(r["required_evidence_or_repair"].strip(), ("", "None"))
        self.assertIn("legacy segment", r["required_evidence_or_repair"])

    def test_readback_refusal_never_reports_none(self):
        for detail in (None, "", "None", "  "):
            r = RB._refusal("loc", RB.ReadbackRefused("SOME_PREDICATE", "x"))
            exc = RB.ReadbackRefused("SOME_PREDICATE", "x")
            exc.detail = detail
            r = RB._refusal("loc", exc)
            self.assertNotIn(str(r["required_evidence_or_repair"]).strip(), ("", "None"), detail)
            self.assertIn("SOME_PREDICATE", r["required_evidence_or_repair"])

    def test_ledger_refusal_never_carries_none(self):
        c = Consumer()
        self.addCleanup(c.close)
        r = c.py('common = load("ledger_common.py")\n'
                 'print(json.dumps([common.LedgerRefusal("x", required_evidence_or_repair=v).refusal["required_evidence_or_repair"] '
                 'for v in (None, "", "None", " None ")]))')
        for value in r:
            self.assertNotIn(value.strip(), ("", "None"))



class LocatorRetryEntrypointFromFile(unittest.TestCase):
    """Lane B #162: the locator refusal names its own path, so the org resident-runtime byte copy stays identical."""

    def load_copy(self, relative):
        import importlib.util
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        target = Path(tmp.name) / "checkout" / relative
        target.parent.mkdir(parents=True)
        shutil.copyfile(COMPONENT / "ledger_store.py", target)
        if not relative.startswith(("org-kernel/", "resident-runtime/")):
            (Path(tmp.name) / "checkout" / ".git").mkdir()
        spec = importlib.util.spec_from_file_location("ledger_store_copy_" + relative.replace("/", "_").replace(".", "_"), target)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with self.assertRaises(module.LedgerLocatorRefused) as caught:
            module.parse_locator("https://github.com/StegVerse-org/.github")
        return caught.exception.refusal["retry_entrypoint"]

    def test_the_component_names_its_component_path(self):
        self.assertEqual(_load_store()._locator_retry_entrypoint(), "org-kernel/organization-ledger/ledger_store.py::parse_locator")

    def test_a_byte_copy_names_where_it_is(self):
        self.assertEqual(self.load_copy("resident-runtime/ledger_store.py"), "resident-runtime/ledger_store.py::parse_locator")
        self.assertEqual(self.load_copy("org-kernel/organization-ledger/ledger_store.py"),
                         "org-kernel/organization-ledger/ledger_store.py::parse_locator")
        self.assertEqual(self.load_copy("tools/ledger/ledger_store.py"), "tools/ledger/ledger_store.py::parse_locator")

    def test_the_module_names_no_ledger_location_of_its_own(self):
        """Mirrors org tests/test_git_ledger_store.py::test_the_module_names_no_ledger_location_of_its_own (Lane B BC1),
        so the org resident-runtime/ledger_store.py byte copy passes the org guard."""
        text = (COMPONENT / "ledger_store.py").read_text()
        for forbidden in ("refs/stegverse", "refs/heads/", "refs/ledger", "DEFAULT_REF", "DEFAULT_LOCATOR"):
            self.assertNotIn(forbidden, text)

    def test_no_path_is_hard_coded(self):
        text = (COMPONENT / "ledger_store.py").read_text()
        self.assertNotIn('"org-kernel/organization-ledger/ledger_store.py', text)


class SharedSuppliedEpochRule(unittest.TestCase):
    """Lane B #162 N2: the same decisions, codes and predicate as org-kernel/kernel.py::supplied_epoch_failure."""

    CASES = (None, "", "33", "32", "31", "0", "+33", " 33", "33 ", "3_3", "33.0", "\u0663\u0663", "1e3", 33, 32, 31, 0, -40,
             True, False, 33.0, [33], {"epoch": 33}, "0033", "999999999999")

    def test_decisions_match_the_kernel(self):
        c = Consumer()
        self.addCleanup(c.close)
        r = c.py('import ast\n'
                 'k = load("../kernel.py"); lc = load("ledger_common.py")\n'
                 'cases = ' + repr(self.CASES) + '\n'
                 'out = []\n'
                 'for v in cases:\n'
                 '    kf = k.supplied_epoch_failure(v); lf = lc.supplied_epoch_failure(v)\n'
                 '    got = refusal(lambda: lc.require_supplied_epoch(v, "t"))\n'
                 '    out.append([repr(v), kf and kf[0], lf and lf[0], (got.get("refused") or {}).get("failed_predicate"), '
                 '(got.get("refused") or {}).get("derived_from_clock"), got.get("returned")])\n'
                 'print(json.dumps({"rows": out, "predicate": k.HB_EPOCH_PREDICATE}))')
        for value, kernel_code, local_code, predicate, derived, returned in r["rows"]:
            self.assertEqual(kernel_code, local_code, value)
            if kernel_code is None:
                self.assertIsNotNone(returned, value)
            else:
                self.assertEqual(predicate, r["predicate"], value)
                self.assertIs(derived, False, value)



class PropagationAlwaysRecorded(unittest.TestCase):
    """Lane B #162 W1 and N1: every outcome is recorded in six fields and --out is always written."""
    REPO = PropagateAfterAppend.REPO
    setUp, emit, propagate = PropagateAfterAppend.setUp, PropagateAfterAppend.emit, PropagateAfterAppend.propagate
    assertSix = PropagateAfterAppend.assertSix

    def test_any_exception_is_recorded_and_out_is_written(self):
        out_dir = Path(self.c.tmp.name) / "outs"
        r = self.c.py('w = load("propagate_after_append.py")\nimport io, contextlib\n'
                      'cases = {"runtime": RuntimeError("LEDGER_STORE_CAS_CONTENTION_EXHAUSTED"), "notfound": FileNotFoundError("HEAD.json"),\n'
                      '         "key": KeyError("receipt_sha256"), "exit_int": SystemExit(2), "exit_none": SystemExit(None),\n'
                      '         "exit_empty": SystemExit(""), "type": TypeError("bad"), "no_allow": None}\n'
                      'res = {}\n'
                      'for name, exc in cases.items():\n'
                      '    def boom(*a, _e=exc):\n'
                      '        if _e is None: return {"schema": "x", "propagated": []}\n'
                      '        raise _e\n'
                      '    w.run = boom\n'
                      '    out = Path(%r) / (name + ".json")\n'
                      '    buf = io.StringIO()\n'
                      '    with contextlib.redirect_stdout(buf): code = w.main(["--repository", "x/y", "--repository-ledger-root", "/nonexistent", "--out", str(out)])\n'
                      '    res[name] = {"code": code, "out": json.loads(out.read_text()) if out.exists() else None}\n'
                      'print(json.dumps(res))' % str(out_dir))
        for name, got in r.items():
            self.assertEqual(got["code"], 1, name)
            self.assertIsNotNone(got["out"], name + ": --out must be written")
            expected = "PROPAGATION_REFUSAL_NOT_RECORDED"
            self.assertSix(got["out"], expected)
            self.assertEqual(got["out"]["failed_predicate"], "EVERY_NON_ALLOW_PROPAGATION_IS_RECORDED_IN_SIX_FIELDS", name)
            self.assertNotIn(got["out"]["required_evidence_or_repair"].strip(), ("", "None"))
        self.assertIn("RuntimeError: LEDGER_STORE_CAS_CONTENTION_EXHAUSTED", r["runtime"]["out"]["detail"])

    def test_a_success_carries_disposition_allow(self):
        self.emit()
        code, out = self.propagate()
        self.assertEqual((code, out["disposition"], out["schema"]), (0, "ALLOW", "stegverse.organization-repository-propagation/v1"))
        absent = self.c.cli("propagate_after_append.py", "--repository", "absent/repo", "--repository-ledger-root",
                            str(Path(self.c.tmp.name) / "nothing-here"), "--hb-epoch", str(EPOCH))
        self.assertEqual((absent.returncode, json.loads(absent.stdout.splitlines()[-1])["disposition"]), (0, "ALLOW"))

    def test_a_partial_append_lists_what_was_committed(self):
        self.emit("t-1")
        self.emit("t-2")
        r = self.c.py('w = load("propagate_after_append.py")\nreal = w._load\ncalls = []\n'
                      'def spy(name):\n    m = real(name)\n    orig = m.organization_ledger.append\n'
                      '    def flaky(*a, **k):\n'
                      '        calls.append(1)\n'
                      '        if len(calls) == 2:\n'
                      '            raise m.common.LedgerRefusal("ORG_LEDGER_APPEND_CONTENTION_EXHAUSTED", retry_entrypoint="t")\n'
                      '        return orig(*a, **k)\n'
                      '    m.organization_ledger.append = flaky\n    return m\n'
                      'w._load = spy\n'
                      'print(json.dumps(refusal(lambda: w.run(%r, Path(%r), "%d"))))' % (self.REPO, str(self.repo_root), EPOCH))
        refused = r["refused"]
        self.assertIs(refused["consequence_committed"], True)
        self.assertEqual(len(refused["propagated_before_refusal"]), 1)
        self.assertEqual(len([p for p in self.c.written("org") if p.startswith("receipts/")]), 1)


class PropagationGate(unittest.TestCase):
    """Lane B #162 G1/G2: the run's last step passes only a recorded ALLOW for every appended request."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.results = Path(self.tmp.name) / "results"

    def request(self, name, marker="ingress.json", marker_doc=None, propagation=None, exit_code=None):
        d = self.results / name
        d.mkdir(parents=True)
        (d / marker).write_text(json.dumps(marker_doc or {"disposition": "ALLOW"}))
        if propagation is not None:
            (d / "propagation.json").write_text(propagation if isinstance(propagation, str) else json.dumps(propagation))
        if exit_code is not None:
            (d / "propagation.exit").write_text(str(exit_code) + "\n")

    def gate(self):
        out = subprocess.run([sys.executable, str(COMPONENT / "propagation_gate.py"), str(self.results)],
                             capture_output=True, text=True)
        findings = [json.loads(l) for l in out.stdout.splitlines() if l.startswith("{")]
        return out.returncode, findings

    def assertRefused(self, code):
        rc, findings = self.gate()
        self.assertEqual(rc, 1)
        refused = [f for f in findings if f.get("disposition") == "FAIL_CLOSED"]
        self.assertTrue(refused)
        for f in refused:
            for field in SIX:
                self.assertTrue(isinstance(f.get(field), str) and f[field].strip(), field)
        self.assertIn(code, [f["failure_code"] for f in refused])
        return refused

    OK = {"schema": "stegverse.organization-repository-propagation/v1", "disposition": "ALLOW", "propagated": []}

    def test_missing_or_empty_results_fail_closed(self):
        self.assertRefused("PROPAGATION_GATE_TREATS_ABSENCE_AS_PASS")
        self.results.mkdir()
        self.assertRefused("PROPAGATION_GATE_TREATS_ABSENCE_AS_PASS")

    def test_an_appended_request_without_a_record_fails_closed(self):
        self.request("req-1")
        self.assertRefused("PROPAGATION_GATE_TREATS_ABSENCE_AS_PASS")
        self.results = Path(self.tmp.name) / "results2"
        self.request("self-closure", marker="closure.json")
        self.assertRefused("PROPAGATION_GATE_TREATS_ABSENCE_AS_PASS")

    def test_only_allow_passes(self):
        for i, record in enumerate(({"schema": self.OK["schema"], "disposition": "DENY", "failure_code": "X_DENIED"},
                                    {"schema": self.OK["schema"], "disposition": "PENDING"},
                                    {"schema": self.OK["schema"], "propagated": []},
                                    {"error": "boom"},
                                    {"schema": "other/v1", "disposition": "ALLOW"},
                                    {"schema": self.OK["schema"], "disposition": "FAIL_CLOSED", "failure_code": "HB_EPOCH_INVALID"})):
            self.results = Path(self.tmp.name) / ("r%d" % i)
            self.request("req", propagation=record, exit_code=0)
            refused = self.assertRefused(record.get("failure_code") or "PROPAGATION_NOT_ALLOW")
            self.assertEqual(refused[0]["failed_predicate"],
                             "EVERY_APPENDED_REQUEST_HAS_A_PROPAGATION_RECORD_AND_ONLY_A_RECOGNIZED_SUCCESS_PASSES")

    def test_unreadable_record_or_nonzero_exit_fails(self):
        self.request("req", propagation="{truncated", exit_code=0)
        self.assertRefused("PROPAGATION_RECORD_UNREADABLE")
        self.results = Path(self.tmp.name) / "r-exit"
        self.request("req", propagation=self.OK, exit_code=1)
        self.assertRefused("PROPAGATION_NOT_ALLOW")

    def test_allow_and_already_recorded_pass(self):
        self.request("req-1", propagation=self.OK, exit_code=0)
        self.request("req-2", marker_doc={"disposition": "ALREADY_RECORDED"})
        self.request("self-closure", marker="closure.json", propagation=self.OK, exit_code=0)
        rc, findings = self.gate()
        self.assertEqual(rc, 0, findings)
        self.assertEqual(findings[-1]["disposition"], "ALLOW")

    def test_the_workflow_runs_this_gate_last_and_always(self):
        wf = (COMPONENT.parents[1] / ".github/workflows/organization-ledger-transition-reusable.yml").read_text()
        step = wf[wf.index("- name: Fail on a recorded propagation refusal (six fields)"):]
        self.assertIn("if: always()", step.split("run: |")[0])
        self.assertIn('python3 "$COMPONENT/propagation_gate.py" "$RUNNER_TEMP/results"', step)
        self.assertIn("PROPAGATION_GATE_TREATS_ABSENCE_AS_PASS", step)
        self.assertNotIn('result.get("disposition") == "FAIL_CLOSED"', wf)
        self.assertNotIn("\n      - name:", step[1:], "it is the last step")


if __name__ == "__main__":
    unittest.main()
