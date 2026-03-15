from dataclasses import dataclass

from process_bot.normalization import TERMINAL_OUTCOMES, normalize_outcome, normalize_stage


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
        raise ParseError("Usage: !process <company> <stage> or !process <company> <outcome> <stage>")

    possible_stage = normalize_stage(tokens[-1])
    possible_outcome = normalize_outcome(tokens[-2]) if len(tokens) >= 3 else None

    if possible_stage:
        company_tokens = tokens[:-1]
        outcome = None
        if possible_outcome:
            company_tokens = tokens[:-2]
            outcome = possible_outcome
        if not company_tokens:
            raise ParseError("Please include a company name before the stage.")
        return ParsedProcessCommand(company=" ".join(company_tokens), stage=possible_stage, outcome=outcome)

    possible_outcome = normalize_outcome(tokens[-1])
    if possible_outcome and possible_outcome in TERMINAL_OUTCOMES:
        company_tokens = tokens[:-1]
        if not company_tokens:
            raise ParseError("Please include a company name before the outcome.")
        return ParsedProcessCommand(company=" ".join(company_tokens), stage="final", outcome=possible_outcome)

    raise ParseError(
        "I couldn't recognize that stage/outcome. Try stages like oa, phone, onsite, final or outcomes like rejected, offered."
    )
