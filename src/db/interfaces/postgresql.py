from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy import create_engine, text, inspect
from typing import Optional, Generator
import logging
from db.interfaces.base import BaseDatabase
from schemas.database.config import PostgreSQLSettings

logger = logging.getLogger(__name__)

Base = declarative_base()

class PostgreSQLDatabase(BaseDatabase):
    def __init__(self, config: PostgreSQLSettings):
        self.config = config
        self.engine: Optional[Engine] = None
        self.session_factory: Optional[sessionmaker] = None

    def start_up(self):
        try:
            logger.info(
                f"Attempting to connect to PostgreSQL database at {self.config.database_url.split('@')[1] if '@' in self.config.database_url else 'localhost'}"
            )

            self.engine = create_engine(
                self.config.database_url,
                echo=self.config.echo_sql,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_pre_ping=True,
            )
            
            self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)

            # Test the connection
            assert self.engine is not None
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                logging.info("Database connection test successful")
            
            # Check the tables exist before creating
            inspector = inspect(self.engine)
            existing_tables = inspector.get_table_names()

            # Create tables if they don't exist
            Base.metadata.create_all(self.engine)

            # Check if any new tables were created
            new_tables = inspector.get_table_names()
            created_tables = set(new_tables) - set(existing_tables)
            if created_tables:
                logger.info(f"Created new tables: {created_tables}")
            else:
                logger.info("All tables already exist - no new tables created")

            logger.info("PostgreSQL database initialized successfully")
            assert self.engine is not None
            logger.info(f"Database: {self.engine.url.database}")
            # logger.info(f"Total tables: {', '.join(updated_tables) if updated_tables else 'None'}") # Variable updated_tables not defined
            logger.info("Database connection established")

        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL database: {e}")
            raise

    def teardown(self):
        # self.session is not defined in __init__, and usually teardown closes engine. 
        # Session scope is handled in get_session
        if self.engine:
            self.engine.dispose()
            logger.info("PostgreSQL database connection closed")

    def get_session(self) -> Generator[Session, None, None]:
        if not self.session_factory:
            raise Exception("Session factory not initialized")
        session = self.session_factory()
        try:
            yield session
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

