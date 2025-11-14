"""Configuración central para filtros y scoring"""

from filters_scoring_config.areas import EXCLUDED_AREA_TERMS_TITLE
from filters_scoring_config.scoring import MIN_YEARS_SENIORITY
from .seniority import (
    POSITIVE_SENIORITY_TERMS,
    EXCLUDED_SENIORITY_TERMS,
)
from .signals import (
    WEAK_IT_SIGNALS,
    STRONG_TECH_SIGNALS,
    STRONG_ROLE_SIGNALS,
    AMBIGUOUS_ROLES,
    REQUIRED_IT_SIGNALS,
)
from .tags import TAGS_KEYWORDS
from .patterns import EXPERIENCE_PATTERNS

__all__ = [
    "MIN_YEARS_SENIORITY",
    "POSITIVE_SENIORITY_TERMS",
    "EXCLUDED_SENIORITY_TERMS",
    "EXCLUDED_AREA_TERMS_TITLE",
    "WEAK_IT_SIGNALS",
    "STRONG_TECH_SIGNALS",
    "STRONG_ROLE_SIGNALS",
    "AMBIGUOUS_ROLES",
    "REQUIRED_IT_SIGNALS",
    "TAGS_KEYWORDS",
    "EXPERIENCE_PATTERNS",
]
