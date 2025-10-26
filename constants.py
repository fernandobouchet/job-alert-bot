import re
import logging
from config import (
    AMBIGUOUS_ROLES,
    POSITIVE_SENIORITY_TERMS,
    EXCLUDED_SENIORITYS,
    EXCLUDED_AREA_TERMS_TITLE,
    REQUIRED_IT_SIGNALS,
    WEAK_IT_SIGNALS,
    STRONG_ROLE_SIGNALS,
    STRONG_TECH_SIGNALS,
)

logger = logging.getLogger(__name__)

logger.info("🔄 Compiling regex patterns from config...")

_REGEX_AREA_PREFILTER = re.compile(
    r"\b(?:" + "|".join(re.escape(t) for t in EXCLUDED_AREA_TERMS_TITLE) + r")",
    re.IGNORECASE,
)

_REGEX_SENIORITY_EXCLUDED = re.compile(
    r"\b(?:" + "|".join(re.escape(s) for s in EXCLUDED_SENIORITYS) + r")",
    re.IGNORECASE,
)

_REGEX_POSITIVE_SENIORITY = re.compile(
    r"\b(?:" + "|".join(re.escape(s) for s in POSITIVE_SENIORITY_TERMS) + r")",
    re.IGNORECASE,
)

_REGEX_IT_SIGNALS = re.compile(
    "|".join(r"(?<!\w)" + re.escape(s) + r"(?!\w)" for s in REQUIRED_IT_SIGNALS),
    re.IGNORECASE,
)

_REGEX_WEAK_IT_SIGNALS = re.compile(
    "|".join(r"(?<!\w)" + re.escape(s) + r"(?!\w)" for s in WEAK_IT_SIGNALS),
    re.IGNORECASE,
)

_REGEX_STRONG_ROLE_SIGNALS = re.compile(
    r"\b(?:" + "|".join(re.escape(s) for s in STRONG_ROLE_SIGNALS) + r")",
    re.IGNORECASE,
)

_REGEX_STRONG_TECH_SIGNALS = re.compile(
    "|".join(r"(?<!\w)" + re.escape(s) + r"(?!\w)" for s in STRONG_TECH_SIGNALS),
    re.IGNORECASE,
)

_REGEX_AMBIGUOUS_ROLES = re.compile(
    r"\b(?:" + "|".join(re.escape(s) for s in AMBIGUOUS_ROLES) + r")",
    re.IGNORECASE,
)

logger.info("✅ Regex patterns compiled")
