import pandas as pd
import re
from constants import (
    _REGEX_AMBIGUOUS_ROLES,
    _REGEX_AREA_PREFILTER,
    _REGEX_IT_SIGNALS,
    _REGEX_POSITIVE_SENIORITY,
    _REGEX_SENIORITY_EXCLUDED,
    _REGEX_STRONG_ROLE_SIGNALS,
    _REGEX_STRONG_TECH_SIGNALS,
    _REGEX_WEAK_IT_SIGNALS,
)
from filters_scoring_config import MIN_YEARS_SENIORITY, SENIOR_EXPERIENCE_PATTERNS



def pre_filter_jobs(df, verbose=True):
    """
    Aplica filtros iniciales y devuelve tanto el DataFrame filtrado como los rechazados.
    """
    if df.empty:
        return df, pd.DataFrame()

    initial_count = len(df)
    if verbose:
        print(f"\\n🔍 Starting pre-filtering for {initial_count} jobs...")

    # Identificar trabajos a rechazar
    mask_reject = df["title"].str.contains(_REGEX_AREA_PREFILTER, na=False)
    df_rejected = df[mask_reject].copy()
    df_filtered = df[~mask_reject].copy()

    # Añadir razón de rechazo (el término específico que causó el rechazo)
    if not df_rejected.empty:
        df_rejected["rejection_reason"] = df_rejected["title"].apply(
            lambda x: f"pre-filter: {', '.join(set(_REGEX_AREA_PREFILTER.findall(x)))}"
        )

    rejected_count = len(df_rejected)
    if verbose:
        print(f"   - Rejected by Area: {rejected_count} jobs")
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
    strong_role_found = bool(
        _REGEX_STRONG_ROLE_SIGNALS.search(title)
    )  # ✅ bool() más claro
    has_ambiguous_role = bool(_REGEX_AMBIGUOUS_ROLES.search(title))
    has_positive_seniority = bool(_REGEX_POSITIVE_SENIORITY.search(full_text))

    all_signals = it_signals_found.union(weak_it_signals_found)

    # ===== 🚨 BLOQUEO: SIN SEÑALES IT =====
    if not all_signals:
        score_details["fatal_no_it_signals"] = True
        score_details["reason"] = "No IT signals found"
        return 0, score_details

    # ===== ⚠️ PENALIZACIÓN: SOLO señales débiles (sin contexto junior) =====
    if (
        weak_it_signals_found
        and not it_signals_found
        and not strong_tech_signals_found
        and not has_positive_seniority
    ):
        penalty = 35
        score -= penalty
        score_details["penalty_only_weak_signals"] = -penalty

    # ===== SENIORITY =====

    # ✅ Bonus por junior (solo si tiene señales IT reales)
    if (it_signals_found or strong_tech_signals_found) and has_positive_seniority:
        bonus = 20
        score += bonus
        score_details["bonus_seniority"] = bonus

    # ❌ Penalización FUERTE por senior
    if _REGEX_SENIORITY_EXCLUDED.search(title):
        penalty = 50  # Muy fuerte - casi garantiza rechazo
        score -= penalty
        score_details["penalty_seniority"] = -penalty

    # ===== ROLES FUERTES =====
    if strong_role_found:
        bonus = 15
        score += bonus
        score_details["strong_role_signal"] = bonus
        score_details["strong_roles_found"] = list(
            _REGEX_STRONG_ROLE_SIGNALS.findall(title)
        )[:3]

    # ===== IT SIGNALS =====

    if it_signals_found:
        bonus = min(len(it_signals_found) * 3, 30)  # 3 puntos c/u, max 30
        score += bonus
        score_details["bonus_it_signals"] = bonus
        score_details["it_signals_count"] = len(it_signals_found)
        score_details["it_signals_found"] = sorted(list(it_signals_found))[
            :10
        ]  # ✅ Sorted

    if weak_it_signals_found:
        bonus = min(len(weak_it_signals_found) * 0.5, 5)  # 0.5 puntos c/u, max 5
        score += bonus
        score_details["bonus_weak_signals"] = bonus
        score_details["weak_signals_found"] = sorted(list(weak_it_signals_found))

    if strong_tech_signals_found:
        bonus = min(len(strong_tech_signals_found) * 10, 25)  # 10 puntos c/u, max 25
        score += bonus
        score_details["bonus_strong_tech"] = bonus
        score_details["strong_tech_count"] = len(strong_tech_signals_found)
        score_details["strong_tech_found"] = sorted(list(strong_tech_signals_found))[:5]

    # ===== PENALIZACIÓN: MUY POCAS SEÑALES =====
    # Si tiene <2 señales IT Y no tiene tech fuerte → probablemente falso positivo
    if len(it_signals_found) < 2 and not strong_tech_signals_found:
        penalty = 15
        score -= penalty
        score_details["penalty_few_signals"] = -penalty

    # ===== ROLES AMBIGUOS =====
    # Penalizar si es ambiguo SIN señales fuertes NI junior explícito
    if (
        has_ambiguous_role
        and not strong_tech_signals_found
        and len(it_signals_found) < 2
        and not has_positive_seniority
    ):
        penalty = 25
        score -= penalty
        score_details["penalty_ambiguous"] = -penalty
        score_details["ambiguous_roles_found"] = list(
            _REGEX_AMBIGUOUS_ROLES.findall(title)
        )[:3]

    # ===== EXPERIENCIA =====

    should_penalize, years_required = has_senior_experience_requirement(
        full_text, has_positive_seniority
    )

    if should_penalize:
        penalty = 15
        score -= penalty
        score_details["penalty_experience"] = -penalty
        score_details["years_required"] = years_required

    # ===== BONUS ADICIONAL: Múltiples señales de calidad =====
    # Bonus por tener MUCHAS señales (job muy bien descrito)
    total_strong_signals = len(it_signals_found) + len(strong_tech_signals_found)
    if total_strong_signals >= 5:
        bonus = min(total_strong_signals - 4, 10)  # Max 10 bonus
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

    # Si encontró requerimiento senior
    if found_senior_req:
        # Pero también tiene términos junior → anuncio multi-nivel, no penalizar
        if has_junior_terms:
            return False, max_years_found
        else:
            return True, max_years_found  # Sí penalizar

    return False, 0


def filter_jobs_with_scoring(df, min_score=50, verbose=True):
    """
    Filtrado basado en pre-filtros y scoring. Devuelve jobs aceptados y rechazados.
    """
    if df.empty:
        if verbose:
            print("⚠️ Empty DataFrame, skipping filtering.")
        return df, pd.DataFrame()  # Devuelve dos dataframes vacíos

    initial_total = len(df)

    df_pre_filtered, df_rejected_pre_filter = pre_filter_jobs(df, verbose=verbose)

    if df_pre_filtered.empty:
        if verbose:
            print("⚠️ No jobs left after pre-filtering.")
        return df_pre_filtered, df_rejected_pre_filter

    if verbose:
        print(f"\n📊 Calculating scores for {len(df_pre_filtered)} jobs...")

    df_scored = df_pre_filtered.copy()
    scores_and_details = df_scored.apply(calculate_job_score, axis=1)
    df_scored["score"] = [item[0] for item in scores_and_details]
    df_scored["score_details"] = [item[1] for item in scores_and_details]

    df_final = df_scored[df_scored["score"] >= min_score].copy()

    df_rejected_score = df_scored[df_scored["score"] < min_score].copy()
    if not df_rejected_score.empty:
        df_rejected_score.loc[:, "rejection_reason"] = "low_score"

    all_rejected = pd.concat(
        [df_rejected_pre_filter, df_rejected_score], ignore_index=True
    )

    df_final = df_final.sort_values("score", ascending=False).reset_index(drop=True)

    if verbose:
        final_count = len(df_final)
        initial_after_prefilter = len(df_scored)
        rejected_by_score_count = initial_after_prefilter - final_count

        print(f"\n📈 Score distribution (on {initial_after_prefilter} jobs):")
        if initial_after_prefilter > 0:
            print(
                f"   - Max: {df_scored['score'].max():.0f}, Mean: {df_scored['score'].mean():.1f}, Min: {df_scored['score'].min():.0f}"
            )

        print(f"\n✅ Filtering complete:")
        print(f"   - Initial jobs: {initial_total}")
        print(f"   - Jobs after pre-filtering: {initial_after_prefilter}")
        print(f"   - Rejected by low score (<{min_score}): {rejected_by_score_count}")
        print(
            f"   - Final jobs passed: {final_count} ({final_count/initial_total*100:.1f}% of total)"
        )

        if final_count > 0:
            print(f"\n⭐ Final score distribution (for jobs with score ≥{min_score}):")
            print(
                f"   - Max: {df_final['score'].max():.0f}, Mean: {df_final['score'].mean():.1f}, Min: {df_final['score'].min():.0f}"
            )

    return df_final, all_rejected
