"""手机知识库加载与文本化。"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.config import DATA_DIR
from app.schemas.models import PhoneDocument

logger = logging.getLogger(__name__)


def load_phone_documents(data_dir: Path | None = None) -> list[PhoneDocument]:
    root = data_dir or DATA_DIR
    if not root.exists():
        logger.warning("Phone data dir missing: %s", root)
        return []

    phones: list[PhoneDocument] = []
    for path in sorted(root.glob("*.json")):
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        items = payload if isinstance(payload, list) else payload.get("phones", [])
        for item in items:
            phones.append(PhoneDocument.model_validate(item))
    return phones


def phone_to_text(phone: PhoneDocument) -> str:
    tags = "、".join(phone.tags) if phone.tags else "无"
    price = f"{phone.price_cny} 元" if phone.price_cny else (phone.price_note or "暂无报价")
    lines = [
        f"品牌：{phone.brand}",
        f"机型：{phone.name}",
        f"上市年份：{phone.year}",
        f"参考起售价：{price}",
        f"处理器：{phone.soc or '未知'}",
        f"屏幕：{phone.display or '未知'}",
        f"电池与充电：{phone.battery or '未知'}",
        f"影像：{phone.camera or '未知'}",
        f"定位标签：{tags}",
        f"简介：{phone.summary or '无'}",
        f"数据日期：{phone.as_of or '未知'}",
        f"来源备注：{phone.source or '公开资料整理'}",
    ]
    return "\n".join(lines)


def phone_to_milvus_doc(phone: PhoneDocument) -> dict[str, Any]:
    meta = phone.model_dump()
    return {
        "id": phone.id,
        "brand": phone.brand,
        "name": phone.name,
        "year": phone.year,
        "price_cny": phone.price_cny or 0,
        "text": phone_to_text(phone),
        "meta_json": json.dumps(meta, ensure_ascii=False),
    }
