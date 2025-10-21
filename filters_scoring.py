import pandas as pd
import re
from filters_scoring_config import (
    AMBIGUOUS_ROLES,
    POSITIVE_SENIORITY_TERMS,
    EXCLUDED_SENIORITYS,
    EXCLUDED_AREA_TERMS_TITLE,
    EXCLUDED_EXPERIENCE_PHRASES,
    REQUIRED_IT_SIGNALS,
    STRONG_ROLE_SIGNALS,
    STRONG_TECH_SIGNALS,
)
from json_handler import save_json
from config import LOG_REJECTED_JOBS


print("🔄 Compiling regex patterns from config...")


_REGEX_AREA_PREFILTER = re.compile(
    r"\b(?:" + "|".join(re.escape(t) for t in EXCLUDED_AREA_TERMS_TITLE) + r")",
    re.IGNORECASE,
)

_REGEX_SENIORITY_EXCLUDED = re.compile(
    r"\b(?:" + "|".join(re.escape(s) for s in EXCLUDED_SENIORITYS) + r")",
    re.IGNORECASE,
)

_REGEX_POSITIVE_SENIORITY = re.compile(
    r"\b(?:" + "|".join(re.escape(s) for s in POSITIVE_SENIORITY_TERMS) + r")",
    re.IGNORECASE,
)

_REGEX_PREFILTER_COMBINED = re.compile(
    f"{_REGEX_AREA_PREFILTER.pattern}|{_REGEX_SENIORITY_EXCLUDED.pattern}",
    re.IGNORECASE,
)

_REGEX_EXPERIENCE = re.compile(
    "|".join(re.escape(e) for e in EXCLUDED_EXPERIENCE_PHRASES), re.IGNORECASE
)

_REGEX_IT_SIGNALS = re.compile(
    "|".join(r"(?<!\w)" + re.escape(s) + r"(?!\w)" for s in REQUIRED_IT_SIGNALS),
    re.IGNORECASE,
)

_REGEX_STRONG_ROLE_SIGNALS = re.compile(
    r"\b(?:" + "|".join(re.escape(s) for s in STRONG_ROLE_SIGNALS) + r")",
    re.IGNORECASE,
)

_REGEX_STRONG_TECH_SIGNALS = re.compile(
    "|".join(r"(?<!\w)" + re.escape(s) + r"(?!\w)" for s in STRONG_TECH_SIGNALS),
    re.IGNORECASE,
)


_REGEX_AMBIGUOUS_ROLES = re.compile(
    r"\b(?:" + "|".join(re.escape(s) for s in AMBIGUOUS_ROLES) + r")",
    re.IGNORECASE,
)

print("✅ Regex patterns compiled")


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
    mask_reject = df["title"].str.contains(_REGEX_PREFILTER_COMBINED, na=False)
    df_rejected = df[mask_reject].copy()
    df_filtered = df[~mask_reject].copy()

    # Añadir razón de rechazo (el término específico que causó el rechazo)
    if not df_rejected.empty:
        df_rejected["rejection_reason"] = df_rejected["title"].apply(
            lambda x: f"pre-filter: {', '.join(set(_REGEX_PREFILTER_COMBINED.findall(x)))}"
        )

    rejected_count = len(df_rejected)
    if verbose:
        print(f"   - Rejected by Area/Seniority: {rejected_count} jobs")
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
    strong_it_signals_found = set(_REGEX_STRONG_TECH_SIGNALS.findall(full_text))
    has_ambiguous_role = set(_REGEX_AMBIGUOUS_ROLES.findall(title))

    # ===== 1. SENIORITY SCORING (POSITIVO Y NEGATIVO) =====

    # ✅ Puntuación positiva para términos Junior/Trainee en el título (SOLO SI HAY SEÑALES IT)
    if len(it_signals_found) >= 2:
        if _REGEX_POSITIVE_SENIORITY.search(title):
            score += 25
            score_details["bonus_seniority"] = 25

    # ❌ Penalización fuerte para términos Senior/Lead en el título
    if _REGEX_SENIORITY_EXCLUDED.search(title):
        penalty = 40
        score -= penalty
        score_details["penalty_seniority"] = -penalty

    if _REGEX_STRONG_ROLE_SIGNALS.search(title):
        score += 20
        score_details["strong_role_signal"] = 20

    # ===== 2. IT SIGNALS SCORING (CON PENALIZACIÓN) =====

    if it_signals_found:
        bonus = min(len(it_signals_found) * 5, 40)
        score += bonus
        score_details["bonus_it_signals"] = bonus
        score_details["it_signals_found"] = list(it_signals_found)
    else:
        penalty = 25
        score -= penalty
        score_details["penalty_no_it_signals"] = -penalty

    if strong_it_signals_found:
        bonus = min(len(strong_it_signals_found) * 10, 20)
        score += bonus
        score_details["bonus_strong_it_signals"] = bonus
        score_details["strong_it_signals_found"] = list(strong_it_signals_found)

    if has_ambiguous_role and not it_signals_found:
        penalty = 15
        score -= penalty
        score_details["penalty_ambiguous_role"] = -penalty

    # ===== 3. EXPERIENCE PENALTY =====

    if _REGEX_EXPERIENCE.search(description):
        penalty = 20
        score -= penalty
        score_details["penalty_experience"] = -penalty

    # Limitar score entre 0 y 100
    final_score = max(0, min(100, score))

    return final_score, score_details


def filter_jobs_with_scoring(df, min_score=50, verbose=True):
    """
    Filtrado basado en pre-filtros y scoring, con detalle de rechazo.
    """
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
