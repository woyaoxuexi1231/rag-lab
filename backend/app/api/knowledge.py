"""知识库：列表 / 详情 / 入库。"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.rag.knowledge import load_phone_documents, phone_to_milvus_doc
from app.rag.milvus_store import get_milvus_store
from app.schemas.models import PhoneDocument, PhoneListResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["knowledge"])


@router.get("/phones", response_model=PhoneListResponse)
def list_phones(brand: str | None = None, year: int | None = None) -> PhoneListResponse:
    phones = load_phone_documents()
    if brand:
        phones = [p for p in phones if p.brand.lower() == brand.lower()]
    if year:
        phones = [p for p in phones if p.year == year]
    phones.sort(key=lambda p: (p.brand, -p.year, p.name))
    return PhoneListResponse(total=len(phones), items=phones)


@router.get("/phones/{phone_id}", response_model=PhoneDocument)
def get_phone(phone_id: str) -> PhoneDocument:
    for phone in load_phone_documents():
        if phone.id == phone_id:
            return phone
    raise HTTPException(status_code=404, detail="机型不存在")


@router.post("/ingest")
def ingest(drop_existing: bool = False) -> dict:
    phones = load_phone_documents()
    if not phones:
        raise HTTPException(status_code=400, detail="本地种子数据为空")
    store = get_milvus_store()
    if drop_existing:
        store.ensure_collection(drop_existing=True)
    docs = [phone_to_milvus_doc(p) for p in phones]
    count = store.upsert_documents(docs)
    logger.info("Ingested %s phone documents", count)
    return {"ok": True, "ingested": count, "collection": store.settings.milvus_collection}
