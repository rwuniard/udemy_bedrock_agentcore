from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

from crewai import LLM

from crewai_tools import SerperDevTool
import os

# Integration with AgentCore
from bedrock_agentcore.runtime import BedrockAgentCoreApp


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
            tools=[SerperDevTool()], # SerperDevTool fetches SERPER_API_KEY from the environment variable automatically.
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
        inputs = {
            "topic": topic,
            "current_year": current_year
        }

        # Run the VacationPlanner crew agent with the user inputs.
        result = VacationPlanner().crew().kickoff(inputs=inputs)

        # Return the result
        return result.raw
    except Exception as e:
        print(f"An error occurred while running the VacationPlanner crew: {e}")
        return {"error": f"An error occurred while running the VacationPlanner crew: {str(e)}"}

if __name__ == "__main__":
    bedrock_agentcore_app.run()