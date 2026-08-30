import hashlib
import unittest

from workers import hil_intr_profiled_ingress as profiled
from workers import sv_dn1_browser_evidence_intr_ingress as svdn1


class SvDn1BrowserEvidenceProfiledIngressTests(unittest.TestCase):
    def test_profile_advertises_existing_web_bootstrap_origin(self):
        profile = profiled.build_profile(tls_enabled=True)
        self.assertIn(svdn1.PROFILE, profile["additional_materialization_profiles"])
        self.assertIn(svdn1.ORIGIN, profile["supported_origins"])
        self.assertEqual(profile["execution_authority"], "NONE")
        self.assertEqual(profile["credential_authority"], "TV/TVC")

    def test_web_bootstrap_headers_are_credentialless_and_hash_bound(self):
        body = b'{"schema":"stegverse.sv-dn1.browser-observation-transport/v1"}'
        digest = hashlib.sha256(body).hexdigest()
        headers = {
            "X-StegVerse-Transport": "InTr",
            "X-StegVerse-Transport-Origin": svdn1.ORIGIN,
            "X-StegVerse-Payload-SHA256": digest,
            "Content-Type": "application/json",
        }
        self.assertEqual(profiled._svdn1_transport_headers(headers, body), digest)

    def test_web_bootstrap_origin_cannot_claim_tvc_authorization(self):
        body = b'{}'
        headers = {
            "X-StegVerse-Transport": "InTr",
            "X-StegVerse-Transport-Origin": svdn1.ORIGIN,
            "X-StegVerse-Payload-SHA256": hashlib.sha256(body).hexdigest(),
            "X-StegVerse-Authorization-Id": "FORBIDDEN",
            "Content-Type": "application/json",
        }
        with self.assertRaisesRegex(ValueError, "cannot_claim_tvc_authorization"):
            profiled._svdn1_transport_headers(headers, body)


if __name__ == "__main__":
    unittest.main()
