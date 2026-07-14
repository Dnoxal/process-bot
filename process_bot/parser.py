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

    for index in range(1, len(tokens)):
        token = tokens[index]
        possible_outcome = normalize_outcome(token)
        possible_stage = normalize_stage(token)

        if not possible_outcome and not possible_stage:
            if normalize_employment_type(token):
                raise ParseError(
                    "Employment type is inferred from the channel. Use `!process <company> <stage>`."
                )
            continue

        company_tokens = tokens[:index]
        reserved_company_token = next(
            (
                company_token
                for company_token in company_tokens
                if normalize_stage(company_token)
                or normalize_outcome(company_token)
                or normalize_employment_type(company_token)
            ),
            None,
        )
        if reserved_company_token:
            raise ParseError(
                "Use `!process <company> <stage>` and put any notes after the stage."
            )

        if not company_tokens:
            raise ParseError("Please include a company name before the stage.")

        if possible_outcome and possible_outcome in TERMINAL_OUTCOMES:
            terminal_stage = "offer" if possible_outcome in {"offered", "accepted"} else "rejected"
            return ParsedProcessCommand(company=" ".join(company_tokens), stage=terminal_stage, outcome=possible_outcome)

        if possible_stage:
            return ParsedProcessCommand(company=" ".join(company_tokens), stage=possible_stage, outcome=None)

    raise ParseError(
        "I couldn't recognize that stage. Try oa, behavioral, technical, offer, or rejection."
    )
