import unittest
import sys
import pandas as pd
import numpy as np
from unittest.mock import MagicMock

# Mock utils.firestore_utils
sys.modules["utils.firestore_utils"] = MagicMock()

from utils.scraping_utils import extract_job_modality_vectorized

class TestModalityExtraction(unittest.TestCase):
    def test_extract_job_modality(self):
        data = [
            "100% onsite required",            # Strict Onsite -> Presencial
            "hybrid working model",            # Hybrid Keyword -> Híbrido
            "remote work available",           # Remote -> Remoto
            "work from our oficina",           # Onsite -> Presencial
            "remote and onsite required",      # Remote + Onsite -> Híbrido
            "no info here",                    # None -> No especificada
        ]
        series = pd.Series(data)
        result = extract_job_modality_vectorized(series)

        expected = np.array([
            "Presencial",
            "Híbrido",
            "Remoto",
            "Presencial",
            "Híbrido",
            "No especificada"
        ])

        np.testing.assert_array_equal(result, expected)

if __name__ == '__main__':
    unittest.main()
