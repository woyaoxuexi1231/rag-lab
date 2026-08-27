"""Milvus 向量存储：集合创建、upsert、search。"""

from __future__ import annotations

import logging
from typing import Any

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from app.config import Settings, get_settings
from app.rag.embedder import Embedder, get_embedder

logger = logging.getLogger(__name__)


class MilvusStore:
    def __init__(self, settings: Settings | None = None, embedder: Embedder | None = None) -> None:
        self.settings = settings or get_settings()
        self.embedder = embedder or get_embedder()
        self._connected = False

    def connect(self) -> None:
        if self._connected:
            return
        connections.connect(alias="default", uri=self.settings.milvus_uri)
        self._connected = True
        logger.info("Connected to Milvus at %s", self.settings.milvus_uri)

    def ensure_collection(self, drop_existing: bool = False) -> Collection:
        self.connect()
        name = self.settings.milvus_collection
        if drop_existing and utility.has_collection(name):
            utility.drop_collection(name)
            logger.info("Dropped collection %s", name)

        if utility.has_collection(name):
            col = Collection(name)
            col.load()
            return col

        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema(name="brand", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="year", dtype=DataType.INT64),
            FieldSchema(name="price_cny", dtype=DataType.INT64),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=8192),
            FieldSchema(name="meta_json", dtype=DataType.VARCHAR, max_length=8192),
            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=self.settings.embed_dim,
            ),
        ]
        schema = CollectionSchema(fields, description="Smartphone RAG knowledge base")
        col = Collection(name, schema)
        col.create_index(
            "embedding",
            {
                "index_type": "IVF_FLAT",
                "metric_type": "IP",
                "params": {"nlist": 128},
            },
        )
        col.load()
        logger.info("Created collection %s", name)
        return col

    def upsert_documents(self, docs: list[dict[str, Any]]) -> int:
        if not docs:
            return 0
        col = self.ensure_collection()
        texts = [d["text"] for d in docs]
        vectors = self.embedder.encode_documents(texts)

        # 先删同 id 再插入，模拟 upsert
        ids = [d["id"] for d in docs]
        try:
            expr = "id in [" + ",".join(f'"{i}"' for i in ids) + "]"
            col.delete(expr)
        except Exception:  # noqa: BLE001
            pass

        entities = [
            ids,
            [d.get("brand", "") for d in docs],
            [d.get("name", "") for d in docs],
            [int(d.get("year", 0)) for d in docs],
            [int(d.get("price_cny") or 0) for d in docs],
            texts,
            [d.get("meta_json", "{}") for d in docs],
            vectors,
        ]
        col.insert(entities)
        col.flush()
        col.load()
        return len(docs)

    def search(self, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
        col = self.ensure_collection()
        k = top_k or self.settings.rag_top_k
        vector = self.embedder.encode_query(query)
        results = col.search(
            data=[vector],
            anns_field="embedding",
            param={"metric_type": "IP", "params": {"nprobe": 16}},
            limit=k,
            output_fields=["id", "brand", "name", "year", "price_cny", "text", "meta_json"],
        )
        hits: list[dict[str, Any]] = []
        threshold = self.settings.rag_score_threshold
        for hit in results[0]:
            score = float(hit.score)
            if score < threshold:
                continue
            entity = hit.entity
            hits.append(
                {
                    "id": entity.get("id"),
                    "brand": entity.get("brand"),
                    "name": entity.get("name"),
                    "year": entity.get("year"),
                    "price_cny": entity.get("price_cny"),
                    "text": entity.get("text"),
                    "meta_json": entity.get("meta_json"),
                    "score": score,
                }
            )
        return hits

    def count(self) -> int:
        self.connect()
        name = self.settings.milvus_collection
        if not utility.has_collection(name):
            return 0
        col = Collection(name)
        col.flush()
        return col.num_entities

    def health(self) -> dict[str, Any]:
        try:
            self.connect()
            name = self.settings.milvus_collection
            exists = utility.has_collection(name)
            count = self.count() if exists else 0
            return {
                "ok": True,
                "uri": self.settings.milvus_uri,
                "collection": name,
                "exists": exists,
                "count": count,
            }
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "uri": self.settings.milvus_uri, "error": str(exc)}


_store: MilvusStore | None = None


def get_milvus_store() -> MilvusStore:
    global _store
    if _store is None:
        _store = MilvusStore()
    return _store
