import json
import os
import secrets
import time
import uuid

import boto3


def _sampled_trace_id() -> str:
    """Build an X-Ray trace header that forces sampling (Sampled=1)."""
    epoch = format(int(time.time()), "x")
    root = secrets.token_hex(12)
    parent = secrets.token_hex(8)
    return f"Root=1-{epoch}-{root};Parent={parent};Sampled=1"


def lambda_handler(event, context):
    client = boto3.client("bedrock-agentcore", region_name="us-west-2")

    user_input = event.get("prompt", "Tokyo")
    payload = json.dumps({"topic": user_input})

    session_id = f"lambda_session_{str(uuid.uuid4()).replace('-', '')}"

    # Lambda often propagates Sampled=0, which suppresses AgentCore spans.
    # See: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-troubleshooting.html#troubleshoot-runtime-lambda-missing-spans
    lambda_trace = os.environ.get("_X_AMZN_TRACE_ID", "not set")
    trace_id = _sampled_trace_id()
    print(f"Lambda _X_AMZN_TRACE_ID: {lambda_trace}")
    print(f"AgentCore traceId (Sampled=1): {trace_id}")
    print(f"Invoking AgentCore with payload: {payload} & session_id: {session_id}")

    response = client.invoke_agent_runtime(
        agentRuntimeArn="arn:aws:bedrock-agentcore:us-west-2:850652371396:runtime/vacation_planner-kqdG1OFLan",
        runtimeSessionId=session_id,
        payload=payload,
        qualifier="vacation_planner",
        traceId=trace_id,
    )
    response_body = response["response"].read()
    print("================================================")
    print(f"response_body: {response_body}")

    response_data = json.loads(response_body)
    print(f"response_data: {response_data}")

    return {
        "statusCode": 200,
        "headers": {
            "Content-type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(
            {
                "result": response_data,
                "session_id": session_id,
            }
        ),
    }
