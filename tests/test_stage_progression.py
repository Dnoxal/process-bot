from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from process_bot import models, schemas, services


def build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    return session_local()


def test_create_process_event_backfills_missing_previous_stages() -> None:
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
    assert [stage for stage, in stages] == ["oa", "behavioral", "technical"]


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
