from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select

from process_bot.database import SessionLocal, init_db
from process_bot.models import ProcessEvent
from process_bot import schemas, services


SEED_EVENTS = [
    ("1001", "alex", "Pinterest", "oa", None, "intern", 42),
    ("1001", "alex", "Pinterest", "behavioral", None, "intern", 35),
    ("1001", "alex", "Pinterest", "onsite", None, "intern", 27),
    ("1001", "alex", "Pinterest", "final", "offered", "intern", 18),
    ("1002", "maria", "Google", "oa", None, "intern", 50),
    ("1002", "maria", "Google", "behavioral", None, "intern", 39),
    ("1002", "maria", "Google", "final", "rejected", "intern", 28),
    ("1003", "sam", "Meta", "oa", None, "full_time", 46),
    ("1003", "sam", "Meta", "onsite", None, "full_time", 29),
    ("1003", "sam", "Meta", "final", "offered", "full_time", 16),
    ("1004", "nina", "Amazon", "oa", None, "full_time", 48),
    ("1004", "nina", "Amazon", "behavioral", None, "full_time", 33),
    ("1004", "nina", "Amazon", "onsite", None, "full_time", 22),
    ("1004", "nina", "Amazon", "final", "rejected", "full_time", 12),
    ("1005", "leo", "Netflix", "behavioral", None, "full_time", 26),
    ("1005", "leo", "Netflix", "onsite", None, "full_time", 17),
    ("1005", "leo", "Netflix", "final", "offered", "full_time", 7),
    ("1006", "ivy", "Apple", "oa", None, "intern", 43),
    ("1006", "ivy", "Apple", "behavioral", None, "intern", 31),
    ("1006", "ivy", "Apple", "final", "rejected", "intern", 20),
    ("1007", "omar", "Microsoft", "oa", None, "intern", 41),
    ("1007", "omar", "Microsoft", "onsite", None, "intern", 24),
    ("1007", "omar", "Microsoft", "final", "offered", "intern", 9),
    ("1008", "zoe", "Databricks", "oa", None, "full_time", 36),
    ("1008", "zoe", "Databricks", "behavioral", None, "full_time", 23),
    ("1008", "zoe", "Databricks", "onsite", None, "full_time", 14),
    ("1008", "zoe", "Databricks", "final", "offered", "full_time", 4),
    ("1009", "jay", "Stripe", "oa", None, "intern", 34),
    ("1009", "jay", "Stripe", "onsite", None, "intern", 19),
    ("1009", "jay", "Stripe", "final", "rejected", "intern", 8),
    ("1010", "maya", "FAANG", "oa", None, "intern", 30),
    ("1010", "maya", "FAANG", "behavioral", None, "intern", 21),
    ("1010", "maya", "FAANG", "onsite", None, "intern", 11),
    ("1011", "ethan", "Pinterest", "oa", None, "full_time", 31),
    ("1011", "ethan", "Pinterest", "onsite", None, "full_time", 15),
    ("1011", "ethan", "Pinterest", "final", "offered", "full_time", 5),
    ("1012", "sophia", "Google", "oa", None, "full_time", 27),
    ("1012", "sophia", "Google", "behavioral", None, "full_time", 18),
    ("1012", "sophia", "Google", "onsite", None, "full_time", 10),
    ("1013", "noah", "Amazon", "oa", None, "intern", 25),
    ("1013", "noah", "Amazon", "final", "rejected", "intern", 13),
]


def seed_mock_data() -> int:
    init_db()
    inserted = 0
    base_time = datetime.utcnow()

    with SessionLocal() as session:
        for index, (user_id, username, company, stage, outcome, employment_type, days_ago) in enumerate(SEED_EVENTS, start=1):
            message_id = f"seed-{user_id}-{index}"
            existing = session.scalar(select(ProcessEvent.id).where(ProcessEvent.discord_message_id == message_id))
            if existing:
                continue
            payload = schemas.ProcessEventCreate(
                discord_user_id=user_id,
                username=username,
                company=company,
                stage=stage,
                outcome=outcome,
                employment_type=employment_type,
                discord_message_id=message_id,
                channel_id="seed-channel",
                occurred_at=base_time - timedelta(days=days_ago),
                source_command="seed",
            )
            services.create_process_event(session, payload)
            inserted += 1
        session.commit()
    return inserted


if __name__ == "__main__":
    count = seed_mock_data()
    print(f"Seeded {count} mock events.")
