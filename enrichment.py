import re
from config import TAGS_KEYWORDS


def extract_tags(text_for_extraction):
    text = text_for_extraction.lower()
    found_tags = []
    for kw in TAGS_KEYWORDS:
        pattern = r"(?<!\w)" + re.escape(kw) + r"(?!\w)"
        if re.search(pattern, text, re.IGNORECASE):
            found_tags.append(kw)
    return found_tags


def extract_job_modality(text_for_extraction):
    text = text_for_extraction.lower()
    if re.search(
        r"\b(100%\s*(on-site|onsite|presencial)|exclusivamente\s*presencial)\b", text
    ):
        return "On-site"
    remote_terms = (
        r"\b(remoto|remote|desde\s*casa|work\s*from\s*home|wfh|teletrabajo|anywhere)\b"
    )
    onsite_terms = (
        r"\b(presencial|on-site|onsite|oficina|sede|caba|buenos\s*aires|viajes)\b"
    )
    is_remote_mentioned = re.search(remote_terms, text)
    is_onsite_mentioned = re.search(onsite_terms, text)
    if re.search(r"\b(híbrido|hybrid|mixto)\b", text) or (
        is_remote_mentioned and is_onsite_mentioned
    ):
        return "Hybrid"
    if is_onsite_mentioned:
        return "On-site"
    if is_remote_mentioned:
        return "Remote"
    return "Not Specified"
