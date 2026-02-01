import unittest
import sys
from unittest.mock import MagicMock

# Mock utils.firestore_utils BEFORE importing utils.scraping_utils
# This is necessary because importing scraping_utils imports firestore_utils,
# which has side-effects (initializing Firestore client) that fail without credentials.
sys.modules["utils.firestore_utils"] = MagicMock()

import pandas as pd
import numpy as np
# Now it is safe to import
from utils.scraping_utils import normalize_text_series, extract_job_modality_vectorized

class TestScrapingUtils(unittest.TestCase):
    def test_normalize_text_series_basics(self):
        """Test basic normalization functionality."""
        data = [
            "Hello World",
            "  Padding  ",
            "UPPERCASE",
            "Mixed Case",
        ]
        series = pd.Series(data)
        result = normalize_text_series(series)
        expected = pd.Series([
            "hello world",
            "padding",
            "uppercase",
            "mixed case",
        ])
        pd.testing.assert_series_equal(result, expected)

    def test_normalize_text_series_special_chars(self):
        """Test handling of special characters and preserved symbols."""
        data = [
            "C++ Developer",
            "C# .NET",
            "Node.js",
            "Python / Django",
            "Java, Python; Ruby!",
            "Garbage @#$%^&* Characters",
        ]
        series = pd.Series(data)
        result = normalize_text_series(series)
        # Preserved: +, #, ., /
        # Replaced: ,, ;, !, @, $, %, ^, &, *
        expected = pd.Series([
            "c++ developer",
            "c# .net",
            "node.js",
            "python / django",
            "java python ruby",
            "garbage # characters",
        ])
        pd.testing.assert_series_equal(result, expected)

    def test_normalize_text_series_whitespace(self):
        """Test whitespace collapsing."""
        data = [
            "Multiple   Spaces",
            "Tabs\t\tHere",
            "Newlines\n\nIncluded",
            " Mixed \t Whitespace \n Types ",
        ]
        series = pd.Series(data)
        result = normalize_text_series(series)
        expected = pd.Series([
            "multiple spaces",
            "tabs here",
            "newlines included",
            "mixed whitespace types",
        ])
        pd.testing.assert_series_equal(result, expected)

    def test_normalize_text_series_edge_cases(self):
        """Test empty series, NaNs, and non-string inputs."""
        # Empty series
        empty_series = pd.Series([], dtype=object)
        result_empty = normalize_text_series(empty_series)
        pd.testing.assert_series_equal(result_empty, empty_series)

        # NaNs and None
        data_nan = [np.nan, None, "Valid"]
        series_nan = pd.Series(data_nan)
        result_nan = normalize_text_series(series_nan)
        # NaNs are filled with "", then processed -> "" (empty string)
        # "Valid" -> "valid"
        expected_nan = pd.Series(["", "", "valid"])
        pd.testing.assert_series_equal(result_nan, expected_nan)

        # Numbers as input
        data_num = [123, 45.67]
        series_num = pd.Series(data_num)
        result_num = normalize_text_series(series_num)
        # Note: pandas Series with mixed ints/floats upgrades ints to floats.
        # So 123 becomes 123.0, and astype(str) makes it "123.0".
        expected_num = pd.Series(["123.0", "45.67"])
        pd.testing.assert_series_equal(result_num, expected_num)

    def test_extract_job_modality_vectorized(self):
        """Test optimized job modality extraction."""
        data = [
            "exclusivamente presencial en oficina",  # Strict Onsite -> Presencial
            "trabajo híbrido 3 dias",                 # Hybrid Keyword -> Híbrido
            "trabajo remoto desde casa",              # Remote -> Remoto
            "trabajo presencial en sede",             # Onsite -> Presencial
            "posibilidad de remoto y presencial",     # Mixed (Remote + Onsite) -> Híbrido
            "trabajo normal sin especificar",         # None -> No especificada
            123,                                      # Non-string -> No especificada
            None,                                     # None -> No especificada
            np.nan                                    # NaN -> No especificada
        ]
        series = pd.Series(data)
        result = extract_job_modality_vectorized(series)
        expected = pd.Series([
            "Presencial",
            "Híbrido",
            "Remoto",
            "Presencial",
            "Híbrido",
            "No especificada",
            "No especificada",
            "No especificada",
            "No especificada"
        ])
        # Note: Depending on the implementation, result could be numpy array or Series.
        # If it returns numpy array, we need to convert to Series for comparison.
        if isinstance(result, np.ndarray):
            result = pd.Series(result)

        pd.testing.assert_series_equal(result, expected)

if __name__ == '__main__':
    unittest.main()
