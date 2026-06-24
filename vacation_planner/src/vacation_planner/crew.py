from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

from crewai import LLM, CrewOutput

from crewai_tools import SerperDevTool
from vacation_planner.dynamo_tool import get_travel_packages
import os

# Import libraries for Memory
import boto3
import uuid
from datetime import datetime

# Initialize the memory client
memory_client = boto3.client("bedrock-agentcore", region_name="us-west-2")



# Integration with AgentCore
from bedrock_agentcore.runtime import BedrockAgentCoreApp, RequestContext

bedrock_agentcore_app = BedrockAgentCoreApp()

if not os.environ.get("SERPER_API_KEY"):
    raise ValueError("SERPER_API_KEY environment variable is required")

llm = LLM(
    model="bedrock/us.amazon.nova-pro-v1:0",
    temperature=0.7,
    max_tokens=4000,
)

@CrewBase
class VacationPlanner():
    """VacationPlanner crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def vacation_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['vacation_researcher'], # type: ignore[index]
            verbose=True,
            tools=[SerperDevTool(), get_travel_packages], # SerperDevTool fetches SERPER_API_KEY from the environment variable automatically.
            llm=llm
        )

    @agent
    def itinerary_planner(self) -> Agent:
        return Agent(
            config=self.agents_config['itinerary_planner'], # type: ignore[index]
            verbose=True,
            llm=llm
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'], # type: ignore[index]
        )

    @task
    def reporting_task(self) -> Task:
        # This doesn't work with concurrent execution
        # return Task(
        #     config=self.tasks_config['reporting_task'], # type: ignore[index]
        #     output_file='report.md'
        # )
        return Task(
            config=self.tasks_config['reporting_task'],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the VacationPlanner crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )

def get_memory(context : RequestContext) -> list[dict]: 
    ''' Get the memory based from the session_id in the context '''
    session_id = getattr(context, "session_id", 'default_session')
    print(f"******************Getting memory for session_id: {session_id}")
    previous_events = memory_client.list_events(
        memoryId = 'vacation_planner_memory-g4IW0FHl3l',
        actorId = 'user', # this should be the user id but this app doesn't have a user id
        sessionId = session_id,
        maxResults= 3
    )
    events = previous_events.get('events', [])
    # We need to extract the information and return it in this format because that's what crewai expects.
    formatted_conversations = []
    for event in events:
        formatted_event = {}
        for key, value in event.items():
            if isinstance(value, datetime):
                formatted_event[key] = value.isoformat()
            else:
                formatted_event[key] = value
        formatted_conversations.append(formatted_event)
    return formatted_conversations

def store_memory(context : RequestContext, inputs : str, result: CrewOutput):
    ''' Store the memory based from the session_id in the context '''
    session_id = getattr(context, "session_id", 'default_session')
    print(f"******************Storing memory for session_id: {session_id}")
    print(f"Inputs: {inputs}")
    memory_client.create_event(
        memoryId = 'vacation_planner_memory-g4IW0FHl3l',
        actorId = 'user', # this should be the user id but this app doesn't have a user id
        sessionId = session_id,
        eventTimestamp = datetime.now().isoformat(),
        payload = [
            {
                "conversational": {
                    "content": {"text": inputs},
                    "role": "USER"
                },
            },
            {
                "conversational": {
                    "content": {"text": result.raw},
                    "role": "ASSISTANT"
                }
            }
        ],
        clientToken = str(uuid.uuid4())
    )


# Entry point for AgentCore
# This function to be executed by the agentcore runtime on an event (prompt) & Creates WebServer Endpoints.
@bedrock_agentcore_app.entrypoint
def crewai_bedrock(payload, context):
    try:

        """
        Invoke the crew with payload.
        """
        topic = payload.get("topic")
        current_year = payload.get("current_year")
        # Get the memory based from the session_id in the context
        formatted_conversations = get_memory(context)

        inputs = {
            "topic": topic,
            "current_year": current_year,so 
            "formatted_conversations": formatted_conversations
        }
        

        # Run the VacationPlanner crew agent with the user inputs.
        result = VacationPlanner().crew().kickoff(inputs=inputs)

        # Store the memory
        store_memory(context, inputs["topic"], result)

        # Return the result
        return result.raw
    except Exception as e:
        print(f"An error occurred while running the VacationPlanner crew: {e}")
        return {"error": f"An error occurred while running the VacationPlanner crew: {str(e)}"}

if __name__ == "__main__":
    bedrock_agentcore_app.run()