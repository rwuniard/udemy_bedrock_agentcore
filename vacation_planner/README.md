# VacationPlanner Crew

A multi-agent vacation planning app built with [crewAI](https://crewai.com). Two agents—a **Vacation Researcher** and an **Itinerary Planner**—collaborate to research a destination and produce a Markdown travel report. The project uses **Amazon Bedrock** (Nova Pro) for LLM inference, **Serper** for web search, and includes an optional **Amazon Bedrock AgentCore** entry point for deployment.

## Prerequisites

- **Python 3.10–3.13** (`>=3.10,<3.14`) — Python 3.14 is not supported by `crewai==1.14.5`
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- AWS credentials with access to Amazon Bedrock (Nova Pro model enabled in your region)
- A [Serper](https://serper.dev/) API key for destination research

## Installation

From the `vacation_planner` directory:

```bash
pip install uv        # if needed
uv sync               # creates .venv and installs dependencies
```

Alternatively, using the CrewAI CLI:

```bash
crewai install
```

### Environment variables

Create a `.env` file in the `vacation_planner` directory:

```env
MODEL=bedrock/us.amazon.nova-pro-v1:0
AWS_DEFAULT_REGION=us-west-2
AWS_PROFILE=your-aws-profile
SERPER_API_KEY=your-serper-api-key
```

Verify your AWS profile:

```bash
export AWS_PROFILE=your-aws-profile   # or set in .env
aws sts get-caller-identity
```

## Customizing

- `src/vacation_planner/config/agents.yaml` — agent roles, goals, and backstories
- `src/vacation_planner/config/tasks.yaml` — task descriptions and outputs
- `src/vacation_planner/crew.py` — agents, tools, Bedrock LLM, and AgentCore entry point
- `src/vacation_planner/main.py` — default `topic` and other kickoff inputs

The destination is passed as the `topic` input and interpolated into YAML templates as `{topic}`.

## Running the Project

All commands below should be run from the `vacation_planner` directory.

### CLI (crew)

```bash
crewai run
```

Equivalent uv commands:

```bash
uv run vacation_planner
# or
uv run run_crew
```

By default, `main.py` sets `topic` (e.g. `Savannah, GA`) and writes a Markdown report (`report.md`) in the project folder.

### Vacation Planner UI (Streamlit)

A browser-based UI is available in [`streamlitui.py`](streamlitui.py). Enter a destination, run the crew, and view or download the generated plan.

```bash
uv run streamlit run streamlitui.py
```

Streamlit opens a local URL (typically `http://localhost:8501`).

## Testing with AgentCore locally

`src/vacation_planner/crew.py` defines a `BedrockAgentCoreApp` with an entry point (`crewai_bedrock`) that AgentCore invokes in production. You can test that same path locally before deploying.

The entry point expects a JSON payload with:

| Field | Description |
|-------|-------------|
| `topic` | Travel destination (e.g. `"Savannah, GA"`) |
| `current_year` | Year string (e.g. `"2026"`) |

To test without Docker, run `uv run python src/vacation_planner/crew.py` and use the same `curl` commands as in [Docker: Build, Run & Test](#docker-build-run--test) below.

## Docker: Build, Run & Test

Package and test the AgentCore entry point locally using [`Dockerfile`](Dockerfile) and the helper scripts in this directory.

This project pins `bedrock-agentcore>=1.7.0,<1.8.0` to stay compatible with `crewai[bedrock]==1.14.5`. Images are built for **`linux/arm64`** (required for AgentCore deployment).

Make the scripts executable (once):

```bash
chmod +x docker_build.sh docker_run.sh test_agent.sh
```

### 1. Export AWS credentials

The container needs AWS credentials to call Bedrock. From the `vacation_planner` directory, set your profile and export credentials into the current shell:

```bash
export AWS_PROFILE=rwuniard                    # use your profile name
aws sso login --profile rwuniard               # skip if not using SSO

eval $(aws configure export-credentials --profile rwuniard --format env)
```

The `export-credentials` command prints `export AWS_ACCESS_KEY_ID=...` lines — wrapping it with `eval $(...)` loads them into your current shell so `docker_run.sh` can forward them to the container.

This sets `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in your terminal. Verify:

```bash
aws sts get-caller-identity
echo $AWS_ACCESS_KEY_ID
```

**Notes:**

- Session tokens expire — re-run `aws sso login` and the `eval` command if Bedrock calls fail later.
- `docker_run.sh` forwards these env vars into the container with `-e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY`.

### 2. Build the image

From the `vacation_planner` directory:

```bash
./docker_build.sh
```

This runs `docker buildx build --platform linux/arm64` and tags the image as `vacation-planner:latest` and `vacation-planner:<git-commit>`.

### 3. Run the container

In **terminal 1** (keep it open — the server runs in the foreground):

```bash
./docker_run.sh
```

This starts a named container (`vacation-planner-local`) on port **8080** running `python -m vacation_planner.crew`.

If port 8080 is already in use:

```bash
lsof -i :8080
docker rm -f vacation-planner-local
```

### 4. Test the agent

In **terminal 2**, while the container is running:

```bash
./test_agent.sh
```

Or run the steps manually:

```bash
curl http://127.0.0.1:8080/ping

curl -X POST http://127.0.0.1:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"topic": "Savannah, GA", "current_year": "2026"}'
```

A successful `/invocations` response returns the crew's Markdown report. The run may take several minutes (Bedrock LLM calls + Serper web search).

### Helper scripts

| Script | Purpose |
|--------|---------|
| [`docker_build.sh`](docker_build.sh) | Build ARM64 image with git commit + `latest` tags |
| [`docker_run.sh`](docker_run.sh) | Run container locally with AWS credentials |
| [`test_agent.sh`](test_agent.sh) | POST test payload to `/invocations` |

When deployed to AgentCore, the runtime uses the container IAM role for Bedrock access instead of passing AWS credentials into `docker run`.

## Understanding your crew

| Agent | Role |
|-------|------|
| `vacation_researcher` | Researches the destination using Serper web search |
| `itinerary_planner` | Turns research into a detailed Markdown itinerary |

Tasks are defined in `config/tasks.yaml` and run sequentially (`Process.sequential`).

## Key dependencies

Managed in `pyproject.toml`:

- `crewai[bedrock,tools]==1.14.5`
- `crewai-tools==1.14.5`
- `bedrock-agentcore>=1.7.0,<1.8.0`
- `streamlit>=1.57.0`

## Support

- [crewAI documentation](https://docs.crewai.com)
- [crewAI GitHub](https://github.com/joaomdmoura/crewai)
- [crewAI Discord](https://discord.com/invite/X4JWnZnxPb)
