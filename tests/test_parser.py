import pytest

from process_bot.parser import ParseError, parse_process_command


def test_parse_stage_only_command() -> None:
    parsed = parse_process_command("amazon oa")
    assert parsed.company == "amazon"
    assert parsed.stage == "oa"
    assert parsed.outcome is None


def test_parse_outcome_and_stage_command() -> None:
    parsed = parse_process_command("google rejected phone")
    assert parsed.company == "google"
    assert parsed.stage == "phone"
    assert parsed.outcome == "rejected"


def test_parse_terminal_outcome_only_command() -> None:
    parsed = parse_process_command("stripe offer")
    assert parsed.company == "stripe"
    assert parsed.stage == "final"
    assert parsed.outcome == "offered"


def test_parse_requires_supported_suffix() -> None:
    with pytest.raises(ParseError):
        parse_process_command("meta maybe")
