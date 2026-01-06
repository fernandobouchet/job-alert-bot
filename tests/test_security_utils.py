import unittest
from unittest.mock import patch
from utils.security_utils import is_safe_url

class TestSecurityUtils(unittest.TestCase):

    @patch('socket.gethostbyname')
    def test_safe_public_url(self, mock_gethostbyname):
        # 8.8.8.8 is Google Public DNS (Public IP)
        mock_gethostbyname.return_value = '8.8.8.8'
        self.assertTrue(is_safe_url('https://google.com'))

    @patch('socket.gethostbyname')
    def test_unsafe_private_ip(self, mock_gethostbyname):
        # 192.168.1.1 is Private
        mock_gethostbyname.return_value = '192.168.1.1'
        self.assertFalse(is_safe_url('http://internal-router.local'))

    @patch('socket.gethostbyname')
    def test_unsafe_localhost(self, mock_gethostbyname):
        # 127.0.0.1 is Loopback
        mock_gethostbyname.return_value = '127.0.0.1'
        self.assertFalse(is_safe_url('http://localhost:8080'))

    def test_unsafe_scheme(self):
        # FTP is not allowed
        self.assertFalse(is_safe_url('ftp://google.com'))
        # File is not allowed
        self.assertFalse(is_safe_url('file:///etc/passwd'))

    @patch('socket.gethostbyname')
    def test_unsafe_aws_metadata(self, mock_gethostbyname):
        # 169.254.169.254 is Link Local (often used for cloud metadata)
        mock_gethostbyname.return_value = '169.254.169.254'
        self.assertFalse(is_safe_url('http://169.254.169.254/latest/meta-data/'))

    @patch('socket.gethostbyname')
    def test_dns_resolution_failure(self, mock_gethostbyname):
        mock_gethostbyname.side_effect = Exception("DNS Error")
        self.assertFalse(is_safe_url('http://invalid-domain.com'))

if __name__ == '__main__':
    unittest.main()
