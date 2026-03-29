import re
from datetime import datetime


STAGE_ALIASES = {
    "apply": "applied",
    "applied": "applied",
    "application": "applied",
    "oa": "oa",
    "onlineassessment": "oa",
    "onlineassessmentround": "oa",
    "recruiter": "recruiter",
    "recruiterscreen": "recruiter",
    "screen": "behavioral",
    "phone": "behavioral",
    "phoneinterview": "phone",
    "technical": "technical",
    "tech": "technical",
    "behavioral": "behavioral",
    "behavioural": "behavioral",
    "behavorial": "behavioral",
    "onsite": "technical",
    "on-site": "technical",
    "superday": "technical",
    "final": "final",
    "finalround": "final",
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
    key = re.sub(r"[^a-z]", "", raw_stage.lower())
    return STAGE_ALIASES.get(key)


def normalize_outcome(raw_outcome: str) -> str | None:
    key = re.sub(r"[^a-z]", "", raw_outcome.lower())
    return OUTCOME_ALIASES.get(key)


def infer_recruiting_season(occurred_at: datetime) -> str:
    if occurred_at.month >= 8:
        return f"Summer {occurred_at.year + 1}"
    return f"Summer {occurred_at.year}"
