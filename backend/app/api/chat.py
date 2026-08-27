"""对话接口 — SSE 流式输出。"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.rag.generator import get_generator
from app.rag.retriever import get_retriever
from app.schemas.models import ChatRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


@router.post("/chat")
async def chat(body: ChatRequest):
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="消息不能为空")

    logger.info("chat question: %s", message)

    retriever = get_retriever()
    try:
        hits = retriever.retrieve(message)
    except Exception as exc:  # noqa: BLE001
        logger.exception("retrieve failed")
        raise HTTPException(status_code=503, detail=f"检索失败: {exc}") from exc

    citations = retriever.citations(hits)
    if not hits:
        logger.info("retrieve hits: (empty)")
    else:
        for i, c in enumerate(citations, start=1):
            logger.info(
                "retrieve hit[%s]: %s %s | score=%.4f | price=%s | year=%s | id=%s",
                i,
                c.get("brand") or "",
                c.get("name") or "",
                float(c.get("score") or 0),
                c.get("price_cny"),
                c.get("year"),
                c.get("id"),
            )

    context = retriever.build_context(hits)
    generator = get_generator()

    async def event_generator():
        yield {
            "event": "meta",
            "data": json.dumps(
                {"citations": citations, "session_id": body.session_id},
                ensure_ascii=False,
            ),
        }
        try:
            async for token in generator.stream_chat(message, context):
                yield {
                    "event": "token",
                    "data": json.dumps({"content": token}, ensure_ascii=False),
                }
            yield {
                "event": "done",
                "data": json.dumps({"ok": True}, ensure_ascii=False),
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception("ollama stream failed")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(exc)}, ensure_ascii=False),
            }

    return EventSourceResponse(event_generator())
