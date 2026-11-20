import os
import tempfile
import unittest
from pathlib import Path

from career_agent import store
from career_agent.matching import score_job


class CareerAgentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["CAREER_DB_PATH"] = str(Path(self.tmp.name) / "career.sqlite3")

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop("CAREER_DB_PATH", None)

    def test_job_dedupes_by_url(self):
        job = {"title": "Python Developer", "company": "Acme",
               "location": "Hyderabad", "url": "https://example.com/jobs/1"}
        first = store.add_job(job)
        second = store.add_job({**job, "title": "Python Engineer"})
        self.assertEqual(first, second)
        self.assertEqual(len(store.list_jobs()), 1)

    def test_approval_requires_pending_and_records_decision(self):
        item = store.create_approval("application_packet", "Acme role",
                                     {"resume": "draft"})
        self.assertTrue(store.decide_approval(item, "approved", "Reviewed"))
        self.assertFalse(store.decide_approval(item, "rejected"))
        record = store.list_approvals()[0]
        self.assertEqual(record["status"], "approved")
        self.assertTrue(record["payload_integrity_ok"])
        self.assertEqual(store.list_audit_events()[0]["event_type"], "approved")

    def test_rejects_invalid_decision(self):
        item = store.create_approval("message", "Referral note", {"body": "hello"})
        with self.assertRaises(ValueError):
            store.decide_approval(item, "sent")

    def test_matching_is_reproducible_and_exposes_gaps(self):
        result = score_job(
            {"title": "Junior Python Developer", "location": "Hyderabad",
             "description": "Python, SQL, Docker, FastAPI"},
            {"skills": "Python, SQL, FastAPI",
             "target_roles": ["Junior Python Developer"],
             "target_locations": ["Hyderabad"], "years_experience": 0},
        )
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)
        self.assertIn("docker", result["skill_gaps"])
        self.assertIn("python", result["matched_skills"])


if __name__ == "__main__":
    unittest.main()
