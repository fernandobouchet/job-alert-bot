import pandas as pd
from filters_scoring_config.compiled_profiles import (
    COMPILED_PROFILES,
    TECH_REVERSE_MAP,
    ROLE_REVERSE_MAP,
    ROLE_TO_PROFILE_MAP,
)
from filters_scoring_config.compiled_regex import (
    _REGEX_ALL_ROLES,
    _REGEX_ALL_TECHS,
    _REGEX_AREA_PREFILTER,
    _REGEX_IT_SIGNALS,
    _REGEX_POSITIVE_SENIORITY,
    _REGEX_EXCLUDED_SENIORITY,
    _REGEX_WEAK_SIGNALS,
    COMPILED_EXPERIENCE_REGEX,
)
from filters_scoring_config.scoring import MIN_YEARS_SENIORITY

# --- CONFIGURACIÓN DE PESOS ---
WEIGHTS = {
    "base": 40,
    "positive_seniority": 20,
    "strong_role": 20,
    "profile_tech": 5,
    "global_tech": 3,
    "it_signal": 1,
    "perfect_match": 10,
    # Penalizaciones
    "senior_experience": 50,
    "ambiguous_no_context": 30,
    "weak_signal_only_penalty": 20,
}


def pre_filter_jobs(df, verbose=True):
    """
    Aplica filtros iniciales y devuelve tanto el DataFrame filtrado como los rechazados.
    Filtros aplicados:
    1. Área no-IT en título
    2. Seniority excluida en título (EXCEPTO si también menciona seniority positiva)
    Optimizado con operaciones vectorizadas de pandas.
    """
    if df.empty:
        return df, pd.DataFrame()

    initial_count = len(df)
    if verbose:
        print(f"\n🔍 Starting pre-filtering for {initial_count} jobs...")

    titles = df["title_normalized"].fillna("")

    # --- FILTRO 1: Área no-IT ---
    # Trigger: coincide con AREA_PREFILTER
    # Exception: coincide con ALL_ROLES o IT_SIGNALS

    # 1. Identificar filas que activan el filtro de Área (Candidatos a rechazo)
    mask_area_trigger = titles.str.contains(_REGEX_AREA_PREFILTER, regex=True)

    # 2. Check excepciones solo para los que activaron el trigger
    mask_reject_area = pd.Series(False, index=df.index)

    if mask_area_trigger.any():
        trigger_indices = mask_area_trigger[mask_area_trigger].index
        titles_subset = titles.loc[trigger_indices]

        # Check Role Exception
        mask_role_exception = titles_subset.str.contains(_REGEX_ALL_ROLES, regex=True)

        # Si encuentra rol, NO es rechazado. Si NO encuentra rol, chequear señal IT.
        indices_check_signal = mask_role_exception[~mask_role_exception].index

        mask_signal_exception = pd.Series(False, index=titles_subset.index)

        if not indices_check_signal.empty:
            mask_signal_exception.loc[indices_check_signal] = (
                titles.loc[indices_check_signal].str.contains(
                    _REGEX_IT_SIGNALS, regex=True
                )
            )

        # Exception es True si Role O Signal
        mask_exception = mask_role_exception | mask_signal_exception

        # Rechazar si Trigger Y NO Exception
        mask_reject_area.loc[trigger_indices] = ~mask_exception

    # --- FILTRO 2: Seniority ---
    # Trigger: coincide con EXCLUDED_SENIORITY
    # Exception: coincide con POSITIVE_SENIORITY
    # Condición: Aplicar solo si NO fue rechazado por Área

    mask_reject_seniority = pd.Series(False, index=df.index)

    # Miramos seniority solo en filas válidas hasta ahora
    valid_indices = mask_reject_area[~mask_reject_area].index

    if not valid_indices.empty:
        titles_valid = titles.loc[valid_indices]

        # Check Excluded Seniority
        mask_excluded = titles_valid.str.contains(
            _REGEX_EXCLUDED_SENIORITY, regex=True
        )

        if mask_excluded.any():
            excluded_indices = mask_excluded[mask_excluded].index
            # Check Positive Seniority Exception solo en estos
            mask_positive = titles.loc[excluded_indices].str.contains(
                _REGEX_POSITIVE_SENIORITY, regex=True
            )

            # Rechazar si Excluded Y NO Positive
            mask_reject_seniority.loc[excluded_indices] = ~mask_positive

    # Máscara final de rechazo
    rejected_mask = mask_reject_area | mask_reject_seniority

    df_rejected = df[rejected_mask].copy()
    df_filtered = df[~rejected_mask].copy()

    # --- Generación de Razones de Rechazo ---
    if not df_rejected.empty:
        reasons = pd.Series(index=df_rejected.index, dtype=object)

        # Rechazos por Área
        area_indices = mask_reject_area[mask_reject_area].index
        if not area_indices.empty:
            def get_area_reason(text):
                matches = _REGEX_AREA_PREFILTER.findall(text)
                return f"area: {', '.join(sorted(set(matches)))}"
            reasons.loc[area_indices] = (
                df_rejected.loc[area_indices, "title_normalized"]
                .apply(get_area_reason)
            )

        # Rechazos por Seniority
        sen_indices = mask_reject_seniority[mask_reject_seniority].index
        if not sen_indices.empty:
            def get_seniority_reason(text):
                matches = _REGEX_EXCLUDED_SENIORITY.findall(text)
                return f"seniority: {', '.join(sorted(set(matches)))}"
            reasons.loc[sen_indices] = (
                df_rejected.loc[sen_indices, "title_normalized"]
                .apply(get_seniority_reason)
            )

        df_rejected["rejection_reason"] = reasons

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
            f"   -> Total rejected: {len(df_rejected)} "
            f"({len(df_rejected)/initial_count*100:.1f}%)"
        )
        print(
            f"   -> Jobs remaining for scoring: {len(df_filtered)} "
            f"({len(df_filtered)/initial_count*100:.1f}%)"
        )

    return df_filtered, df_rejected


def get_empty_score_details():
    """
    Devuelve el esqueleto estándar para los detalles de puntuación.
    """
    return {
        "score": 0,
        "quality_tier": "reject",
        "base": WEIGHTS["base"],
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

    # OPTIMIZATION: Use search for boolean checks to avoid expensive findall on full text
    has_positive_seniority = bool(_REGEX_POSITIVE_SENIORITY.search(full_text))

    # Negative Seniority: Search ONLY in Title to avoid false positives in body
    has_negative_seniority = bool(_REGEX_EXCLUDED_SENIORITY.search(title))

    # Check positive seniority in TITLE specifically
    has_positive_seniority_in_title = bool(_REGEX_POSITIVE_SENIORITY.search(title))

    # --- 2. Categorización por Perfil y Roles ---
    found_profiles = []
    raw_role_matches = set()
    # Cache profile tech matches to avoid re-scanning in step 3
    profile_tech_cache = {}

    # OPTIMIZATION: Scan for ALL roles at once using the combined regex.
    # This avoids iterating through every profile and running a separate regex search for each.
    # Complexity reduction: O(num_profiles * text_len) -> O(text_len + matched_profiles * text_len)

    all_role_matches = _REGEX_ALL_ROLES.findall(full_text)

    # Identify potential profiles based on matches
    potential_profiles = set()
    # Use set to avoid redundant lookups for the same role mentioned multiple times
    for match in set(all_role_matches):
        # match is already lowercase because full_text is normalized
        profiles = ROLE_TO_PROFILE_MAP.get(match)
        if profiles:
            potential_profiles.update(profiles)

    # Only validate potential profiles
    for profile_name in potential_profiles:
        compiled_data = COMPILED_PROFILES[profile_name]

        # Profile Validation: Only keep profile if it has its specific tech
        profile_tech_matches = compiled_data["tech"].findall(full_text)

        if profile_tech_matches:
            found_profiles.append(profile_name)
            profile_tech_cache[profile_name] = profile_tech_matches

            # Extract only the role matches relevant to this profile
            # Since we already found ALL matches, we filter them for this profile.
            # This is faster than re-running regex.
            # Use set(all_role_matches) here for checking to optimize if list is long?
            # Actually, we need to add the matched terms to raw_role_matches.
            # Since raw_role_matches is a set, duplicates don't matter,
            # so iterating over unique matches is sufficient and faster.
            valid_roles_for_this_profile = [
                m for m in set(all_role_matches)
                if profile_name in ROLE_TO_PROFILE_MAP.get(m, [])
            ]
            raw_role_matches.update(valid_roles_for_this_profile)

    normalized_roles = {
        ROLE_REVERSE_MAP.get(role, role) for role in raw_role_matches
    }
    final_roles = sorted(list(normalized_roles))


    # --- 3. Obtención de Tecnologías y Señales ---
    raw_tech_matches = set()
    raw_signal_matches = set()

    if found_profiles:
        for profile_name in found_profiles:
            # Reuse cached tech matches (optimization)
            tech_matches = profile_tech_cache.get(profile_name, [])
            raw_tech_matches.update(tech_matches)
            signal_matches = COMPILED_PROFILES[profile_name]["signals"].findall(full_text)
            raw_signal_matches.update(signal_matches)
    else:
        tech_matches = _REGEX_ALL_TECHS.findall(full_text)
        raw_tech_matches.update(tech_matches)

    # Combine tech and signals for scoring purposes
    raw_all_matches = raw_tech_matches | raw_signal_matches

    weak_tech_matches = set(_REGEX_WEAK_SIGNALS.findall(full_text))

    strong_tech_matches = raw_all_matches - weak_tech_matches

    normalized_tags = {
        TECH_REVERSE_MAP.get(tag, tag) for tag in raw_tech_matches
    }
    final_tags = sorted(list(normalized_tags))

    # Determine if it's a valid IT job
    is_it_job = bool(found_profiles) or (len(strong_tech_matches) >= 2 and bool(it_signals_found))

    # --- 4. Lógica de Puntuación (Bonus y Penalizaciones) ---

    # 🚨 BLOQUEO CRÍTICO: SIN PERFIL NI SEÑALES IT
    if not is_it_job:
        if weak_tech_matches:
            penalty = WEIGHTS["weak_signal_only_penalty"]
            score -= penalty
            details["penalties"].append({
                "key": "weak_signal_only",
                "label": "Only Weak Signals",
                "value": -penalty,
                "meta": sorted(list(weak_tech_matches))[:5]
            })
        else:
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
    if has_positive_seniority and is_it_job:
        positive_seniority_matches = _REGEX_POSITIVE_SENIORITY.findall(full_text)
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

    # BONUS: Tecnologías encontradas (tech + signals for scoring)
    techs_for_bonus = raw_all_matches if found_profiles else strong_tech_matches

    if len(techs_for_bonus) > 0:
        if found_profiles:
            bonus = min(len(techs_for_bonus) * WEIGHTS["profile_tech"], 25)
            score += bonus
            details["bonuses"].append({
                "key": "profile_tech",
                "label": "Tech Stack Match",
                "value": bonus,
                "meta": sorted(techs_for_bonus)[:5]
            })
        else:
            bonus = min(len(techs_for_bonus) * WEIGHTS["global_tech"], 15)
            score += bonus
            details["bonuses"].append({
                "key": "global_tech",
                "label": "Tech Keywords",
                "value": bonus,
                "meta": sorted(techs_for_bonus)[:5]
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
    if found_profiles and has_positive_seniority and raw_all_matches:
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

    # Decide if we should apply seniority penalty
    # 1. If years are explicitly high, we penalize UNLESS the title says Junior (strong override).
    #    We ignore "junior" in the body because it often refers to "mentoring juniors".
    # 2. If title has negative seniority (Senior/Manager),
    #    we penalize UNLESS the title ALSO says Junior (contradiction/hybrid).

    apply_seniority_penalty = False

    if should_penalize_years:
        if not has_positive_seniority_in_title:
            apply_seniority_penalty = True
    elif has_negative_seniority:
        if not has_positive_seniority_in_title:
            apply_seniority_penalty = True

    if apply_seniority_penalty:
        penalty = WEIGHTS["senior_experience"]
        score -= penalty

        meta_data = [years_required] if years_required else []
        if has_negative_seniority:
            negative_seniority_matches = _REGEX_EXCLUDED_SENIORITY.findall(title)
            meta_data.extend(sorted(list(set(negative_seniority_matches))))

        details["penalties"].append({
            "key": "senior_experience",
            "label": "Senior Experience Required",
            "value": -penalty,
            "meta": meta_data
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
    Optimized: Uses a single combined regex scan instead of iterating multiple patterns.
    Assumes input text is already normalized to lowercase.
    """
    years_found = []
    # findall with combined regex returns a list of tuples (one group per capturing group in the whole regex)
    matches = COMPILED_EXPERIENCE_REGEX.findall(text)

    for match in matches:
        nums = []
        # Flatten the tuple and find all non-empty digit strings
        if isinstance(match, tuple):
            for group in match:
                if group:
                    try:
                        nums.append(int(group))
                    except ValueError:
                        pass
        elif match:  # Fallback if regex has only one group (though here it has many)
            try:
                nums.append(int(match))
            except ValueError:
                pass

        if not nums:
            continue

        # Logic inference:
        # If 2 numbers found -> Range (min-max). Use min.
        # If 1 number found -> Single value (min/required). Use it.
        if len(nums) == 2:
            min_years, max_years = nums
            if 1 <= min_years < max_years <= 50:
                years_found.append(min_years)
        elif len(nums) == 1:
            if 1 <= nums[0] <= 50:
                years_found.append(nums[0])

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
        df_rejected_pre_filter["score_details"] = df_rejected_pre_filter[
            "rejection_reason"
        ].apply(get_rejection_details)

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
            f"   - Total rejected: {len(all_rejected)} "
            f"({len(all_rejected)/initial_total*100:.1f}%)"
        )

        if not df_final.empty:
            print(f"\n📊 Score distribution:")
            print(
                f"   - Excellent (75-100): "
                f"{(df_final['quality_tier'] == 'excellent').sum()}"
            )
            print(f"   - Good (60-74): {(df_final['quality_tier'] == 'good').sum()}")
            print(
                f"   - Review (45-59): {(df_final['quality_tier'] == 'review').sum()}"
            )

    return df_final, all_rejected
