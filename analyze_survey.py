from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
SURVEY_PATH = BASE_DIR / "anketa191776-2026-04-10.xlsx"
OFFICIAL_CODES_PATH = BASE_DIR.parent / "Uporabniki - kode.xlsx"
OUTPUT_DIR = BASE_DIR / "analysis_outputs"


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    text = "".join(
        char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char)
    )
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


def clean_code(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return re.sub(r"\.0$", "", text)


def load_official_codes() -> pd.DataFrame:
    raw = pd.read_excel(OFFICIAL_CODES_PATH).iloc[1:].copy()
    raw.columns = ["Predmet", "Koda", "Poslano", "Opazovani_CV"]
    raw["Koda"] = raw["Koda"].map(clean_code)
    raw = raw[raw["Koda"].str.fullmatch(r"\d{8}", na=False)].copy()
    raw["cv_norm"] = raw["Opazovani_CV"].map(normalize_text)
    return raw


def build_prefix_map(official_codes: pd.DataFrame) -> dict[str, list[tuple[str, str, str]]]:
    prefix_map: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for _, row in official_codes.iterrows():
        code = row["Koda"]
        cv_name = str(row["Opazovani_CV"])
        cv_norm = str(row["cv_norm"])
        for prefix_len in range(4, 8):
            prefix_map[code[:prefix_len]].append((code, cv_name, cv_norm))
    return prefix_map


def resolve_code(
    code: str,
    q7_norm: str,
    official_code_set: set[str],
    prefix_map: dict[str, list[tuple[str, str, str]]],
) -> tuple[str | None, str]:
    if re.fullmatch(r"\d{8}", code):
        if code in official_code_set:
            return code, "exact_official_8"
        return None, "exact_8_not_in_official"

    if re.fullmatch(r"\d{4}|\d{5}|\d{6}|\d{7}", code):
        matches = prefix_map.get(code, [])
        if len(matches) == 1:
            return matches[0][0], f"unique_prefix_{len(code)}"
        if len(matches) > 1:
            cv_matches = [match for match in matches if match[2] == q7_norm]
            if len(cv_matches) == 1:
                return cv_matches[0][0], f"cv_disambiguated_prefix_{len(code)}"
            return None, f"ambiguous_prefix_{len(code)}"

    return None, "invalid_format"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    survey = pd.read_excel(SURVEY_PATH, sheet_name="Podatki")
    survey = survey[survey["status"] != "Status"].copy()

    official_codes = load_official_codes()
    official_code_set = set(official_codes["Koda"])
    prefix_map = build_prefix_map(official_codes)

    survey["status_num"] = pd.to_numeric(survey["status"], errors="coerce")
    survey["Q1_clean"] = survey["Q1"].map(clean_code)
    survey["Q7_clean"] = survey["Q7"].fillna("").astype(str).str.strip()
    survey["Q7_norm"] = survey["Q7_clean"].map(normalize_text)
    survey["itime_date"] = pd.to_datetime(survey["itime"], format="%d.%m.%Y", errors="coerce")

    text_df = survey.fillna("").astype(str)
    test_mask = text_df.apply(lambda col: col.str.contains("test", case=False, na=False, regex=False))
    survey["analiza_contains_test"] = test_mask.any(axis=1)
    survey["analiza_test_columns"] = test_mask.apply(
        lambda row: ", ".join(row.index[row].tolist()),
        axis=1,
    )

    survey["analiza_code_is_digits"] = survey["Q1_clean"].str.fullmatch(r"\d+", na=False)
    survey["analiza_q1_code_len"] = survey["Q1_clean"].where(survey["analiza_code_is_digits"]).str.len()
    survey["analiza_code_category"] = survey["analiza_q1_code_len"].map(
        lambda x: f"{int(x)}-mestna" if pd.notna(x) else "ni numerična"
    )
    survey["analiza_status_6"] = survey["status_num"] == 6
    survey["analiza_status_lt_6"] = survey["status_num"] < 6
    survey["analiza_not_8_digit_entry"] = survey["analiza_q1_code_len"] != 8

    resolved = survey.apply(
        lambda row: resolve_code(row["Q1_clean"], row["Q7_norm"], official_code_set, prefix_map),
        axis=1,
        result_type="expand",
    )
    survey["analiza_resolved_official_code"] = resolved[0]
    survey["analiza_code_resolution"] = resolved[1]

    survey["analiza_valid_loose"] = survey["analiza_status_6"] & (~survey["analiza_contains_test"])
    survey["analiza_valid_official_code"] = survey["analiza_valid_loose"] & survey[
        "analiza_resolved_official_code"
    ].notna()
    survey["analiza_short_code_entry"] = survey["analiza_q1_code_len"].isin([4, 5, 6, 7])

    def invalid_reason(row: pd.Series) -> str:
        reasons: list[str] = []
        if not row["analiza_status_6"]:
            reasons.append("status_ni_6")
        if row["analiza_contains_test"]:
            reasons.append("vsebina_vsebuje_test")
        if not row["analiza_code_is_digits"]:
            reasons.append("koda_ni_numericna")
        elif row["analiza_q1_code_len"] != 8:
            reasons.append(f"koda_dolzina_{int(row['analiza_q1_code_len'])}")
        if row["analiza_code_resolution"] == "exact_8_not_in_official":
            reasons.append("8_mestna_koda_ni_na_uradnem_seznamu")
        elif row["analiza_valid_loose"] and pd.isna(row["analiza_resolved_official_code"]):
            reasons.append("kode_ni_bilo_mogoce_povezati_z_uradnim_seznamom")
        return "; ".join(reasons)

    survey["analiza_invalid_reason"] = survey.apply(invalid_reason, axis=1)

    strict_valid = survey[survey["analiza_valid_official_code"]].copy()
    strict_valid["iso_year"] = strict_valid["itime_date"].dt.isocalendar().year
    strict_valid["iso_week"] = strict_valid["itime_date"].dt.isocalendar().week

    short_codes = survey[
        survey["analiza_short_code_entry"] & survey["analiza_valid_loose"]
    ][
        [
            "recnum",
            "itime",
            "Q1",
            "analiza_q1_code_len",
            "analiza_code_category",
            "Q7",
            "analiza_code_resolution",
            "analiza_resolved_official_code",
            "analiza_invalid_reason",
        ]
    ].copy()

    suspicious_codes = survey[
        survey["analiza_valid_loose"] & survey["analiza_resolved_official_code"].isna()
    ][
        ["recnum", "itime", "Q1", "Q7", "Q3A", "analiza_code_resolution", "analiza_invalid_reason"]
    ].copy()

    excluded_cases = survey[
        survey["analiza_contains_test"]
        | survey["analiza_status_lt_6"]
        | survey["analiza_not_8_digit_entry"]
    ].copy()
    excluded_cases["analiza_excluded_is_test"] = excluded_cases["analiza_contains_test"]
    excluded_cases["analiza_excluded_status_lt_6"] = excluded_cases["analiza_status_lt_6"]
    excluded_cases["analiza_excluded_not_8_digit"] = excluded_cases["analiza_not_8_digit_entry"]

    def exclusion_reasons(row: pd.Series) -> str:
        reasons: list[str] = []
        if row["analiza_excluded_is_test"]:
            reasons.append("test")
        if row["analiza_excluded_status_lt_6"]:
            reasons.append("status_manjsi_od_6")
        if row["analiza_excluded_not_8_digit"]:
            reasons.append("ni_8_mestna_koda")
        return "; ".join(reasons)

    excluded_cases["analiza_excluded_reasons"] = excluded_cases.apply(exclusion_reasons, axis=1)
    excluded_cases = excluded_cases[
        [
            "recnum",
            "status",
            "itime",
            "Q1",
            "Q7",
            "Q3A",
            "analiza_excluded_is_test",
            "analiza_excluded_status_lt_6",
            "analiza_excluded_not_8_digit",
            "analiza_excluded_reasons",
            "analiza_code_category",
            "analiza_code_resolution",
            "analiza_invalid_reason",
        ]
    ].copy()

    weekly = (
        strict_valid.groupby(["iso_year", "iso_week"])
        .agg(
            valid_rows=("analiza_resolved_official_code", "size"),
            unique_participants=("analiza_resolved_official_code", "nunique"),
            date_min=("itime_date", "min"),
            date_max=("itime_date", "max"),
        )
        .reset_index()
    )

    per_participant = (
        strict_valid.groupby("analiza_resolved_official_code")
        .size()
        .rename("n_valid_responses")
        .reset_index()
    )

    strict_valid["week_label"] = strict_valid["iso_year"].astype(str) + "-W" + strict_valid["iso_week"].astype(str)
    participant_week_counts = (
        strict_valid.groupby(["analiza_resolved_official_code", "week_label"])
        .size()
        .unstack(fill_value=0)
        .sort_index(axis=1)
        .reset_index()
    )

    duplicates_same_week = (
        strict_valid.groupby(["iso_year", "iso_week", "analiza_resolved_official_code"])
        .size()
        .rename("n_rows")
        .reset_index()
    )
    duplicates_same_week = duplicates_same_week[duplicates_same_week["n_rows"] > 1].copy()

    metrics_rows = [
        ("skupno_vrstic_brez_opisne_vrstice", len(survey)),
        ("status_6_skupaj", int((survey["status_num"] == 6).sum())),
        ("test_vrstice_skupaj", int(survey["analiza_contains_test"].sum())),
        ("veljavni_odgovori_osnovno_status6_brez_test", int(survey["analiza_valid_loose"].sum())),
        ("veljavni_odgovori_z_uradno_ali_razreseno_kodo", int(survey["analiza_valid_official_code"].sum())),
        (
            "unikatni_veljavni_udelezenci_po_uradni_8_mestni_kodi",
            int(strict_valid["analiza_resolved_official_code"].nunique()),
        ),
        (
            "unikatne_pravilno_vnesene_8_mestne_uradne_kode",
            int(
                survey.loc[
                    survey["analiza_valid_loose"]
                    & (survey["analiza_code_resolution"] == "exact_official_8"),
                    "analiza_resolved_official_code",
                ].nunique()
            ),
        ),
        (
            "4_mestne_kode_med_veljavnimi",
            int((survey["analiza_valid_loose"] & (survey["analiza_q1_code_len"] == 4)).sum()),
        ),
        (
            "5_mestne_kode_med_veljavnimi",
            int((survey["analiza_valid_loose"] & (survey["analiza_q1_code_len"] == 5)).sum()),
        ),
        (
            "7_mestne_kode_med_veljavnimi",
            int((survey["analiza_valid_loose"] & (survey["analiza_q1_code_len"] == 7)).sum()),
        ),
        (
            "sumljive_8_mestne_kode_izven_uradnega_seznama",
            int(
                (
                    survey["analiza_valid_loose"]
                    & (survey["analiza_code_resolution"] == "exact_8_not_in_official")
                ).sum()
            ),
        ),
    ]
    metrics = pd.DataFrame(metrics_rows, columns=["metric", "value"])

    summary = {
        "metrics": {row[0]: row[1] for row in metrics_rows},
        "code_resolution_counts_valid_loose": survey.loc[
            survey["analiza_valid_loose"], "analiza_code_resolution"
        ].value_counts().to_dict(),
        "weekly_distribution": weekly.assign(
            date_min=weekly["date_min"].dt.strftime("%Y-%m-%d"),
            date_max=weekly["date_max"].dt.strftime("%Y-%m-%d"),
        ).to_dict(orient="records"),
        "participant_response_count_distribution": per_participant["n_valid_responses"]
        .value_counts()
        .sort_index()
        .to_dict(),
    }

    survey.to_csv(OUTPUT_DIR / "survey_marked.csv", index=False, encoding="utf-8-sig")
    short_codes.to_csv(OUTPUT_DIR / "short_codes_review.csv", index=False, encoding="utf-8-sig")
    suspicious_codes.to_csv(OUTPUT_DIR / "suspicious_codes.csv", index=False, encoding="utf-8-sig")
    weekly.to_csv(OUTPUT_DIR / "weekly_counts.csv", index=False, encoding="utf-8-sig")
    per_participant.to_csv(OUTPUT_DIR / "participant_response_counts.csv", index=False, encoding="utf-8-sig")
    participant_week_counts.to_csv(
        OUTPUT_DIR / "participant_week_counts.csv",
        index=False,
        encoding="utf-8-sig",
    )
    excluded_cases.to_csv(OUTPUT_DIR / "excluded_cases.csv", index=False, encoding="utf-8-sig")
    duplicates_same_week.to_csv(OUTPUT_DIR / "duplicate_participant_week_rows.csv", index=False, encoding="utf-8-sig")
    metrics.to_csv(OUTPUT_DIR / "summary_metrics.csv", index=False, encoding="utf-8-sig")
    (OUTPUT_DIR / "short_codes_review.json").write_text(
        short_codes.to_json(orient="records", force_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "suspicious_codes.json").write_text(
        suspicious_codes.to_json(orient="records", force_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "weekly_counts.json").write_text(
        weekly.assign(
            date_min=weekly["date_min"].dt.strftime("%Y-%m-%d"),
            date_max=weekly["date_max"].dt.strftime("%Y-%m-%d"),
        ).to_json(orient="records", force_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "participant_week_counts.json").write_text(
        participant_week_counts.to_json(orient="records", force_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "excluded_cases.json").write_text(
        excluded_cases.to_json(orient="records", force_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "summary_metrics.json").write_text(
        metrics.to_json(orient="records", force_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
