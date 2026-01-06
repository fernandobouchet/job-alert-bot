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
    r"(?<!\w)(?:" + "|".join(re.escape(s) for s in EXCLUDED_AREA_TERMS_TITLE) + r")(?!\w)",
    re.IGNORECASE | re.UNICODE,
)

_REGEX_EXCLUDED_SENIORITY = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s) for s in EXCLUDED_SENIORITY_TERMS) + r")(?!\w)",
    re.IGNORECASE | re.UNICODE,
)

_REGEX_POSITIVE_SENIORITY = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s) for s in POSITIVE_SENIORITY_TERMS) + r")(?!\w)",
    re.IGNORECASE | re.UNICODE,
)

_REGEX_AMBIGUOUS_ROLES = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s) for s in AMBIGUOUS_ROLES) + r")(?!\w)",
    re.IGNORECASE | re.UNICODE,
)

_REGEX_IT_SIGNALS = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s) for s in IT_CONTEXT_SIGNALS) + r")(?!\w)",
    re.IGNORECASE | re.UNICODE,
)

_REGEX_WEAK_SIGNALS = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s) for s in WEAK_IT_SIGNALS) + r")(?!\w)",
    re.IGNORECASE | re.UNICODE,
)

_REGEX_ALL_ROLES = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s) for s in _ALL_ROLES_KEYWORDS) + r")(?!\w)",
    re.IGNORECASE | re.UNICODE,
)

_REGEX_ALL_TECHS = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s) for s in _ALL_TECHS_KEYWORDS) + r")(?!\w)",
    re.IGNORECASE | re.UNICODE,
)

COMPILED_EXPERIENCE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in EXPERIENCE_PATTERNS
]


print("✅ Regex patterns compiled")
