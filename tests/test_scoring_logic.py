
import unittest
import pandas as pd
from utils.scoring_utils import calculate_job_score, extract_keywords_optimized
import re
from filters_scoring_config.compiled_regex import split_keywords

class TestScoringLogic(unittest.TestCase):
    def test_extract_keywords_optimized(self):
        # Setup
        single_set = {"java", "python"}
        multi_regex = re.compile(r"react native")

        # Case 1: Single matches
        text = "we need java and python developers"
        tokens = set(re.findall(r'[a-z0-9]+', text))
        found = extract_keywords_optimized(tokens, text, single_set, multi_regex)
        self.assertEqual(sorted(list(found)), ["java", "python"])

        # Case 2: Multi match
        text = "we need react native developers"
        tokens = set(re.findall(r'[a-z0-9]+', text))
        found = extract_keywords_optimized(tokens, text, single_set, multi_regex)
        self.assertEqual(sorted(list(found)), ["react native"])

        # Case 3: Mixed
        text = "java and react native"
        tokens = set(re.findall(r'[a-z0-9]+', text))
        found = extract_keywords_optimized(tokens, text, single_set, multi_regex)
        self.assertEqual(sorted(list(found)), ["java", "react native"])

        # Case 4: Partial match (should fail for single)
        text = "javascript"
        tokens = set(re.findall(r'[a-z0-9]+', text))
        found = extract_keywords_optimized(tokens, text, single_set, multi_regex)
        self.assertEqual(list(found), [])

        # Case 5: Partial match (should fail for multi if regex is strict)
        from filters_scoring_config.compiled_regex import _SET_IT_SIGNALS_SINGLE, _REGEX_IT_SIGNALS_MULTI

        # "software" is in _SET_IT_SIGNALS_SINGLE
        text = "we build software"
        tokens = set(re.findall(r'[a-z0-9]+', text))
        found = extract_keywords_optimized(tokens, text, _SET_IT_SIGNALS_SINGLE, _REGEX_IT_SIGNALS_MULTI)
        self.assertIn("software", found)

        # "computer science" is in _REGEX_IT_SIGNALS_MULTI (as "computer science")
        text = "degree in computer science"
        tokens = set(re.findall(r'[a-z0-9]+', text))
        found = extract_keywords_optimized(tokens, text, _SET_IT_SIGNALS_SINGLE, _REGEX_IT_SIGNALS_MULTI)
        self.assertIn("computer science", found)

    def test_extract_keywords_optimized_edge_cases(self):
        # Case 1: Hyphenated keyword (should be in regex, not set)

        single, multi = split_keywords({"front-end", "backend"})
        self.assertIn("backend", single)
        self.assertNotIn("front-end", single)
        self.assertIn("front-end", multi)

        regex = re.compile(r"(?<!\w)" + re.escape("front-end") + r"(?!\w)")

        text = "we need a front-end developer"
        tokens = set(re.findall(r'[a-z0-9]+', text))
        found = extract_keywords_optimized(tokens, text, single, regex)
        self.assertIn("front-end", found)
        self.assertNotIn("backend", found)

        # Case 2: Mixed Case keyword
        single, multi = split_keywords({"Java", "Python"})
        self.assertIn("java", single)
        self.assertIn("python", single)

        text = "we need java developers"
        tokens = set(re.findall(r'[a-z0-9]+', text))
        found = extract_keywords_optimized(tokens, text, single, None)
        self.assertIn("java", found)

        # Case 3: Mixed Case in text
        text_normalized = "we need java"
        tokens = set(re.findall(r'[a-z0-9]+', text_normalized))
        found = extract_keywords_optimized(tokens, text_normalized, single, None)
        self.assertIn("java", found)

    def test_calculate_job_score_integration(self):
        # Basic integration test to ensure it runs without error and detects IT signals
        row = {
            "title_normalized": "senior software engineer",
            "full_text_normalized": "we need a senior software engineer with java and python experience. degree in computer science required."
        }
        score, details = calculate_job_score(row)

        self.assertGreater(score, 0)
        # Should have found "software" (IT signal) and "computer science" (IT signal)
        signals = [b for b in details["bonuses"] if b["key"] == "it_signals"]
        self.assertTrue(signals, "Should have IT signals bonus")
        found_signals = signals[0]["meta"]
        self.assertIn("software", found_signals)
        self.assertIn("computer science", found_signals)

        # Should have found "java", "python" (Techs)
        techs = [b for b in details["bonuses"] if b["key"] == "profile_tech"]
        self.assertTrue(techs, "Should have profile tech bonus")
        found_techs = techs[0]["meta"]
        self.assertIn("java", found_techs)
        self.assertIn("python", found_techs)

if __name__ == '__main__':
    unittest.main()
