from datetime import datetime, timezone

from PIL import Image

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


def test_build_company_stats_card_handles_long_company_names() -> None:
    stats = schemas.CompanyStatsResponse(
        company="International Wastewater Revenue Alpha Holdings Municipal Research Collective",
        slug="municipal-research",
        total_events=7,
        total_candidates=5,
        latest_activity=datetime(2026, 7, 8, tzinfo=timezone.utc),
        stage_distribution={"oa": 3, "behavioral": 2, "technical": 1, "offer": 1},
        outcome_distribution={"offered": 1, "rejected": 1},
    )

    image_bytes = build_company_stats_card(stats)
    image = Image.open(image_bytes)

    assert image.size == (1200, 820)
