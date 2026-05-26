#!/usr/bin/env bash
set -euo pipefail

export AWS_PROFILE="${AWS_PROFILE:-rwuniard}"
export AWS_REGION="${AWS_REGION:-us-west-2}"
export AGENT_RUNTIME_ID="${AGENT_RUNTIME_ID:-vacation_planner-kqdG1OFLan}"

if [[ -z "${SERPER_API_KEY:-}" ]]; then
  if [[ -f .env ]]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
  fi
fi

if [[ -z "${SERPER_API_KEY:-}" ]]; then
  echo "SERPER_API_KEY is not set."
  echo "Export it or add it to vacation_planner/.env, then re-run."
  exit 1
fi

RUNTIME_JSON="$(aws bedrock-agentcore-control get-agent-runtime \
  --agent-runtime-id "${AGENT_RUNTIME_ID}" \
  --region "${AWS_REGION}" \
  --output json)"

ROLE_ARN="$(echo "${RUNTIME_JSON}" | python3 -c "import sys,json; print(json.load(sys.stdin)['roleArn'])")"
CONTAINER_URI="$(echo "${RUNTIME_JSON}" | python3 -c "import sys,json; print(json.load(sys.stdin)['agentRuntimeArtifact']['containerConfiguration']['containerUri'])")"

ENV_VARS_JSON="$(ENV_VARS_JSON="$(echo "${RUNTIME_JSON}" | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin).get('environmentVariables') or {}))")" \
  SERPER_API_KEY="${SERPER_API_KEY}" \
  python3 - <<'PY'
import json
import os

env = json.loads(os.environ["ENV_VARS_JSON"])
env["SERPER_API_KEY"] = os.environ["SERPER_API_KEY"]
print(json.dumps(env))
PY
)"

echo "Updating SERPER_API_KEY on runtime: ${AGENT_RUNTIME_ID}"
echo "Keeping container URI: ${CONTAINER_URI}"

UPDATE_VERSION="$(aws bedrock-agentcore-control update-agent-runtime \
  --agent-runtime-id "${AGENT_RUNTIME_ID}" \
  --agent-runtime-artifact "{\"containerConfiguration\":{\"containerUri\":\"${CONTAINER_URI}\"}}" \
  --role-arn "${ROLE_ARN}" \
  --network-configuration '{"networkMode":"PUBLIC"}' \
  --environment-variables "${ENV_VARS_JSON}" \
  --region "${AWS_REGION}" \
  --query 'agentRuntimeVersion' \
  --output text)"

AGENT_RUNTIME_ENDPOINT="${AGENT_RUNTIME_ENDPOINT:-vacation_planner}"

aws bedrock-agentcore-control update-agent-runtime-endpoint \
  --agent-runtime-id "${AGENT_RUNTIME_ID}" \
  --endpoint-name "${AGENT_RUNTIME_ENDPOINT}" \
  --agent-runtime-version "${UPDATE_VERSION}" \
  --region "${AWS_REGION}"

echo "SERPER_API_KEY updated. Runtime version: ${UPDATE_VERSION}"
