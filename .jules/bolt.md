## 2024-05-23 - Global Regex vs Profile-Specific Regex
**Learning:** Consolidating multiple profile-specific regexes into one giant global regex (`_REGEX_ALL_TECHS`) to scan once and then filter turned out to be SLOWER than running multiple smaller, specific regexes.
**Reason:** The global regex (`_REGEX_ALL_TECHS`) is extremely large and complex. Searching it against the text takes longer than searching for a few specific profile tech lists (e.g., just Backend or Frontend techs) which are much smaller. The "happy path" (finding a profile) typically involves matching 1 or 2 profiles, so the overhead of the giant regex outweighs the benefit of O(1) profile scans.
**Action:** Prefer selective, smaller regex scans when the number of candidates (e.g., potential profiles) is small. Avoid giant "catch-all" regexes if they are not strictly necessary for fallback.

## 2024-05-24 - Homogeneous Regex Consolidation
**Learning:** Consolidating multiple structurally similar regexes (like experience patterns) into a single regex with alternations (`|`) yielded a ~10% performance improvement.
**Reason:** Unlike the complex profile regexes, these patterns are simple and scanned unconditionally for every job. Reducing the overhead of multiple Python-to-C context switches in `re.findall` proved beneficial.
**Action:** Combine small, homogeneous, unconditionally-executed regex patterns into a single compiled regex using non-capturing groups.

## 2025-02-20 - Redundant String Normalization & Regex Search
**Learning:** Removing redundant `text.lower()` calls when input is already normalized yielded a ~16x speedup for that specific operation. Replacing `findall` with `search` for boolean existence checks yielded a ~2x speedup.
**Reason:** String normalization (allocating new strings) is expensive in tight loops. `findall` scans the entire string and builds a list, while `search` stops at the first match.
**Action:** Trust upstream normalization contracts (and document them). Use `re.search` (or `regex.search`) when only boolean existence is needed, especially for short strings like titles.

## 2025-02-24 - Set Intersection vs Regex for Keywords
**Learning:** Splitting regex matching into "single-word set intersection" + "multi-word regex" yielded a ~40% performance improvement for keyword matching.
**Reason:** Regex engines have overhead for state machine traversal. For simple token matching (e.g., "java", "python"), `set.intersection` is O(min(len(s1), len(s2))) on hashed items, which is significantly faster than regex scanning over a large text body.
**Action:** Tokenize text once (`set(text.split())`) and use set operations for single-word keywords. Reserve regex only for complex patterns or multi-word phrases.
