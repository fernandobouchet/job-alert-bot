import re
from filters_scoring_config.compiled_profiles import COMPILED_PROFILES

software_profile = COMPILED_PROFILES["software"]
print("Tech Set sample:", list(software_profile["tech_set"])[:5])
print("Tech Multi Regex:", software_profile["tech_multi_regex"].pattern)

text_csharp = "we need c# knowledge"
matches_csharp = software_profile["tech_multi_regex"].findall(text_csharp)
print(f"Matches for '{text_csharp}': {matches_csharp}")

text_node = "experience with node.js is required"
matches_node = software_profile["tech_multi_regex"].findall(text_node)
print(f"Matches for '{text_node}': {matches_node}")

# Verify if c# is in the regex
import filters_scoring_config.profiles as p
terms = []
for item in p.PROFILES["software"]["tech"]:
    if isinstance(item, str): terms.append(item)
    else: terms.extend(item["search"])

csharp_term = "c#"
print(f"'c#' in raw terms? {csharp_term in terms}")

# Check compiled_profiles logic manually
lower_term = "c#"
if " " in lower_term or not lower_term.isalnum():
    print(f"Logic check: '{lower_term}' goes to multi/regex")
else:
    print(f"Logic check: '{lower_term}' goes to set")
