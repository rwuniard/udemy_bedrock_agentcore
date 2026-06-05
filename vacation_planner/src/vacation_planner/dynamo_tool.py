from crewai.tools import tool


import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")
TOKEN_URL = "https://us-west-2ojx6gvssl.auth.us-west-2.amazoncognito.com/oauth2/token"
GATEWAY_URL = os.getenv("GATEWAY_URL")

def fetch_access_token(client_id, client_secret, token_url):
  response = requests.post(
    token_url,
    data="grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}".format(client_id=client_id, client_secret=client_secret),
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  print("This is Auth token: ", response.json()['access_token'])

  return response.json()['access_token']


# Get Access Token
access_token = fetch_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)


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


@tool("Get Travel Packages")
def get_travel_packages(city: str) -> str:
    """Get travel packages for a given city"""
    access_token = fetch_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
    response = call_tool(GATEWAY_URL, access_token, "target-travel-agent-tool___get_travel_packages", {"city": city})
    return str(response)



