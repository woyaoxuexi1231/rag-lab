# RAG CS Lab — 智能手机导购智能客服

RAG Lab 后端：基于 **RAG** 的手机导购客服。

- 向量库：本机 **Milvus**
- Embedding：本机 CPU **`BAAI/bge-small-zh-v1.5`**
- 大模型：远程 **Ollama + qwen2.5**（建议跑在 1650 算力机）
- 前端：独立仓库 `rag-lab/frontend` → `/#/rag-cs`

---

## 架构

```text
浏览器 (Vue :13000)
    │  /api/rag-cs/**
    ▼
FastAPI rag-cs-lab (:18100)
    ├─ bge-small-zh (本机 CPU) ──► Milvus (:19530)
    └─ prompt + context ─────────► Ollama qwen2.5 (远程)
```

### 为何 Embedding 不放 Ollama / 1650

GTX 1650 约 4GB 显存，对话模型已占大头。Embedding 算力需求远低于生成，放在本机 CPU：

1. 避免与 qwen2.5 争抢显存或频繁换模
2. 中文检索用 `bge-small-zh-v1.5`，体积小、CPU 友好
3. 算力机专心做流式生成

---

## 目录

```text
backend/
  app/                 # FastAPI + RAG
  data/phones/         # 机型种子 JSON
  scripts/ingest.py    # 离线入库
  pyproject.toml       # uv 项目与依赖
  uv.lock
  .env.example
```

---

## 环境要求

| 组件 | 说明 |
|------|------|
| [uv](https://docs.astral.sh/uv/) | Python 包管理（会按需拉取 Python） |
| Python | 3.11+（由 uv 管理） |
| Milvus | 本机可访问，默认 `http://localhost:19530` |
| Ollama | 算力机已安装，并拉取 `qwen2.5` |
| 前端 | 仓库根目录 `frontend/`（Vite） |

---

## 安装 Embedding：`bge-small-zh-v1.5`

**不用单独装成 Ollama 模型。** 本项目通过 Python 包 `sentence-transformers` 在本机 CPU 加载 Hugging Face 上的 `BAAI/bge-small-zh-v1.5`。

### 1. 装依赖（已含 sentence-transformers）

```powershell
cd backend
uv sync
```

`sentence-transformers` 会连带装上 PyTorch（CPU 版即可）。

### 2. 下载模型权重（二选一）

**方式 A — 入库时自动下载（最简单）**

首次执行 `uv run python scripts/ingest.py --drop` 时，若本机还没有该模型，会自动从 Hugging Face 拉取并缓存。体积大约 **100MB 级**，需能访问外网（或镜像）。

**方式 B — 提前手动下载（推荐，可确认是否成功）**

```powershell
uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-zh-v1.5'); print('bge-small-zh-v1.5 ready')"
```

成功后模型缓存在用户目录，例如：

```text
%USERPROFILE%\.cache\huggingface\hub\models--BAAI--bge-small-zh-v1.5\
```

之后 `ingest` / 启动 API 都会直接读本地缓存，无需再下。

### 3. 国内下载慢：用 Hugging Face 镜像

PowerShell 当前会话：

```powershell
$env:HF_ENDPOINT = "https://hf-mirror.com"
uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-zh-v1.5'); print('ok')"
```

或写入用户环境变量 `HF_ENDPOINT=https://hf-mirror.com` 后重开终端。

### 4. 验证是否可用

```powershell
uv run python -c "from sentence_transformers import SentenceTransformer; m=SentenceTransformer('BAAI/bge-small-zh-v1.5'); v=m.encode(['测试'], normalize_embeddings=True); print(len(v[0]))"
```

应输出 `512`（与 `.env` 里 `EMBED_DIM=512` 一致）。

`.env` 中对应配置：

```text
EMBED_MODEL=BAAI/bge-small-zh-v1.5
EMBED_DIM=512
```

一般无需修改。若改用本地目录路径，把 `EMBED_MODEL` 设成模型文件夹的绝对路径即可。

---

## 快速启动

### 1. 后端

```powershell
cd backend
uv sync
copy .env.example .env
# 编辑 .env：把 OLLAMA_BASE_URL 改成算力机 IP，例如 http://192.168.x.x:11434
```

按上一节装好 / 下载好 `bge-small-zh-v1.5` 后，首次入库：

```powershell
uv run python scripts/ingest.py --drop
```

启动 API：

```powershell
uv run uvicorn app.main:app --host 0.0.0.0 --port 18100 --reload
```

健康检查：<http://localhost:18100/api/rag-cs/health>  
Swagger：<http://localhost:18100/docs>

### 2. 前端

```powershell
cd ../frontend
npm install
npm run dev
```

打开：<http://localhost:13007/#/rag-cs/chat>

开发代理已配置：`/api/rag-cs` → `http://localhost:18100`。

---

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/rag-cs/health` | Milvus / Ollama / Embedder 状态 |
| GET | `/api/rag-cs/phones` | 机型列表（可 `brand` / `year` 筛选） |
| GET | `/api/rag-cs/phones/{id}` | 机型详情 |
| POST | `/api/rag-cs/ingest?drop_existing=true` | 重建并写入向量库 |
| POST | `/api/rag-cs/chat` | SSE 对话（`meta` / `token` / `done` / `error`） |

Chat 请求体：

```json
{ "message": "预算 5000 推荐什么手机？", "session_id": null }
```

---

## 知识库说明

`data/phones/*.json` 覆盖 Apple / Samsung / Xiaomi / Huawei / OPPO / vivo / Honor / OnePlus / Google 等 **2024–2026 主流代表机型**（约 60+ 款），字段包括价格、SoC、屏幕、电池、影像、标签与 `as_of` 日期。

- 不是全球全 SKU 清单
- 价格为人民币**参考快照**，可能滞后
- 扩展方式：按品牌新增 JSON，再执行 `uv run python scripts/ingest.py --drop`

---

## 配置项（`.env`）

| 变量 | 默认 | 说明 |
|------|------|------|
| `MILVUS_URI` | `http://localhost:19530` | Milvus 地址 |
| `MILVUS_COLLECTION` | `phone_kb` | 集合名 |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | 远程 Ollama |
| `OLLAMA_MODEL` | `qwen2.5` | 对话模型 |
| `EMBED_MODEL` | `BAAI/bge-small-zh-v1.5` | 本机 Embedding |
| `EMBED_DIM` | `512` | 向量维度（需与模型一致） |
| `RAG_TOP_K` | `5` | 检索条数 |
| `RAG_SCORE_THRESHOLD` | `0.35` | 相似度阈值（IP） |

---

## 常见问题

**Ollama 连不上**  
确认算力机防火墙放行 11434，且 `.env` 中 IP 正确；本机可 `curl http://<IP>:11434/api/tags`。

**Milvus 为空 / 检索无结果**  
先跑 `uv run python scripts/ingest.py --drop`，或在前端「机型库」页点「重建入库」。

**首次 uv sync / 模型下载很慢**  
`sentence-transformers` 会拉取较大的 PyTorch；模型权重见上文「安装 Embedding」。国内可设 `HF_ENDPOINT=https://hf-mirror.com` 后再跑预下载命令。

**提示找不到 BAAI/bge-small-zh-v1.5**  
确认已 `uv sync`，且预下载命令能打印 `ready` / `512`。防火墙或代理拦截 Hugging Face 时改用镜像。
