import math
import zoneinfo
import re
from datetime import datetime, timedelta
import dateparser
from constants import TIMEZONE

# OPTIMIZATION: Pre-compiled regex for fast ISO date checking
_REGEX_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def safe_parse_date_to_ISO(date):
    """
    Normaliza una fecha a ISO 8601 con timezone de TIMEZONE.
    - Si no hay fecha o es inválida, devuelve la fecha y hora actual en TIMEZONE.
    - Siempre devuelve cadena compatible con pd.to_datetime().
    - Normaliza a medianoche (00:00:00) para consistencia.
    """
    tz = zoneinfo.ZoneInfo(TIMEZONE)
    now = datetime.now(tz)

    if date is None or (isinstance(date, float) and math.isnan(date)):
        return now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    # OPTIMIZATION: Fast path for simple YYYY-MM-DD strings to avoid expensive dateparser
    if isinstance(date, str) and _REGEX_ISO_DATE.match(date):
        try:
            # Parse directly using strptime which is much faster than dateparser
            parsed_date = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=tz)
            parsed_date = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
            return parsed_date.isoformat()
        except ValueError:
            pass # Fallback to dateparser if values are invalid (e.g. 2024-99-99)

    settings = {
        "TIMEZONE": TIMEZONE,
        "RETURN_AS_TIMEZONE_AWARE": True,
        "DATE_ORDER": "YMD",
        "PREFER_DAY_OF_MONTH": "first",
    }

    try:
        parsed_date = None

        if isinstance(date, (int, float)) and not math.isnan(date):
            parsed_date = datetime.fromtimestamp(date, tz=tz)
        else:
            parsed_date = dateparser.parse(
                str(date), settings=settings, languages=["es", "en"]
            )

        if not parsed_date:
            return now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

        if parsed_date.tzinfo is None:
            parsed_date = parsed_date.replace(tzinfo=tz)
        else:
            parsed_date = parsed_date.astimezone(tz)

        parsed_date = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)

        return parsed_date.isoformat()

    except Exception:
        fallback = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return fallback.isoformat()


def get_timestamp_24_hours_ago():
    """
    Calcula el Timestamp Unix exacto de hace 24 horas.
    """
    tz = zoneinfo.ZoneInfo(TIMEZONE)

    now_timezone = datetime.now(tz)

    time_24_hours_ago = now_timezone - timedelta(hours=24)

    return time_24_hours_ago.timestamp()
