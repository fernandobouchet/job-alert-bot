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
    WEAK_IT_SIGNALS,
)
from filters_scoring_config.patterns import EXPERIENCE_PATTERNS


print("🔄 Compiling regex patterns from config...")

# OPTIMIZATION: Use non-capturing group with single lookaround pair for all patterns
# This significantly reduces regex compilation time and execution speed.

_REGEX_AREA_PREFILTER = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s) for s in sorted(EXCLUDED_AREA_TERMS_TITLE, key=len, reverse=True)) + r")(?!\w)",
    re.IGNORECASE | re.UNICODE,
)

_REGEX_EXCLUDED_SENIORITY = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s) for s in sorted(EXCLUDED_SENIORITY_TERMS, key=len, reverse=True)) + r")(?!\w)",
    re.IGNORECASE | re.UNICODE,
)

_REGEX_POSITIVE_SENIORITY = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s) for s in sorted(POSITIVE_SENIORITY_TERMS, key=len, reverse=True)) + r")(?!\w)",
    re.IGNORECASE | re.UNICODE,
)

_REGEX_AMBIGUOUS_ROLES = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s) for s in sorted(AMBIGUOUS_ROLES, key=len, reverse=True)) + r")(?!\w)",
    re.IGNORECASE | re.UNICODE,
)

_REGEX_IT_SIGNALS = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s) for s in sorted(IT_CONTEXT_SIGNALS, key=len, reverse=True)) + r")(?!\w)",
    re.IGNORECASE | re.UNICODE,
)

_REGEX_WEAK_SIGNALS = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s) for s in sorted(WEAK_IT_SIGNALS, key=len, reverse=True)) + r")(?!\w)",
    re.IGNORECASE | re.UNICODE,
)

_REGEX_ALL_ROLES = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s) for s in sorted(_ALL_ROLES_KEYWORDS, key=len, reverse=True)) + r")(?!\w)",
    re.IGNORECASE | re.UNICODE,
)

_REGEX_ALL_TECHS = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s) for s in sorted(_ALL_TECHS_KEYWORDS, key=len, reverse=True)) + r")(?!\w)",
    re.IGNORECASE | re.UNICODE,
)

COMPILED_EXPERIENCE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in EXPERIENCE_PATTERNS
]


print("✅ Regex patterns compiled")
