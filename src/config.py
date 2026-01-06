import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pydantic import Field, validator

PROJECT_DIR = Path(__file__).parent
ENV_FILE_PATH = PROJECT_DIR / ".env"


class BaseConfigSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".env", str(ENV_FILE_PATH)],
        extra="ignore",
        frozen=True,
        env_nested_delimiter="__",
        case_sensitive=False,
    )


class OpenSearchSettings(BaseConfigSettings):
    model_config = SettingsConfigDict(
        env_file=[".env", str(ENV_FILE_PATH)],
        env_prefix="OPENSEARCH__",
        extra="ignore",
        frozen=True,
        case_sensitive=False,
    )

    host: str = "http://localhost:9200"
    index_name: str = "arxiv-papers"
    chunk_index_suffix: str = "chunks"
    max_text_size: int = 1000000

    # Vector search settings
    vector_dimension: int = 1024
    vector_space_type: str = "cosinesimil"

    # Hybrid search settings
    rrf_pipeline_name: str = "hybrid-rrf-pipeline"
    hybrid_search_size_multiplier: int = 2  # Get k*multiplier for better recall


class RedisSetting(BaseConfigSettings):
    model_config = SettingsConfigDict(
        env_file=[".env", str(ENV_FILE_PATH)],
        env_prefix="REDIS__",
        extra="ignore",
        frozen=True,
        case_sensitive=False,
    )
    
    host: str = "localhost"
    port: int = 6379
    password: str = ""
    db: int = 0
    decode_responses: bool = True
    socket_timeout: int = 30
    socket_connect_timeout: int = 30
    ttl_hours: int = 6 # Cache TTL in hours
    

class Settings(BaseConfigSettings):
    app_version: str = "0.0.1"
    debug: bool = True
    enviornment: Literal["development", "staging", "production"] = "development"
    service_name: str = "rag-api"
    
    postgres_database_url: str = "postgresql://rag_user:rag_password@localhost:5432/rag_db"
    postgres_echo_sql: bool = False
    postgres_pool_size: int = 5
    postgres_max_overflow: int = 0

    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:1b"
    ollama_timeout: int = 300

    opensearch: OpenSearchSettings = Field(default_factory=OpenSearchSettings)
    redis: RedisSetting = Field(default_factory=RedisSetting)


    @validator("postgres_database_url") 
    @classmethod
    def validate_database_url(cls, v:str)-> str:
        if not (v.startswith("postgresql://") or v.startswith("postgresql+psycopg2://")):
            raise ValueError("Database URL must start with 'postgresql://' or 'postgresql+psycopg2://'")
        return v    
    
def get_settings() -> Settings:
    return Settings()