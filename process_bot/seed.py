from __future__ import annotations

from datetime import UTC, datetime, timedelta
import random

from sqlalchemy import select

from process_bot.database import SessionLocal, init_db
from process_bot.models import ProcessEvent
from process_bot import schemas, services


COMPANY_WEIGHTS = [
    ("Amazon", 1.15),
    ("Google", 1.05),
    ("Meta", 0.92),
    ("Microsoft", 0.88),
    ("Apple", 0.74),
    ("Netflix", 0.42),
    ("Pinterest", 0.55),
    ("Stripe", 0.58),
    ("Databricks", 0.64),
    ("NVIDIA", 0.48),
    ("OpenAI", 0.38),
    ("Airbnb", 0.41),
    ("Uber", 0.5),
    ("LinkedIn", 0.33),
    ("Salesforce", 0.29),
    ("Palantir", 0.36),
    ("Robinhood", 0.26),
    ("Jane Street", 0.24),
    ("Capital One", 0.31),
    ("Snowflake", 0.27),
]

FIRST_NAMES = [
    "alex", "jordan", "maria", "sophia", "sam", "nina", "ethan", "maya", "zoe", "noah",
    "liam", "olivia", "ava", "isabella", "amelia", "harper", "charlotte", "evelyn", "abigail", "emily",
    "elizabeth", "mila", "ella", "avery", "sofia", "camila", "aria", "scarlett", "victoria", "madison",
    "luna", "grace", "chloe", "penelope", "layla", "riley", "zoey", "nora", "lily", "eleanor",
    "hannah", "lillian", "addison", "aubrey", "ellie", "stella", "natalie", "leah", "hazel", "violet",
    "aurora", "savannah", "audrey", "brooklyn", "bella", "claire", "skylar", "lucy", "paisley", "everly",
    "anna", "caroline", "nova", "genesis", "emilia", "kennedy", "samantha", "maya", "willow", "kinsley",
]

LAST_NAMES = [
    "kim", "nguyen", "patel", "chen", "singh", "johnson", "williams", "brown", "jones", "garcia",
    "miller", "davis", "rodriguez", "martinez", "hernandez", "lopez", "gonzalez", "wilson", "anderson", "thomas",
    "taylor", "moore", "jackson", "martin", "lee", "perez", "thompson", "white", "harris", "sanchez",
    "clark", "ramirez", "lewis", "robinson", "walker", "young", "allen", "king", "wright", "scott",
    "torres", "hill", "flores", "green", "adams", "nelson", "baker", "hall", "rivera", "campbell",
]

TRACK_WEIGHTS = [("intern", 0.58), ("full_time", 0.42)]

STAGE_PATHS = {
    "intern": [
        [("oa", None), ("behavioral", None), ("technical", None), ("final", "offered")],
        [("oa", None), ("technical", None), ("final", "rejected")],
        [("oa", None), ("behavioral", None), ("final", "rejected")],
        [("oa", None), ("technical", None), ("final", "offered")],
        [("oa", None)],
    ],
    "full_time": [
        [("oa", None), ("behavioral", None), ("technical", None), ("final", "offered")],
        [("oa", None), ("behavioral", None), ("technical", None), ("final", "rejected")],
        [("behavioral", None), ("technical", None), ("final", "offered")],
        [("oa", None), ("technical", None)],
        [("technical", None), ("final", "rejected")],
    ],
}

STAGE_PATH_WEIGHTS = {
    "intern": [0.2, 0.24, 0.2, 0.1, 0.26],
    "full_time": [0.18, 0.26, 0.18, 0.22, 0.16],
}

SMALL_SEED_EVENTS = [
    ("1001", "alex", "Pinterest", "oa", None, "intern", 42),
    ("1001", "alex", "Pinterest", "behavioral", None, "intern", 35),
    ("1001", "alex", "Pinterest", "technical", None, "intern", 27),
    ("1001", "alex", "Pinterest", "final", "offered", "intern", 18),
    ("1002", "maria", "Google", "oa", None, "intern", 50),
    ("1002", "maria", "Google", "behavioral", None, "intern", 39),
    ("1002", "maria", "Google", "final", "rejected", "intern", 28),
    ("1003", "sam", "Meta", "oa", None, "full_time", 46),
    ("1003", "sam", "Meta", "technical", None, "full_time", 29),
    ("1003", "sam", "Meta", "final", "offered", "full_time", 16),
]


def weighted_choice(rng: random.Random, pairs: list[tuple[str, float]]) -> str:
    labels = [label for label, _ in pairs]
    weights = [weight for _, weight in pairs]
    return rng.choices(labels, weights=weights, k=1)[0]


def make_username(index: int, rng: random.Random) -> str:
    first = FIRST_NAMES[index % len(FIRST_NAMES)]
    last = LAST_NAMES[(index * 7) % len(LAST_NAMES)]
    suffix = rng.randint(10, 999)
    return f"{first}_{last}_{suffix}"


def generate_synthetic_events(user_count: int = 1400) -> list[tuple[str, str, str, str, str | None, str, int]]:
    rng = random.Random(20260321)
    synthetic_events: list[tuple[str, str, str, str, str | None, str, int]] = []

    for user_index in range(user_count):
        discord_user_id = f"seed-user-{user_index + 2000}"
        username = make_username(user_index, rng)
        company = weighted_choice(rng, COMPANY_WEIGHTS)
        employment_type = weighted_choice(rng, TRACK_WEIGHTS)
        path = rng.choices(STAGE_PATHS[employment_type], weights=STAGE_PATH_WEIGHTS[employment_type], k=1)[0]

        process_start_days_ago = rng.randint(4, 330)
        current_day = process_start_days_ago

        for stage, outcome in path:
            synthetic_events.append(
                (
                    discord_user_id,
                    username,
                    company,
                    stage,
                    outcome,
                    employment_type,
                    current_day,
                )
            )
            current_day -= rng.randint(2, 18)
            if current_day < 0:
                current_day = 0

    return synthetic_events


def seed_mock_data() -> int:
    init_db()
    inserted = 0
    base_time = datetime.now(UTC)
    generated_events = SMALL_SEED_EVENTS + generate_synthetic_events()

    with SessionLocal() as session:
        for index, (user_id, username, company, stage, outcome, employment_type, days_ago) in enumerate(generated_events, start=1):
            message_id = f"seed-v3-{index}"
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
