from datetime import datetime, timezone

from process_bot import schemas
from process_bot.stats_card import build_company_stats_card


def test_build_company_stats_card_returns_png() -> None:
    stats = schemas.CompanyStatsResponse(
        company="Example Co",
        slug="example-co",
        total_events=12,
        total_candidates=8,
        latest_activity=datetime(2026, 7, 7, tzinfo=timezone.utc),
        stage_distribution={"oa": 5, "technical": 4, "offer": 3},
        outcome_distribution={"advanced": 6, "offered": 3, "rejected": 2},
    )

    image = build_company_stats_card(stats)

    assert image.getvalue().startswith(b"\x89PNG\r\n\x1a\n")
    assert len(image.getvalue()) > 1000
