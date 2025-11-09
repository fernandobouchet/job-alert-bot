SENIOR_EXPERIENCE_PATTERNS = [
    # 1. RANGO: Captura (Inferior, Superior)
    r"(?:de\s*)?(\d+)\s*(?:-|to|a|y)\s*(\d+)\s*(?:a[ñn]os|years?)",
    # 2. MÍNIMO EXPLÍCITO: Captura el número mínimo (incluye "mínimo", "+", "de")
    r"(?:m[íi]nimo|minimum|min\.?|al\s*menos|at\s*least|de\s*|of\s*|por\s*)*(\d+)\+?\s*(?:a[ñn]os|years?)",
]
