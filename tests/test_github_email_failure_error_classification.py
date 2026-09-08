from __future__ import annotations

import unittest

from scripts.normalize_github_failure_email_events import notification_class, signature


class GitHubEmailFailureErrorClassificationTests(unittest.TestCase):
    def test_failure_notification_is_classified_separately(self):
        row = {
            "repository": "StegVerse-Labs/.github",
            "workflow": "Heartbeat Worker Project",
            "subject": "PR run failed: Heartbeat Worker Project",
            "snippet": "All jobs have failed",
        }
        self.assertEqual(notification_class(row), "FAILURE")
        self.assertTrue(signature(row)[2].startswith("failure:"))

    def test_error_notification_has_precedence(self):
        row = {
            "repository": "StegVerse-Labs/.github",
            "workflow": "Heartbeat Worker Project",
            "subject": "Workflow error: Heartbeat Worker Project",
            "snippet": "Error while evaluating job",
        }
        self.assertEqual(notification_class(row), "ERROR")
        self.assertTrue(signature(row)[2].startswith("error:"))

    def test_explicit_class_is_preserved(self):
        row = {
            "notification_class": "ERROR",
            "repository": "StegVerse-Labs/Site",
            "subject": "Run failed",
        }
        self.assertEqual(notification_class(row), "ERROR")
        self.assertTrue(signature(row)[2].startswith("error:"))


if __name__ == "__main__":
    unittest.main()
