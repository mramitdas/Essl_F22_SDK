# essl_f22

**Synchronous Python SDK for eSSL/ZKTeco F22 terminals.**

[![CI](https://github.com/mramitdas/essl-f22-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/mramitdas/essl-f22-sdk/actions/workflows/ci.yml)

## Quickstart

```bash
uv sync                      # install deps (creates .venv)
uv run pytest                # run tests with coverage
uv run ruff check .          # lint
uv run mypy src/             # type-check
```

## Project layout

```
src/essl_f22/   # your package (src layout)
tests/               # pytest tests
pyproject.toml       # project metadata + tool config
```

## License

essl_f22 is distributed under the terms of the
Apache License 2.0. See `LICENSE` for details.
