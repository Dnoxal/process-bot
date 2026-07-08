import re
from datetime import datetime


STAGE_ALIASES = {
    "apply": "oa",
    "applied": "oa",
    "application": "oa",
    "oa": "oa",
    "onlineassessment": "oa",
    "onlineassessmentround": "oa",
    "codesignal": "oa",
    "hackerrank": "oa",
    "recruiter": "behavioral",
    "recruiterscreen": "behavioral",
    "screen": "behavioral",
    "phone": "behavioral",
    "phoneinterview": "behavioral",
    "technical": "technical",
    "tech": "technical",
    "technicalinterview": "technical",
    "technicalround": "technical",
    "technicalone": "technical",
    "technicaltwo": "technical",
    "technicalthree": "technical",
    "technical1": "technical",
    "technical2": "technical",
    "technical3": "technical",
    "techone": "technical",
    "techtwo": "technical",
    "techthree": "technical",
    "tech1": "technical",
    "tech2": "technical",
    "tech3": "technical",
    "interview": "technical",
    "interviews": "technical",
    "behavioral": "behavioral",
    "behavioural": "behavioral",
    "behavorial": "behavioral",
    "onsite": "technical",
    "on-site": "technical",
    "superday": "technical",
    "final": "technical",
    "finalround": "technical",
    "offer": "offer",
    "offered": "offer",
    "accepted": "offer",
    "accept": "offer",
    "rejected": "rejected",
    "reject": "rejected",
    "rej": "rejected",
    "rejection": "rejected",
    "withdrawn": "rejected",
    "withdraw": "rejected",
}

OUTCOME_ALIASES = {
    "advanced": "advanced",
    "advance": "advanced",
    "passed": "advanced",
    "rejected": "rejected",
    "reject": "rejected",
    "rej": "rejected",
    "rejection": "rejected",
    "offer": "offered",
    "offered": "offered",
    "accepted": "accepted",
    "accept": "accepted",
    "withdrawn": "withdrawn",
    "withdraw": "withdrawn",
}

TERMINAL_OUTCOMES = {"offered", "accepted", "rejected", "withdrawn"}
PROCESS_STAGE_ORDER = ("oa", "behavioral", "technical", "offer")
PROCESS_STAGE_LABELS = {
    "oa": "OA",
    "behavioral": "Behavioral",
    "technical": "Technical",
    "offer": "Offer",
    "rejected": "Rejected",
}


def normalize_company_name(company_name: str) -> str:
    cleaned = re.sub(r"\s+", " ", company_name).strip()
    if not cleaned:
        raise ValueError("Company name is required.")
    return " ".join(part.capitalize() if part.islower() else part for part in cleaned.split(" "))


def slugify_company_name(company_name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", company_name.lower()).strip("-")
    if not normalized:
        raise ValueError("Company name must contain letters or numbers.")
    return normalized


def normalize_stage(raw_stage: str) -> str | None:
    key = re.sub(r"[^a-z0-9]", "", raw_stage.lower())
    return STAGE_ALIASES.get(key)


def normalize_outcome(raw_outcome: str) -> str | None:
    key = re.sub(r"[^a-z]", "", raw_outcome.lower())
    return OUTCOME_ALIASES.get(key)


def stage_display_name(stage: str) -> str:
    return PROCESS_STAGE_LABELS.get(stage, stage.replace("_", " ").title())


def ordered_process_distribution(distribution: dict[str, int]) -> dict[str, int]:
    return {stage: distribution.get(stage, 0) for stage in PROCESS_STAGE_ORDER}


def infer_recruiting_season(occurred_at: datetime) -> str:
    if occurred_at.month >= 8:
        return f"Summer {occurred_at.year + 1}"
    return f"Summer {occurred_at.year}"
