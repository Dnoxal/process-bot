from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from process_bot.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()

if settings.database_url.startswith("sqlite:///"):
    db_path = Path(settings.database_url.removeprefix("sqlite:///"))
    db_path.parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    from process_bot import models

    Base.metadata.create_all(bind=engine)
    run_migrations()


def run_migrations() -> None:
    inspector = inspect(engine)
    if "process_events" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("process_events")}
    if "employment_type" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE process_events ADD COLUMN employment_type VARCHAR(32)"))
