import sys
from unittest.mock import MagicMock

# Mock utils.firestore_utils BEFORE importing utils.scraping_utils
mock_firestore_utils = MagicMock()
sys.modules["utils.firestore_utils"] = mock_firestore_utils

import unittest
import pandas as pd
from utils.scraping_utils import normalize_text_series

class TestNormalization(unittest.TestCase):
    def test_normalize_text_series(self):
        input_data = [
            "Senior Java/Spring Boot Developer (Remote)",
            "C++ Engineer - High Performance",
            "Fullstack .NET/React Developer!!!",
            "Data Scientist (Python, SQL, Pandas)",
            "  Badly   Formatted   String...  ",
            "Node.js/Express.js Backend",
            "QA Automation (Selenium, Cypress)",
            "DevOps/SRE (AWS, Kubernetes, Terraform)",
            "Product Owner/Project Manager",
            "Tech Lead - Hands on",
            "Simple string",
            "",
            None,
            "Special: @#%^&*()",
            "Kept: + # . /"
        ]

        expected_data = [
            "senior java/spring boot developer remote",  # () removed, / kept
            "c++ engineer high performance",           # - removed, + kept
            "fullstack .net/react developer",          # !!! removed, . / kept
            "data scientist python sql pandas",        # , removed
            "badly formatted string...",               # spaces collapsed, ... kept
            "node.js/express.js backend",              # . kept
            "qa automation selenium cypress",          # () removed
            "devops/sre aws kubernetes terraform",     # / kept
            "product owner/project manager",
            "tech lead hands on",
            "simple string",
            "",
            "",
            "special #",                               # only # kept from special chars
            "kept + # . /"
        ]

        series = pd.Series(input_data)
        normalized = normalize_text_series(series)

        # Compare as lists
        result_list = normalized.tolist()

        for i, (res, exp) in enumerate(zip(result_list, expected_data)):
            if input_data[i] is None:
                 self.assertEqual(res, "", f"Mismatch at index {i} (None input)")
            else:
                 self.assertEqual(res, exp, f"Mismatch at index {i}: '{input_data[i]}'")

if __name__ == '__main__':
    unittest.main()
