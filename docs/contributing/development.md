# Development

## Why this matters

This project talks to real hardware and can change access control. A passing
unit test is necessary but not sufficient. The development workflow is designed
to keep speculative changes, untested writes, and unreviewed documentation out
of the integration branches.

## Before you start

- Read the repository `AGENTS.md`.
- Check open issues and pull requests.
- Confirm the target issue and branch.
- Do not push directly to `dev`, `stag`, or `prod`.

## Branch flow

```text
feature/issue branch  ->  dev  ->  stag  ->  prod
```

- Feature and fix branches start from `dev`.
- Pull requests target `dev`, except promotion PRs.
- Promotion is one hop at a time and PR-only:
  - `dev` → `stag`
  - `stag` → `prod`
- Never skip or reorder a hop.
- Never merge with `--delete-branch` when the head is an integration branch.

Branch naming:

```text
<type>/<issue#>-<slug>
```

Examples:

```text
feat/42-add-backend
fix/43-handle-timeout
docs/36-complete-handbook
```

## Setup

```bash
uv sync
```

This installs the development group and the project in editable mode. Optional
storage drivers are not installed unless you add their extras.

To work on documentation:

```bash
uv sync --extra docs
```

## The quality gates

Run all of these before opening a pull request:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest
```

And, for documentation changes:

```bash
uv run mkdocs build --strict
```

The gates must be clean. Do not disable a rule, add a blanket `type: ignore`, or
skip a test to make a change pass. Fix the cause.

## Tests

The default suite must not require a physical device:

```bash
uv run pytest
```

Use fake transports and sessions for unit tests. Put hardware-specific tests
behind the `hardware` marker.

### Hardware test

The hardware test is read-only:

```bash
ESSL_F22_HOST=192.168.1.50 \
ESSL_F22_PORT=4370 \
ESSL_F22_COMM_KEY=0 \
uv run pytest -m hardware
```

It is skipped when `ESSL_F22_HOST` is unset. It must not call block/unblock or
write to the device.

### Storage contract tests

External backends are opt-in:

```bash
ESSL_F22_POSTGRES_DSN=postgresql://user:pass@db/app \
ESSL_F22_MYSQL_DSN=mysql://user:pass@db/app \
ESSL_F22_MONGO_URI=mongodb://localhost/app \
ESSL_F22_REDIS_URL=redis://localhost/0 \
uv run pytest tests/test_storage_contract.py
```

Run the tests against the exact database versions and permissions you support.
Do not commit test credentials.

### Test naming

Test names should describe the behaviour, not the implementation. A reader
should know what broke from the failure message.

## Code style

- Python 3.12+.
- Ruff for lint and format.
- Mypy strict over `src/`.
- Follow the style of the module you touch.
- No comments unless they explain something the code cannot.
- No `TODO` markers, commented-out code, or dead files.
- No `v2`, `copy`, `.new`, `backup`, or `-final` variants.

## Architecture

```text
src/essl_f22/
  errors.py       exception hierarchy
  protocol.py     constants, checksums, frames, codecs
  transport.py    TCP socket transport
  session.py      connect/auth, command I/O, buffered reads
  models.py       dataclasses and record codecs
  device.py       high-level device API
  mirror.py       read-only mirror and sync
  access.py       block/unblock manager
  storage/        protocols, codecs, backends, factory
  state.py        SQLite block-state compatibility shim
  __init__.py     public exports
```

Keep layering intact:

- `device.py` orchestrates; it should not reimplement frame parsing.
- `session.py` handles command exchange and buffering.
- `protocol.py` owns constants and binary codecs.
- `storage/` owns persistence and backend selection.
- `mirror.py` and `access.py` depend on protocols, not concrete sockets.

## Documentation

This handbook lives in `docs/` and is built with MkDocs Material.

Preview locally:

```bash
uv run mkdocs serve
```

Validate strictly:

```bash
uv run mkdocs build --strict
```

### Publishing the handbook

GitHub Pages is not available for this private repository on the free plan.
Cloudflare Pages supports private GitHub repositories on its free plan, with
unlimited bandwidth and 500 builds per month.

To publish:

1. In the Cloudflare dashboard, open **Workers & Pages** and create a Pages
   project.
2. Connect the `mramitdas/Essl_F22_SDK` GitHub repository.
3. Set the production branch to `prod`.
4. Set the build command to
   `python -m pip install mkdocs-material && mkdocs build --strict`.
5. Set the build output directory to `site`.
6. Set `PYTHON_VERSION` to `3.13` if the build image does not select a supported
   version automatically.

The generated `site/` directory is ignored by git. Set `site_url` in
`mkdocs.yml` only after the public hostname is known.

Rules:

- Every behaviour or setup change updates the relevant page.
- Use plain language for operator-facing pages, then exact signatures in the
  reference.
- Do not document unverified device behaviour as fact.

## Pull request checklist

- [ ] One issue, one logical change.
- [ ] Branch targets `dev`.
- [ ] Tests cover the behaviour change.
- [ ] `uv run ruff check .` passes.
- [ ] `uv run ruff format --check .` passes.
- [ ] `uv run mypy src/` passes.
- [ ] `uv run pytest` passes.
- [ ] Documentation updated if setup, behaviour, or API changed.
- [ ] `uv run mkdocs build --strict` passes for docs changes.
- [ ] No secrets, `.env`, or credentials in the diff.
- [ ] `git diff` contains only intended changes.

## Commit and PR style

- Conventional commit type: `feat:`, `fix:`, `docs:`, `test:`, `chore:`.
- Subject at most 50 characters.
- Body ends with `refs #N`.
- PR targets the correct branch.
- Do not force-push or skip hooks.

## Reporting a bug

Include the package version, Python version, OS, device model/platform/firmware,
steps to reproduce, and the full traceback. Redact secrets and personal data.

See [Troubleshooting](../help/troubleshooting.md) for what to collect.

## Next

- [Release](release.md)
- [Contributing source](https://github.com/mramitdas/Essl_F22_SDK/blob/dev/CONTRIBUTING.md)
- [Project rules](https://github.com/mramitdas/Essl_F22_SDK/blob/dev/AGENTS.md)
