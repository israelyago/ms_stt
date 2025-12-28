# ===============================
# Stage 1: Builder
# ===============================
FROM python:3.12-slim-trixie as builder
COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /uvx /bin/

# Copy the project into the image
COPY . /app

# Disable development dependencies
ENV UV_NO_DEV=1

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
RUN uv sync --no-install-project

# ===============================
# Stage 2: Runtime
# ===============================
FROM python:3.10-slim
COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /uvx /bin/

WORKDIR /app

# # Copy only virtualenv and source code from builder
COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

RUN uv sync

# Expose gRPC port
EXPOSE 50051

# Default command: run the STT server
CMD ["uv", "run", "-m", "ms_stt.main"]