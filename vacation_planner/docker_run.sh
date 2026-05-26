#!/usr/bin/env bash
set -euo pipefail

# Load .env if present (SERPER_API_KEY, AWS_PROFILE, etc.)
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [[ -z "${SERPER_API_KEY:-}" ]]; then
  echo "SERPER_API_KEY is not set."
  echo "Add it to vacation_planner/.env or run: export SERPER_API_KEY=your-key"
  exit 1
fi

if [[ -z "${AWS_ACCESS_KEY_ID:-}" || -z "${AWS_SECRET_ACCESS_KEY:-}" ]]; then
  echo "AWS credentials are not set in this shell."
  echo "Run: eval \$(aws configure export-credentials --profile rwuniard --format env)"
  exit 1
fi

# Local Docker Desktop only — skip ADOT export (no OTLP collector on localhost:4317).
# Production image CMD uses opentelemetry-instrument; AgentCore injects OTEL env at runtime.
echo "Starting local agent on http://127.0.0.1:8080 (telemetry export disabled for local run)."
docker run --name vacation-planner-local --rm -p 8080:8080 \
  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY \
  -e AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-west-2}" \
  -e SERPER_API_KEY \
  -e OTEL_SDK_DISABLED=true \
  vacation-planner:latest \
  python -m vacation_planner.crew
