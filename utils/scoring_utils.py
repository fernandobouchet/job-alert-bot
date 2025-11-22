import pandas as pd
import re
from filters_scoring_config.compiled_profiles import (
    COMPILED_PROFILES,
    TECH_REVERSE_MAP,
    ROLE_REVERSE_MAP,
)
from filters_scoring_config.compiled_regex import (
    _REGEX_ALL_ROLES,
    _REGEX_ALL_TECHS,
    _REGEX_AMBIGUOUS_ROLES,
    _REGEX_AREA_PREFILTER,
    _REGEX_IT_SIGNALS,
    _REGEX_POSITIVE_SENIORITY,
    _REGEX_EXCLUDED_SENIORITY,
)
from filters_scoring_config.patterns import EXPERIENCE_PATTERNS
from filters_scoring_config.scoring import MIN_YEARS_SENIORITY

# Pesos para la puntuación. Ajustar estos valores modificará la importancia
# de cada tipo de señal en la puntuación final.
WEIGHTS = {
    # Bonuses
    "it_signal": 1,
    "profile_tech": 5,
    "global_tech": 2,
    "strong_role": 15,
    "positive_seniority": 15,
    "perfect_match": 5,
    # Penalties (valores positivos, se restan en el código)
    "senior_experience": 50,
    "ambiguous_no_context": 30,
}


def pre_filter_jobs(df, verbose=True):
    """
    Aplica filtros iniciales y devuelve tanto el DataFrame filtrado como los rechazados.
    Filtros aplicados:
    1. Área no-IT en título
    2. Seniority excluida en título (EXCEPTO si también menciona seniority positiva)
    """
    if df.empty:
        return df, pd.DataFrame()

    initial_count = len(df)
    if verbose:
        print(f"\n🔍 Starting pre-filtering for {initial_count} jobs...")

    rejected_indices = []
    rejection_reasons = {}

    for idx, row in df.iterrows():
        title = row.get("title_normalized", "")
        rejection_reason = None

        # FILTRO 1: Área no-IT
        if _REGEX_AREA_PREFILTER.search(title):
            # Excepción: no rechazar si contiene un rol IT fuerte Y señales IT
            if not _REGEX_ALL_ROLES.search(title) and not _REGEX_IT_SIGNALS.search(
                title
            ):
                matches = _REGEX_AREA_PREFILTER.findall(title)
                rejection_reason = f"area: {', '.join(sorted(set(matches)))}"

        # FILTRO 2: Seniority (solo si pasó filtro de área)
        elif _REGEX_EXCLUDED_SENIORITY.search(title):
            if not _REGEX_POSITIVE_SENIORITY.search(title):
                matches = _REGEX_EXCLUDED_SENIORITY.findall(title)
                rejection_reason = f"seniority: {', '.join(sorted(set(matches)))}"

        if rejection_reason:
            rejected_indices.append(idx)
            rejection_reasons[idx] = rejection_reason

    # Crear DataFrames
    if rejected_indices:
        df_rejected = df.loc[rejected_indices].copy()
        df_rejected["rejection_reason"] = df_rejected.index.map(rejection_reasons)
        df_filtered = df.drop(index=rejected_indices).copy()
    else:
        df_rejected = pd.DataFrame()
        df_filtered = df.copy()

    if verbose:
        rejected_by_area = (
            df_rejected["rejection_reason"].str.startswith("area").sum()
            if not df_rejected.empty
            else 0
        )
        rejected_by_seniority = (
            df_rejected["rejection_reason"].str.startswith("seniority").sum()
            if not df_rejected.empty
            else 0
        )
        print(f"   - Rejected by Area: {rejected_by_area} jobs")
        print(f"   - Rejected by Seniority: {rejected_by_seniority} jobs")
        print(
            f"   -> Total rejected: {len(df_rejected)} ({len(df_rejected)/initial_count*100:.1f}%)"
        )
        print(
            f"   -> Jobs remaining for scoring: {len(df_filtered)} ({len(df_filtered)/initial_count*100:.1f}%)"
        )

    return df_filtered, df_rejected


def get_empty_score_details():
    """
    Devuelve el esqueleto estándar para los detalles de puntuación.
    """
    return {
        "score": 0,
        "quality_tier": "reject",
        "base": 50,
        "bonuses": [],
        "penalties": [],
        "profiles": [],
        "roles": [],
        "tags": []
    }


def calculate_job_score(row):
    """
    Sistema de scoring 0-100 que integra la lógica de perfiles.
    """
    # Inicializar con el esqueleto estándar
    details = get_empty_score_details()
    score = details["base"]

    title = row.get("title_normalized", "")
    full_text = row.get("full_text_normalized", "")

    # --- 1. Detección de Señales y Perfiles ---
    it_signals_found = set(_REGEX_IT_SIGNALS.findall(full_text))
    ambiguous_roles_found = _REGEX_AMBIGUOUS_ROLES.findall(title)
    has_ambiguous_role = bool(ambiguous_roles_found)
    positive_seniority_matches = _REGEX_POSITIVE_SENIORITY.findall(full_text)
    negative_seniority_matches = _REGEX_EXCLUDED_SENIORITY.findall(full_text)

    has_positive_seniority = bool(positive_seniority_matches)
    has_negative_seniority = bool(negative_seniority_matches)

    # --- 2. Categorización por Perfil y Roles ---
    found_profiles = []
    raw_role_matches = set()
    for profile_name, compiled_data in COMPILED_PROFILES.items():
        role_matches = compiled_data["roles"].findall(full_text)
        if role_matches:
            found_profiles.append(profile_name)
            raw_role_matches.update(role_matches)

    normalized_roles = {
        ROLE_REVERSE_MAP.get(role.lower(), role) for role in raw_role_matches
    }
    final_roles = sorted(list(normalized_roles))

    # --- 3. Obtención de Tecnologías ---
    raw_tech_matches = set()
    if found_profiles:
        for profile_name in found_profiles:
            tech_matches = COMPILED_PROFILES[profile_name]["tech"].findall(full_text)
            raw_tech_matches.update(tech_matches)
    else:
        tech_matches = _REGEX_ALL_TECHS.findall(full_text)
        raw_tech_matches.update(tech_matches)

    normalized_tags = {
        TECH_REVERSE_MAP.get(tag.lower(), tag) for tag in raw_tech_matches
    }
    final_tags = sorted(list(normalized_tags))

    # --- 4. Lógica de Puntuación (Bonus y Penalizaciones) ---
    
    # 🚨 BLOQUEO CRÍTICO: SIN PERFIL NI SEÑALES IT
    if not found_profiles and not (it_signals_found or raw_tech_matches):
        details["penalties"].append({
            "key": "fatal_no_it",
            "label": "No IT Signals",
            "value": -50,
            "meta": []
        })
        details["score"] = 0
        details["quality_tier"] = "reject"
        return 0, details

    # BONUS: Seniority Jr/Trainee
    if has_positive_seniority:
        score += WEIGHTS["positive_seniority"]
        details["bonuses"].append({
            "key": "positive_seniority",
            "label": "Junior/Trainee Seniority",
            "value": WEIGHTS["positive_seniority"],
            "meta": sorted(list(set(positive_seniority_matches)))
        })

    # BONUS: Rol técnico claro (perfil encontrado)
    if final_roles:
        score += WEIGHTS["strong_role"]
        details["bonuses"].append({
            "key": "strong_role",
            "label": "Strong IT Role",
            "value": WEIGHTS["strong_role"],
            "meta": final_roles[:3]
        })

    # BONUS: Tecnologías encontradas
    if len(raw_tech_matches) > 1:
        if found_profiles:
            bonus = min(len(raw_tech_matches) * WEIGHTS["profile_tech"], 40)
            score += bonus
            details["bonuses"].append({
                "key": "profile_tech",
                "label": "Tech Stack Match",
                "value": bonus,
                "meta": sorted(raw_tech_matches)[:5]
            })
        else:
            bonus = min(len(raw_tech_matches) * WEIGHTS["global_tech"], 20)
            score += bonus
            details["bonuses"].append({
                "key": "global_tech",
                "label": "Tech Keywords",
                "value": bonus,
                "meta": sorted(raw_tech_matches)[:5]
            })

    # BONUS: Señales IT
    if len(it_signals_found) > 1:
        bonus = min(len(it_signals_found) * WEIGHTS["it_signal"], 5)
        score += bonus
        details["bonuses"].append({
            "key": "it_signals",
            "label": "IT Context Signals",
            "value": bonus,
            "meta": sorted(it_signals_found)[:10]
        })

    # BONUS: Combinación perfecta
    if found_profiles and has_positive_seniority and raw_tech_matches:
        score += WEIGHTS["perfect_match"]
        details["bonuses"].append({
            "key": "perfect_match",
            "label": "Perfect Match",
            "value": WEIGHTS["perfect_match"],
            "meta": []
        })

    # PENALIZACIONES

    # Penalización por experiencia senior explícita
    should_penalize_years, years_required = has_senior_experience_requirement(full_text)
    if (should_penalize_years or has_negative_seniority) and not has_positive_seniority:
        penalty = WEIGHTS["senior_experience"]
        score -= penalty
        
        meta_data = [years_required] if years_required else []
        if has_negative_seniority:
             meta_data.extend(sorted(list(set(negative_seniority_matches))))
        
        details["penalties"].append({
            "key": "senior_experience",
            "label": "Senior Experience Required",
            "value": -penalty,
            "meta": meta_data
        })

    # Penalización por rol ambiguo sin suficiente contexto
    if has_ambiguous_role and not (found_profiles or len(raw_tech_matches) > 1):
        penalty = WEIGHTS["ambiguous_no_context"]
        score -= penalty
        details["penalties"].append({
            "key": "ambiguous_no_context",
            "label": "Ambiguous Role",
            "value": -penalty,
            "meta": sorted(set(ambiguous_roles_found))
        })

    # --- 5. Finalización ---
    final_score = round(max(0, min(100, score)), 1)

    # Rellenar campos restantes del esqueleto
    details["score"] = final_score
    details["profiles"] = found_profiles
    details["roles"] = final_roles
    details["tags"] = final_tags

    if final_score >= 75:
        details["quality_tier"] = "excellent"
    elif final_score >= 60:
        details["quality_tier"] = "good"
    elif final_score >= 45:
        details["quality_tier"] = "review"
    else:
        details["quality_tier"] = "reject"

    return final_score, details


def has_senior_experience_requirement(text):
    """
    Detecta si requiere experiencia senior (>= MIN_YEARS_SENIORITY).
    """
    years_found = []
    for pattern in EXPERIENCE_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                if isinstance(match, tuple):
                    nums = [int(n) for n in match if n]
                    if len(nums) == 2:
                        min_years, max_years = nums
                        if 1 <= min_years < max_years <= 50:
                            years_found.append(min_years)
                    elif len(nums) == 1:
                        if 1 <= nums[0] <= 50:
                            years_found.append(nums[0])
                else:
                    years = int(match)
                    if 1 <= years <= 50:
                        years_found.append(years)
            except (ValueError, TypeError):
                continue
    if not years_found:
        return False, None
    max_years = max(years_found)
    is_senior = max_years >= MIN_YEARS_SENIORITY
    return is_senior, max_years


def filter_jobs_with_scoring(df, min_score=60, verbose=True):
    """
    Filtrado basado en pre-filtros y scoring. Devuelve jobs aceptados y rechazados.
    """
    if df.empty:
        if verbose:
            print("⚠️ Empty DataFrame, skipping filtering.")
        return df, pd.DataFrame()

    initial_total = len(df)

    # Pre-filtro (área + seniority)
    df_pre_filtered, df_rejected_pre_filter = pre_filter_jobs(df, verbose=verbose)

    # Asegurar que los rechazados por pre-filtro tengan el esqueleto de score_details
    if not df_rejected_pre_filter.empty:
        def get_rejection_details(reason):
            details = get_empty_score_details()
            details["penalties"].append({
                "key": "pre_filter_rejection",
                "label": f"Rejected by {reason.split(':')[0]}",
                "value": -50,
                "meta": [reason]
            })
            return details
        
        df_rejected_pre_filter["score"] = 0
        df_rejected_pre_filter["quality_tier"] = "reject"
        df_rejected_pre_filter["score_details"] = df_rejected_pre_filter["rejection_reason"].apply(get_rejection_details)

    if df_pre_filtered.empty:
        if verbose:
            print("⚠️ No jobs left after pre-filtering.")
        return df_pre_filtered, df_rejected_pre_filter

    # Scoring
    if verbose:
        print(f"\n📊 Calculating scores for {len(df_pre_filtered)} jobs...")

    df_scored = df_pre_filtered.copy()
    scores_and_details = df_scored.apply(calculate_job_score, axis=1)

    # Descartar los que devuelven None
    valid_results_mask = scores_and_details.notna()
    df_scored = df_scored[valid_results_mask]
    scores_and_details = scores_and_details[valid_results_mask]

    df_scored["score"] = [item[0] for item in scores_and_details]
    df_scored["score_details"] = [item[1] for item in scores_and_details]

    df_scored["quality_tier"] = df_scored["score_details"].apply(
        lambda x: x.get("quality_tier", "unknown")
    )

    # Filtrar por score mínimo
    df_final = df_scored[df_scored["score"] >= min_score].copy()
    df_rejected_score = df_scored[df_scored["score"] < min_score].copy()

    if not df_rejected_score.empty:
        df_rejected_score["rejection_reason"] = df_rejected_score.apply(
            lambda row: f"low_score: {row['score']:.0f}", axis=1
        )

    # Consolidar rechazados
    all_rejected = pd.concat(
        [df_rejected_pre_filter, df_rejected_score], ignore_index=True
    )

    # Ordenar por score
    df_final = df_final.sort_values("score", ascending=False).reset_index(drop=True)

    # Reporting
    if verbose:
        print(f"\n✅ Scoring completed!")
        print(f"   - Jobs passing score threshold (>={min_score}): {len(df_final)}")
        print(f"   - Jobs rejected by low score: {len(df_rejected_score)}")
        print(
            f"   - Total rejected: {len(all_rejected)} ({len(all_rejected)/initial_total*100:.1f}%)"
        )

        if not df_final.empty:
            print(f"\n📊 Score distribution:")
            print(
                f"   - Excellent (75-100): {(df_final['quality_tier'] == 'excellent').sum()}"
            )
            print(f"   - Good (60-74): {(df_final['quality_tier'] == 'good').sum()}")
            print(
                f"   - Review (45-59): {(df_final['quality_tier'] == 'review').sum()}"
            )

    return df_final, all_rejected
