"""FastAPI 入口。"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, health, knowledge
from app.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

settings = get_settings()

app = FastAPI(
    title="RAG CS Lab",
    description="Study Hub — 智能手机导购智能客服（RAG）",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/rag-cs")
app.include_router(knowledge.router, prefix="/api/rag-cs")
app.include_router(chat.router, prefix="/api/rag-cs")


@app.get("/")
def root():
    return {
        "project": "rag-cs-lab",
        "docs": "/docs",
        "health": "/api/rag-cs/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
    )
