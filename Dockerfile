FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

COPY src/ src/

USER 1000:1000

CMD ["uv", "run", "--no-sync", "python", "-c", "from essl_f22.core import add; print(add(1, 2))"]
