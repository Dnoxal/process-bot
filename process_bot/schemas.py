from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class CompanyAliasCreate(BaseModel):
    company_slug: str
    alias: str = Field(min_length=1, max_length=255)


class ProcessEventCreate(BaseModel):
    discord_user_id: str
    username: str
    company: str
    stage: str
    outcome: str | None = None
    notes: str | None = None
    discord_message_id: str
    channel_id: str
    occurred_at: datetime | None = None
    source_command: str | None = None


class ProcessEventUpdate(BaseModel):
    stage: str | None = None
    outcome: str | None = None
    notes: str | None = None


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class ProcessEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    company_slug: str
    stage: str
    outcome: str | None
    recruiting_season: str | None
    notes: str | None
    occurred_at: datetime
    username: str


class GlobalStatsResponse(BaseModel):
    total_events: int
    total_users: int
    total_companies: int
    stage_distribution: dict[str, int]
    outcome_distribution: dict[str, int]
    top_companies: list[dict[str, int | str]]


class CompanyStatsResponse(BaseModel):
    company: str
    slug: str
    total_events: int
    total_candidates: int
    latest_activity: datetime | None
    stage_distribution: dict[str, int]
    outcome_distribution: dict[str, int]


class TrendPoint(BaseModel):
    period_start: str
    events: int
