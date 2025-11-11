EXPERIENCE_PATTERNS = [
    # Rangos: "3-5 años" o "de 3 a 5 años" + contexto de experiencia
    r"(?:experiencia|experience).*?(\d+)\s*(?:-|a|to)\s*(\d+)\s*(?:años|years)",
    r"(\d+)\s*(?:-|a|to)\s*(\d+)\s*(?:años|years).*?(?:experiencia|experience)",
    # Número + años de experiencia: "5 años de experiencia"
    r"(\d+)\+?\s*(?:años|years)\s*de\s*(?:experiencia|experience)",
    # Mínimo explícito: "mínimo 5 años"
    r"(?:mínimo|minimum|al menos|at least)\s*(\d+)\s*(?:años|years)",
    # Con + explícito: "5+ años"
    r"(\d+)\+\s*(?:años|years)",
]
