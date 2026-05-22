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

# Get the execution role for the agent runtime
ROLE_ARN="$(aws bedrock-agentcore-control get-agent-runtime \
  --agent-runtime-id "${AGENT_RUNTIME_ID}" \
  --region "${AWS_REGION}" \
  --query 'roleArn' \
  --output text)"

echo "Execution role:  ${ROLE_ARN}"

aws bedrock-agentcore-control update-agent-runtime \
  --agent-runtime-id "${AGENT_RUNTIME_ID}" \
  --agent-runtime-artifact "{\"containerConfiguration\":{\"containerUri\":\"${CONTAINER_URI}\"}}" \
  --role-arn "${ROLE_ARN}" \
  --network-configuration '{"networkMode":"PUBLIC"}' \
  --region "${AWS_REGION}"

echo "AgentCore runtime update submitted."
