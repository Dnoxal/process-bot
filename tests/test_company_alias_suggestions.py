from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from process_bot import models, services



def build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    return session_local()



def test_known_alias_returns_suggestion_for_new_company() -> None:
    with build_session() as session:
        suggestion = services.suggest_company_from_alias(session, "zon")

    assert suggestion is not None
    assert suggestion.alias == "zon"
    assert suggestion.canonical_name == "Amazon"



def test_known_alias_does_not_prompt_after_alias_is_saved() -> None:
    with build_session() as session:
        company = services.get_or_create_company(session, "Amazon")
        services.create_company_alias(session, company.slug, "zon")
        session.commit()

        suggestion = services.suggest_company_from_alias(session, "zon")

    assert suggestion is None


def test_known_alias_still_prompts_when_alias_was_saved_as_company_name() -> None:
    with build_session() as session:
        services.get_or_create_company(session, "Zon")
        session.commit()

        suggestion = services.suggest_company_from_alias(session, "zon")

    assert suggestion is not None
    assert suggestion.alias == "zon"
    assert suggestion.canonical_name == "Amazon"


def test_popular_abbreviations_return_expected_companies() -> None:
    expected = {
        "hrt": "Hudson River Trading",
        "oai": "OpenAI",
        "c1": "Capital One",
        "jp": "JP Morgan",
        "jpmc": "JP Morgan",
        "jpm": "JP Morgan",
        "lhm": "Lockheed Martin",
        "wf": "Wells Fargo",
        "js": "Jane Street",
        "sig": "Susquehanna International Group",
    }

    with build_session() as session:
        for alias, canonical_name in expected.items():
            suggestion = services.suggest_company_from_alias(session, alias)
            assert suggestion is not None
            assert suggestion.alias == alias
            assert suggestion.canonical_name == canonical_name
