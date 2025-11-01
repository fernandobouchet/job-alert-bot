import re
from filters_scoring_config import (
    AMBIGUOUS_ROLES,
    POSITIVE_SENIORITY_TERMS,
    EXCLUDED_SENIORITYS,
    EXCLUDED_AREA_TERMS_TITLE,
    REQUIRED_IT_SIGNALS,
    WEAK_IT_SIGNALS,
    STRONG_ROLE_SIGNALS,
    STRONG_TECH_SIGNALS,
)

print("🔄 Compiling regex patterns from config...")

_REGEX_AREA_PREFILTER = re.compile(
    "|".join(r"(?<!\w)" + re.escape(s) + r"(?!\w)" for s in EXCLUDED_AREA_TERMS_TITLE),
    re.IGNORECASE | re.UNICODE,
)

_REGEX_SENIORITY_EXCLUDED = re.compile(
    "|".join(r"(?<!\w)" + re.escape(s) + r"(?!\w)" for s in EXCLUDED_SENIORITYS),
    re.IGNORECASE | re.UNICODE,
)

_REGEX_POSITIVE_SENIORITY = re.compile(
    "|".join(r"(?<!\w)" + re.escape(s) + r"(?!\w)" for s in POSITIVE_SENIORITY_TERMS),
    re.IGNORECASE | re.UNICODE,
)

_REGEX_AMBIGUOUS_ROLES = re.compile(
    "|".join(r"(?<!\w)" + re.escape(s) + r"(?!\w)" for s in AMBIGUOUS_ROLES),
    re.IGNORECASE | re.UNICODE,
)

_REGEX_IT_SIGNALS = re.compile(
    "|".join(r"(?<!\w)" + re.escape(s) + r"(?!\w)" for s in REQUIRED_IT_SIGNALS),
    re.IGNORECASE | re.UNICODE,
)

_REGEX_WEAK_IT_SIGNALS = re.compile(
    "|".join(r"(?<!\w)" + re.escape(s) + r"(?!\w)" for s in WEAK_IT_SIGNALS),
    re.IGNORECASE | re.UNICODE,
)

_REGEX_STRONG_ROLE_SIGNALS = re.compile(
    "|".join(r"(?<!\w)" + re.escape(s) + r"(?!\w)" for s in STRONG_ROLE_SIGNALS),
    re.IGNORECASE | re.UNICODE,
)

_REGEX_STRONG_TECH_SIGNALS = re.compile(
    "|".join(r"(?<!\w)" + re.escape(s) + r"(?!\w)" for s in STRONG_TECH_SIGNALS),
    re.IGNORECASE | re.UNICODE,
)


print("✅ Regex patterns compiled")
