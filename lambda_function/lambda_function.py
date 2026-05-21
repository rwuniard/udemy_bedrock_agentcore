import boto3
import json
import uuid


def lambda_handler(event, context):
    # TODO implement
 
    # Create a client connection with Bedrock AgentCore
    client = boto3.client('bedrock-agentcore', region_name='us-west-2')

    # Get user input from event, match to the expected Agent payload structure
    user_input = event.get('prompt', 'Tokyo')
    payload = json.dumps({"topic": user_input})

    # Generate a unique session ID (must be 33+ characters) using UUID without hyphens.
    session_id = f"lambda_session_{str(uuid.uuid4()).replace('-', '')}"

    print(f"Invoking AgentCore with payload: {payload} & session_id: {session_id}")

    # Invoke the AgentCore runtime for Vacation Planner.
    response = client.invoke_agent_runtime(
        agentRuntimeArn='arn:aws:bedrock-agentcore:us-west-2:850652371396:runtime/vacation_planner-kqdG1OFLan',
        runtimeSessionId=session_id, # Must be 33+ char. Every new SessionId will create a new MicroVM
        payload=payload,
        qualifier="vacation_planner" # This is Optional. When the field is not provided, Runtime will use DEFAULT endpoint
    )
    response_body = response['response'].read()
    print("================================================")
    print(f"response_body: {response_body}")

    response_data = json.loads(response_body)
    print(f"response_data: {response_data}")

    return {
        'statusCode': 200,
        'headers': {
            'Content-type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(
            {
                'result': response_data,
                'session_id': session_id
            }
        )
    }