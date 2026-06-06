from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from process_bot import models, schemas, services


def build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    return session_local()


def test_create_process_event_does_not_backfill_without_company_stage_history() -> None:
    with build_session() as session:
        event = services.create_process_event(
            session,
            schemas.ProcessEventCreate(
                discord_user_id="user-1",
                username="tester",
                company="Amazon",
                stage="technical",
                employment_type="intern",
                discord_message_id="msg-1",
                channel_id="chan-1",
                source_command="!process amazon technical",
            ),
        )
        session.commit()

        stages = session.query(models.ProcessEvent.stage).order_by(models.ProcessEvent.id.asc()).all()

    assert event.stage == "technical"
    assert [stage for stage, in stages] == ["technical"]


def test_create_process_event_backfills_only_observed_company_stages() -> None:
    with build_session() as session:
        services.create_process_event(
            session,
            schemas.ProcessEventCreate(
                discord_user_id="user-2",
                username="other",
                company="Amazon",
                stage="oa",
                employment_type="intern",
                discord_message_id="msg-1",
                channel_id="chan-1",
                source_command="!process amazon oa",
            ),
        )
        services.create_process_event(
            session,
            schemas.ProcessEventCreate(
                discord_user_id="user-2",
                username="other",
                company="Amazon",
                stage="behavioral",
                employment_type="intern",
                discord_message_id="msg-2",
                channel_id="chan-1",
                source_command="!process amazon behavioral",
            ),
        )
        event = services.create_process_event(
            session,
            schemas.ProcessEventCreate(
                discord_user_id="user-1",
                username="tester",
                company="Amazon",
                stage="technical",
                employment_type="intern",
                discord_message_id="msg-3",
                channel_id="chan-1",
                source_command="!process amazon technical",
            ),
        )
        session.commit()

        user_stages = (
            session.query(models.ProcessEvent.stage)
            .join(models.User)
            .where(models.User.discord_user_id == "user-1")
            .order_by(models.ProcessEvent.id.asc())
            .all()
        )

    assert event.stage == "technical"
    assert [stage for stage, in user_stages] == ["oa", "behavioral", "technical"]


def test_create_process_event_ignores_duplicate_stage_for_same_track_and_season() -> None:
    with build_session() as session:
        first = services.create_process_event(
            session,
            schemas.ProcessEventCreate(
                discord_user_id="user-1",
                username="tester",
                company="Pinterest",
                stage="oa",
                employment_type="intern",
                discord_message_id="msg-1",
                channel_id="chan-1",
                occurred_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
                source_command="!process pinterest oa",
            ),
        )
        second = services.create_process_event(
            session,
            schemas.ProcessEventCreate(
                discord_user_id="user-1",
                username="tester",
                company="Pinterest",
                stage="oa",
                employment_type="intern",
                discord_message_id="msg-2",
                channel_id="chan-1",
                occurred_at=datetime(2026, 9, 2, tzinfo=timezone.utc),
                source_command="!process pinterest oa",
            ),
        )
        session.commit()

        event_count = session.query(models.ProcessEvent).count()

    assert second.id == first.id
    assert event_count == 1


def test_create_process_event_allows_same_stage_for_different_track_or_season() -> None:
    with build_session() as session:
        services.create_process_event(
            session,
            schemas.ProcessEventCreate(
                discord_user_id="user-1",
                username="tester",
                company="Pinterest",
                stage="oa",
                employment_type="intern",
                discord_message_id="msg-1",
                channel_id="chan-1",
                occurred_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
                source_command="!process pinterest oa",
            ),
        )
        services.create_process_event(
            session,
            schemas.ProcessEventCreate(
                discord_user_id="user-1",
                username="tester",
                company="Pinterest",
                stage="oa",
                employment_type="full_time",
                discord_message_id="msg-2",
                channel_id="chan-1",
                occurred_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
                source_command="!process pinterest oa",
            ),
        )
        services.create_process_event(
            session,
            schemas.ProcessEventCreate(
                discord_user_id="user-1",
                username="tester",
                company="Pinterest",
                stage="oa",
                employment_type="intern",
                discord_message_id="msg-3",
                channel_id="chan-1",
                occurred_at=datetime(2027, 9, 1, tzinfo=timezone.utc),
                source_command="!process pinterest oa",
            ),
        )
        session.commit()

        event_count = session.query(models.ProcessEvent).count()

    assert event_count == 3


def test_dashboard_company_funnel_counts_implied_previous_stages() -> None:
    with build_session() as session:
        services.create_process_event(
            session,
            schemas.ProcessEventCreate(
                discord_user_id="user-1",
                username="tester",
                company="Amazon",
                stage="technical",
                employment_type="intern",
                discord_message_id="msg-1",
                channel_id="chan-1",
                source_command="!process amazon technical",
            ),
        )
        session.commit()

        company = services.find_company(session, "Amazon")
        result = services.dashboard_company(session, company.slug, employment_type="all")

    assert result is not None
    assert result.funnel_points == [
        schemas.FunnelPoint(label="OA", value=100.0),
        schemas.FunnelPoint(label="Behavioral", value=100.0),
        schemas.FunnelPoint(label="Technical", value=100.0),
    ]


def test_dashboard_overview_includes_recent_offer_companies_without_usernames() -> None:
    with build_session() as session:
        services.create_process_event(
            session,
            schemas.ProcessEventCreate(
                discord_user_id="user-1",
                username="tester",
                company="Pinterest",
                stage="final",
                outcome="offered",
                employment_type="intern",
                discord_message_id="msg-1",
                channel_id="chan-1",
                occurred_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
                source_command="!process pinterest offer",
            ),
        )
        session.commit()

        result = services.dashboard_overview(session, employment_type="all")
        serialized_offer = result.recent_offers[0].model_dump()

    assert result.recent_offers[0].company == "Pinterest"
    assert "username" not in serialized_offer
