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

def split_keywords(keywords):
    """Split keywords into single-word alphanumeric set and multi-word list."""
    # Ensure keywords are lowercase for set intersection
    # Only strictly alphanumeric keywords go to set (to match [a-z0-9]+ tokenization)
    single = {k.lower() for k in keywords if k.isalnum()}
    # Remaining keywords go to regex (preserved in original form, lowercased during compilation)
    multi = [k for k in keywords if k.lower() not in single]
    return single, multi

# OPTIMIZATION: Use non-capturing group with single lookaround pair for all patterns
# This significantly reduces regex compilation time and execution speed.

_REGEX_AREA_PREFILTER = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s.lower()) for s in sorted(EXCLUDED_AREA_TERMS_TITLE, key=len, reverse=True)) + r")(?!\w)",
    re.UNICODE,
)

_REGEX_EXCLUDED_SENIORITY = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s.lower()) for s in sorted(EXCLUDED_SENIORITY_TERMS, key=len, reverse=True)) + r")(?!\w)",
    re.UNICODE,
)

_REGEX_POSITIVE_SENIORITY = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s.lower()) for s in sorted(POSITIVE_SENIORITY_TERMS, key=len, reverse=True)) + r")(?!\w)",
    re.UNICODE,
)

_REGEX_AMBIGUOUS_ROLES = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s.lower()) for s in sorted(AMBIGUOUS_ROLES, key=len, reverse=True)) + r")(?!\w)",
    re.UNICODE,
)

# --- Optimized Signals (Set + Regex) ---
_SET_IT_SIGNALS_SINGLE, _IT_SIGNALS_MULTI = split_keywords(IT_CONTEXT_SIGNALS)
_REGEX_IT_SIGNALS_MULTI = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s.lower()) for s in sorted(_IT_SIGNALS_MULTI, key=len, reverse=True)) + r")(?!\w)",
    re.UNICODE,
)
# Keep original for backward compatibility
_REGEX_IT_SIGNALS = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s.lower()) for s in sorted(IT_CONTEXT_SIGNALS, key=len, reverse=True)) + r")(?!\w)",
    re.UNICODE,
)

_SET_WEAK_SIGNALS_SINGLE, _WEAK_SIGNALS_MULTI = split_keywords(WEAK_IT_SIGNALS)
_REGEX_WEAK_SIGNALS_MULTI = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s.lower()) for s in sorted(_WEAK_SIGNALS_MULTI, key=len, reverse=True)) + r")(?!\w)",
    re.UNICODE,
)
# Keep original for backward compatibility
_REGEX_WEAK_SIGNALS = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s.lower()) for s in sorted(WEAK_IT_SIGNALS, key=len, reverse=True)) + r")(?!\w)",
    re.UNICODE,
)

_REGEX_ALL_ROLES = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s.lower()) for s in sorted(_ALL_ROLES_KEYWORDS, key=len, reverse=True)) + r")(?!\w)",
    re.UNICODE,
)

# --- Optimized Techs (Set + Regex) ---
_SET_ALL_TECHS_SINGLE, _ALL_TECHS_MULTI = split_keywords(_ALL_TECHS_KEYWORDS)
_REGEX_ALL_TECHS_MULTI = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s.lower()) for s in sorted(_ALL_TECHS_MULTI, key=len, reverse=True)) + r")(?!\w)",
    re.UNICODE,
)
# Keep original for backward compatibility
_REGEX_ALL_TECHS = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s.lower()) for s in sorted(_ALL_TECHS_KEYWORDS, key=len, reverse=True)) + r")(?!\w)",
    re.UNICODE,
)

# OPTIMIZATION: Combine all experience patterns into a single regex for faster scanning.
# Each pattern is wrapped in a non-capturing group to allow combining with OR.
# Note: Input text is always normalized to lowercase, so re.IGNORECASE is not needed.
_COMBINED_EXPERIENCE_PATTERN = "|".join(f"(?:{p})" for p in EXPERIENCE_PATTERNS)
COMPILED_EXPERIENCE_REGEX = re.compile(_COMBINED_EXPERIENCE_PATTERN)

COMPILED_EXPERIENCE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in EXPERIENCE_PATTERNS
]


print("✅ Regex patterns compiled")
