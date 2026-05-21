# Contributing

Thanks for helping improve this project.

## Development

Install dependencies:

```bash
git submodule update --init --recursive
uv sync --extra dev --extra deepdoc
```

Run checks:

```bash
uv run ruff check app tests infinity scripts
uv run pytest
```

Run the service:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8010
```

## Scope

This repository is intended to stay focused on document parsing:

- upload a document
- run DeepDoc or plain parsing
- return Markdown, text, structured sections and tables

Chunking, embedding generation and vector indexing should live in downstream
applications unless they are reintroduced behind an explicit optional module.

## Licensing

Do not remove upstream license headers from vendored RAGFlow files. If you
update vendored code, also update `NOTICE.md` with the upstream commit.
