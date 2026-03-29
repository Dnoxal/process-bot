import pytest

from process_bot.parser import ParseError, parse_process_command


def test_parse_stage_only_command() -> None:
    parsed = parse_process_command("amazon oa")
    assert parsed.company == "amazon"
    assert parsed.stage == "oa"
    assert parsed.outcome is None


def test_parse_multiword_company_command() -> None:
    parsed = parse_process_command("general motors technical")
    assert parsed.company == "general motors"
    assert parsed.stage == "technical"
    assert parsed.outcome is None


def test_parse_terminal_outcome_only_command() -> None:
    parsed = parse_process_command("stripe offer")
    assert parsed.company == "stripe"
    assert parsed.stage == "final"
    assert parsed.outcome == "offered"


def test_parse_rejection_alias_command() -> None:
    parsed = parse_process_command("google rejection")
    assert parsed.company == "google"
    assert parsed.stage == "final"
    assert parsed.outcome == "rejected"


def test_parse_rej_alias_command() -> None:
    parsed = parse_process_command("google rej")
    assert parsed.company == "google"
    assert parsed.stage == "final"
    assert parsed.outcome == "rejected"


def test_parse_phone_maps_to_behavioral() -> None:
    parsed = parse_process_command("amazon phone")
    assert parsed.company == "amazon"
    assert parsed.stage == "behavioral"
    assert parsed.outcome is None


def test_parse_screen_maps_to_behavioral() -> None:
    parsed = parse_process_command("amazon screen")
    assert parsed.company == "amazon"
    assert parsed.stage == "behavioral"
    assert parsed.outcome is None


def test_parse_onsite_maps_to_technical() -> None:
    parsed = parse_process_command("amazon onsite")
    assert parsed.company == "amazon"
    assert parsed.stage == "technical"
    assert parsed.outcome is None


def test_parse_superday_maps_to_technical() -> None:
    parsed = parse_process_command("amazon superday")
    assert parsed.company == "amazon"
    assert parsed.stage == "technical"
    assert parsed.outcome is None


def test_parse_requires_supported_suffix() -> None:
    with pytest.raises(ParseError):
        parse_process_command("meta maybe")


def test_parse_rejects_legacy_outcome_stage_shape() -> None:
    with pytest.raises(ParseError):
        parse_process_command("google rejected phone")


def test_parse_rejects_legacy_employment_type_shape() -> None:
    with pytest.raises(ParseError):
        parse_process_command("amazon oa intern")
