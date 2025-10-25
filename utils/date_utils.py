import math
import zoneinfo
from datetime import datetime
import dateparser
from config import TIMEZONE


def safe_parse_date_to_ISO(date):
    """
    Parsea una fecha desde diversos formatos (en inglés o español) a ISO 8601 con timezone.
    Se espera que las fechas vengan en formato YYYY-MM-DD.
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
        "DATE_ORDER": "YMD",  # Evita inversión día/mes
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

            return parsed_date.isoformat()

    except Exception:
        pass

    return now.isoformat()
