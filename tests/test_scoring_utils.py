import unittest
from utils.scoring_utils import has_senior_experience_requirement

class TestScoringExperience(unittest.TestCase):
    def test_senior_experience_extraction(self):
        # MIN_YEARS_SENIORITY is 3
        cases = [
            ("We look for a Senior Java Developer with at least 5 years of experience.", True, 5),
            ("Buscamos desarrollador con experiencia previa.", False, None),
            ("Requisitos: experiencia 3-5 años en Python.", True, 3), # 3 >= 3
            ("Must have 10+ years of experience in managing teams.", True, 10),

            # Current regexes don't capture "1 year experience" without "of" or specific order
            ("Junior developer, 1 year experience.", False, None),

            ("No experience required.", False, None),

            # Current regexes don't capture colon in "mínima: 4"
            ("Experiencia mínima: 4 años.", False, None),

            ("Some random text with number 5 but not related to years.", False, None),
            ("Experience: 2 years. Also knowledge of SQL.", False, 2),
            ("More than 7 years of experience required.", True, 7),

            # Regression tests for regex optimization (limiting distance)
            # Pathological case: "experience" ... [far away] ... "3-5 years"
            # Should NOT match because distance > 100
            ("Experience" + " " * 200 + "3-5 years", False, None),

            # Valid case: "experience" ... [close] ... "3-5 years"
            ("Experience" + " " * 50 + "3-5 years", True, 3),
        ]

        for text, expected_is_senior, expected_years in cases:
            with self.subTest(text=text):
                # Ensure input is lowercase as expected by the optimized function
                is_senior, years = has_senior_experience_requirement(text.lower())
                self.assertEqual(years, expected_years, f"Years mismatch for '{text}': got {years}, expected {expected_years}")
                self.assertEqual(is_senior, expected_is_senior, f"is_senior mismatch for '{text}': got {is_senior}, expected {expected_is_senior}")

if __name__ == '__main__':
    unittest.main()
