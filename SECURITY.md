# Security Policy

## Reporting a Vulnerability

Please report security issues privately to the repository maintainers instead
of opening a public issue.

Include:

- affected version or commit
- reproduction steps
- impact
- suggested mitigation, if known

## Sensitive Data

Do not commit:

- `.env` files
- API keys or access tokens
- uploaded user documents
- parsed document results
- model weights

The default `.gitignore` excludes local storage, model artifacts and local
environment files.
