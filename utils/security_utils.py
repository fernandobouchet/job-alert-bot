import ipaddress
import socket
from urllib.parse import urlparse

def is_safe_url(url: str) -> bool:
    """
    Validates a URL to prevent SSRF attacks.
    Checks that the URL scheme is http or https and that the hostname
    does not resolve to a private, loopback, or link-local IP address.

    Args:
        url (str): The URL to validate.

    Returns:
        bool: True if the URL is considered safe, False otherwise.
    """
    if not url:
        return False

    try:
        parsed = urlparse(url)
    except Exception:
        return False

    if parsed.scheme not in ('http', 'https'):
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    try:
        # Resolve hostname to IP
        # Note: This has a TOCTOU (Time-of-Check Time-of-Use) race condition vulnerability
        # if the DNS record is changed between check and use.
        # However, it provides a first layer of defense.
        ip_addresses = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        # If we can't resolve it, we can't verify it's safe.
        # Fail safe by rejecting.
        return False

    for info in ip_addresses:
        # socket.getaddrinfo returns a list of tuples.
        # The IP address is in the 4th element (sockaddr), which is a tuple (ip, port, ...)
        ip_str = info[4][0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
                return False
        except ValueError:
            # If we can't parse the IP, assume unsafe
            return False

    return True
