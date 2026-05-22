# Vacation Planner — Amazon Bedrock AgentCore runtime image
#
# Build:
#   docker build -t vacation-planner .
#
# Run locally:
#   docker run --rm -p 8080:8080 \
#     -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY \
#     -e AWS_DEFAULT_REGION=us-west-2 \
#     vacation-planner

FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DOCKER_CONTAINER=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY src ./src
COPY knowledge ./knowledge

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN uv sync --frozen --no-dev \
    && uv pip install "aws-opentelemetry-distro==0.15.0"

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://127.0.0.1:8080/ping || exit 1

# ADOT is Docker-only (conflicts with crewai OTEL pins in pyproject.toml).
# AgentCore injects OTEL env vars at runtime; opentelemetry-instrument exports GenAI spans to CloudWatch.
CMD ["opentelemetry-instrument", "python", "-m", "vacation_planner.crew"]
