import unittest
from utils.scoring_utils import calculate_job_score

class TestScoringFull(unittest.TestCase):
    """Tests for job scoring logic covering full flow."""
    def test_calculate_job_score_ambiguous_penalty(self):
        """Case: Ambiguous role (e.g., 'analyst') without IT profile or strong signals."""
        row = {
            "title_normalized": "analyst",
            "full_text_normalized": "looking for an analyst to join our team."
        }
        score, details = calculate_job_score(row)

        penalties = [p["key"] for p in details["penalties"]]
        # Expect fatal rejection due to no IT signals
        self.assertIn("fatal_no_it", penalties)
        self.assertEqual(score, 0)

    def test_calculate_job_score_ambiguous_valid(self):
        """Case: Ambiguous role BUT with IT profile (found via role or tech)."""
        row = {
            "title_normalized": "analyst",
            "full_text_normalized": (
                "looking for an analyst with python and django software development experience."
            )
        }
        score, details = calculate_job_score(row)

        penalties = [p["key"] for p in details["penalties"]]
        self.assertNotIn("ambiguous_no_context", penalties)
        self.assertNotIn("fatal_no_it", penalties)
        self.assertGreater(score, 0)

    def test_calculate_job_score_positive_seniority(self):
        """Case: Junior role -> Bonus."""
        row = {
            "title_normalized": "junior python developer",
            "full_text_normalized": "we are looking for a junior python developer."
        }
        _, details = calculate_job_score(row)

        bonuses = [b["key"] for b in details["bonuses"]]
        self.assertIn("positive_seniority", bonuses)
        # Check metadata
        bonus = next(b for b in details["bonuses"] if b["key"] == "positive_seniority")
        self.assertTrue(len(bonus["meta"]) > 0)

    def test_calculate_job_score_negative_seniority(self):
        """Case: Senior role -> Penalty."""
        row = {
            "title_normalized": "senior python developer",
            "full_text_normalized": "we are looking for a senior python developer."
        }
        _, details = calculate_job_score(row)

        penalties = [p["key"] for p in details["penalties"]]
        self.assertIn("senior_experience", penalties)
        # Check metadata
        penalty = next(p for p in details["penalties"] if p["key"] == "senior_experience")
        self.assertTrue(len(penalty["meta"]) > 0)

if __name__ == '__main__':
    unittest.main()
