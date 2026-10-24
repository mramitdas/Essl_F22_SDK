# Contributing

Thanks for your interest in contributing to essl_f22.

## Workflow

1. Fork and create a feature branch from `dev`.
2. Install dev dependencies: `uv sync`.
3. Make your change with tests.
4. Run the quality gates:

   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run mypy src/
   uv run pytest
   ```

5. Open a pull request targeting `dev`.

## Release

Releases are published to PyPI from `prod` with Trusted Publishing.

One-time setup: add a PyPI pending trusted publisher for this repository,
workflow `release.yml`, and environment `pypi`, then create the matching
GitHub environment.

1. Update `CHANGELOG.md` and `__version__` in `src/essl_f22/__init__.py`.
2. Merge the release change through `dev` → `stag` → `prod`.
3. Tag `prod` with `vX.Y.Z` and push the tag.
4. The `release.yml` workflow builds and publishes the sdist and wheel.
5. Verify `pip install essl_f22==X.Y.Z` in a clean environment.

## Code of Conduct

Please read and follow the [Code of Conduct](CODE_OF_CONDUCT.md).
