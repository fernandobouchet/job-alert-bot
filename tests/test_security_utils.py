import unittest
from utils.security_utils import is_safe_url

class TestSecurityUtils(unittest.TestCase):
    def test_safe_urls(self):
        self.assertTrue(is_safe_url("https://www.google.com"))
        self.assertTrue(is_safe_url("http://example.com/foo/bar"))
        self.assertTrue(is_safe_url("https://github.com"))

    def test_unsafe_schemes(self):
        self.assertFalse(is_safe_url("ftp://example.com"))
        self.assertFalse(is_safe_url("file:///etc/passwd"))
        self.assertFalse(is_safe_url("javascript:alert(1)"))
        self.assertFalse(is_safe_url("data:text/plain,base64..."))

    def test_private_ips(self):
        # Localhost
        self.assertFalse(is_safe_url("http://127.0.0.1"))
        self.assertFalse(is_safe_url("http://localhost"))

        # Private ranges
        self.assertFalse(is_safe_url("http://192.168.1.1"))
        self.assertFalse(is_safe_url("http://10.0.0.1"))
        self.assertFalse(is_safe_url("http://172.16.0.1"))

        # Link-local
        self.assertFalse(is_safe_url("http://169.254.169.254")) # AWS metadata service

    def test_invalid_urls(self):
        self.assertFalse(is_safe_url(""))
        self.assertFalse(is_safe_url(None))
        self.assertFalse(is_safe_url("not a url"))

if __name__ == '__main__':
    unittest.main()
