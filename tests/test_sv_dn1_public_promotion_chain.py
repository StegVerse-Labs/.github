from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts import run_sv_dn1_first_round_chain as chain


class SvDn1PublicPromotionChainTests(unittest.TestCase):
    def test_public_promotion_is_exact_successor_of_sdk_analysis(self) -> None:
        self.assertEqual(chain.TASKS[-2:], (
            "SV-DN1-SDK-FIRST-ROUND-001",
            "SV-DN1-PUBLIC-PROMOTION-001",
        ))

    def test_public_promotion_receipt_requires_zero_authority_exact_projection(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            path = base / ".stegverse/state/sv-dn1-public-promotion/receipts/latest.json"
            path.parent.mkdir(parents=True)
            path.write_text(
                '{"schema":"stegverse.sv-dn1.public-promotion-worker-receipt/v1","state":"COMPLETE","transition_id":"SV_DN1_PUBLIC_PROMOTION_READY","observation_class":"LIVE","publication_state":"PUBLIC_OBSERVED","exact_bytes_preserved":true,"semantic_rewrite_performed":false,"network_fetch_performed":false,"credential_used":false,"repository_writeback_performed":false,"deployment_performed":false,"release_performed":false,"certification_claimed":false,"authority_effect":"NONE_STATIC_PROJECTION_ONLY","source_artifact_sha256":{"first-round-analysis.json":"a","production-pipeline-observation.json":"b","result-receipt.json":"c","report.md":"d","index.html":"e"},"destination_artifact_sha256":{"first-round-analysis.json":"a","production-pipeline-observation.json":"b","result-receipt.json":"c","report.md":"d","index.html":"e"}}\n'
            )
            with mock.patch.object(chain.Path, "home", return_value=base):
                observed = chain.validate_durable_receipt("SV-DN1-PUBLIC-PROMOTION-001", {"HOME": str(base)})
            self.assertEqual(observed["receipt_path"], str(path))

    def test_public_promotion_rejects_non_public_observation_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            path = base / ".stegverse/state/sv-dn1-public-promotion/receipts/latest.json"
            path.parent.mkdir(parents=True)
            path.write_text(
                '{"schema":"stegverse.sv-dn1.public-promotion-worker-receipt/v1","state":"COMPLETE","transition_id":"SV_DN1_PUBLIC_PROMOTION_READY","observation_class":"LIVE","publication_state":"WITHHELD","exact_bytes_preserved":true,"semantic_rewrite_performed":false,"network_fetch_performed":false,"credential_used":false,"repository_writeback_performed":false,"deployment_performed":false,"release_performed":false,"certification_claimed":false,"authority_effect":"NONE_STATIC_PROJECTION_ONLY","source_artifact_sha256":{},"destination_artifact_sha256":{}}\n'
            )
            with mock.patch.object(chain.Path, "home", return_value=base):
                with self.assertRaisesRegex(RuntimeError, "publication_state"):
                    chain.validate_durable_receipt("SV-DN1-PUBLIC-PROMOTION-001", {"HOME": str(base)})


if __name__ == "__main__":
    unittest.main()
