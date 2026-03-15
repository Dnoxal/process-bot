from collections import Counter
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from process_bot import models, schemas
from process_bot.normalization import (
    infer_recruiting_season,
    normalize_company_name,
    normalize_outcome,
    normalize_stage,
    slugify_company_name,
)


def get_or_create_user(session: Session, discord_user_id: str, username: str) -> models.User:
    user = session.scalar(select(models.User).where(models.User.discord_user_id == discord_user_id))
    if user:
        user.username = username
        return user

    user = models.User(discord_user_id=discord_user_id, username=username)
    session.add(user)
    session.flush()
    return user


def get_or_create_company(session: Session, company_name: str) -> models.Company:
    normalized_name = normalize_company_name(company_name)
    slug = slugify_company_name(normalized_name)

    company = find_company(session, company_name)
    if company:
        return company

    company = models.Company(name=normalized_name, slug=slug)
    session.add(company)
    session.flush()
    return company


def find_company(session: Session, company_name: str) -> models.Company | None:
    normalized_name = normalize_company_name(company_name)
    slug = slugify_company_name(normalized_name)

    company = session.scalar(
        select(models.Company)
        .options(joinedload(models.Company.aliases))
        .where((models.Company.slug == slug) | (models.Company.name == normalized_name))
    )
    if company:
        return company

    alias_match = session.scalar(
        select(models.CompanyAlias).options(joinedload(models.CompanyAlias.company)).where(models.CompanyAlias.alias == slug)
    )
    return alias_match.company if alias_match else None


def create_company_alias(session: Session, company_slug: str, alias: str) -> models.CompanyAlias:
    company = session.scalar(select(models.Company).where(models.Company.slug == company_slug))
    if not company:
        raise ValueError(f"Unknown company slug: {company_slug}")

    normalized_alias = slugify_company_name(alias)
    existing = session.scalar(select(models.CompanyAlias).where(models.CompanyAlias.alias == normalized_alias))
    if existing:
        return existing

    company_alias = models.CompanyAlias(company_id=company.id, alias=normalized_alias)
    session.add(company_alias)
    session.flush()
    return company_alias


def create_process_event(session: Session, payload: schemas.ProcessEventCreate) -> models.ProcessEvent:
    stage = normalize_stage(payload.stage)
    if not stage:
        raise ValueError(f"Unsupported stage: {payload.stage}")

    outcome = normalize_outcome(payload.outcome) if payload.outcome else None
    company = get_or_create_company(session, payload.company)
    user = get_or_create_user(session, discord_user_id=payload.discord_user_id, username=payload.username)
    occurred_at = payload.occurred_at or datetime.utcnow()

    existing = session.scalar(
        select(models.ProcessEvent).where(models.ProcessEvent.discord_message_id == payload.discord_message_id)
    )
    if existing:
        return existing

    event = models.ProcessEvent(
        user_id=user.id,
        company_id=company.id,
        stage=stage,
        outcome=outcome,
        notes=payload.notes,
        recruiting_season=infer_recruiting_season(occurred_at),
        discord_message_id=payload.discord_message_id,
        channel_id=payload.channel_id,
        occurred_at=occurred_at,
        source_command=payload.source_command,
    )
    session.add(event)
    session.flush()
    session.refresh(event)
    return event


def list_user_processes(session: Session, discord_user_id: str) -> list[schemas.ProcessEventResponse]:
    events = session.scalars(
        select(models.ProcessEvent)
        .join(models.User)
        .join(models.Company)
        .where(models.User.discord_user_id == discord_user_id)
        .order_by(models.ProcessEvent.occurred_at.desc())
    ).all()
    return [serialize_process_event(event) for event in events]


def list_companies(session: Session) -> list[models.Company]:
    return session.scalars(select(models.Company).order_by(models.Company.name.asc())).all()


def list_all_process_events(session: Session) -> list[schemas.ProcessEventResponse]:
    events = session.scalars(
        select(models.ProcessEvent).join(models.Company).join(models.User).order_by(models.ProcessEvent.occurred_at.desc())
    ).all()
    return [serialize_process_event(event) for event in events]


def update_process_event(session: Session, event_id: int, payload: schemas.ProcessEventUpdate) -> models.ProcessEvent | None:
    event = session.get(models.ProcessEvent, event_id)
    if not event:
        return None

    if payload.stage is not None:
        stage = normalize_stage(payload.stage)
        if not stage:
            raise ValueError(f"Unsupported stage: {payload.stage}")
        event.stage = stage
    if payload.outcome is not None:
        if payload.outcome == "":
            event.outcome = None
        else:
            outcome = normalize_outcome(payload.outcome)
            if not outcome:
                raise ValueError(f"Unsupported outcome: {payload.outcome}")
            event.outcome = outcome
    if payload.notes is not None:
        event.notes = payload.notes
    session.flush()
    session.refresh(event)
    return event


def delete_process_event(session: Session, event_id: int) -> bool:
    event = session.get(models.ProcessEvent, event_id)
    if not event:
        return False
    session.delete(event)
    session.flush()
    return True


def serialize_process_event(event: models.ProcessEvent) -> schemas.ProcessEventResponse:
    return schemas.ProcessEventResponse(
        id=event.id,
        company=event.company.name,
        company_slug=event.company.slug,
        stage=event.stage,
        outcome=event.outcome,
        recruiting_season=event.recruiting_season,
        notes=event.notes,
        occurred_at=event.occurred_at,
        username=event.user.username,
    )


def global_stats(session: Session) -> schemas.GlobalStatsResponse:
    total_events = session.scalar(select(func.count(models.ProcessEvent.id))) or 0
    total_users = session.scalar(select(func.count(models.User.id))) or 0
    total_companies = session.scalar(select(func.count(models.Company.id))) or 0

    stage_counts = Counter(
        dict(session.execute(select(models.ProcessEvent.stage, func.count()).group_by(models.ProcessEvent.stage)).all())
    )
    outcome_counts = Counter(
        dict(
            session.execute(
                select(models.ProcessEvent.outcome, func.count())
                .where(models.ProcessEvent.outcome.is_not(None))
                .group_by(models.ProcessEvent.outcome)
            ).all()
        )
    )
    top_companies_rows = session.execute(
        select(models.Company.name, func.count(models.ProcessEvent.id).label("events"))
        .join(models.ProcessEvent)
        .group_by(models.Company.id)
        .order_by(func.count(models.ProcessEvent.id).desc(), models.Company.name.asc())
        .limit(10)
    ).all()

    return schemas.GlobalStatsResponse(
        total_events=total_events,
        total_users=total_users,
        total_companies=total_companies,
        stage_distribution=dict(stage_counts),
        outcome_distribution={key: value for key, value in outcome_counts.items() if key},
        top_companies=[{"company": row[0], "events": row[1]} for row in top_companies_rows],
    )


def company_stats(session: Session, company_slug: str) -> schemas.CompanyStatsResponse | None:
    company = session.scalar(select(models.Company).where(models.Company.slug == company_slug))
    if not company:
        return None

    rows = session.scalars(select(models.ProcessEvent).where(models.ProcessEvent.company_id == company.id)).all()
    stage_counts = Counter(row.stage for row in rows)
    outcome_counts = Counter(row.outcome for row in rows if row.outcome)
    latest_activity = max((row.occurred_at for row in rows), default=None)
    total_candidates = len({row.user_id for row in rows})
    return schemas.CompanyStatsResponse(
        company=company.name,
        slug=company.slug,
        total_events=len(rows),
        total_candidates=total_candidates,
        latest_activity=latest_activity,
        stage_distribution=dict(stage_counts),
        outcome_distribution=dict(outcome_counts),
    )


def event_trends(session: Session, company_slug: str | None = None) -> list[schemas.TrendPoint]:
    query = select(func.date(models.ProcessEvent.occurred_at).label("period_start"), func.count(models.ProcessEvent.id))
    if company_slug:
        company = session.scalar(select(models.Company).where(models.Company.slug == company_slug))
        if not company:
            return []
        query = query.where(models.ProcessEvent.company_id == company.id)

    rows = session.execute(
        query.group_by(func.date(models.ProcessEvent.occurred_at)).order_by(func.date(models.ProcessEvent.occurred_at).asc())
    ).all()
    return [schemas.TrendPoint(period_start=str(row[0]), events=row[1]) for row in rows]
