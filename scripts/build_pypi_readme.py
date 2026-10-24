#!/usr/bin/env python3
"""Build README.md from docs/ for the PyPI long description.

Keeps docs/ as the source of truth. Regenerate README.md whenever docs change:

    python scripts/build_pypi_readme.py

CI runs this script and fails if README.md is out of date.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MKDOCS = ROOT / "mkdocs.yml"
README = ROOT / "README.md"
REPO = "https://github.com/mramitdas/Essl_F22_SDK"

HEADER = """# Essl F22 SDK

**A synchronous Python SDK for eSSL/ZKTeco F22 attendance and access terminals.**

[![CI](https://github.com/mramitdas/Essl_F22_SDK/actions/workflows/ci.yml/badge.svg)](https://github.com/mramitdas/Essl_F22_SDK/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://github.com/mramitdas/Essl_F22_SDK)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

Essl_F22_SDK 0.1.0 is published on PyPI.

This README is generated from `docs/`; the full handbook lives in the repository.

## Install

```bash
pip install Essl_F22_SDK
```

```bash
uv add Essl_F22_SDK
```

Optional extras:

```bash
pip install "Essl_F22_SDK[postgres]"
pip install "Essl_F22_SDK[mysql]"
pip install "Essl_F22_SDK[mongo]"
pip install "Essl_F22_SDK[redis]"
pip install "Essl_F22_SDK[docs]"
```

The distribution name is `Essl_F22_SDK`. Some package tools display the
normalized spelling `essl-f22-sdk`; that is the same package. The import name is
`essl_f22`.

---
"""


def iter_pages() -> Iterator[Path]:
    """Yield documentation pages in mkdocs.yml nav order."""
    in_nav = False
    for line in MKDOCS.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped == "nav:":
            in_nav = True
            continue
        if in_nav:
            if line == "" or not line[0:1].isspace():
                in_nav = False
                continue
            if stripped.startswith("- "):
                item = stripped[2:]
                if ":" in item:
                    _, path = item.split(":", 1)
                    path = path.strip()
                    if path.endswith(".md"):
                        yield Path(path)


def convert_admonitions(text: str) -> str:
    """Convert MkDocs admonitions to PyPI-safe Markdown blockquotes."""
    out = []
    in_admonition = False
    for line in text.splitlines():
        m = re.match(r"^!!! (\w+)(?: \"(.*?)\")?\s*$", line)
        if m:
            title = m.group(2) or m.group(1).capitalize()
            out.append(f"> **{title}:**")
            in_admonition = True
            continue
        if in_admonition:
            if line == "":
                out.append(">")
                continue
            if not line[0:1].isspace():
                in_admonition = False
                out.append(line)
                continue
            out.append("> " + line[4:] if line.startswith("    ") else "> " + line)
            continue
        out.append(line)
    return "\n".join(out)


def convert_links(text: str, base_dir: Path) -> str:
    """Rewrite relative doc links/images to absolute GitHub URLs."""

    def repl(match: re.Match[str]) -> str:
        alt, url = match.group(1), match.group(2)
        if url.startswith(("http://", "https://", "mailto:")) or url.startswith("#"):
            return f"[{alt}]({url})"
        target = (base_dir / url).resolve()
        try:
            rel = target.relative_to(ROOT)
        except ValueError:
            return f"[{alt}]({url})"
        if url.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")):
            return f"![{alt}]({REPO}/raw/prod/{rel})"
        return f"[{alt}]({REPO}/blob/prod/{rel})"

    return re.sub(r"!?\[([^\]]*)\]\(([^)]+)\)", repl, text)


def read_page(path: Path) -> str:
    text = (DOCS / path).read_text(encoding="utf-8")
    text = convert_admonitions(text)
    text = convert_links(text, DOCS / path.parent)
    return text


def build() -> None:
    parts = [HEADER]
    for path in iter_pages():
        parts.append(f"\n---\n\n### From [docs/{path}]({REPO}/blob/prod/docs/{path})\n")
        parts.append(read_page(path))
    README.write_text("\n".join(parts) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
