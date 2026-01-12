## 2024-05-22 - Regex Optimization in Scoring
**Learning:** Compiling regex patterns and using vectorized operations significantly speeds up scoring.
**Action:** Always look for opportunities to vectorize pandas operations.
## 2024-05-22 - Tech Scoring Optimization
**Learning:** Reusing the result of `_REGEX_ALL_TECHS.findall` and checking set intersection is O(N) instead of O(N*M) where M is number of potential profiles. However, with small N and M, the overhead of creating sets and python loops might offset regex speedups.
**Action:** For large text or many profiles, this is definitely better. For small cases, it's comparable.
