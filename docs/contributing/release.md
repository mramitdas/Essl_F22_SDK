# Release

## Why this matters

A Python release is immutable in practice: once a version is published to PyPI,
you should not reuse that version number. A bad tag or a missing trusted
publisher can block the release, and a partial release can leave users with a
wheel that does not match the tag.

This page is the release runbook. It assumes the branch flow and quality gates
in [Development](development.md) are already satisfied.

## Current release status

The `0.1.0` package is published to PyPI. Publication used Trusted Publishing;
do not reuse version `0.1.0`.

One-time trusted publisher setup is complete for this project.

Do not create the release tag until that setup is complete and verified.

## One-time PyPI setup

Configure a **pending trusted publisher** on PyPI:

| Field | Value |
| --- | --- |
| PyPI project | `Essl_F22_SDK` |
| Owner | `mramitdas` |
| Repository | `Essl_F22_SDK` |
| Workflow filename | `release.yml` |
| Environment | `pypi` |

Then create the matching `pypi` environment in the GitHub repository settings.
The workflow uses OpenID Connect, so no PyPI API token is stored in GitHub.

Until this is done, the release workflow cannot publish. A PyPI page returning
`404` is expected before the first successful release.

## Versioning

The version is defined in one place:

```python
# src/essl_f22/__init__.py
__version__ = "0.1.0"
```

`pyproject.toml` reads it dynamically through Hatch:

```toml
[tool.hatch.version]
path = "src/essl_f22/__init__.py"
```

Do not hard-code a second version in `pyproject.toml`.

The project follows Semantic Versioning. Before `1.0.0`, minor versions may
contain API changes; document them in the changelog.

## Release steps

### 1. Prepare the release change

- Update `__version__`.
- Update `CHANGELOG.md` with the release date and user-visible changes.
- Update documentation if setup, behaviour, or compatibility changed.
- Run every quality gate.
- Build and inspect the artifacts locally.

```bash
uv sync --extra docs
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest
uv run mkdocs build --strict
uv build
uvx twine check dist/*
```

### 2. Verify the artifacts

Install the wheel into a clean environment:

```bash
uv venv --python 3.14 /tmp/essl_f22-release
uv pip install --python /tmp/essl_f22-release/bin/python dist/*.whl
/tmp/essl_f22-release/bin/python -c \
  "from importlib.metadata import version; import essl_f22; from essl_f22 import Device; assert essl_f22.__version__ == version('Essl_F22_SDK'); print(essl_f22.__version__, Device)"
```

Check:

- the wheel imports;
- `essl_f22.__version__` matches the wheel metadata;
- `py.typed` is present;
- the sdist contains the source tree and expected metadata;
- no secrets, local databases, or build junk are included.

### 3. Merge through the branch chain

The release change must travel through the normal PR flow:

```text
feature/issue branch -> dev -> stag -> prod
```

- Merge the change into `dev` by PR.
- Promote `dev` to `stag` by PR.
- Promote `stag` to `prod` by PR.
- Do not merge with `--delete-branch` when the head is `dev` or `stag`.

Do not tag a commit that is not on `prod`.

### 4. Tag `prod`

```bash
git checkout prod
git pull --ff-only origin prod
git tag -a v0.1.0 -m "Essl F22 SDK 0.1.0"
git push origin v0.1.0
```

The release workflow triggers on tags matching `v*`.

Before pushing the tag, confirm:

- the working tree is clean;
- `prod` is at the intended commit;
- the version in `__init__.py` matches the tag;
- the changelog is updated;
- the trusted publisher and `pypi` environment exist.

### 5. Watch the workflow

The `release.yml` workflow:

1. checks out the tagged commit;
2. installs uv and Python 3.14;
3. builds the sdist and wheel with `uv build`;
4. checks metadata with `twine check`;
5. publishes with `pypa/gh-action-pypi-publish` using Trusted Publishing.

The job uses the `pypi` environment and has `id-token: write` permission.

If the workflow fails before publishing, fix the cause and push a new tag only
if the version has not been consumed. If PyPI accepted the files, do not reuse
the version.

### 6. Verify the published release

```bash
uv venv --python 3.14 /tmp/essl_f22-pypi
uv pip install --python /tmp/essl_f22-pypi/bin/python Essl_F22_SDK==0.1.0
/tmp/essl_f22-pypi/bin/python -c \
  "from importlib.metadata import version; import essl_f22; print(version('Essl_F22_SDK'), essl_f22.__version__)"
```

Also verify:

- PyPI shows the expected files and metadata;
- the project page renders the README;
- installation works with `pip` and `uv`;
- the import name is `essl_f22`;
- the `docs` extra installs.

## Failed or partial release

### Workflow failed before upload

Fix the cause, re-run the workflow, or delete and recreate the tag only if the
version was never published.

Deleting or force-moving a tag is a destructive operation. Get explicit
approval.

### Upload succeeded but the release is wrong

Do not reuse the version. Options:

- yank the release on PyPI if it must not be installed;
- publish a new patch version with the fix;
- document the issue in the changelog.

Yanking hides a release from resolution but does not delete it. Treat any PyPI
mutation as a release decision, not a routine edit.

### Trusted publishing rejects the workflow

Check:

- the PyPI pending publisher owner/repository/workflow/environment values;
- the GitHub environment name is exactly `pypi`;
- the workflow is running from the tagged `prod` commit;
- the repository has the expected permissions;
- the PyPI project name is `Essl_F22_SDK`.

A `404` on the PyPI project page before the first release is expected.

## Post-release

- Close the release issue only after the package is published and verified.
- Update any deployment pins to the new version.
- Announce changes according to your project process.
- Keep the built wheel and sdist if your retention policy requires a rollback
  artifact.
- Do not commit `dist/` to the repository.

## Release checklist

- [ ] Version updated in `src/essl_f22/__init__.py`.
- [ ] Changelog updated.
- [ ] Docs updated.
- [ ] Ruff, format, mypy, pytest pass.
- [ ] `mkdocs build --strict` passes.
- [ ] `uv build` succeeds.
- [ ] `twine check` passes.
- [ ] Clean wheel install and import succeed.
- [ ] Changes merged through `dev` → `stag` → `prod`.
- [ ] Trusted publisher and `pypi` environment verified.
- [ ] Tag created on `prod` and pushed.
- [ ] Release workflow succeeded.
- [ ] PyPI install verified.
- [ ] Issue closed only after verification.

## Next

- [Development](development.md)
- [Compatibility](../help/compatibility.md)
- [CI workflow](https://github.com/mramitdas/Essl_F22_SDK/blob/dev/.github/workflows/ci.yml)
