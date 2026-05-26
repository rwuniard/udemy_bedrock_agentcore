#!/usr/bin/env bash
set -euo pipefail

export AWS_PROFILE="${AWS_PROFILE:-rwuniard}"
export AWS_REGION="${AWS_REGION:-us-west-2}"
export AWS_ACCOUNT_ID
AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"

export ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/vacation-planner"
export AGENT_RUNTIME_ID="${AGENT_RUNTIME_ID:-vacation_planner-kqdG1OFLan}"
export AGENTCORE_IMAGE_TAG="${AGENTCORE_IMAGE_TAG:-$(git rev-parse --short HEAD)}"

CONTAINER_URI="${ECR_URI}:${AGENTCORE_IMAGE_TAG}"

echo "AWS profile:     ${AWS_PROFILE}"
echo "ECR URI:         ${ECR_URI}"
echo "Container URI:   ${CONTAINER_URI}"
echo "Agent runtime:   ${AGENT_RUNTIME_ID}"

RUNTIME_JSON="$(aws bedrock-agentcore-control get-agent-runtime \
  --agent-runtime-id "${AGENT_RUNTIME_ID}" \
  --region "${AWS_REGION}" \
  --output json)"

ROLE_ARN="$(echo "${RUNTIME_JSON}" | python3 -c "import sys,json; print(json.load(sys.stdin)['roleArn'])")"

echo "Execution role:  ${ROLE_ARN}"

# update-agent-runtime creates a full new version snapshot — omitting
# environmentVariables clears them. Re-apply existing vars (+ optional override).
ENV_VARS_JSON="$(ENV_VARS_JSON="$(echo "${RUNTIME_JSON}" | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin).get('environmentVariables') or {}))")" \
  SERPER_API_KEY="${SERPER_API_KEY:-}" \
  python3 - <<'PY'
import json
import os

env = json.loads(os.environ["ENV_VARS_JSON"])
if os.environ.get("SERPER_API_KEY"):
    env["SERPER_API_KEY"] = os.environ["SERPER_API_KEY"]
print(json.dumps(env))
PY
)"

ENV_ARGS=()
if [[ "${ENV_VARS_JSON}" != "{}" ]]; then
  ENV_ARGS=(--environment-variables "${ENV_VARS_JSON}")
  echo "Environment variables preserved:"
  echo "${ENV_VARS_JSON}" | python3 -c "import sys,json; [print(f'  {k}') for k in json.load(sys.stdin)]"
else
  echo "Warning: no environment variables on this runtime."
  echo "Set SERPER_API_KEY once via ./update_serpapi_key.sh or the AgentCore console."
fi

UPDATE_VERSION="$(aws bedrock-agentcore-control update-agent-runtime \
  --agent-runtime-id "${AGENT_RUNTIME_ID}" \
  --agent-runtime-artifact "{\"containerConfiguration\":{\"containerUri\":\"${CONTAINER_URI}\"}}" \
  --role-arn "${ROLE_ARN}" \
  --network-configuration '{"networkMode":"PUBLIC"}' \
  "${ENV_ARGS[@]}" \
  --region "${AWS_REGION}" \
  --query 'agentRuntimeVersion' \
  --output text)"

echo "Runtime update submitted. New version: ${UPDATE_VERSION}"

# DEFAULT auto-follows the latest version; custom endpoints (e.g. vacation_planner) do not.
AGENT_RUNTIME_ENDPOINT="${AGENT_RUNTIME_ENDPOINT:-vacation_planner}"

echo "Updating endpoint: ${AGENT_RUNTIME_ENDPOINT} -> version ${UPDATE_VERSION}"

aws bedrock-agentcore-control update-agent-runtime-endpoint \
  --agent-runtime-id "${AGENT_RUNTIME_ID}" \
  --endpoint-name "${AGENT_RUNTIME_ENDPOINT}" \
  --agent-runtime-version "${UPDATE_VERSION}" \
  --region "${AWS_REGION}"

echo "Endpoint update submitted."
