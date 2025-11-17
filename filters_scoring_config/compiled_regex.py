import re

from filters_scoring_config.areas import EXCLUDED_AREA_TERMS_TITLE
from filters_scoring_config.compiled_profiles import (
    _ALL_ROLES_KEYWORDS,
    _ALL_TECHS_KEYWORDS,
)
from filters_scoring_config.seniority import (
    EXCLUDED_SENIORITY_TERMS,
    POSITIVE_SENIORITY_TERMS,
)
from filters_scoring_config.signals import (
    AMBIGUOUS_ROLES,
    IT_CONTEXT_SIGNALS,
)


print("🔄 Compiling regex patterns from config...")

_REGEX_AREA_PREFILTER = re.compile(
    "|".join(r"(?<!\w)" + re.escape(s) + r"(?!\w)" for s in EXCLUDED_AREA_TERMS_TITLE),
    re.IGNORECASE | re.UNICODE,
)

_REGEX_EXCLUDED_SENIORITY = re.compile(
    "|".join(r"(?<!\w)" + re.escape(s) + r"(?!\w)" for s in EXCLUDED_SENIORITY_TERMS),
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
    "|".join(r"(?<!\w)" + re.escape(s) + r"(?!\w)" for s in IT_CONTEXT_SIGNALS),
    re.IGNORECASE | re.UNICODE,
)

_REGEX_ALL_ROLES = re.compile(
    "|".join(r"(?<!\w)" + re.escape(s) + r"(?!\w)" for s in _ALL_ROLES_KEYWORDS),
    re.IGNORECASE | re.UNICODE,
)

_REGEX_ALL_TECHS = re.compile(
    "|".join(r"(?<!\w)" + re.escape(s) + r"(?!\w)" for s in _ALL_TECHS_KEYWORDS),
    re.IGNORECASE | re.UNICODE,
)


print("✅ Regex patterns compiled")
