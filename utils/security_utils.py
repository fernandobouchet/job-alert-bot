import ipaddress
import socket
from urllib.parse import urlparse

def validate_url(url: str, allowed_domains: list[str] = None) -> bool:
    """
    Validates a URL to prevent SSRF attacks.
    Checks for:
    - Valid scheme (http/https)
    - Hostname resolution
    - Private/Local/Loopback/Link-local/Multicast IP addresses
    - Allowed domains whitelist

    Args:
        url (str): The URL to validate.
        allowed_domains (list[str], optional): List of allowed domains.
            If provided, the URL's hostname must match one of these domains
            or be a subdomain of one.

    Returns:
        bool: True if the URL is considered safe and valid, False otherwise.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False

        if not parsed.hostname:
            return False

        # Domain whitelist check
        if allowed_domains:
            # Check if hostname matches any allowed domain or is a subdomain of it
            is_allowed = False
            for domain in allowed_domains:
                if parsed.hostname == domain or parsed.hostname.endswith('.' + domain):
                    is_allowed = True
                    break

            if not is_allowed:
                return False

        # Resolve hostname to IP to check for private IPs
        # Note: Time-of-check to Time-of-use (TOCTOU) race condition is still possible here
        # if DNS rebinding happens, but this is a good first layer of defense.
        try:
            ip_str = socket.gethostbyname(parsed.hostname)
        except socket.gaierror:
            return False

        ip = ipaddress.ip_address(ip_str)

        if (ip.is_private or
            ip.is_loopback or
            ip.is_link_local or
            ip.is_multicast or
            ip.is_reserved):
            return False

        return True

    except Exception:
        return False
