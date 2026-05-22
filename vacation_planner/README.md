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

### Vacation Planner UI (Streamlit + API Gateway)

[`streamlit_api.py`](streamlit_api.py) is the **production-style UI**. It does not run the crew locally — it calls your deployed AWS stack:

```
streamlit_api.py  →  API Gateway  →  Lambda  →  AgentCore Runtime  →  Vacation Planner crew
```

| Layer | Component | Role |
|-------|-----------|------|
| UI | [`streamlit_api.py`](streamlit_api.py) | Sends `POST {"prompt": "<destination>"}` to API Gateway |
| API | API Gateway (`vacation_planner_resource`) | HTTP endpoint in front of Lambda |
| Compute | [`lambda_function/lambda_function.py`](../lambda_function/lambda_function.py) | Maps `prompt` → `topic`, calls `invoke_agent_runtime` |
| Agent | AgentCore Runtime (ECR container) | Runs `crewai_bedrock` in [`crew.py`](src/vacation_planner/crew.py) |

**Request flow**

1. User enters a destination in Streamlit.
2. `streamlit_api.py` posts to API Gateway.
3. Lambda receives the event, builds payload `{"topic": "<destination>"}`, and invokes the AgentCore runtime.
4. AgentCore runs the Vacation Planner crew (Bedrock Nova Pro + Serper search).
5. Lambda returns `{"result": "<markdown report>", "session_id": "..."}`.
6. Streamlit parses `body["result"]` and displays the Markdown plan.

Run the API-backed UI:

```bash
uv run streamlit run streamlit_api.py
```

Update `API_URL` in `streamlit_api.py` to your API Gateway invoke URL if it differs.

**Compare the two UIs**

| File | Runs crew | Use case |
|------|-----------|----------|
| [`streamlitui.py`](streamlitui.py) | Locally (in-process) | Development / demo without AWS deploy |
| [`streamlit_api.py`](streamlit_api.py) | Via API Gateway → Lambda → AgentCore | End-to-end AWS architecture |

## Docker: Build, Run & Test

Package and test the AgentCore entry point locally using [`Dockerfile`](Dockerfile) and the helper scripts in this directory.

This project pins `bedrock-agentcore>=1.7.0,<1.8.0` to stay compatible with `crewai[bedrock]==1.14.5`. Images are built for **`linux/arm64`** (required for AgentCore deployment).

Make the scripts executable (once):

```bash
chmod +x docker_build.sh docker_run.sh test_agent.sh build_push_ecr.sh deploy_agentcore.sh aws_ecr_create.sh
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

This starts a named container (`vacation-planner-local`) on port **8080** running the AgentCore entry point with ADOT auto-instrumentation (`opentelemetry-instrument python -m vacation_planner.crew`).

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

### Helper scripts (local Docker)

| Script | Purpose |
|--------|---------|
| [`docker_build.sh`](docker_build.sh) | Build ARM64 image locally (`vacation-planner:latest` + git tag) |
| [`docker_run.sh`](docker_run.sh) | Run container locally with AWS credentials |
| [`test_agent.sh`](test_agent.sh) | POST test payload to `/invocations` |

When deployed to AgentCore, the runtime uses the container IAM role for Bedrock access instead of passing AWS credentials into `docker run`.

### Observability (ADOT)

The [`Dockerfile`](Dockerfile) installs `aws-opentelemetry-distro` **only in the container image**, not in `pyproject.toml`, because CrewAI 1.14.5 pins `opentelemetry-sdk~=1.34.0` and ADOT requires a different SDK version.

**Without ADOT** (platform metrics only): invocation latency, errors, token usage, runtime logs.

**With ADOT** (in the Docker image): GenAI traces in CloudWatch — per-agent/task spans, tool calls (Serper), and Bedrock LLM calls with a step-by-step timeline.

One-time AWS setup:

1. Enable [CloudWatch Transaction Search](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-TransactionSearch.html) in your account/region.
2. In the AgentCore console, open your runtime → **Tracing** → **Enable**.
3. Ensure the runtime execution role can write to CloudWatch Logs and X-Ray (see [AgentCore runtime permissions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html)).

After deploy, view traces under [CloudWatch GenAI Observability](https://console.aws.amazon.com/cloudwatch/home#gen-ai-observability) or **Transaction Search** (`/aws/spans/default`).

**Traces work when invoking AgentCore directly, but not via Lambda?**

This is a [documented AgentCore behavior](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-troubleshooting.html#troubleshoot-runtime-lambda-missing-spans). Lambda often forwards an `X-Amzn-Trace-Id` with `Sampled=0`, which tells AgentCore to skip span generation.

[`lambda_function/lambda_function.py`](../lambda_function/lambda_function.py) fixes this by passing `traceId=...;Sampled=1` on `invoke_agent_runtime`. **Redeploy the Lambda** after pulling that change.

Alternative (console): enable **Active tracing** on the Lambda function (Monitoring → AWS X-Ray). Either approach works; the code fix is explicit and does not require X-Ray on Lambda.

### Deploy to AgentCore (ECR + runtime update)

Publishing a new image to ECR does **not** automatically update AgentCore. You need two steps:

1. **Push** — build the ARM64 image and upload it to ECR ([`build_push_ecr.sh`](build_push_ecr.sh))
2. **Register** — tell AgentCore to use that image ([`deploy_agentcore.sh`](deploy_agentcore.sh))

You can also update the container URI in the [AgentCore console](https://console.aws.amazon.com/bedrock-agentcore/agents) instead of running `deploy_agentcore.sh` — both call the same `UpdateAgentRuntime` API.

#### 1. Authenticate with AWS

`build_push_ecr.sh` and `deploy_agentcore.sh` use the AWS CLI with your profile (default: `rwuniard`):

```bash
export AWS_PROFILE=rwuniard          # or your profile name
aws sso login --profile rwuniard     # skip if not using SSO
aws sts get-caller-identity          # verify account/region
```

For **local Docker only** (`docker_run.sh`), you still need exported credentials — see [Export AWS credentials](#1-export-aws-credentials) above. The deploy scripts do not need `eval $(aws configure export-credentials ...)`.

#### 2. Create the ECR repository (once)

```bash
./aws_ecr_create.sh
```

#### 3. Push a new image to ECR

```bash
./build_push_ecr.sh
```

This script:

- Logs Docker into ECR
- Builds the image for **`linux/arm64`** from the current directory
- Pushes two tags to `vacation-planner`:
  - `:latest` (mutable — always points at the most recent push)
  - `:<git-commit>` (immutable — e.g. `:f243386`)

The image is pushed directly to ECR (`--push`); it is **not** loaded into local Docker Desktop.

#### 4. Update the AgentCore runtime

After the push completes, register the new image with AgentCore:

```bash
./deploy_agentcore.sh
```

This script:

- Uses `AWS_PROFILE` (default `rwuniard`) and region `us-west-2`
- Sets the container URI to `850652371396.dkr.ecr.us-west-2.amazonaws.com/vacation-planner:<git-commit>` (current `git rev-parse --short HEAD`)
- Fetches the existing **execution role** from AgentCore (`get-agent-runtime`) — you do not hardcode it
- Calls `update-agent-runtime`, which creates a new immutable runtime version (V2, V3, …)
- Updates the **`vacation_planner`** endpoint to that new version (Lambda uses `qualifier="vacation_planner"`, not `DEFAULT`)

Wait until the runtime and endpoint status are **`READY`** in the console before testing.

**Override defaults when needed:**

```bash
# Deploy a specific image tag (must already exist in ECR)
AGENTCORE_IMAGE_TAG=f243386 ./deploy_agentcore.sh

# Different runtime, profile, or endpoint
AGENT_RUNTIME_ID=vacation_planner-kqdG1OFLan \
AGENT_RUNTIME_ENDPOINT=vacation_planner \
AWS_PROFILE=rwuniard ./deploy_agentcore.sh
```

**Why the endpoint step matters:** `update-agent-runtime` creates a new version, and `DEFAULT` follows it automatically. Your Lambda uses the custom qualifier `vacation_planner`, which stays on the old version until you update that endpoint (the deploy script does this for you).

**Full redeploy workflow:**

```bash
export AWS_PROFILE=rwuniard
aws sso login --profile rwuniard
./build_push_ecr.sh
./deploy_agentcore.sh
```

#### 5. Test after deploy

- Use a **new session ID** when invoking — existing sessions may keep the previous container version until they expire.
- Confirm the **`vacation_planner`** endpoint shows the new version under **Endpoints** in the AgentCore console (or re-run `./deploy_agentcore.sh`, which updates it automatically).

#### Deploy helper scripts

| Script | Purpose |
|--------|---------|
| [`aws_ecr_create.sh`](aws_ecr_create.sh) | Create ECR repository (once) |
| [`build_push_ecr.sh`](build_push_ecr.sh) | Build ARM64 image and push to ECR (`:latest` + git tag) |
| [`deploy_agentcore.sh`](deploy_agentcore.sh) | Update AgentCore runtime to use the pushed image |

## AWS deployment architecture

End-to-end flow when using `streamlit_api.py`:

```mermaid
flowchart LR
    A["streamlit_api.py"] -->|POST prompt| B["API Gateway"]
    B --> C["Lambda\nlambda_function.py"]
    C -->|invoke_agent_runtime| D["Bedrock AgentCore\nvacation-planner container"]
    D --> E["CrewAI crew\ncrewai_bedrock"]
    E -->|Markdown report| D
    D --> C
    C --> B
    B --> A
```

Deploy steps (high level):

1. **AgentCore** — `./build_push_ecr.sh` then `./deploy_agentcore.sh` (or update container URI in the console)
2. **Lambda** — deploy [`lambda_function/lambda_function.py`](../lambda_function/lambda_function.py) with permission to call `bedrock-agentcore:InvokeAgentRuntime`
3. **API Gateway** — REST/API HTTP route integrated with Lambda (`vacation_planner_resource`)
4. **Streamlit** — run [`streamlit_api.py`](streamlit_api.py) with `API_URL` set to your Gateway endpoint

## Testing with AgentCore locally

`src/vacation_planner/crew.py` defines a `BedrockAgentCoreApp` with an entry point (`crewai_bedrock`) that AgentCore invokes in production. You can test that same path locally before deploying.

The entry point expects a JSON payload with:

| Field | Description |
|-------|-------------|
| `topic` | Travel destination (e.g. `"Savannah, GA"`) |
| `current_year` | Year string (e.g. `"2026"`) |

To test without Docker, run `uv run python src/vacation_planner/crew.py` and use the same `curl` commands as in [Docker: Build, Run & Test](#docker-build-run--test).

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
