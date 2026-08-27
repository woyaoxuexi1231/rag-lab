"""本机 CPU Embedding — BAAI/bge-small-zh-v1.5。"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Sequence

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class Embedder:
    """懒加载 sentence-transformers，避免启动时立刻下载模型。"""

    def __init__(self, model_name: str, dim: int) -> None:
        self.model_name = model_name
        self.dim = dim
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            logger.info("Loading embedding model: %s", self.model_name)
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        model = self._ensure_model()
        # bge 检索：query 侧建议加指令前缀；文档侧原样
        vectors = model.encode(
            list(texts),
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [v.tolist() for v in vectors]

    def encode_query(self, text: str) -> list[float]:
        # bge-zh 官方推荐 query 前缀
        prefixed = f"为这个句子生成表示以用于检索相关文章：{text}"
        return self.encode([prefixed])[0]

    def encode_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self.encode(texts)

    def ready(self) -> dict:
        try:
            self._ensure_model()
            return {"ok": True, "model": self.model_name, "dim": self.dim}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "model": self.model_name, "error": str(exc)}


@lru_cache
def get_embedder() -> Embedder:
    settings: Settings = get_settings()
    return Embedder(settings.embed_model, settings.embed_dim)
