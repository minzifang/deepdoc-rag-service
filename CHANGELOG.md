# Changelog

## 0.1.6 - 2026-05-21

- 清理 DeepDoc 表格输出中的内部对象：过滤 PIL 图片对象和坐标块，将 HTML table 转换为 Markdown 表格。
- 增强单段长 Go 代码识别，避免 OCR 合并后的代码被当作普通正文展示。

## 0.1.5 - 2026-05-21

- 合并 Claude Code 后续 UI 改动记录：Markdown 预览使用 `marked`、`DOMPurify` 和 `highlight.js`，并保留无 CDN 时的安全 fallback。
- GET 历史结果时用当前格式化器重建 `text`/`markdown`，并改为原子写回，避免旧结果继续显示为纯文本。
- 增加轻量代码块识别：代码文件会输出 fenced code block，连续代码样式行会合成为 Markdown 代码块。
- README 补充“独立服务和完整 RAGFlow/DeepDoc 平台能力差异”说明。

## 0.1.4 - 2026-05-21

- Markdown 输出不再直接等同纯文本：PDF DeepDoc 解析会保留版面类型，格式化层会把标题、编号标题、DOCX Heading 和项目符号合成为 Markdown。
- 增加 Markdown 格式化单元测试，覆盖标题、列表和已有 Markdown 保留行为。

## 0.1.3 - 2026-05-21

- 优化 `/ui` Markdown 预览，保留解析结果中的换行，避免连续文本被合并成一整段。
- `/ui` 结果区增加复制和下载按钮，可按当前 Markdown、Text、JSON 或 Tables 标签页导出内容。

## 0.1.2 - 2026-05-21

- `/ui` 的 Markdown 结果视图改为渲染后的 HTML 预览，不再只以纯文本 `<pre>` 展示。
- `/ui` 会记住最近一次解析任务，页面强制刷新后自动恢复任务状态和已落盘解析结果。
- 任务状态和解析结果改为原子写入，避免上传后立即轮询时读到未写完的 JSON。
- README 补充刷新、清空和结果持久化行为说明。

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
