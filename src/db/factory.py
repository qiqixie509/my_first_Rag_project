from db.interfaces.base import BaseDatabase
from config import get_settings
from db.interfaces.postgresql import PostgreSQLDatabase
from schemas.config import PostgreSQLSettings


def make_database()->BaseDatabase:
    settings = get_settings()
    config = PostgreSQLSettings(
        database_url=settings.postgres_database_url,
        echo_sql=settings.postgres_echo_sql,
        pool_size=settings.postgres_pool_size,
        max_overflow=settings.postgres_max_overflow,
    )

    database = PostgreSQLDatabase(config)
    database.start_up()
    return database