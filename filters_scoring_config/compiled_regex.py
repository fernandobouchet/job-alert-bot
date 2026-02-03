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

_REGEX_IT_SIGNALS = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s.lower()) for s in sorted(IT_CONTEXT_SIGNALS, key=len, reverse=True)) + r")(?!\w)",
    re.UNICODE,
)

_REGEX_WEAK_SIGNALS = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s.lower()) for s in sorted(WEAK_IT_SIGNALS, key=len, reverse=True)) + r")(?!\w)",
    re.UNICODE,
)

_REGEX_ALL_ROLES = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s.lower()) for s in sorted(_ALL_ROLES_KEYWORDS, key=len, reverse=True)) + r")(?!\w)",
    re.UNICODE,
)

_REGEX_ALL_TECHS = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s.lower()) for s in sorted(_ALL_TECHS_KEYWORDS, key=len, reverse=True)) + r")(?!\w)",
    re.UNICODE,
)

_REGEX_AREA_EXCEPTION = re.compile(
    r"(?<!\w)(?:" +
    "|".join(re.escape(s.lower()) for s in sorted(_ALL_ROLES_KEYWORDS, key=len, reverse=True)) +
    "|" +
    "|".join(re.escape(s.lower()) for s in sorted(IT_CONTEXT_SIGNALS, key=len, reverse=True)) +
    r")(?!\w)",
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


# OPTIMIZATION: Combine Role, IT, Seniority, and Weak signals into a single unified scanner
# to reduce the number of passes over the full text.
# Conflict resolution: Longest match wins (handled by sorting).
# Overlap handling: Precedence is implicit in the map.
# Priority: ROLE > IT > SENIORITY > WEAK

print("🔄 Compiling unified scanner...")

_TERM_TYPE_MAP = {}

# Populate map with priority
# WEAK first (lowest priority, will be overwritten)
for term in WEAK_IT_SIGNALS:
    _TERM_TYPE_MAP[term.lower()] = "WEAK"

# SENIORITY second
for term in POSITIVE_SENIORITY_TERMS:
    _TERM_TYPE_MAP[term.lower()] = "SEN"

# IT third
for term in IT_CONTEXT_SIGNALS:
    _TERM_TYPE_MAP[term.lower()] = "IT"

# ROLE last (highest priority)
for term in _ALL_ROLES_KEYWORDS:
    _TERM_TYPE_MAP[term.lower()] = "ROLE"

_ALL_UNIFIED_TERMS = sorted(_TERM_TYPE_MAP.keys(), key=len, reverse=True)

_REGEX_UNIFIED_SCANNER = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s) for s in _ALL_UNIFIED_TERMS) + r")(?!\w)",
    re.UNICODE,
)

print("✅ Unified scanner compiled")


print("✅ Regex patterns compiled")
