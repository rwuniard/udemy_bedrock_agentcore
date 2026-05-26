#!/usr/bin/env bash
# Wait until an AgentCore runtime version is READY (required before update-agent-runtime-endpoint).
# Usage: wait_agent_runtime_ready.sh <agent-runtime-id> <version>
set -euo pipefail

AGENT_RUNTIME_ID="${1:?agent-runtime-id required}"
VERSION="${2:?version required}"
AWS_REGION="${AWS_REGION:-us-west-2}"
MAX_ATTEMPTS="${WAIT_MAX_ATTEMPTS:-40}"
SLEEP_SECS="${WAIT_SLEEP_SECS:-15}"

echo "Waiting for runtime version ${VERSION} to reach READY (poll every ${SLEEP_SECS}s)..."

for ((attempt = 1; attempt <= MAX_ATTEMPTS; attempt++)); do
  STATUS="$(aws bedrock-agentcore-control get-agent-runtime \
    --agent-runtime-id "${AGENT_RUNTIME_ID}" \
    --agent-runtime-version "${VERSION}" \
    --region "${AWS_REGION}" \
    --query 'status' \
    --output text)"

  echo "  [${attempt}/${MAX_ATTEMPTS}] version ${VERSION}: ${STATUS}"

  if [[ "${STATUS}" == "READY" ]]; then
    echo "Runtime version ${VERSION} is READY."
    exit 0
  fi

  case "${STATUS}" in
    FAILED | CREATE_FAILED | DELETE_FAILED | DELETED)
      echo "Runtime version ${VERSION} is in terminal status: ${STATUS}"
      exit 1
      ;;
  esac

  sleep "${SLEEP_SECS}"
done

echo "Timed out waiting for version ${VERSION} to become READY."
exit 1
