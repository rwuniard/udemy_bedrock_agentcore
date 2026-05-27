import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")
TOKEN_URL = "https://us-west-2ojx6gvssl.auth.us-west-2.amazoncognito.com/oauth2/token"

def fetch_access_token(client_id, client_secret, token_url):
  response = requests.post(
    token_url,
    data="grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}".format(client_id=client_id, client_secret=client_secret),
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  print("This is Auth token: ", response.json()['access_token'])

  return response.json()['access_token']

def list_tools(gateway_url, access_token):
  headers = {
      "Content-Type": "application/json",
      "Authorization": f"Bearer {access_token}"
  }

  payload = {
      "jsonrpc": "2.0",
      "id": "list-tools-request",
      "method": "tools/list",
      "params": {},
  }

  response = requests.post(gateway_url, headers=headers, json=payload)
  return response.json()

# Example usage
gateway_url = "https://gateway-vacation-planner-n4gbeusz4g.gateway.bedrock-agentcore.us-west-2.amazonaws.com/mcp"
access_token = fetch_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
tools = list_tools(gateway_url, access_token)
print(json.dumps(tools, indent=2))


# Calling the tool
def call_tool(gateway_url, access_token, tool_name, tool_input):
  headers = {
      "Content-Type": "application/json",
      "Authorization": f"Bearer {access_token}"
  }

  # MCP spec: params.name + params.arguments (not tool_name / tool_input)
  payload = {
      "jsonrpc": "2.0",
      "id": "call-tool-request",
      "method": "tools/call",
      "params": {
          "name": tool_name,
          "arguments": tool_input,
      },
  }

  response = requests.post(gateway_url, headers=headers, json=payload)
  return response.json()

# Example usage of the tool
print("================================================")
print("This is the tool call response: ", json.dumps(call_tool(gateway_url, access_token, "target-travel-agent-tool___get_travel_packages", {"city": "Savannah"}), indent=2))
print("================================================")