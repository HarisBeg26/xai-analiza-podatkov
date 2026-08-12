from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
RAW_PATH = BASE_DIR / "anketa191776-2026-05-11.xlsx"
OFFICIAL_CODES_PATH = BASE_DIR.parent.parent / "Uporabniki - kode.xlsx"
OUTPUT_DIR = BASE_DIR / "analysis_outputs_2026_05_11"


CANDIDATE_META = {
    "Janez Novak": {
        "biased": 0,
        "bias_type": "",
        "candidate_fit": "primeren",
        "expected_decision": "pozitivna_odlocitev",
    },
    "Enver Bajrami": {
        "biased": 0,
        "bias_type": "",
        "candidate_fit": "primeren",
        "expected_decision": "pozitivna_odlocitev",
    },
    "Živa Kopitar": {
        "biased": 1,
        "bias_type": "pozitivni_bias_nacionalnost",
        "candidate_fit": "primeren",
        "expected_decision": "pozitivna_odlocitev",
    },
    "Maja Nikolič": {
        "biased": 0,
        "bias_type": "",
        "candidate_fit": "neprimeren",
        "expected_decision": "negativna_odlocitev",
    },
    "Marko Prevc": {
        "biased": 0,
        "bias_type": "",
        "candidate_fit": "neprimeren",
        "expected_decision": "negativna_odlocitev",
    },
    "Amira Bašić": {
        "biased": 1,
        "bias_type": "negativni_bias_nacionalnost",
        "candidate_fit": "neprimeren",
        "expected_decision": "negativna_odlocitev",
    },
}


MENTAL_MODEL_Q3A_EXPECTED = {
    "janeznovak": [
        "location",
        "digital",
        "employment_status",
        "certificates",
        "education",
        "work_experience",
        "project_history",
    ],
    "enverbajrami": [
        "location",
        "digital",
        "employment_status",
        "certificates",
        "education",
        "work_experience",
        "project_history",
    ],
    "zivakopitar": [
        "location",
        "digital",
        "employment_status",
        "certificates",
        "education",
        "work_experience",
        "project_history",
    ],
    "majanikolic": [
        "location",
        "language",
        "digital",
        "employment_status",
        "certificates",
        "education",
        "work_experience",
        "project_history",
    ],
    "markoprevc": [
        "location",
        "language",
        "digital",
        "employment_status",
        "certificates",
        "education",
        "work_experience",
        "project_history",
    ],
    "amirabasic": [
        "location",
        "language",
        "digital",
        "employment_status",
        "certificates",
        "education",
        "work_experience",
        "project_history",
    ],
}


MENTAL_MODEL_CONCEPT_PATTERNS = {
    "location": [r"\boddaljen", r"\blokacij", r"\bkraj", r"\bblizin"],
    "language": [r"\bjezik", r"\bangles", r"\bnemsc", r"\bb1\b"],
    "digital": [r"\bdigital", r"\bracunal", r"\bexcel", r"\bkompetenc"],
    "employment_status": [r"\bstatus", r"\bzaposlit", r"\bstudent"],
    "certificates": [r"\bcertifikat", r"\bcertifik"],
    "education": [r"\bizobraz", r"\bstopnj", r"\bsrednj", r"\bfakult"],
    "work_experience": [r"\bizkus", r"\bdelovn"],
    "project_history": [r"\bprojekt", r"\bgodovin"],
}


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    text = "".join(
        char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char)
    )
    return re.sub(r"[^a-z0-9]+", "", text)


def clean_code(value: object) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\.0$", "", str(value).strip())


def load_official_codes() -> pd.DataFrame:
    raw = pd.read_excel(OFFICIAL_CODES_PATH).iloc[1:].copy()
    raw.columns = ["Predmet", "Koda", "Poslano", "Opazovani_CV"]
    raw["Koda"] = raw["Koda"].map(clean_code)
    raw = raw[raw["Koda"].str.fullmatch(r"\d{8}", na=False)].copy()
    raw["Opazovani_CV_norm"] = raw["Opazovani_CV"].map(normalize_text)
    return raw


def build_prefix_map(official_codes: pd.DataFrame) -> dict[str, list[tuple[str, str]]]:
    prefix_map: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for _, row in official_codes.iterrows():
        code = row["Koda"]
        cv_norm = row["Opazovani_CV_norm"]
        for prefix_len in range(4, 8):
            prefix_map[code[:prefix_len]].append((code, cv_norm))
    return prefix_map


def build_candidate_aliases() -> dict[str, str]:
    aliases = {
        "janez": "Janez Novak",
        "janeznovak": "Janez Novak",
        "janez_novak": "Janez Novak",
        "janeznovakcvpdf": "Janez Novak",
        "enver": "Enver Bajrami",
        "enverbajrami": "Enver Bajrami",
        "enver_bajrami": "Enver Bajrami",
        "enverbjarami": "Enver Bajrami",
        "ejmir": "Enver Bajrami",
        "marko": "Marko Prevc",
        "markoprevc": "Marko Prevc",
        "markoprevc": "Marko Prevc",
        "markoprevrec": "Marko Prevc",
        "marko_prevc": "Marko Prevc",
        "maja": "Maja Nikolič",
        "majanikolic": "Maja Nikolič",
        "majanikoliccvpdf": "Maja Nikolič",
        "maja_nikolic": "Maja Nikolič",
        "majanikoliccv": "Maja Nikolič",
        "ziva": "Živa Kopitar",
        "zivakopitar": "Živa Kopitar",
        "ziva_kopitar": "Živa Kopitar",
        "amirabasic": "Amira Bašić",
        "amira": "Amira Bašić",
        "amirbasic": "Amira Bašić",
        "amirbasic": "Amira Bašić",
        "amriabasic": "Amira Bašić",
        "amirabasicpdf": "Amira Bašić",
        "amirabasiccvpdf": "Amira Bašić",
        "amirabasiccv": "Amira Bašić",
    }
    return {normalize_text(key): value for key, value in aliases.items()}


def resolve_code(
    code: str,
    q7_norm: str,
    official_code_set: set[str],
    prefix_map: dict[str, list[tuple[str, str]]],
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
            cv_matches = [match for match in matches if match[1] == q7_norm]
            if len(cv_matches) == 1:
                return cv_matches[0][0], f"cv_disambiguated_prefix_{len(code)}"
            return None, f"ambiguous_prefix_{len(code)}"

    return None, "invalid_format"


def canonical_candidate_name(
    q7_value: str,
    resolved_code: str | None,
    official_lookup: dict[str, str],
    aliases: dict[str, str],
) -> str:
    normalized = normalize_text(q7_value)
    if normalized in aliases:
        return aliases[normalized]

    for alias_norm, canonical in aliases.items():
        if alias_norm and alias_norm in normalized:
            return canonical

    if resolved_code and resolved_code in official_lookup:
        short_name = official_lookup[resolved_code]
        short_norm = normalize_text(short_name)
        if short_norm in aliases:
            return aliases[short_norm]

    return ""


def build_bias_document() -> str:
    lines = [
        "# Bias In Pravilna Odločitev",
        "",
        "| Življenjepis | Kandidat | Biased | Tip biasa | Pričakovana pravilna odločitev |",
        "|---|---|---:|---|---|",
    ]
    for candidate, meta in CANDIDATE_META.items():
        lines.append(
            f"| {candidate} | {meta['candidate_fit']} | {meta['biased']} | {meta['bias_type'] or 'brez_biasa'} | {meta['expected_decision']} |"
        )
    lines.extend(
        [
            "",
            "Opomba:",
            "- `Biased = 1` pomeni, da je v scenarij vključen bias.",
            "- `pozitivna_odlocitev` pomeni, da bi moral biti kandidat ocenjen kot primeren.",
            "- `negativna_odlocitev` pomeni, da bi moral biti kandidat ocenjen kot neprimeren.",
        ]
    )
    return "\n".join(lines)


def build_mental_model_draft() -> str:
    lines = [
        "# Osnutek Pravil Za Mentalne Modele",
        "",
        "To je začetni osnutek pravil. Dataset-a še nisem samodejno ocenjeval z 0/1, ker bi bilo to brez potrditve kriterijev preveč tvegano.",
        "",
        "Predlog za ročno potrditev pravil:",
    ]
    for candidate, meta in CANDIDATE_META.items():
        lines.extend(
            [
                "",
                f"## {candidate}",
                f"- Kandidat: {meta['candidate_fit']}",
                f"- Biased: {meta['biased']}",
                f"- Tip biasa: {meta['bias_type'] or 'brez_biasa'}",
                "- Sprejemljive pravilne razlage naj omenjajo relevantne kompetence iz CV-ja (izobrazba, izkušnje, jeziki, digitalne kompetence) in pri biased primerih tudi pristranski vpliv nacionalnosti.",
                "- Napačne razlage bi bile tiste, ki kandidata postavijo v nasprotno kategorijo ali zgrešijo ključni bias pri biased scenarijih.",
            ]
        )
    lines.extend(
        [
            "",
            "Naslednji varen korak je, da skupaj potrdiva 5–10 sprejemljivih ključnih formulacij za vsakega kandidata, nato pa lahko dodam 0/1 stolpce za pravilnost nalog.",
        ]
    )
    return "\n".join(lines)


def normalize_free_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    text = "".join(
        char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char)
    )
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def score_q3a(text: object) -> int:
    normalized = normalize_free_text(text)
    if not normalized or normalized in {"ne vem", "dobro", "smiselno", "v redu"}:
        return 0

    patterns = {
        "experience": [r"\bizkus", r"\bdelovn"],
        "education": [r"\bizobraz"],
        "digital": [r"\bdigital", r"\bkompetenc", r"\bcertifikat", r"\bracunal"],
        "language": [r"\bjezik", r"\bangles"],
        "nationality": [r"\bnacional", r"\bdrzavlj", r"\btuj"],
        "gender": [r"\bspol", r"\bzensk", r"\bmosk"],
        "location": [r"\blokacij", r"\boddaljen"],
    }

    matched = set()
    for group, group_patterns in patterns.items():
        if any(re.search(pattern, normalized) for pattern in group_patterns):
            matched.add(group)

    core_present = bool({"experience", "education", "digital", "language"} & matched)
    context_present = bool({"nationality", "gender", "location"} & matched)
    return int(len(matched) >= 3 and core_present and context_present)


def score_q3b2(label_text: object) -> int:
    normalized = normalize_free_text(label_text)
    return int(
        normalized in {"delno smiselna", "ne ne zdi se smiselna"}
    )


def score_q3b3(text: object, candidate_name: str) -> int:
    normalized = normalize_free_text(text)
    if not normalized:
        return 0

    no_issue_patterns = [
        r"^/$",
        r"^\.$",
        r"^\\\\$",
        r"\bni sporno\b",
        r"\bnic ni sporno\b",
        r"\bnic se mi ne zdi napacno\b",
        r"\bni napacna\b",
        r"\bni nenavadna\b",
        r"\bzdi se vredu\b",
        r"\bv redu\b",
        r"\bvse ok\b",
        r"\brazlaga se mi zdi dobra\b",
        r"\bzdi se mi smiselno\b",
        r"\bzdi se smiselna\b",
        r"\bbrez komentar",
    ]
    bias_patterns = [
        r"\bnacional",
        r"\bdrzavlj",
        r"\bspol",
        r"\bzensk",
        r"\bmosk",
        r"\bpristr",
        r"\bdiskrimin",
        r"\bbias",
        r"\bseksis",
        r"\bxenoph",
    ]

    biased_candidate = CANDIDATE_META.get(candidate_name, {}).get("biased", 0) == 1
    if biased_candidate:
        return int(any(re.search(pattern, normalized) for pattern in bias_patterns))

    return int(any(re.search(pattern, normalized) for pattern in no_issue_patterns))


def score_q3c2(label_text: object) -> int:
    normalized = normalize_free_text(label_text)
    return int(normalized == "visoka negativna ocena")


MENTAL_MODEL_Q3A_EXPECTED = {
    "Janez Novak": [
        "location",
        "digital",
        "employment_status",
        "certificates",
        "education",
        "work_experience",
        "project_history",
    ],
    "Enver Bajrami": [
        "location",
        "digital",
        "employment_status",
        "certificates",
        "education",
        "work_experience",
        "project_history",
    ],
    "Å½iva Kopitar": [
        "location",
        "digital",
        "employment_status",
        "certificates",
        "education",
        "work_experience",
        "project_history",
    ],
    "Maja NikoliÄ": [
        "location",
        "language",
        "digital",
        "employment_status",
        "certificates",
        "education",
        "work_experience",
        "project_history",
    ],
    "Marko Prevc": [
        "location",
        "language",
        "digital",
        "employment_status",
        "certificates",
        "education",
        "work_experience",
        "project_history",
    ],
    "Amira BaÅ¡iÄ‡": [
        "location",
        "language",
        "digital",
        "employment_status",
        "certificates",
        "education",
        "work_experience",
        "project_history",
    ],
}


MENTAL_MODEL_CONCEPT_PATTERNS = {
    "location": [r"\boddaljen", r"\blokacij", r"\bkraj", r"\bblizin"],
    "language": [r"\bjezik", r"\bangles", r"\bnemsc", r"\bb1\b"],
    "digital": [r"\bdigital", r"\bracunal", r"\bexcel", r"\bkompetenc"],
    "employment_status": [r"\bstatus", r"\bzaposlit", r"\bstudent"],
    "certificates": [r"\bcertifikat", r"\bcertifik"],
    "education": [r"\bizobraz", r"\bstopnj", r"\bsrednj", r"\bfakult"],
    "work_experience": [r"\bizkus", r"\bdelovn"],
    "project_history": [r"\bprojekt", r"\bgodovin"],
}


def contains_any(patterns: list[str], normalized_text: str) -> bool:
    return any(re.search(pattern, normalized_text) for pattern in patterns)


def extract_mental_model_concepts(normalized_text: str) -> set[str]:
    matched = set()
    for concept, patterns in MENTAL_MODEL_CONCEPT_PATTERNS.items():
        if contains_any(patterns, normalized_text):
            matched.add(concept)
    return matched


def q3a_expected_for_candidate(candidate_name: str) -> list[str]:
    candidate_norm = normalize_text(candidate_name)
    return MENTAL_MODEL_Q3A_EXPECTED.get(candidate_norm, [])


def build_mental_model_draft() -> str:
    lines = [
        "# Osnutek Pravil Za Mentalne Modele",
        "",
        "Pravila so posodobljena glede na roÄno potrjene pravilne odgovore.",
        "",
        "## Q3B_2 - Razumevanje: zaznavanje napak",
        "",
        "Pravilna odgovora sta:",
        "- Delno smiselna",
        "- Ne, ne zdi se smiselna",
        "",
        "## Q3A in Q3B_3 po posameznem Å¾ivljenjepisu",
    ]
    for candidate, meta in CANDIDATE_META.items():
        q3a_concepts = ", ".join(q3a_expected_for_candidate(candidate))
        candidate_norm = normalize_text(candidate)
        if candidate_norm == "zivakopitar":
            q3b3_rule = (
                "Sprejemljiv odgovor omenja, da ni napaÄnih razlag, vendar je nenavadno ali sporno, "
                "da je bila narodnost pomemben faktor."
            )
        elif candidate_norm == "amirabasic":
            q3b3_rule = (
                "Sprejemljiv odgovor omenja napako, da je sistem uporabil spol in/ali narodnost "
                "za negativno odloÄitev o kandidatki."
            )
        elif meta["candidate_fit"] == "primeren":
            q3b3_rule = (
                "Sprejemljiv odgovor omenja, da ni napaÄnih razlag in da je sistem kandidata pravilno "
                "oznaÄil kot primernega."
            )
        else:
            q3b3_rule = (
                "Sprejemljiv odgovor omenja, da ni napaÄnih razlag in da je sistem kandidata pravilno "
                "oznaÄil kot neprimernega."
            )
        lines.extend(
            [
                "",
                f"## {candidate}",
                f"- Kandidat: {meta['candidate_fit']}",
                f"- Biased: {meta['biased']}",
                f"- Tip biasa: {meta['bias_type'] or 'brez_biasa'}",
                f"- Q3A: sprejemljive pravilne razlage naj omenjajo veÄ relevantnih konceptov, kot so: {q3a_concepts}.",
                f"- Q3B_3: {q3b3_rule}",
                "- NapaÄni odgovori so tisti, ki kandidata postavijo v nasprotno kategorijo, ne zaznajo bias-a tam kjer je prisoten ali navajajo oÄitno nepovezane razloge.",
            ]
        )
    lines.extend(
        [
            "",
            "## Q3C - Napovedno sklepanje",
            "",
            "Za `Q3C_2` sta pravilna odgovora:",
            "- Rahlo negativna ocena",
            "- Visoka negativna ocena",
            "",
            "Za `Q3C_3` je pravilen vrstni red:",
            "1. Digitalne kompetence",
            "2. Stopnja izobrazbe",
            "3. Delovne izkuÅ¡nje",
            "4. Jezikovne kompetence",
            "5. Lokacija",
            "6. Nacionalnost",
            "7. Spol",
        ]
    )
    return "\n".join(lines)


def score_q3a(text: object, candidate_name: str) -> int:
    normalized = normalize_free_text(text)
    if not normalized or normalized in {"ne vem", "dobro", "smiselno", "v redu"}:
        return 0

    matched = extract_mental_model_concepts(normalized)
    expected = set(q3a_expected_for_candidate(candidate_name))
    expected_hits = matched & expected
    core_present = bool({"education", "work_experience", "digital"} & expected_hits)
    supporting_present = bool(
        {"location", "employment_status", "certificates", "project_history", "language"} & expected_hits
    )
    return int(len(expected_hits) >= 4 and core_present and supporting_present)


def score_q3b3(text: object, candidate_name: str) -> int:
    normalized = normalize_free_text(text)
    if not normalized:
        return 0
    candidate_norm = normalize_text(candidate_name)

    no_issue_patterns = [
        r"^/$",
        r"^\.$",
        r"^\\\\$",
        r"\bni sporno\b",
        r"\bnic ni sporno\b",
        r"\bnic se mi ne zdi napacno\b",
        r"\bni napacna\b",
        r"\bni nenavadna\b",
        r"\bzdi se vredu\b",
        r"\bv redu\b",
        r"\bvse ok\b",
        r"\brazlaga se mi zdi dobra\b",
        r"\bzdi se mi smiselno\b",
        r"\bzdi se smiselna\b",
        r"\bbrez komentar",
        r"\bni napacnih razlag\b",
    ]
    bias_patterns = [
        r"\bnacional",
        r"\bdrzavlj",
        r"\bspol",
        r"\bzensk",
        r"\bmosk",
        r"\bpristr",
        r"\bdiskrimin",
        r"\bbias",
        r"\bseksis",
        r"\bxenoph",
    ]
    strange_patterns = [r"\bcudn", r"\bnenavad", r"\bsporn", r"\bproblem", r"\bzakaj"]
    positive_decision_patterns = [r"\bprimeren", r"\bustreza", r"\bustrez", r"\bpozitiv"]
    negative_decision_patterns = [r"\bneprimer", r"\bnegativ", r"\bne ustreza", r"\bzavrn"]
    correctness_patterns = [r"\bpraviln", r"\bsmiseln", r"\bustrezn", r"\bdobra odloc"]
    error_patterns = [r"\bnapak", r"\bnarobe", r"\bproblem", r"\bsporn", r"\bpristr"]

    no_issue = contains_any(no_issue_patterns, normalized)
    has_bias = contains_any(bias_patterns, normalized)
    is_strange = contains_any(strange_patterns, normalized)
    says_positive = contains_any(positive_decision_patterns, normalized)
    says_negative = contains_any(negative_decision_patterns, normalized)
    says_correct = contains_any(correctness_patterns, normalized)
    says_error = contains_any(error_patterns, normalized)

    if candidate_norm == "zivakopitar":
        return int(has_bias and (is_strange or no_issue))

    if candidate_norm == "amirabasic":
        return int(has_bias and (says_error or says_negative))

    expected_fit = None
    for raw_name, meta in CANDIDATE_META.items():
        if normalize_text(raw_name) == candidate_norm:
            expected_fit = meta.get("candidate_fit")
            break
    if expected_fit == "primeren":
        return int((no_issue or says_correct) and says_positive)
    if expected_fit == "neprimeren":
        return int((no_issue or says_correct) and says_negative)
    return 0


def score_q3c2(label_text: object) -> int:
    normalized = normalize_free_text(label_text)
    return int(normalized in {"rahlo negativna ocena", "visoka negativna ocena"})


MENTAL_MODEL_Q3A_EXPECTED = {
    "janeznovak": [
        "location",
        "digital",
        "employment_status",
        "certificates",
        "education",
        "work_experience",
        "project_history",
    ],
    "enverbajrami": [
        "location",
        "digital",
        "employment_status",
        "certificates",
        "education",
        "work_experience",
        "project_history",
    ],
    "zivakopitar": [
        "location",
        "digital",
        "employment_status",
        "certificates",
        "education",
        "work_experience",
        "project_history",
    ],
    "majanikolic": [
        "location",
        "language",
        "digital",
        "employment_status",
        "certificates",
        "education",
        "work_experience",
        "project_history",
    ],
    "markoprevc": [
        "location",
        "language",
        "digital",
        "employment_status",
        "certificates",
        "education",
        "work_experience",
        "project_history",
    ],
    "amirabasic": [
        "location",
        "language",
        "digital",
        "employment_status",
        "certificates",
        "education",
        "work_experience",
        "project_history",
    ],
}


MENTAL_MODEL_CONCEPT_PATTERNS = {
    "location": [r"\boddaljen", r"\blokacij", r"\bkraj", r"\bblizin"],
    "language": [r"\bjezik", r"\bangles", r"\bnemsc", r"\bb1\b"],
    "digital": [r"\bdigital", r"\bracunal", r"\bexcel", r"\bkompetenc", r"\borodj", r"\btehnolog"],
    "employment_status": [r"\bstatus", r"\bzaposlit", r"\bstudent"],
    "certificates": [r"\bcertifikat", r"\bcertifik", r"\breferenc"],
    "education": [r"\bizobraz", r"\bstopnj", r"\bsrednj", r"\bfakult"],
    "work_experience": [r"\bizkus", r"\bdelovn"],
    "project_history": [r"\bprojekt", r"\bgodovin", r"\bnalog", r"\brezultat"],
}


def q3a_expected_for_candidate(candidate_name: str) -> list[str]:
    return MENTAL_MODEL_Q3A_EXPECTED.get(normalize_text(candidate_name), [])


def score_q3a(text: object, candidate_name: str) -> int:
    normalized = normalize_free_text(text)
    if not normalized or normalized in {"ne vem", "dobro", "smiselno", "v redu"}:
        return 0

    matched = extract_mental_model_concepts(normalized)
    expected_hits = matched & set(q3a_expected_for_candidate(candidate_name))
    core_present = bool({"education", "work_experience", "digital"} & expected_hits)
    return int(len(expected_hits) >= 3 and core_present)


def build_mental_model_draft() -> str:
    entries = [
        ("janeznovak", "Janez Novak", "primeren", 0, "brez_biasa"),
        ("enverbajrami", "Enver Bajrami", "primeren", 0, "brez_biasa"),
        ("zivakopitar", "\u017diva Kopitar", "primeren", 1, "pozitivni_bias_nacionalnost"),
        ("majanikolic", "Maja Nikoli\u010d", "neprimeren", 0, "brez_biasa"),
        ("markoprevc", "Marko Prevc", "neprimeren", 0, "brez_biasa"),
        ("amirabasic", "Amira Ba\u0161i\u0107", "neprimeren", 1, "negativni_bias_nacionalnost"),
    ]
    lines = [
        "# Osnutek Pravil Za Mentalne Modele",
        "",
        "Pravila so posodobljena glede na ročno potrjene pravilne odgovore.",
        "",
        "## Q3B_2 - Razumevanje: zaznavanje napak",
        "",
        "Pravilna odgovora sta:",
        "- Delno smiselna",
        "- Ne, ne zdi se smiselna",
        "",
        "## Q3A in Q3B_3 po posameznem življenjepisu",
    ]
    for key, display_name, fit, biased, bias_type in entries:
        if key == "zivakopitar":
            q3b3_rule = (
                "Sprejemljiv odgovor omenja, da ni napačnih razlag, vendar je nenavadno ali sporno, "
                "da je bila narodnost pomemben faktor."
            )
        elif key == "amirabasic":
            q3b3_rule = (
                "Sprejemljiv odgovor omenja napako, da je sistem uporabil spol in/ali narodnost "
                "za negativno odločitev o kandidatki."
            )
        elif fit == "primeren":
            q3b3_rule = (
                "Sprejemljiv odgovor omenja, da ni napačnih razlag in da je sistem kandidata pravilno "
                "označil kot primernega."
            )
        else:
            q3b3_rule = (
                "Sprejemljiv odgovor omenja, da ni napačnih razlag in da je sistem kandidata pravilno "
                "označil kot neprimernega."
            )
        q3a_concepts = ", ".join(MENTAL_MODEL_Q3A_EXPECTED[key])
        lines.extend(
            [
                "",
                f"## {display_name}",
                f"- Kandidat: {fit}",
                f"- Biased: {biased}",
                f"- Tip biasa: {bias_type}",
                f"- Q3A: sprejemljive pravilne razlage naj omenjajo več relevantnih konceptov, kot so: {q3a_concepts}.",
                f"- Q3B_3: {q3b3_rule}",
                "- Napačni odgovori so tisti, ki kandidata postavijo v nasprotno kategorijo, ne zaznajo bias-a tam kjer je prisoten ali navajajo očitno nepovezane razloge.",
            ]
        )
    lines.extend(
        [
            "",
            "## Q3C - Napovedno sklepanje",
            "",
            "Za `Q3C_2` sta pravilna odgovora:",
            "- Rahlo negativna ocena",
            "- Visoka negativna ocena",
            "",
            "Za `Q3C_3` je pravilen vrstni red:",
            "1. Digitalne kompetence",
            "2. Stopnja izobrazbe",
            "3. Delovne izkušnje",
            "4. Jezikovne kompetence",
            "5. Lokacija",
            "6. Nacionalnost",
            "7. Spol",
        ]
    )
    return \"\\n\".join(lines)


def score_q3c3_item(value: object, expected_rank: int) -> int:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return 0
    return int(int(numeric) == expected_rank)


def reverse_1_to_5(value: object) -> float | pd.NA:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric) or numeric not in {1, 2, 3, 4, 5}:
        return pd.NA
    mapping = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}
    return mapping.get(int(numeric), pd.NA)


def reverse_1_to_7(value: object) -> float | pd.NA:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric) or numeric not in {1, 2, 3, 4, 5, 6, 7}:
        return pd.NA
    mapping = {1: 7, 2: 6, 3: 5, 4: 4, 5: 3, 6: 2, 7: 1}
    return mapping.get(int(numeric), pd.NA)


def reverse_likert_1_to_5(value: object) -> float | pd.NA:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric) or int(numeric) == -1:
        return pd.NA
    mapping = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}
    return mapping.get(int(numeric), pd.NA)


def clean_likert_1_to_7(value: object) -> float | pd.NA:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric) or int(numeric) == -1:
        return pd.NA
    return int(numeric)


def clean_likert_1_to_5(value: object) -> float | pd.NA:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric) or numeric not in {1, 2, 3, 4, 5}:
        return pd.NA
    return int(numeric)


def next_available_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    counter = 2
    while True:
        candidate = path.with_name(f"{stem}_v{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    survey = pd.read_excel(RAW_PATH, sheet_name="Podatki")
    survey = survey[survey["status"] != "Status"].copy()
    labels = pd.read_excel(RAW_PATH, sheet_name="Labele odgovorov")
    labels = labels[labels["status"] != "Status"].copy()
    official_codes = load_official_codes()
    official_code_set = set(official_codes["Koda"])
    prefix_map = build_prefix_map(official_codes)
    official_cv_lookup = dict(zip(official_codes["Koda"], official_codes["Opazovani_CV"]))
    aliases = build_candidate_aliases()

    survey["analiza_status_num"] = pd.to_numeric(survey["status"], errors="coerce")
    labels["recnum"] = pd.to_numeric(labels["recnum"], errors="coerce")
    survey["recnum"] = pd.to_numeric(survey["recnum"], errors="coerce")
    survey["analiza_itime_date"] = pd.to_datetime(survey["itime"], format="%d.%m.%Y", errors="coerce")
    survey["analiza_q1_clean"] = survey["Q1"].map(clean_code)
    survey["analiza_q7_clean"] = survey["Q7"].fillna("").astype(str).str.strip()
    survey["analiza_q7_norm"] = survey["analiza_q7_clean"].map(normalize_text)
    survey["analiza_code_is_digits"] = survey["analiza_q1_clean"].str.fullmatch(r"\d+", na=False)
    survey["analiza_code_length"] = survey["analiza_q1_clean"].where(
        survey["analiza_code_is_digits"]
    ).str.len()

    text_df = survey.fillna("").astype(str)
    contains_test = text_df.apply(
        lambda col: col.str.contains("test", case=False, na=False, regex=False)
    ).any(axis=1)
    survey["analiza_contains_test"] = contains_test

    resolved = survey.apply(
        lambda row: resolve_code(
            row["analiza_q1_clean"],
            row["analiza_q7_norm"],
            official_code_set,
            prefix_map,
        ),
        axis=1,
        result_type="expand",
    )
    survey["analiza_resolved_code"] = resolved[0]
    survey["analiza_code_resolution"] = resolved[1]
    survey["analiza_valid_status6_no_test"] = (
        survey["analiza_status_num"] == 6
    ) & (~survey["analiza_contains_test"])
    survey["analiza_valid_resolved"] = survey["analiza_valid_status6_no_test"] & survey[
        "analiza_resolved_code"
    ].notna()

    survey["analiza_cv_name"] = survey.apply(
        lambda row: canonical_candidate_name(
            row["analiza_q7_clean"],
            row["analiza_resolved_code"],
            official_cv_lookup,
            aliases,
        ),
        axis=1,
    )
    survey["Biased"] = survey["analiza_cv_name"].map(
        lambda name: CANDIDATE_META.get(name, {}).get("biased", pd.NA)
    )
    survey["analiza_bias_type"] = survey["analiza_cv_name"].map(
        lambda name: CANDIDATE_META.get(name, {}).get("bias_type", "")
    )
    survey["analiza_candidate_fit"] = survey["analiza_cv_name"].map(
        lambda name: CANDIDATE_META.get(name, {}).get("candidate_fit", "")
    )
    survey["analiza_expected_decision"] = survey["analiza_cv_name"].map(
        lambda name: CANDIDATE_META.get(name, {}).get("expected_decision", "")
    )

    label_lookup = labels.set_index("recnum")[["Q3B_2", "Q3C_2"]].rename(
        columns={
            "Q3B_2": "analiza_label_q3b2",
            "Q3C_2": "analiza_label_q3c2",
        }
    )
    survey = survey.merge(label_lookup, on="recnum", how="left")

    valid_resolved = survey[survey["analiza_valid_resolved"]].copy()
    valid_resolved = valid_resolved.sort_values(
        ["analiza_resolved_code", "analiza_itime_date", "recnum"]
    ).copy()
    valid_resolved["analiza_view_number"] = valid_resolved.groupby("analiza_resolved_code").cumcount() + 1
    valid_resolved["analiza_total_participations"] = valid_resolved.groupby("analiza_resolved_code")[
        "analiza_resolved_code"
    ].transform("size")

    survey = survey.merge(
        valid_resolved[
            [
                "recnum",
                "analiza_view_number",
                "analiza_total_participations",
            ]
        ],
        on="recnum",
        how="left",
    )

    expected_q3c3 = {
        "Q3C_3a": 2,
        "Q3C_3b": 3,
        "Q3C_3c": 4,
        "Q3C_3d": 1,
        "Q3C_3e": 7,
        "Q3C_3f": 5,
        "Q3C_3g": 6,
    }

    valid_mask = survey["analiza_valid_resolved"]
    survey["analiza_mm_q3a_correct"] = pd.NA
    survey.loc[valid_mask, "analiza_mm_q3a_correct"] = survey.loc[valid_mask].apply(
        lambda row: score_q3a(row["Q3A"], row["analiza_cv_name"]),
        axis=1,
    )

    survey["analiza_mm_q3b2_correct"] = pd.NA
    survey.loc[valid_mask, "analiza_mm_q3b2_correct"] = survey.loc[
        valid_mask, "analiza_label_q3b2"
    ].map(score_q3b2)

    survey["analiza_mm_q3b3_correct"] = pd.NA
    survey.loc[valid_mask, "analiza_mm_q3b3_correct"] = survey.loc[valid_mask].apply(
        lambda row: score_q3b3(row["Q3B_3"], row["analiza_cv_name"]),
        axis=1,
    )

    survey["analiza_mm_q3c2_correct"] = pd.NA
    survey.loc[valid_mask, "analiza_mm_q3c2_correct"] = survey.loc[
        valid_mask, "analiza_label_q3c2"
    ].map(score_q3c2)

    for column, expected_rank in expected_q3c3.items():
        score_column = f"analiza_mm_{column.lower()}_correct"
        survey[score_column] = pd.NA
        survey.loc[valid_mask, score_column] = survey.loc[valid_mask, column].map(
            lambda value: score_q3c3_item(value, expected_rank)
        )

    mental_model_columns = [
        "analiza_mm_q3a_correct",
        "analiza_mm_q3b2_correct",
        "analiza_mm_q3b3_correct",
        "analiza_mm_q3c2_correct",
        "analiza_mm_q3c_3a_correct",
        "analiza_mm_q3c_3b_correct",
        "analiza_mm_q3c_3c_correct",
        "analiza_mm_q3c_3d_correct",
        "analiza_mm_q3c_3e_correct",
        "analiza_mm_q3c_3f_correct",
        "analiza_mm_q3c_3g_correct",
    ]
    survey["analiza_mm_total_correct_count"] = pd.NA
    survey["analiza_mm_total_correct_share"] = pd.NA
    survey.loc[valid_mask, "analiza_mm_total_correct_count"] = (
        survey.loc[valid_mask, mental_model_columns]
        .apply(pd.to_numeric, errors="coerce")
        .sum(axis=1)
    )
    survey.loc[valid_mask, "analiza_mm_total_correct_share"] = (
        survey.loc[valid_mask, "analiza_mm_total_correct_count"] / len(mental_model_columns)
    )

    trust_source_columns = ["Q4Aa", "Q4Ab", "Q4Ac", "Q4Ad", "Q4Ae", "Q4Af", "Q4Ag"]
    distrust_source_columns = ["Q4Ba", "Q4Bb", "Q4Bc", "Q4Bd", "Q4Be"]
    distrust_recoded_columns = [
        "analiza_nezaupanje_t1_recoded_1_7",
        "analiza_nezaupanje_t2_recoded_1_7",
        "analiza_nezaupanje_t3_recoded_1_7",
        "analiza_nezaupanje_t4_recoded_1_7",
        "analiza_nezaupanje_t5_recoded_1_7",
    ]
    for raw_col, recoded_col in zip(distrust_source_columns, distrust_recoded_columns):
        survey[recoded_col] = survey[raw_col].map(reverse_1_to_7)

    trust_raw_numeric = survey[trust_source_columns].apply(pd.to_numeric, errors="coerce")
    distrust_raw_numeric = survey[distrust_source_columns].apply(pd.to_numeric, errors="coerce")
    trust_new_mask = valid_mask & trust_raw_numeric.isin([1, 2, 3, 4, 5, 6, 7]).any(axis=1)
    trust_old_mask = valid_mask & trust_raw_numeric.eq(-1).all(axis=1) & distrust_raw_numeric.eq(-1).all(axis=1)

    survey["analiza_trust_version"] = pd.NA
    survey.loc[trust_old_mask, "analiza_trust_version"] = "old"
    survey.loc[trust_new_mask, "analiza_trust_version"] = "new"
    survey["analiza_trust_usable"] = 0
    survey.loc[trust_new_mask, "analiza_trust_usable"] = 1

    trust_new_columns = []
    trust_old_columns = []
    for source_column in trust_source_columns:
        clean_values = survey[source_column].map(clean_likert_1_to_7)
        new_column = f"analiza_trust_new_{source_column.lower()}"
        old_column = f"analiza_trust_old_{source_column.lower()}"
        trust_new_columns.append(new_column)
        trust_old_columns.append(old_column)
        survey[new_column] = pd.NA
        survey[old_column] = pd.NA
        survey.loc[trust_new_mask, new_column] = clean_values.loc[trust_new_mask]

    survey["analiza_faktor_nezaupanje_mean"] = pd.NA
    survey.loc[trust_new_mask, "analiza_faktor_nezaupanje_mean"] = survey.loc[
        trust_new_mask, distrust_recoded_columns
    ].apply(pd.to_numeric, errors="coerce").mean(axis=1)
    survey["analiza_faktor_zaupanje_mean"] = pd.NA
    survey.loc[trust_new_mask, "analiza_faktor_zaupanje_mean"] = survey.loc[
        trust_new_mask, trust_new_columns
    ].apply(pd.to_numeric, errors="coerce").mean(axis=1)
    survey["analiza_skupna_ocena_zaupanja_mean"] = pd.NA
    survey.loc[trust_new_mask, "analiza_skupna_ocena_zaupanja_mean"] = survey.loc[
        trust_new_mask, distrust_recoded_columns + trust_new_columns
    ].apply(pd.to_numeric, errors="coerce").mean(axis=1)

    satisfaction_source_columns = [
        "Q2a",
        "Q2b",
        "Q2c",
        "Q2d",
        "Q2e",
        "Q2f",
        "Q2g",
        "Q2h",
        "Q3a",
        "Q3b",
        "Q3c",
        "Q3d",
        "Q3e",
        "Q3f",
        "Q3g",
    ]
    satisfaction_clean_columns = []
    for source_column in satisfaction_source_columns:
        target_column = f"analiza_zadovoljstvo_{source_column.lower()}_clean_1_5"
        satisfaction_clean_columns.append(target_column)
        survey[target_column] = survey[source_column].map(clean_likert_1_to_5)
    survey["analiza_zadovoljstvo_mean"] = pd.NA
    survey.loc[valid_mask, "analiza_zadovoljstvo_mean"] = survey.loc[
        valid_mask, satisfaction_clean_columns
    ].apply(pd.to_numeric, errors="coerce").mean(axis=1)

    participant_counts = (
        valid_resolved.groupby("analiza_resolved_code")
        .agg(
            n_participations=("analiza_resolved_code", "size"),
            first_date=("analiza_itime_date", "min"),
            last_date=("analiza_itime_date", "max"),
        )
        .reset_index()
    )
    participant_counts["first_date"] = participant_counts["first_date"].dt.strftime("%Y-%m-%d")
    participant_counts["last_date"] = participant_counts["last_date"].dt.strftime("%Y-%m-%d")

    participant_week_matrix = (
        valid_resolved.assign(
            analiza_week_label=lambda df: df["analiza_itime_date"].dt.isocalendar().year.astype(str)
            + "-W"
            + df["analiza_itime_date"].dt.isocalendar().week.astype(str)
        )
        .groupby(["analiza_resolved_code", "analiza_week_label"])
        .size()
        .unstack(fill_value=0)
        .sort_index(axis=1)
        .reset_index()
    )

    participant_views = valid_resolved[
        [
            "analiza_resolved_code",
            "analiza_view_number",
            "analiza_cv_name",
            "itime",
        ]
    ].copy()
    participant_view_table = participant_views.pivot(
        index="analiza_resolved_code",
        columns="analiza_view_number",
        values="analiza_cv_name",
    )
    participant_view_table = participant_view_table.rename(
        columns=lambda col: f"view_{int(col)}_cv"
    ).reset_index()
    participant_view_dates = participant_views.pivot(
        index="analiza_resolved_code",
        columns="analiza_view_number",
        values="itime",
    )
    participant_view_dates = participant_view_dates.rename(
        columns=lambda col: f"view_{int(col)}_date"
    ).reset_index()
    participant_summary = participant_counts.merge(participant_view_table, on="analiza_resolved_code", how="left")
    participant_summary = participant_summary.merge(
        participant_view_dates, on="analiza_resolved_code", how="left"
    )

    summary = {
        "valid_rows_status6_no_test": int(survey["analiza_valid_status6_no_test"].sum()),
        "valid_rows_with_resolved_code": int(survey["analiza_valid_resolved"].sum()),
        "unique_participants_resolved": int(valid_resolved["analiza_resolved_code"].nunique()),
        "resolution_counts": survey.loc[
            survey["analiza_valid_status6_no_test"], "analiza_code_resolution"
        ].value_counts().to_dict(),
        "participation_distribution": valid_resolved.groupby("analiza_resolved_code")
        .size()
        .value_counts()
        .sort_index()
        .to_dict(),
        "unresolved_valid_rows": survey.loc[
            survey["analiza_valid_status6_no_test"] & survey["analiza_resolved_code"].isna(),
            ["recnum", "itime", "Q1", "Q7", "analiza_code_resolution"],
        ]
        .fillna("")
        .astype(str)
        .to_dict(orient="records"),
        "mental_model_item_means": {
            column: float(pd.to_numeric(survey.loc[valid_mask, column], errors="coerce").mean())
            for column in mental_model_columns
        },
        "trust_scale_coverage": {
            "trust_version_old": int(trust_old_mask.sum()),
            "trust_version_new": int(trust_new_mask.sum()),
            "trust_usable_rows": int(survey["analiza_trust_usable"].sum()),
            "nezaupanje_mean_non_null": int(survey["analiza_faktor_nezaupanje_mean"].notna().sum()),
            "zaupanje_mean_non_null": int(survey["analiza_faktor_zaupanje_mean"].notna().sum()),
            "skupna_ocena_zaupanja_non_null": int(
                survey["analiza_skupna_ocena_zaupanja_mean"].notna().sum()
            ),
            "zadovoljstvo_mean_non_null": int(survey["analiza_zadovoljstvo_mean"].notna().sum()),
        },
    }

    metrics = pd.DataFrame(
        [
            ("veljavni_status6_brez_test", summary["valid_rows_status6_no_test"]),
            ("veljavni_z_razreseno_kodo", summary["valid_rows_with_resolved_code"]),
            ("unikatni_udelezenci", summary["unique_participants_resolved"]),
            (
                "4_ali_7_mestni_vnosi_med_veljavnimi",
                int(
                    survey.loc[
                        survey["analiza_valid_status6_no_test"]
                        & survey["analiza_code_length"].isin([4, 6, 7]),
                        "recnum",
                    ].count()
                ),
            ),
            (
                "8_mestni_pravilni_vnosi_med_veljavnimi",
                int(
                    survey.loc[
                        survey["analiza_valid_status6_no_test"]
                        & (survey["analiza_code_resolution"] == "exact_official_8"),
                        "recnum",
                    ].count()
                ),
            ),
        ],
        columns=["metric", "value"],
    )

    analysis_dataset_path = next_available_path(OUTPUT_DIR / "anketa191776-2026-05-11_dataset_analiza.csv")
    participant_counts_path = next_available_path(OUTPUT_DIR / "participant_counts.csv")
    participant_summary_path = next_available_path(OUTPUT_DIR / "participant_summary.csv")
    participant_week_matrix_path = next_available_path(OUTPUT_DIR / "participant_week_matrix.csv")
    summary_metrics_path = next_available_path(OUTPUT_DIR / "summary_metrics.csv")
    summary_json_path = next_available_path(OUTPUT_DIR / "summary.json")
    participant_summary_json_path = next_available_path(OUTPUT_DIR / "participant_summary.json")
    participant_week_matrix_json_path = next_available_path(OUTPUT_DIR / "participant_week_matrix.json")

    survey.to_csv(analysis_dataset_path, index=False, encoding="utf-8-sig")
    participant_counts.to_csv(participant_counts_path, index=False, encoding="utf-8-sig")
    participant_summary.to_csv(participant_summary_path, index=False, encoding="utf-8-sig")
    participant_week_matrix.to_csv(
        participant_week_matrix_path, index=False, encoding="utf-8-sig"
    )
    metrics.to_csv(summary_metrics_path, index=False, encoding="utf-8-sig")
    summary["output_files"] = {
        "dataset_csv": str(analysis_dataset_path),
        "participant_counts_csv": str(participant_counts_path),
        "participant_summary_csv": str(participant_summary_path),
        "participant_week_matrix_csv": str(participant_week_matrix_path),
        "summary_metrics_csv": str(summary_metrics_path),
    }
    summary_json_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    participant_summary_json_path.write_text(
        participant_summary.to_json(orient="records", force_ascii=False, indent=2),
        encoding="utf-8",
    )
    participant_week_matrix_json_path.write_text(
        participant_week_matrix.to_json(orient="records", force_ascii=False, indent=2),
        encoding="utf-8",
    )

    (OUTPUT_DIR / "bias_in_pravilna_odlocitev.md").write_text(
        build_bias_document(),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "mental_model_pravila_draft.md").write_text(
        build_mental_model_draft(),
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
