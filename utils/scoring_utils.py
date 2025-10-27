import pandas as pd
import re
from filters_scoring_config import MIN_YEARS_SENIORITY, SENIOR_EXPERIENCE_PATTERNS
from utils.constants import (
    _REGEX_AMBIGUOUS_ROLES,
    _REGEX_AREA_PREFILTER,
    _REGEX_IT_SIGNALS,
    _REGEX_POSITIVE_SENIORITY,
    _REGEX_SENIORITY_EXCLUDED,
    _REGEX_STRONG_ROLE_SIGNALS,
    _REGEX_STRONG_TECH_SIGNALS,
    _REGEX_WEAK_IT_SIGNALS,
)


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
        title = str(row.get("title", "")).lower()
        rejection_reason = None

        # FILTRO 1: Área no-IT
        if _REGEX_AREA_PREFILTER.search(title):
            matches = _REGEX_AREA_PREFILTER.findall(title)
            rejection_reason = f"area: {', '.join(sorted(set(matches)))}"

        # FILTRO 2: Seniority (solo si pasó filtro de área)
        elif _REGEX_SENIORITY_EXCLUDED.search(title):
            # Verificar si también tiene términos junior
            if not _REGEX_POSITIVE_SENIORITY.search(title):
                matches = _REGEX_SENIORITY_EXCLUDED.findall(title)
                rejection_reason = f"seniority: {', '.join(sorted(set(matches)))}"

        if rejection_reason:
            rejected_indices.append(idx)
            rejection_reasons[idx] = rejection_reason

    # Crear DataFrames
    if rejected_indices:
        df_rejected = df.loc[rejected_indices].copy()
        df_rejected["rejection_reason"] = df_rejected.index.map(rejection_reasons)
        df_filtered = df[~df.index.isin(rejected_indices)].copy()
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


def calculate_job_score(row):
    """
    Sistema de scoring 0-100 optimizado.

    Escala:
    - 80-100: Excelente (junior IT clarísimo)
    - 65-79: Bueno (junior IT válido)
    - 50-64: Aceptable (revisar)
    - 30-49: Dudoso
    - 0-29: Rechazar
    """
    score = 50
    score_details = {"base": 50}

    title = str(row.get("title", "")).lower()
    description = str(row.get("description", "")).lower()
    full_text = f"{title} {description}"

    # Detectar señales
    it_signals_found = set(_REGEX_IT_SIGNALS.findall(full_text))
    weak_it_signals_found = set(_REGEX_WEAK_IT_SIGNALS.findall(full_text))
    strong_tech_signals_found = set(_REGEX_STRONG_TECH_SIGNALS.findall(full_text))
    strong_role_found = bool(_REGEX_STRONG_ROLE_SIGNALS.search(title))
    has_ambiguous_role = bool(_REGEX_AMBIGUOUS_ROLES.search(title))
    has_positive_seniority = bool(_REGEX_POSITIVE_SENIORITY.search(full_text))

    all_signals = it_signals_found | weak_it_signals_found

    # ===== 🚨 BLOQUEO: SIN SEÑALES IT =====
    if not all_signals:
        score_details["fatal_no_it_signals"] = True
        score_details["reason"] = "No IT signals found"
        return 0, score_details

    # ===== ⚠️ PENALIZACIÓN: SOLO señales débiles  =====
    if (
        weak_it_signals_found
        and not it_signals_found
        and not strong_tech_signals_found
        and not has_positive_seniority
        and not strong_role_found
    ):
        penalty = 25
        score -= penalty
        score_details["penalty_only_weak_signals"] = -penalty

    # ===== SENIORITY =====
    # Bonus por junior (solo si tiene señales IT reales)
    if (it_signals_found or strong_tech_signals_found) and has_positive_seniority:
        bonus = 20
        score += bonus
        score_details["bonus_seniority"] = bonus

    # ===== ROLES FUERTES =====
    if strong_role_found:
        bonus = 15
        score += bonus
        score_details["strong_role_signal"] = bonus
        score_details["strong_roles_found"] = sorted(
            _REGEX_STRONG_ROLE_SIGNALS.findall(title)
        )[:3]

    # ===== IT SIGNALS =====
    if it_signals_found:
        bonus = min(len(it_signals_found) * 2, 20)
        score += bonus
        score_details["bonus_it_signals"] = bonus
        score_details["it_signals_count"] = len(it_signals_found)
        score_details["it_signals_found"] = sorted(it_signals_found)[:10]

    if weak_it_signals_found:
        bonus = min(len(weak_it_signals_found) * 0.5, 5)
        score += bonus
        score_details["bonus_weak_signals"] = bonus
        score_details["weak_signals_found"] = sorted(weak_it_signals_found)

    if strong_tech_signals_found:
        bonus = min(len(strong_tech_signals_found) * 12, 30)
        score += bonus
        score_details["bonus_strong_tech"] = bonus
        score_details["strong_tech_count"] = len(strong_tech_signals_found)
        score_details["strong_tech_found"] = sorted(strong_tech_signals_found)[:5]

    # ===== PENALIZACIÓN: MUY POCAS SEÑALES =====
    if len(it_signals_found) < 2 and not strong_tech_signals_found:
        penalty = 15
        score -= penalty
        score_details["penalty_few_signals"] = -penalty

    # ===== ROLES AMBIGUOS =====
    if (
        has_ambiguous_role
        and not strong_tech_signals_found
        and len(it_signals_found) < 2
        and not has_positive_seniority
    ):
        penalty = 25
        score -= penalty
        score_details["penalty_ambiguous"] = -penalty
        score_details["ambiguous_roles_found"] = sorted(
            _REGEX_AMBIGUOUS_ROLES.findall(title)
        )[:3]

    # ===== EXPERIENCIA =====
    should_penalize, years_required = has_senior_experience_requirement(
        full_text, has_positive_seniority
    )

    if should_penalize:
        penalty = 20
        score -= penalty
        score_details["penalty_experience"] = -penalty
        score_details["years_required"] = years_required

    # ===== BONUS: Múltiples señales de calidad =====
    total_strong_signals = len(it_signals_found) + len(strong_tech_signals_found)
    if total_strong_signals >= 5:
        bonus = min(total_strong_signals - 4, 10)
        score += bonus
        score_details["bonus_rich_description"] = bonus

    # Limitar entre 0-100
    final_score = max(0, min(100, score))

    # Agregar categoría para fácil filtrado
    if final_score >= 80:
        score_details["quality_tier"] = "excellent"
    elif final_score >= 65:
        score_details["quality_tier"] = "good"
    elif final_score >= 50:
        score_details["quality_tier"] = "review"
    else:
        score_details["quality_tier"] = "reject"

    return final_score, score_details


def has_senior_experience_requirement(text, has_junior_terms):
    """
    Detecta si pide experiencia senior (>=3 años).
    NO penaliza si también menciona términos junior (anuncio multi-nivel).
    """
    found_senior_req = False
    max_years_found = 0

    for pattern in SENIOR_EXPERIENCE_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                years = int(match)
                max_years_found = max(max_years_found, years)
                if years >= MIN_YEARS_SENIORITY:
                    found_senior_req = True
                    break
            except (ValueError, TypeError):
                continue
        if found_senior_req:
            break

    # Si encontró requerimiento senior pero también tiene términos junior
    # → anuncio multi-nivel, no penalizar
    if found_senior_req and not has_junior_terms:
        return True, max_years_found

    return False, max_years_found if found_senior_req else 0


def filter_jobs_with_scoring(df, min_score=50, verbose=True):
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

    if df_pre_filtered.empty:
        if verbose:
            print("⚠️ No jobs left after pre-filtering.")
        return df_pre_filtered, df_rejected_pre_filter

    # Scoring
    if verbose:
        print(f"\n📊 Calculating scores for {len(df_pre_filtered)} jobs...")

    df_scored = df_pre_filtered.copy()
    scores_and_details = df_scored.apply(calculate_job_score, axis=1)
    df_scored["score"] = [item[0] for item in scores_and_details]
    df_scored["score_details"] = [item[1] for item in scores_and_details]

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
        final_count = len(df_final)
        initial_after_prefilter = len(df_scored)
        rejected_by_score_count = initial_after_prefilter - final_count

        print(f"\n📈 Score distribution (on {initial_after_prefilter} jobs):")
        if initial_after_prefilter > 0:
            print(
                f"   - Max: {df_scored['score'].max():.0f}, "
                f"Mean: {df_scored['score'].mean():.1f}, "
                f"Min: {df_scored['score'].min():.0f}"
            )

        print(f"\n✅ Filtering complete:")
        print(f"   - Initial jobs: {initial_total}")
        print(f"   - After pre-filtering: {initial_after_prefilter}")
        print(f"   - Rejected by low score (<{min_score}): {rejected_by_score_count}")
        print(
            f"   - Final jobs passed: {final_count} "
            f"({final_count/initial_total*100:.1f}% of total)"
        )

        if final_count > 0:
            print(f"\n⭐ Final score distribution (jobs with score ≥{min_score}):")
            print(
                f"   - Max: {df_final['score'].max():.0f}, "
                f"Mean: {df_final['score'].mean():.1f}, "
                f"Min: {df_final['score'].min():.0f}"
            )

    return df_final, all_rejected
