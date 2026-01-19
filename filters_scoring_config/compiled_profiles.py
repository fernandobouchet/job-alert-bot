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

def process_terms(terms_list, is_role=False, profile_name=None):
    """
    Helper to extract terms, update global sets, and reverse maps.
    Returns:
        all_terms: list of all terms
        single_word_terms: set of terms that are single words
        multi_word_terms: list of terms that are multi words
    """
    all_terms = []
    single_word_terms = set()
    multi_word_terms = []

    for item in terms_list:
        current_terms = []
        display_tag = None

        if isinstance(item, str):
            current_terms.append(item)
            display_tag = item
        elif isinstance(item, dict):
            display_tag = item["display"]
            current_terms.extend(item["search"])

        for term in current_terms:
            lower_term = term.lower()
            all_terms.append(lower_term)

            # Split logic:
            # 1. Terms with spaces -> Regex (multi-word)
            # 2. Terms with non-alphanumeric chars (c++, node.js) -> Regex (to handle boundaries correctly)
            # 3. Purely alphanumeric terms (java, python) -> Set (fast O(1) lookup)
            if " " in lower_term or not lower_term.isalnum():
                multi_word_terms.append(lower_term)
            else:
                single_word_terms.add(lower_term)

            if is_role:
                _ALL_ROLES_KEYWORDS.add(term) # Keep original casing in set if needed? Old code did it.
                ROLE_REVERSE_MAP[lower_term] = display_tag
                if profile_name:
                    ROLE_TO_PROFILE_MAP[lower_term].append(profile_name)
            else:
                # Techs and Signals share the same reverse map
                TECH_REVERSE_MAP[lower_term] = display_tag
                if profile_name and not is_role: # Only populate tech map for techs
                     TECH_TO_PROFILE_MAP[lower_term].append(profile_name)

    return all_terms, single_word_terms, multi_word_terms

def compile_regex(terms):
    if not terms:
        return re.compile(r"(?!.*)", re.UNICODE)
    # Sort terms by length descending
    sorted_terms = sorted(terms, key=len, reverse=True)
    pattern = r"(?<!\w)(?:" + "|".join(re.escape(s) for s in sorted_terms) + r")(?!\w)"
    return re.compile(pattern, re.UNICODE)

for profile_name, profile_data in PROFILES.items():
    # --- Roles ---
    roles_all, roles_single, roles_multi = process_terms(
        profile_data["roles"], is_role=True, profile_name=profile_name
    )
    _ALL_ROLES_KEYWORDS.update(roles_all)

    # Compile regexes
    # We keep the "full" regex for backward compatibility or cases where we need full scan
    compiled_roles = compile_regex(roles_all)
    compiled_roles_multi = compile_regex(roles_multi)

    # --- Tech ---
    tech_all, tech_single, tech_multi = process_terms(
        profile_data["tech"], is_role=False, profile_name=profile_name
    )
    _ALL_TECHS_KEYWORDS.update(tech_all)

    compiled_tech = compile_regex(tech_all)
    compiled_tech_multi = compile_regex(tech_multi)

    # --- Signals ---
    signals_all, signals_single, signals_multi = process_terms(
        profile_data.get("signals", []), is_role=False, profile_name=None # Signals don't map back to profile via TECH_TO_PROFILE_MAP usually?
        # Actually TECH_TO_PROFILE_MAP is for tech. The loop above didn't use signals for map.
    )
    _ALL_SIGNALS_KEYWORDS.update(signals_all)

    compiled_signals = compile_regex(signals_all)
    compiled_signals_multi = compile_regex(signals_multi)

    COMPILED_PROFILES[profile_name] = {
        "roles": compiled_roles,
        "tech": compiled_tech,
        "signals": compiled_signals,
        # Optimized structures
        "tech_set": tech_single,
        "tech_multi_regex": compiled_tech_multi,
        "signals_set": signals_single,
        "signals_multi_regex": compiled_signals_multi,
        # Roles usually scanned via _REGEX_ALL_ROLES so maybe not needed here,
        # but kept for consistency
        "roles_set": roles_single,
        "roles_multi_regex": compiled_roles_multi,
    }

print("✅ Profile regex patterns and reverse map compiled.")
