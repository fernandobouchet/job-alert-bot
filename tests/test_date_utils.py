import unittest
from datetime import datetime
import zoneinfo
from utils.date_utils import safe_parse_date_to_ISO
from constants import TIMEZONE

class TestDateUtils(unittest.TestCase):
    def setUp(self):
        self.tz = zoneinfo.ZoneInfo(TIMEZONE)

    def test_safe_parse_date_to_ISO_fast_path(self):
        # YYYY-MM-DD format (fast path)
        input_date = "2024-05-23"
        expected = datetime(2024, 5, 23, 0, 0, 0, tzinfo=self.tz).isoformat()
        result = safe_parse_date_to_ISO(input_date)
        self.assertEqual(result, expected)

    def test_safe_parse_date_to_ISO_fallback(self):
        # Relative date (fallback to dateparser)
        # Note: This depends on "now", so we just check it returns a valid string
        input_date = "Yesterday"
        result = safe_parse_date_to_ISO(input_date)
        self.assertIsInstance(result, str)
        # Check ISO format roughly
        self.assertIn("T00:00:00", result)

    def test_safe_parse_date_to_ISO_invalid_fast_path(self):
        # Invalid date matching regex (should fallback and return today or parsed if dateparser handles it differently)
        # 2024-99-99 is invalid. dateparser might return None or Today.
        input_date = "2024-99-99"
        result = safe_parse_date_to_ISO(input_date)
        # Should be today (fallback)
        now = datetime.now(self.tz).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        # Allow slight difference if test runs exactly at midnight boundary (unlikely)
        self.assertEqual(result, now)

    def test_safe_parse_date_to_ISO_timestamp(self):
        # Timestamp
        ts = 1716422400.0 # 2024-05-23 00:00:00 UTC? No, this is random example.
        # 1716422400 is roughly May 2024.
        result = safe_parse_date_to_ISO(ts)
        self.assertIsInstance(result, str)
        self.assertIn("T00:00:00", result)

    def test_safe_parse_date_to_ISO_none(self):
        # None
        result = safe_parse_date_to_ISO(None)
        now = datetime.now(self.tz).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        self.assertEqual(result, now)

if __name__ == "__main__":
    unittest.main()
