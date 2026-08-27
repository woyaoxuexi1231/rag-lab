"""API 请求 / 响应模型。"""

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None


class PhoneDocument(BaseModel):
    id: str
    brand: str
    name: str
    year: int
    price_cny: int | None = None
    price_note: str | None = None
    soc: str | None = None
    display: str | None = None
    battery: str | None = None
    camera: str | None = None
    tags: list[str] = Field(default_factory=list)
    summary: str | None = None
    as_of: str | None = None
    source: str | None = None


class PhoneListResponse(BaseModel):
    total: int
    items: list[PhoneDocument]


class HealthResponse(BaseModel):
    status: str
    milvus: dict[str, Any]
    ollama: dict[str, Any]
    embedder: dict[str, Any]
