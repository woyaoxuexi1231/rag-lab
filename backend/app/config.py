"""应用配置 — 全部可通过环境变量 / .env 覆盖。"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "phones"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    milvus_uri: str = "http://localhost:19530"
    milvus_collection: str = "phone_kb"

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5"

    embed_model: str = "BAAI/bge-small-zh-v1.5"
    embed_dim: int = 512

    rag_top_k: int = 5
    rag_score_threshold: float = 0.35

    app_host: str = "0.0.0.0"
    app_port: int = 18100


@lru_cache
def get_settings() -> Settings:
    return Settings()
