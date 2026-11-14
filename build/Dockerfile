# Multi-stage build of the website image. Build from the repository root:
#   docker build -f build/Dockerfile --target website-run .

FROM ghcr.io/astral-sh/uv:python3.15-trixie-slim@sha256:053efa9652f89ac056731b55b4912131fca1dd644d472b6a40340a62f183a5db AS website-builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Dependencies first, so this layer is cached until uv.lock changes.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project

COPY pyproject.toml uv.lock .python-version README.md LICENSE ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable


FROM python:3.15-slim-trixie@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928 AS website-run

RUN useradd --system --uid 10001 --no-create-home website

COPY --from=website-builder --chown=website:website /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Source revision shown on the About page (AGPL §13); passed in by CI or compose.
ARG WEBSITE_REVISION=
ENV WEBSITE_REVISION=${WEBSITE_REVISION}

USER website
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"]

# Proxy headers are trusted from any address because the container is only reachable from the
# internal Compose network (via Caddy).
CMD ["uvicorn", "website.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
