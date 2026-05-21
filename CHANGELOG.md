# Changelog

## 2026-05-20

- 初始化独立 DeepDoc Parse 服务。
- 引入 RAGFlow 官方 `deepdoc`、`rag`、`common` 和 `conf` 核心目录作为 vendor 源。
- 增加 FastAPI 上传、任务状态、解析结果查询和 Markdown 查询接口。
- 增加后台解析任务、进度落盘和失败反馈。
- 增加独立 `infinity.rag_tokenizer` 兼容层，避免单独服务被完整 RAGFlow 平台依赖卡住。
- 增加内置测试页面 `/ui`，支持上传文档、轮询任务状态和预览解析结果。
- 移除切分、embedding 和索引运行链路，服务定位调整为纯 DeepDoc 解析输出。
- 测试页面改为展示 Markdown、Text、JSON 和 Tables。
