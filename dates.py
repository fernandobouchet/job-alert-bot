import math
import zoneinfo
from datetime import datetime, timedelta
import dateparser
from config import TIMEZONE


def safe_parse_date_to_ISO(d):
    """
    Parsea una fecha desde diversos formatos a ISO 8601 con timezone.
    Utiliza la librería dateparser para manejar múltiples formatos de entrada.
    Devuelve la fecha actual si el parsing falla.
    """
    tz = zoneinfo.ZoneInfo(TIMEZONE)
    now = datetime.now(tz)

    if d is None or (isinstance(d, float) and math.isnan(d)):
        return now.isoformat()

    # Forzar el parsing de fechas relativas (ej. "yesterday") en el contexto de la zona horaria correcta
    settings = {"TIMEZONE": TIMEZONE, "RETURN_AS_TIMEZONE_AWARE": True}

    # Intentar parsear la fecha
    try:
        if isinstance(d, (int, float)):
            # Interpretar como timestamp si es numérico
            parsed_date = datetime.fromtimestamp(d, tz=tz)
        else:
            # Usar dateparser para strings y otros formatos
            parsed_date = dateparser.parse(str(d), settings=settings)

        if parsed_date:
            # Si el parsing fue exitoso, asegurar que tenga timezone
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=tz)
            return parsed_date.isoformat()
    except Exception:
        pass  # La excepción se ignora para devolver `now` como fallback

    # Fallback: si todo lo demás falla, devolver la fecha y hora actuales
    return now.isoformat()


def its_job_days_old(published_at_iso, days_limit=1):
    """Comprueba si un trabajo es más antiguo que el límite de días."""
    try:
        published_date = datetime.fromisoformat(published_at_iso.replace("Z", "+00:00"))
        cutoff_date = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)) - timedelta(
            days=days_limit
        )
        return published_date < cutoff_date
    except (ValueError, TypeError):
        return False
