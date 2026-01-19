import unittest
from utils.scoring_utils import calculate_job_score
from filters_scoring_config.compiled_profiles import COMPILED_PROFILES

class TestOptimizedMatching(unittest.TestCase):
    def test_single_word_with_punctuation(self):
        # "java," should match "java" via set intersection (alphanumeric tokenization)
        row = {
            "title_normalized": "developer",
            "full_text_normalized": "we need a developer with java, skills",
            "company": "Test",
            "source": "Test"
        }
        score, details = calculate_job_score(row)

        found_techs = []
        for bonus in details["bonuses"]:
            if bonus["key"] in ["global_tech", "profile_tech"]:
                found_techs.extend(bonus["meta"])

        self.assertIn("java", found_techs, "Java should be found even if followed by comma")

    def test_special_char_term(self):
        # "c#" should be matched via regex path
        # We ensure 'developer' is in text so a profile is found, avoiding early exit
        row = {
            "title_normalized": "developer",
            "full_text_normalized": "we need a developer with c# knowledge",
            "company": "Test",
            "source": "Test"
        }
        score, details = calculate_job_score(row)

        found_techs = []
        for bonus in details["bonuses"]:
            if bonus["key"] in ["global_tech", "profile_tech"]:
                found_techs.extend(bonus["meta"])

        self.assertIn("c#", found_techs, "C# should be found via regex path")

    def test_node_js_term(self):
        # "node.js" should be matched via regex path
        row = {
            "title_normalized": "developer",
            "full_text_normalized": "developer experience with node.js is required",
            "company": "Test",
            "source": "Test"
        }
        score, details = calculate_job_score(row)

        found_techs = []
        for bonus in details["bonuses"]:
            if bonus["key"] in ["global_tech", "profile_tech"]:
                found_techs.extend(bonus["meta"])

        self.assertIn("node.js", found_techs, "Node.js should be found via regex path")

if __name__ == "__main__":
    unittest.main()
