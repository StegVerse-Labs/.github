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


if __name__ == "__main__":
    unittest.main()
