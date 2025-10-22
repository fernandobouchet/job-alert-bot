import pandas as pd
from constants import (
    _REGEX_AMBIGUOUS_ROLES,
    _REGEX_AREA_PREFILTER,
    _REGEX_EXPERIENCE,
    _REGEX_IT_SIGNALS,
    _REGEX_POSITIVE_SENIORITY,
    _REGEX_SENIORITY_EXCLUDED,
    _REGEX_STRONG_ROLE_SIGNALS,
    _REGEX_STRONG_TECH_SIGNALS,
    _REGEX_WEAK_IT_SIGNALS,
)
from json_handler import save_json, handle_rejected_jobs_file
from config import LOG_REJECTED_JOBS


def pre_filter_jobs(df, verbose=True):
    """
    Aplica filtros iniciales y devuelve tanto el DataFrame filtrado como los rechazados.
    """
    if df.empty:
        return df, pd.DataFrame()

    initial_count = len(df)
    if verbose:
        print(f"\n🔍 Starting pre-filtering for {initial_count} jobs...")

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
    Sistema de scoring 0-100.
    Devuelve el score y un diccionario con los detalles del scoring.
    """
    score = 50
    score_details = {"base": 50}

    title = str(row.get("title", "")).lower()
    description = str(row.get("description", "")).lower()
    full_text = f"{title} {description}"

    it_signals_found = set(_REGEX_IT_SIGNALS.findall(full_text))
    weak_it_signals_found = set(_REGEX_WEAK_IT_SIGNALS.findall(full_text))
    strong_it_signals_found = set(_REGEX_STRONG_TECH_SIGNALS.findall(full_text))
    strong_role_found = set(_REGEX_STRONG_ROLE_SIGNALS.findall(title))
    has_ambiguous_role = set(_REGEX_AMBIGUOUS_ROLES.findall(title))

    all_signals_found = it_signals_found.union(weak_it_signals_found)

    # ===== 1. NOT IT SIGNALS OR WEAKS_SIGNALS ONLY =====
    if not all_signals_found:
        score = 0
        score_details["fatal_no_it_signals"] = True
        score_details["reason"] = "No IT signals found"
        return 0, score_details

    if weak_it_signals_found and not it_signals_found and not strong_it_signals_found:
        penalty = 35
        score -= penalty
        score_details["penalty_only_weak_signals"] = -penalty

    # ===== 2. SENIORITY SCORING (POSITIVO Y NEGATIVO) =====

    # ✅ Bonus por junior (SOLO si hay señales IT fuertes)
    if len(it_signals_found) >= 1 or strong_it_signals_found:
        if _REGEX_POSITIVE_SENIORITY.search(title):
            bonus = 20
            score += bonus
            score_details["bonus_seniority"] = bonus

    # ❌ Penalización fuerte para términos Senior/Lead en el título
    if _REGEX_SENIORITY_EXCLUDED.search(title):
        penalty = 50
        score -= penalty
        score_details["penalty_seniority"] = -penalty

    # ✅ Puntuación positiva roles fuertes
    if strong_role_found:
        bonus = 15
        score += bonus
        score_details["strong_role_signal"] = bonus

    # ===== 3. IT SIGNALS SCORING (CON PENALIZACIÓN) =====
    if it_signals_found:
        # 3 puntos por señal IT
        bonus = min(len(it_signals_found) * 3, 30)  # Max 30
        score += bonus
        score_details["bonus_it_signals"] = bonus
        score_details["it_signals_found"] = list(it_signals_found)[:10]  # Top 10

    if weak_it_signals_found:
        # 0.5 por señal débil
        bonus = min(len(weak_it_signals_found) * 0.5, 5)
        score += bonus
        score_details["bonus_weak_signals"] = bonus

    if strong_it_signals_found:
        # 10 puntos por tech fuerte
        bonus = min(len(strong_it_signals_found) * 10, 25)  # Max 25
        score += bonus
        score_details["bonus_strong_tech"] = bonus
        score_details["strong_tech_found"] = list(strong_it_signals_found)[:5]

    # ===== ROLES AMBIGUOS =====
    if has_ambiguous_role and not strong_it_signals_found and len(it_signals_found) < 2:
        penalty = 25
        score -= penalty
        score_details["penalty_ambiguous"] = -penalty

    # ===== EXPERIENCE =====
    if _REGEX_EXPERIENCE.search(description):
        penalty = 15
        score -= penalty
        score_details["penalty_experience"] = -penalty

    # Limitar score entre 0 y 100
    final_score = max(0, min(100, score))

    return final_score, score_details


def filter_jobs_with_scoring(df, min_score=50, verbose=True):
    """
    Filtrado basado en pre-filtros y scoring, con detalle de rechazo.
    """
    handle_rejected_jobs_file(LOG_REJECTED_JOBS, verbose=verbose)

    if df.empty:
        if verbose:
            print("⚠️ Empty DataFrame, skipping filtering.")
        return df

    initial_total = len(df)

    df_pre_filtered, df_rejected_pre_filter = pre_filter_jobs(df, verbose=verbose)

    if df_pre_filtered.empty:
        if verbose:
            print("⚠️ No jobs left after pre-filtering.")
        if LOG_REJECTED_JOBS and not df_rejected_pre_filter.empty:
            save_json(
                df_rejected_pre_filter.to_dict("records"), "data/rejected_jobs.json"
            )
            print(
                f"💾 Saved {len(df_rejected_pre_filter)} rejected jobs to data/rejected_jobs.json"
            )
        return df_pre_filtered

    if verbose:
        print(f"\n📊 Calculating scores for {len(df_pre_filtered)} jobs...")

    df_scored = df_pre_filtered.copy()
    # Aplicar la función y desempaquetar los resultados en dos nuevas columnas
    scores_and_details = df_scored.apply(calculate_job_score, axis=1)
    df_scored["score"] = [item[0] for item in scores_and_details]
    df_scored["score_details"] = [item[1] for item in scores_and_details]

    df_final = df_scored[df_scored["score"] >= min_score].copy()

    # Capturar los trabajos rechazados por score
    df_rejected_score = df_scored[df_scored["score"] < min_score].copy()
    df_rejected_score["rejection_reason"] = "low_score"

    if LOG_REJECTED_JOBS:
        # Combinar ambos dataframes de rechazados
        all_rejected = pd.concat(
            [df_rejected_pre_filter, df_rejected_score], ignore_index=True
        )
        if not all_rejected.empty:
            save_json(all_rejected.to_dict("records"), "data/rejected_jobs.json")
            if verbose:
                print(
                    f"💾 Saved {len(all_rejected)} rejected jobs to data/rejected_jobs.json"
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

    return df_final
