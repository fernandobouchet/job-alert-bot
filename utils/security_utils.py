import socket
import ipaddress
from urllib.parse import urlparse


def is_safe_url(url):
    """
    Verifica si una URL es segura para realizar una petición HTTP.

    Protege contra Server-Side Request Forgery (SSRF) validando que:
    1. El esquema sea http o https.
    2. El hostname no resuelva a direcciones IP privadas, loopback o link-local.

    Nota: Esta validación es susceptible a ataques de redirección (si requests.get sigue redirects)
    y DNS rebinding. Se recomienda usar con allow_redirects=False si es crítico.

    Args:
        url (str): La URL a verificar.

    Returns:
        bool: True si la URL es segura, False en caso contrario o si hay error.
    """
    try:
        parsed = urlparse(url)
        # 1. Validar esquema
        if parsed.scheme not in ('http', 'https'):
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        # 2. Resolver hostname a IP
        try:
            ip_str = socket.gethostbyname(hostname)
        except socket.error:
            # Si no se puede resolver, asumimos inseguro por precaución (Fail Secure)
            return False

        # 3. Validar tipo de IP
        ip = ipaddress.ip_address(ip_str)

        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False

        # Adicionalmente rechazar multicast y reservadas
        if ip.is_multicast or ip.is_reserved:
            return False

        return True

    except Exception:
        # Cualquier error inesperado (parsing, etc.) se trata como inseguro
        return False
