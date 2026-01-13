import re
from collections import defaultdict
from filters_scoring_config.profiles import PROFILES

print("🔄 Compiling profile regex patterns...")

COMPILED_PROFILES = {}
_ALL_ROLES_KEYWORDS = set()
_ALL_TECHS_KEYWORDS = set()
_ALL_SIGNALS_KEYWORDS = set()
TECH_REVERSE_MAP = {}
ROLE_REVERSE_MAP = {}
ROLE_TO_PROFILE_MAP = defaultdict(list)
TECH_TO_PROFILE_MAP = defaultdict(list)

for profile_name, profile_data in PROFILES.items():
    # --- Compile roles regex from hybrid list for the current profile ---
    profile_roles_search_terms = []
    for item in profile_data["roles"]:
        if isinstance(item, str):
            profile_roles_search_terms.append(item)
            _ALL_ROLES_KEYWORDS.add(item)
            ROLE_REVERSE_MAP[item.lower()] = item
            ROLE_TO_PROFILE_MAP[item.lower()].append(profile_name)
        elif isinstance(item, dict):
            display_tag = item["display"]
            search_terms = item["search"]
            profile_roles_search_terms.extend(search_terms)
            _ALL_ROLES_KEYWORDS.update(search_terms)
            for term in search_terms:
                ROLE_REVERSE_MAP[term.lower()] = display_tag
                ROLE_TO_PROFILE_MAP[term.lower()].append(profile_name)

    # OPTIMIZATION: Use non-capturing group with single lookaround pair
    # instead of repeating lookarounds for every term.
    # From: (?<!\w)A(?!\w)|(?<!\w)B(?!\w)
    # To:   (?<!\w)(?:A|B)(?!\w)
    if profile_roles_search_terms:
        # Sort terms by length descending to ensure longer matches take precedence
        sorted_terms = sorted(profile_roles_search_terms, key=len, reverse=True)
        roles_pattern = r"(?<!\w)(?:" + "|".join(re.escape(s.lower()) for s in sorted_terms) + r")(?!\w)"
        compiled_roles = re.compile(roles_pattern, re.UNICODE)
    else:
        compiled_roles = re.compile(r"(?!.*)", re.UNICODE)

    # --- Compile tech regex from hybrid list for the current profile ---
    profile_tech_search_terms = []
    for item in profile_data["tech"]:
        if isinstance(item, str):
            profile_tech_search_terms.append(item)
            _ALL_TECHS_KEYWORDS.add(item)
            TECH_REVERSE_MAP[item.lower()] = item  # Maps to itself
            TECH_TO_PROFILE_MAP[item.lower()].append(profile_name)
        elif isinstance(item, dict):
            display_tag = item["display"]
            search_terms = item["search"]
            profile_tech_search_terms.extend(search_terms)
            _ALL_TECHS_KEYWORDS.update(search_terms)
            for term in search_terms:
                TECH_REVERSE_MAP[term.lower()] = display_tag
                TECH_TO_PROFILE_MAP[term.lower()].append(profile_name)

    if profile_tech_search_terms:
        sorted_tech = sorted(profile_tech_search_terms, key=len, reverse=True)
        tech_pattern = r"(?<!\w)(?:" + "|".join(re.escape(s.lower()) for s in sorted_tech) + r")(?!\w)"
        compiled_tech = re.compile(tech_pattern, re.UNICODE)
    else:
        compiled_tech = re.compile(r"(?!.*)", re.UNICODE)

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
        sorted_signals = sorted(profile_signals_search_terms, key=len, reverse=True)
        signals_pattern = r"(?<!\w)(?:" + "|".join(re.escape(s.lower()) for s in sorted_signals) + r")(?!\w)"
        compiled_signals = re.compile(signals_pattern, re.UNICODE)
    else:
        # Create empty regex that never matches
        compiled_signals = re.compile(r"(?!.*)", re.UNICODE)

    COMPILED_PROFILES[profile_name] = {
        "roles": compiled_roles,
        "tech": compiled_tech,
        "signals": compiled_signals,
    }


print("✅ Profile regex patterns and reverse map compiled.")
