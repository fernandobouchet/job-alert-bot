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

## 2025-02-21 - Heterogeneous Regex Consolidation vs Set Intersection
**Learning:** Combining heterogeneous regexes (Roles, IT Signals, Seniority) into a single Unified Scanner with longest-match precedence was faster (~1.24x) than multiple passes. Conversely, switching to `set.intersection` for single-word terms was SLOWER (0.57x).
**Reason:** The overhead of Python-side tokenization and set operations outweighed the benefit of reducing regex size, especially since many terms are multi-word. The C-based regex engine is extremely efficient at single-pass scanning even with many alternations.
**Action:** Consolidate unconditional regex passes into a single unified regex when possible, using a map to disambiguate matches. Avoid moving logic to Python (sets/tokenization) unless the set is significantly larger than the regex component.

## 2025-02-22 - Combined Regex for Exception Handling
**Learning:** Combining "Role" and "IT Signal" regexes into a single "Exception" regex for the Area Pre-filter improved performance by ~7.5%.
**Reason:** In the "reject" path (which is the common case for this filter), checking `Role OR Signal` previously required two separate regex passes (both failing). Combining them allows a single pass to determine if any exception exists.
**Action:** When filtering based on `A OR B` conditions, especially in "reject" paths, combine A and B into a single regex to minimize scans.
