"""Ollama 生成层 — 拼 prompt + 流式输出。"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是 Study Hub 智能手机导购智能客服。
规则：
1. 只根据「参考资料」回答用户关于手机价格、参数、定位与选购的问题。
2. 若资料不足，明确说「知识库暂无足够信息」，不要编造具体价格或参数。
3. 报价均为人民币参考价，可能滞后；回答时可用「参考价约 xxx 元」表述。
4. 回答简洁、专业、口语化，可做对比，但必须基于资料。
5. 不要输出与手机导购无关的内容。
"""


class Generator:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _messages(self, question: str, context: str) -> list[dict[str, str]]:
        user_content = (
            f"参考资料：\n{context}\n\n"
            f"用户问题：{question}\n\n"
            "请基于参考资料作答。"
        )
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    async def health(self) -> dict[str, Any]:
        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                return {
                    "ok": True,
                    "base_url": self.settings.ollama_base_url,
                    "model": self.settings.ollama_model,
                    "models": models,
                }
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "base_url": self.settings.ollama_base_url,
                "model": self.settings.ollama_model,
                "error": str(exc),
            }

    async def stream_chat(self, question: str, context: str) -> AsyncIterator[str]:
        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/chat"
        messages = self._messages(question, context)
        payload = {
            "model": self.settings.ollama_model,
            "messages": messages,
            "stream": True,
        }
        logger.info(
            "ollama request model=%s url=%s",
            self.settings.ollama_model,
            url,
        )
        for msg in messages:
            logger.info(
                "ollama message [%s]:\n%s",
                msg["role"],
                msg["content"],
            )
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    message = chunk.get("message") or {}
                    content = message.get("content") or ""
                    if content:
                        yield content
                    if chunk.get("done"):
                        break


def get_generator() -> Generator:
    return Generator()
