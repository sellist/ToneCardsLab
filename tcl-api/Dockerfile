# dockerfile
FROM python:3.14-alpine AS builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apk add --no-cache \
      build-base \
      cargo \
      gcc \
      libffi-dev \
      musl-dev \
      openssl-dev \
      rust

WORKDIR /app

COPY pyproject.toml uv.lock* /app/
COPY src/ /app/src/

RUN pip install --upgrade pip && \
    pip install --no-cache-dir uv && \
    uv --version && \
    uv sync

FROM python:3.14-alpine
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

RUN addgroup -S app && adduser -S -G app app

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --chown=app:app src/ /app/src/

USER app

EXPOSE 8000

# use the virtual environment python
CMD ["/app/.venv/bin/uvicorn", "tcl_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
