from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class CompanyAliasCreate(BaseModel):
    company_slug: str = Field(min_length=1, max_length=255)
    alias: str = Field(min_length=1, max_length=255)


class ProcessEventCreate(BaseModel):
    discord_user_id: str = Field(min_length=1, max_length=32)
    username: str = Field(min_length=1, max_length=255)
    company: str = Field(min_length=1, max_length=255)
    stage: str = Field(min_length=1, max_length=64)
    outcome: str | None = Field(default=None, max_length=64)
    employment_type: str | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=2000)
    discord_message_id: str = Field(min_length=1, max_length=128)
    channel_id: str = Field(min_length=1, max_length=128)
    occurred_at: datetime | None = None
    source_command: str | None = Field(default=None, max_length=2000)


class ProcessEventUpdate(BaseModel):
    stage: str | None = Field(default=None, max_length=64)
    outcome: str | None = Field(default=None, max_length=64)
    employment_type: str | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=2000)


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
    employment_type: str | None
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


class NamedCount(BaseModel):
    label: str
    value: int


class FunnelPoint(BaseModel):
    label: str
    value: float


class RecentOffer(BaseModel):
    company: str
    company_slug: str
    occurred_at: datetime


class DashboardOverviewResponse(BaseModel):
    total_events: int
    total_candidates: int
    total_companies: int
    offers: int
    stage_distribution: dict[str, int]
    outcome_distribution: dict[str, int]
    employment_distribution: dict[str, int]
    top_companies: list[NamedCount]
    trend_points: list[TrendPoint]
    recent_offers: list[RecentOffer]


class DashboardCompanyResponse(BaseModel):
    company: str
    slug: str
    employment_type: str
    total_events: int
    total_candidates: int
    offers: int
    latest_activity: datetime | None
    stage_distribution: dict[str, int]
    outcome_distribution: dict[str, int]
    trend_points: list[TrendPoint]
    funnel_points: list[FunnelPoint]
