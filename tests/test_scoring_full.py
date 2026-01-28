import unittest
import pandas as pd
from utils.scoring_utils import calculate_job_score

class TestScoringFull(unittest.TestCase):
    def test_calculate_job_score_profile_match(self):
        # Case 1: Clear profile match (Junior Software Engineer -> Developer)
        # Should be efficient path
        row = {
            "title_normalized": "junior software engineer",
            "full_text_normalized": "we are looking for a junior software engineer with experience in python and django. remote work."
        }
        score, details = calculate_job_score(row)

        self.assertGreater(score, 60)
        self.assertIn("software", details["profiles"])
        # 'python' might be lowercase due to map overwrites, accept both
        tags_lower = [t.lower() for t in details["tags"]]
        self.assertIn("python", tags_lower)
        self.assertEqual(details["quality_tier"], "excellent")

        # Verify bonuses
        bonus_keys = [b["key"] for b in details["bonuses"]]
        self.assertIn("strong_role", bonus_keys)
        self.assertIn("profile_tech", bonus_keys) # Should trigger profile_tech bonus

    def test_calculate_job_score_no_profile_match(self):
        # Case 2: No profile match but IT signals (Generic IT job)
        # Should be slow path (calculates weak/strong techs)
        row = {
            "title_normalized": "it specialist",
            "full_text_normalized": "we need an it specialist who knows python and sql. knowledge of excel is a plus."
        }

        score, details = calculate_job_score(row)

        # Should be IT job because strong tech matches (Python, SQL) >= 2 and IT signal found ("it")

        self.assertGreater(score, 0)
        self.assertEqual(details["profiles"], []) # No profile

        tags_lower = [t.lower() for t in details["tags"]]
        self.assertIn("python", tags_lower)
        self.assertIn("sql", tags_lower)

        # Verify bonuses
        bonus_keys = [b["key"] for b in details["bonuses"]]
        self.assertIn("global_tech", bonus_keys) # Should trigger global_tech bonus, not profile_tech

    def test_calculate_job_score_rejection(self):
        # Case 3: Non-IT job
        row = {
            "title_normalized": "hr manager",
            "full_text_normalized": "looking for an hr manager with experience in recruiting. must know excel."
        }
        score, details = calculate_job_score(row)

        self.assertEqual(score, 0)
        self.assertEqual(details["quality_tier"], "reject")

        penalty_keys = [p["key"] for p in details["penalties"]]

        if "weak_signal_only" in penalty_keys:
             pass
        else:
             self.assertIn("fatal_no_it", penalty_keys)

    def test_calculate_job_score_ambiguous_penalty(self):
        # Case 4: Ambiguous role (Project Manager) without IT context
        row = {
            "title_normalized": "project manager",
            "full_text_normalized": "looking for a project manager to lead the team."
        }
        score, details = calculate_job_score(row)

        self.assertEqual(score, 0)
        self.assertIn("fatal_no_it", [p["key"] for p in details["penalties"]])

if __name__ == '__main__':
    unittest.main()
