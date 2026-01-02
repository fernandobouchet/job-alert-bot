import re

# Regex constants for job modality extraction
REGEX_STRICT_ONSITE = r"\b(?:100%\s*(?:on-site|onsite|presencial)|exclusivamente\s*presencial)\b"
REGEX_REMOTE = r"\b(?:remoto|remote|desde\s*casa|work\s*from\s*home|wfh|teletrabajo|anywhere)\b"
REGEX_ONSITE = r"\b(?:presencial|on-site|onsite|oficina|sede|caba|buenos\s*aires|viajes)\b"
REGEX_HYBRID = r"\b(?:híbrido|hybrid|mixto)\b"

# Compiled patterns
# Note: Input text is expected to be normalized (lowercase), so we don't strictly need re.IGNORECASE,
# but adding it makes the patterns robust against future changes in normalization.
COMPILED_STRICT_ONSITE = re.compile(REGEX_STRICT_ONSITE, re.IGNORECASE)
COMPILED_REMOTE = re.compile(REGEX_REMOTE, re.IGNORECASE)
COMPILED_ONSITE = re.compile(REGEX_ONSITE, re.IGNORECASE)
COMPILED_HYBRID = re.compile(REGEX_HYBRID, re.IGNORECASE)
