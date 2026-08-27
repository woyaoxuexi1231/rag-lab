"""检索层：topK + 引用整理。"""

from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.rag.milvus_store import MilvusStore, get_milvus_store


class Retriever:
    def __init__(self, store: MilvusStore | None = None) -> None:
        self.store = store or get_milvus_store()
        self.settings = get_settings()

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
        return self.store.search(query, top_k=top_k or self.settings.rag_top_k)

    def build_context(self, hits: list[dict[str, Any]]) -> str:
        if not hits:
            return "（知识库中未检索到相关机型资料）"
        blocks: list[str] = []
        for i, hit in enumerate(hits, start=1):
            blocks.append(
                f"[{i}] {hit.get('brand', '')} {hit.get('name', '')}\n{hit.get('text', '')}"
            )
        return "\n\n".join(blocks)

    def citations(self, hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "id": h.get("id"),
                "brand": h.get("brand"),
                "name": h.get("name"),
                "year": h.get("year"),
                "price_cny": h.get("price_cny"),
                "score": round(float(h.get("score", 0)), 4),
            }
            for h in hits
        ]


def get_retriever() -> Retriever:
    return Retriever()
