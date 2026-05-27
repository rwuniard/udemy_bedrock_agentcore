# Udemy — Amazon Bedrock AgentCore

Two related projects demonstrating **AgentCore Runtime** (hosted agents) and **AgentCore Gateway** (MCP tools).

| Project | Directory | What it does |
|---------|-----------|--------------|
| **1 — Vacation Planner runtime** | [`vacation_planner/`](vacation_planner/README.md) | CrewAI multi-agent app on AgentCore (Bedrock Nova Pro + Serper); deploy via ECR, Lambda, API Gateway, Streamlit |
| **2 — Travel packages gateway** | [`test_agent_core_gateways/`](test_agent_core_gateways/README.md) | AgentCore **Gateway** as MCP server; JWT inbound auth; Lambda tool queries DynamoDB |

## Quick links

- **Deploy the crew agent:** [`vacation_planner/README.md`](vacation_planner/README.md) — `build_push_ecr.sh` → `deploy_agentcore.sh`
- **Test the gateway:** [`test_agent_core_gateways/README.md`](test_agent_core_gateways/README.md) — Cognito token + [`test_agent_core_gateways.py`](test_agent_core_gateways/test_agent_core_gateways.py)

## Shared AWS assets

- [`lambda_function/agent_core_lambda/`](lambda_function/agent_core_lambda/) — invokes the vacation planner **runtime** (Project 1)
- [`lambda_function/travel_package_lambda/`](lambda_function/travel_package_lambda/) — DynamoDB lookup used as a **gateway target** (Project 2)
