# Installation

## Why this matters

The SDK is a library, not an application. Installing it correctly means your
project's Python interpreter can import `essl_f22`, and that optional database
drivers are present only when you actually use those databases. Installing it
incorrectly usually shows up later as `ModuleNotFoundError` or as a package that
works in one terminal window but not in your program.

## Requirements

- **Python 3.12 or newer.** The package declares `requires-python = ">=3.12"`.
- **Network access to the device** on TCP port `4370` (or the port you configured).
- A virtual environment for your project. Do not install project dependencies
  into the system Python.
- No database driver is required for the default SQLite, JSON, or memory
  backends.

Check your interpreter:

```bash
python --version
```

If that prints 3.11 or older, install a newer Python before continuing.

## Create a virtual environment

=== "macOS / Linux"

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    ```

=== "Windows PowerShell"

    ```powershell
    py -3.12 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    ```

Your prompt should show the environment name, for example `(.venv)`. Every
command below assumes the environment is active.

## Install the library

=== "pip"

    ```bash
    python -m pip install essl_f22
    ```

=== "uv"

    ```bash
    uv add essl_f22
    ```

Inside an existing uv project, `uv add` records the dependency in
`pyproject.toml` and updates the lock file. `uv sync` installs the environment
from the lock file.

!!! note "Release availability"
    This handbook assumes `essl_f22` is available from your configured package
    index. If you are working before the first public release, install a wheel
    built from the repository:

    ```bash
    python -m pip install /path/to/essl_f22-0.1.0-py3-none-any.whl
    ```

    Do not install from an untrusted index or an unofficial package with a
    similar name.

## Verify the import

```bash
python -c "from essl_f22 import Device, __version__; print(__version__); print(Device)"
```

Expected shape:

```text
0.1.0
<class 'essl_f22.device.Device'>
```

The exact version may be newer. If the import fails, see
[Troubleshooting](../help/troubleshooting.md#the-import-fails).

## Optional database drivers

The core package has no runtime dependencies. External storage drivers are
optional extras so that a program using SQLite does not need a PostgreSQL or
MongoDB driver.

| Backend | Extra | Driver installed |
| --- | --- | --- |
| PostgreSQL | `postgres` | `psycopg[binary]` |
| MySQL | `mysql` | `pymysql` |
| MongoDB | `mongo` | `pymongo` |
| Redis | `redis` | `redis` |
| Documentation build | `docs` | `mkdocs-material` |

Install only what you need:

```bash
python -m pip install "essl_f22[postgres]"
python -m pip install "essl_f22[mysql]"
python -m pip install "essl_f22[mongo]"
python -m pip install "essl_f22[redis]"
```

With uv:

```bash
uv add "essl_f22[postgres]"
```

If you select a backend without its extra, the SDK raises
`StorageConfigurationError` with an installation hint when it tries to create
the backend. The core import still works because drivers are loaded lazily.

## This is a library, not a CLI

There is no `essl-f22` command and no console entry point. After installation
you write Python code that imports the package.

`pipx` and `uvx` are application runners. They can run a Python command in an
isolated environment, but they do not add the library to your project's
interpreter. Use `pip` or `uv add` for normal project use.

For a one-off import check with uv:

```bash
uvx --from essl_f22 python -c "from essl_f22 import Device; print(Device)"
```

That command runs `python` inside a temporary environment. It does not make
`essl_f22` importable from your own script afterward.

## Upgrading

=== "pip"

    ```bash
    python -m pip install --upgrade essl_f22
    ```

=== "uv"

    ```bash
    uv sync --upgrade-package essl_f22
    ```

Read the project changelog before upgrading across minor versions. Record,
storage, and error behaviour can change even when the core API stays familiar.

## Uninstalling

```bash
python -m pip uninstall essl_f22
```

Uninstalling the package does not delete your mirror, SQLite state database, or
JSON files. Those are your data. Remove them deliberately, after taking a
backup, if you no longer need them.

## Package-name spelling

The distribution and import name are `essl_f22`. Some tools display
`essl-f22` because Python package normalization (PEP 503) treats `-` and `_` as
equivalent. Use `essl_f22` in `pyproject.toml`, install commands, imports, and
documentation.

If `pip show essl_f22` reports the package but `pip show essl-f22` does not (or
the reverse), that is normal spelling normalization, not a second package.

## Next step

You have the library installed. Now make a safe, read-only connection:
[First connection](first-connection.md).
