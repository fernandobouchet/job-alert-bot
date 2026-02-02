import unittest
import pandas as pd
from utils.scoring_utils import pre_filter_jobs

class TestPreFilterJobs(unittest.TestCase):
    def test_pre_filter_logic(self):
        # Define test cases
        # Structure: title, expected_kept (True/False), expected_reason_start (optional)
        test_cases = [
            # --- Area Filter Tests ---

            # Case 1: Trigger + No Exception -> Reject
            # "HR Manager" -> "hr" (Trigger), "manager" (No role/signal exception)
            ("HR Manager", False, "area"),

            # Case 2: Trigger + Role Exception -> Keep
            # "HR Developer" -> "hr" (Trigger), "developer" (Role Exception)
            ("HR Developer", True, None),

            # Case 3: Trigger + Signal Exception -> Keep
            # "Finance Software Specialist" -> "finance" (Trigger), "software" (Signal Exception)
            ("Finance Software Specialist", True, None),

            # Case 4: Multiple Triggers + Exception -> Keep
            # "Financial Data Science" -> "financial" (Trigger), "data science" (Signal Exception)
            ("Financial Data Science", True, None),

            # Case 5: Trigger only -> Reject
            # "Office Manager" -> "office manager" (Trigger)
            ("Office Manager", False, "area"),

            # --- Seniority Filter Tests ---
            # (Only checked if Area Filter passes)

            # Case 6: Seniority Trigger + No Exception -> Reject
            # "Senior Java Developer" -> "senior" (Trigger)
            ("Senior Java Developer", False, "seniority"),

            # Case 7: Seniority Trigger + Exception -> Keep
            # "Senior Junior Developer" -> "senior" (Trigger), "junior" (Exception)
            ("Senior Junior Developer", True, None),

            # Case 8: No Seniority Trigger -> Keep
            # "Java Developer"
            ("Java Developer", True, None),

            # Case 9: Explicit Junior -> Keep
            # "Junior Python Developer"
            ("Junior Python Developer", True, None),

            # --- Edge Cases ---

            # Case 10: Mixed Case
            ("hr developer", True, None),

            # Case 11: Empty title
            ("", True, None),
        ]

        # Create DataFrame
        df = pd.DataFrame({
            "title_normalized": [t[0].lower() for t in test_cases],
            "full_text_normalized": ["dummy text"] * len(test_cases) # Not used in pre-filter
        })

        # Run pre-filter
        df_filtered, df_rejected = pre_filter_jobs(df, verbose=False)

        # Verify results
        kept_titles = set(df_filtered["title_normalized"])
        rejected_titles = set(df_rejected["title_normalized"]) if not df_rejected.empty else set()

        for title_raw, expected_keep, reason_start in test_cases:
            title = title_raw.lower()
            if expected_keep:
                self.assertIn(title, kept_titles, f"Expected '{title}' to be KEPT, but it was REJECTED.")
                self.assertNotIn(title, rejected_titles)
            else:
                self.assertIn(title, rejected_titles, f"Expected '{title}' to be REJECTED, but it was KEPT.")
                self.assertNotIn(title, kept_titles)

                # Check reason
                if reason_start and not df_rejected.empty:
                    actual_reason = df_rejected.loc[df_rejected["title_normalized"] == title, "rejection_reason"].iloc[0]
                    self.assertTrue(actual_reason.startswith(reason_start),
                                    f"Expected rejection reason for '{title}' to start with '{reason_start}', got '{actual_reason}'")

if __name__ == '__main__':
    unittest.main()
