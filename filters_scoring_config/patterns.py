EXPERIENCE_PATTERNS = [
    # Rangos: "3-5 años" o "de 3 a 5 años" + contexto de experiencia
    # ES/EN: experiencia/experience/exp
    # Optimized: replaced .*? with .{0,100}? to prevent catastrophic backtracking and long-distance false positives
    # usage of non-greedy quantifier (?) ensures we match the closest numbers
    r"(?:exp\.?|experiencia|experience).{0,100}?(\d+)\s*(?:-|a|to|y)\s*(\d+)\s*(?:años|years)",
    r"(\d+)\s*(?:-|a|to|y)\s*(\d+)\s*(?:años|years).{0,100}?(?:exp\.?|experiencia|experience)",

    # Número + años de experiencia: "5 años de experiencia" / "5 years of experience"
    # Supports "5+ years of exp"
    r"(\d+)\+?\s*(?:años|years)\s*(?:de|of)\s*(?:exp\.?|experiencia|experience)",

    # Mínimo explícito: "mínimo 5 años", "min. 5 years", "at least 5 years"
    # Added m[íi]nim[oa] for "mínima"
    r"(?:m[íi]nim[oa]|m[íi]n\.?|minimum|al menos|at least)\s*(\d+)\s*(?:años|years)",

    # Con + explícito: "5+ años", "5+ years"
    r"(\d+)\+\s*(?:años|years)",

    # Colon/Label style: "Experience: 5 years", "Exp: 5 years", "Experiencia requerida: 5 años"
    # Improved to handle optional colon separated from optional 'required'
    r"(?:exp\.?|experiencia|experience)\s*(?:required|requerid[ao])?\s*:?\s*(\d+)\s*(?:años|years)",

    # More than: "More than 5 years", "Más de 5 años"
    r"(?:más de|more than)\s*(\d+)\s*(?:años|years)",
]
