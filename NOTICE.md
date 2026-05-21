# Notices

This project is a standalone document parsing service that wraps selected
RAGFlow DeepDoc components behind a small FastAPI service.

## Upstream Software

Portions of this project include or adapt source code from RAGFlow:

- Project: RAGFlow
- Upstream repository: https://github.com/infiniflow/ragflow
- Upstream commit used during extraction: `6499bce`
- License: Apache License 2.0
- Local vendor path: `vendor/ragflow`

RAGFlow source files retain their original copyright and license headers.
The upstream RAGFlow license is also preserved at `vendor/ragflow/LICENSE`.

## Model Artifacts

The service can use model artifacts from InfiniFlow:

- `InfiniFlow/deepdoc`: https://huggingface.co/InfiniFlow/deepdoc
- `InfiniFlow/text_concat_xgb_v1.0`: https://huggingface.co/InfiniFlow/text_concat_xgb_v1.0
- License shown by the model repositories: Apache License 2.0

Model weights are intentionally not committed to this repository. Download
them locally with:

```bash
uv run python scripts/download_models.py --mirror https://hf-mirror.com
```

## Trademark Notice

RAGFlow, DeepDoc, InfiniFlow and related names may be trademarks or brand
names of their respective owners. This project is not an official RAGFlow or
InfiniFlow product.
