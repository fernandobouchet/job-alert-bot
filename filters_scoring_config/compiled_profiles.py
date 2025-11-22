import re
from filters_scoring_config.profiles import PROFILES

print("🔄 Compiling profile regex patterns...")

COMPILED_PROFILES = {}
_ALL_ROLES_KEYWORDS = set()
_ALL_TECHS_KEYWORDS = set()
_ALL_SIGNALS_KEYWORDS = set()
TECH_REVERSE_MAP = {}
ROLE_REVERSE_MAP = {}

for profile_name, profile_data in PROFILES.items():
    # --- Compile roles regex from hybrid list for the current profile ---
    profile_roles_search_terms = []
    for item in profile_data["roles"]:
        if isinstance(item, str):
            profile_roles_search_terms.append(item)
            _ALL_ROLES_KEYWORDS.add(item)
            ROLE_REVERSE_MAP[item.lower()] = item
        elif isinstance(item, dict):
            display_tag = item["display"]
            search_terms = item["search"]
            profile_roles_search_terms.extend(search_terms)
            _ALL_ROLES_KEYWORDS.update(search_terms)
            for term in search_terms:
                ROLE_REVERSE_MAP[term.lower()] = display_tag

    roles_pattern = "|".join(
        r"(?<!\w)" + re.escape(s) + r"(?!\w)" for s in profile_roles_search_terms
    )
    compiled_roles = re.compile(roles_pattern, re.IGNORECASE | re.UNICODE)

    # --- Compile tech regex from hybrid list for the current profile ---
    profile_tech_search_terms = []
    for item in profile_data["tech"]:
        if isinstance(item, str):
            profile_tech_search_terms.append(item)
            _ALL_TECHS_KEYWORDS.add(item)
            TECH_REVERSE_MAP[item.lower()] = item  # Maps to itself
        elif isinstance(item, dict):
            display_tag = item["display"]
            search_terms = item["search"]
            profile_tech_search_terms.extend(search_terms)
            _ALL_TECHS_KEYWORDS.update(search_terms)
            for term in search_terms:
                TECH_REVERSE_MAP[term.lower()] = display_tag

    tech_pattern = "|".join(
        r"(?<!\w)" + re.escape(s) + r"(?!\w)" for s in profile_tech_search_terms
    )
    compiled_tech = re.compile(tech_pattern, re.IGNORECASE | re.UNICODE)

    # --- Compile signals regex from hybrid list for the current profile ---
    profile_signals_search_terms = []
    for item in profile_data.get("signals", []):  
        if isinstance(item, str):
            profile_signals_search_terms.append(item)
            _ALL_SIGNALS_KEYWORDS.add(item)
            TECH_REVERSE_MAP[item.lower()] = item 
        elif isinstance(item, dict):
            display_tag = item["display"]
            search_terms = item["search"]
            profile_signals_search_terms.extend(search_terms)
            _ALL_SIGNALS_KEYWORDS.update(search_terms)
            for term in search_terms:
                TECH_REVERSE_MAP[term.lower()] = display_tag 
    if profile_signals_search_terms:
        signals_pattern = "|".join(
            r"(?<!\w)" + re.escape(s) + r"(?!\w)" for s in profile_signals_search_terms
        )
        compiled_signals = re.compile(signals_pattern, re.IGNORECASE | re.UNICODE)
    else:
        # Create empty regex that never matches
        compiled_signals = re.compile(r"(?!.*)", re.IGNORECASE | re.UNICODE)

    COMPILED_PROFILES[profile_name] = {
        "roles": compiled_roles,
        "tech": compiled_tech,
        "signals": compiled_signals,
    }


print("✅ Profile regex patterns and reverse map compiled.")
