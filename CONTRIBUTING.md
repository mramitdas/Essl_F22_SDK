# Contributing

Thanks for your interest in contributing to essl_f22.

## Workflow

1. Fork and create a feature branch from `main`.
2. Install dev dependencies: `uv sync`.
3. Make your change with tests.
4. Run the quality gates:

   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run mypy src/
   uv run pytest
   ```

5. Open a pull request.

## Code of Conduct

Please read and follow the [Code of Conduct](CODE_OF_CONDUCT.md).
