# RAG Lab

从 Study Hub 抽离的 RAG 智能客服实验室：智能手机导购对话，后端 FastAPI + 前端 Vue。

## 目录结构

```text
rag-lab/
├── backend/     # FastAPI + Milvus + sentence-transformers (:18100)
└── frontend/    # Vue 3 + Vite (:13007)
```

## 架构

```text
浏览器 (Vue :13007)
    │  /api/rag-cs/**
    ▼
FastAPI (:18100)
    ├─ bge-small-zh (本机 CPU) ──► Milvus (:19530)
    └─ prompt + context ─────────► Ollama qwen2.5 (远程)
```

## 后端

```powershell
cd backend
uv sync
copy .env.example .env
# 编辑 .env：OLLAMA_BASE_URL、MILVUS_URI 等

uv run python scripts/ingest.py --drop
uv run uvicorn app.main:app --host 0.0.0.0 --port 18100 --reload
```

- 健康检查：<http://localhost:18100/api/rag-cs/health>
- Swagger：<http://localhost:18100/docs>

## 前端

```powershell
cd frontend
npm install
npm run dev
```

浏览器打开 <http://127.0.0.1:13007/#/rag-cs/chat> 。

开发代理：`/api/rag-cs` → `http://localhost:18100`。

## 环境要求

| 组件 | 说明 |
|------|------|
| [uv](https://docs.astral.sh/uv/) | Python 包管理 |
| Python | 3.11+ |
| Milvus | 默认 `http://localhost:19530` |
| Ollama | 远程算力机，模型 `qwen2.5` |

详细配置与 Embedding 安装见 [backend/README.md](backend/README.md)。

## 来源

原位于 [study-hub](https://github.com/woyaoxuexi1231/study-hub) 的 `rag-cs-lab` 模块，现独立维护于 [rag-lab](https://github.com/woyaoxuexi1231/rag-lab)。
