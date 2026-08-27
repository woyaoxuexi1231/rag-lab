#!/usr/bin/env python3
"""离线入库脚本：读取 data/phones/*.json → Embedding → Milvus。"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# 保证从项目根目录可 import app
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.rag.knowledge import load_phone_documents, phone_to_milvus_doc
from app.rag.milvus_store import get_milvus_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("ingest")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest phone knowledge into Milvus")
    parser.add_argument("--drop", action="store_true", help="重建集合后再写入")
    args = parser.parse_args()

    phones = load_phone_documents()
    if not phones:
        logger.error("No phone documents found under data/phones")
        return 1

    store = get_milvus_store()
    if args.drop:
        store.ensure_collection(drop_existing=True)
    else:
        store.ensure_collection(drop_existing=False)

    docs = [phone_to_milvus_doc(p) for p in phones]
    count = store.upsert_documents(docs)
    logger.info("Ingested %s documents into %s", count, store.settings.milvus_collection)
    logger.info("Collection entity count: %s", store.count())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
