import math
import zoneinfo
from datetime import datetime, timedelta
import dateparser
from config import TIMEZONE


def safe_parse_date_to_ISO(date):
    """
    Parsea una fecha desde diversos formatos (en inglés o español) a ISO 8601 con timezone.
    Si no tiene hora, asigna la hora actual.
    Devuelve la fecha actual si el parsing falla.
    """
    tz = zoneinfo.ZoneInfo(TIMEZONE)
    now = datetime.now(tz)

    if date is None or (isinstance(date, float) and math.isnan(date)):
        return now.isoformat()

    settings = {
        "TIMEZONE": TIMEZONE,
        "RETURN_AS_TIMEZONE_AWARE": True,
        "DATE_ORDER": "DMY",  # Evita inversión día/mes
        "PREFER_DAY_OF_MONTH": "first",
    }

    try:
        if isinstance(date, (int, float)):
            parsed_date = datetime.fromtimestamp(date, tz=tz)
        else:
            parsed_date = dateparser.parse(
                str(date),
                settings=settings,
                languages=["es", "en"],  # Soporta español e inglés
            )

        if parsed_date:
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=tz)

            # Si solo tiene fecha sin hora, asignar hora actual
            if (
                parsed_date.hour == 0
                and parsed_date.minute == 0
                and parsed_date.second == 0
            ):
                parsed_date = parsed_date.replace(
                    hour=now.hour,
                    minute=now.minute,
                    second=now.second,
                    microsecond=now.microsecond,
                )

            return parsed_date.isoformat()

    except Exception:
        pass

    return now.isoformat()


def its_job_older_than_threshold(published_at_iso, hours_limit=12):
    """Comprueba si un trabajo es más antiguo que el límite en horas."""
    try:
        published_date = datetime.fromisoformat(published_at_iso)
        cutoff_date = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)) - timedelta(
            hours=hours_limit
        )
        return published_date < cutoff_date
    except (ValueError, TypeError):
        return False
