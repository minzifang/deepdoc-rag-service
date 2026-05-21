# DeepDoc Parse Service

一个独立的文档解析服务。它把 RAGFlow 官方 DeepDoc 作为解析内核，外层补上任务化 API、状态查询、失败反馈，以及 Markdown / Text / JSON 输出。

官方来源：

- RAGFlow: https://github.com/infiniflow/ragflow
- DeepDoc: `vendor/ragflow/deepdoc`
- Upstream commit: `6499bce`

RAGFlow 代码遵循其原始 Apache-2.0 License，本项目保留 `vendor/ragflow/LICENSE`。

## 特性

- 上传文档后立即返回 `task_id`，解析在后台执行。
- 支持 `auto`、`deepdoc`、`plain` 三种解析模式。
- `deepdoc` 模式使用官方 OCR、版面识别和表格识别能力。
- `auto` 模式优先尝试 DeepDoc，依赖或模型不可用时回退到普通文本抽取。
- 任务状态完整落盘：`queued / parsing / done / failed`。
- 解析结果以 JSON 保存，包含 `text`、`markdown`、`sections`、`tables` 和 `metadata`。

## 快速启动

基础模式只安装轻量依赖，可跑 `plain` 和部分文档类型：

```bash
cd /Users/leeleo/Documents/Www/deepdoc-rag-service
git submodule update --init --recursive
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8010
```

完整 DeepDoc 模式安装官方解析依赖：

```bash
uv sync --extra deepdoc
uv run uvicorn app.main:app --host 0.0.0.0 --port 8010
```

首次运行 DeepDoc 会下载 OCR、layout、table 和拼接模型。国内网络建议在 `.env` 设置：

```bash
HF_ENDPOINT=https://hf-mirror.com
HF_TOKEN=
```

也可以提前手动下载模型：

```bash
uv sync --extra deepdoc
uv run python scripts/download_models.py --mirror https://hf-mirror.com
```

只查看模型清单和大小：

```bash
uv run python scripts/download_models.py --list
```

## API

测试页面：

```bash
open http://localhost:8010/ui
```

上传文档：

```bash
curl -F "file=@/path/to/demo.pdf" \
  -F "kb_id=demo" \
  -F "parser_mode=auto" \
  http://localhost:8010/api/v1/documents
```

查询任务：

```bash
curl http://localhost:8010/api/v1/tasks/{task_id}
```

获取结果：

```bash
curl http://localhost:8010/api/v1/documents/{doc_id}/result
```

获取 Markdown：

```bash
curl http://localhost:8010/api/v1/documents/{doc_id}/markdown
```

## 与官方 RAGFlow 的关系

这个服务不是完整 RAGFlow 平台的替代品，它只抽离文档解析链路：

- 保留官方 DeepDoc 解析能力。
- 不启动 RAGFlow 的用户系统、租户系统、数据库模型配置、Agent、Web UI。
- 自己实现轻量任务状态、API 契约和解析结果持久化。
- 内置 `infinity.rag_tokenizer` 兼容层，让官方 `rag.nlp` 在独立服务中可运行；需要完全使用官方 tokenizer 时，可以在镜像环境里替换该兼容层。

这样做的好处是服务更小，容易接入现有项目；代价是部分官方高级能力需要逐步补齐，比如多租户模型配置、图片 VLM 描述、复杂知识库权限和可视化解析编辑。

## 推荐接入方式

业务系统只调用这个服务：

1. `POST /api/v1/documents` 上传文档。
2. 轮询 `GET /api/v1/tasks/{task_id}`。
3. 成功后读取 `GET /api/v1/documents/{doc_id}/result` 或 `GET /api/v1/documents/{doc_id}/markdown`。
4. 业务系统自己决定是否做切分、向量化或入库。

## 配置

复制 `.env.example` 为 `.env` 后调整。

重要项：

- `DEFAULT_PARSER_MODE`: `auto`、`deepdoc` 或 `plain`。
- `MAX_PAGE_NUMBER`: 限制最大解析页数，避免超大 PDF 长时间占用。
- `PARALLEL_DEVICES`: 官方 DeepDoc 并行设备数，CPU 单机建议保持 `0`。

## Docker

```bash
cp .env.example .env
docker compose up -d --build
```
