from dataclasses import dataclass

from process_bot.normalization import TERMINAL_OUTCOMES, normalize_outcome, normalize_stage
from process_bot.services import normalize_employment_type


class ParseError(ValueError):
    pass


@dataclass(slots=True)
class ParsedProcessCommand:
    company: str
    stage: str
    outcome: str | None


def parse_process_command(command_body: str) -> ParsedProcessCommand:
    tokens = [token for token in command_body.strip().split() if token]
    if len(tokens) < 2:
        raise ParseError("Usage: !process <company> <stage>")

    if len(tokens) >= 3:
        reserved_token = next(
            (
                token
                for token in tokens[:-1]
                if normalize_stage(token) or normalize_outcome(token) or normalize_employment_type(token)
            ),
            None,
        )
        if reserved_token:
            raise ParseError(
                "Use exactly one stage token at the end: !process <company> <stage>."
            )

    possible_stage = normalize_stage(tokens[-1])

    if possible_stage:
        if not tokens[:-1]:
            raise ParseError("Please include a company name before the stage.")
        return ParsedProcessCommand(company=" ".join(tokens[:-1]), stage=possible_stage, outcome=None)

    possible_outcome = normalize_outcome(tokens[-1])
    if possible_outcome and possible_outcome in TERMINAL_OUTCOMES:
        if not tokens[:-1]:
            raise ParseError("Please include a company name before the outcome.")
        return ParsedProcessCommand(company=" ".join(tokens[:-1]), stage="final", outcome=possible_outcome)

    raise ParseError(
        "I couldn't recognize that stage. Try oa, behavioral, technical, offer, or rejection."
    )
