# Changelog

## 0.1.1 - 2026-05-21

- 修复 GitHub Actions 中 pytest 误收集 `vendor/ragflow` 上游测试的问题。
- CI 明确只运行本服务的 `tests/` 测试目录。
- 更新 GitHub Actions 依赖版本，减少 Dependabot 初始 PR 噪音。

## 2026-05-20

- 初始化独立 DeepDoc Parse 服务。
- 引入 RAGFlow 官方 `deepdoc`、`rag`、`common` 和 `conf` 核心目录作为 vendor 源。
- 增加 FastAPI 上传、任务状态、解析结果查询和 Markdown 查询接口。
- 增加后台解析任务、进度落盘和失败反馈。
- 增加独立 `infinity.rag_tokenizer` 兼容层，避免单独服务被完整 RAGFlow 平台依赖卡住。
- 增加内置测试页面 `/ui`，支持上传文档、轮询任务状态和预览解析结果。
- 移除切分、embedding 和索引运行链路，服务定位调整为纯 DeepDoc 解析输出。
- 测试页面改为展示 Markdown、Text、JSON 和 Tables。
