"""健康检查。"""

from fastapi import APIRouter

from app.rag.embedder import get_embedder
from app.rag.generator import get_generator
from app.rag.milvus_store import get_milvus_store
from app.schemas.models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    milvus = get_milvus_store().health()
    ollama = await get_generator().health()
    # embedder 首次加载较慢，health 只报告配置，不强制加载
    embedder = {
        "ok": True,
        "model": get_embedder().model_name,
        "dim": get_embedder().dim,
        "loaded": get_embedder()._model is not None,
    }
    status = "ok" if milvus.get("ok") else "degraded"
    if not ollama.get("ok"):
        status = "degraded"
    return HealthResponse(status=status, milvus=milvus, ollama=ollama, embedder=embedder)
