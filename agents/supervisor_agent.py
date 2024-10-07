from agents.base_agent import Agent, add_to_message
from agents.implementation_agent import ImplAgent
import chainlit as cl

SUPERVISOR_PROMPT = """

You are a coding project supervisor. Your task is to take a web coding project from the user and do the following:

1. Convert it into a plan using the planning tool calling feature.
2. Execute the plan one milestone at a time, using the implementation tool calling feature. Keep the user updated of the progress.

Use the planning agent tool calling feature to create a plan as needed.
Once a plan has been created, use the implementation agent to execute the plan. 

"""


class SupervisorAgent(Agent):

    SUPERVISOR_AGENT_NAME: str = "Supervisor Agent"

    def __init__(self, client,  gen_kwargs=None) -> None:
        super().__init__(SupervisorAgent.SUPERVISOR_AGENT_NAME, client, prompt=SUPERVISOR_PROMPT, gen_kwargs=gen_kwargs)
        #self.impl_message_history = [{"role": "system", "content": SUPERVISOR_PROMPT},]


    
    async def execute_impl(self, message_history):
        #self.impl_message_history.append({"role": "system", "content": f"Ask the user for a web project to plan and implement."})
        self.message_history = message_history
        await self.execute(message_history)
        return "Project implementation completed.", Agent.TASK_RESULT_SUCCESS

    async def callAgent(self, agent_args_dict):
        msg, result_code = await super().callAgent(agent_args_dict)
        if  result_code != Agent.AGENT_UNPROCESSED:
            return msg, result_code

        # Attempt to process it here.

        agent_name = agent_args_dict["agent_name"]
        if self.name == agent_name:
            print(f"Recursive call to self. Can't proceed. self = f{self.name}, agent_name = {agent_name}")
            return None, Agent.AGENT_ERROR
        from agents.planning_agent import PlanningAgent
        if agent_name == PlanningAgent.PLANNING_AGENT_STR:
            if "project_desc" not in agent_args_dict:
                print("callAgent('planning') but no project_desc ! ", agent_args_dict)
                return None, Agent.AGENT_ERROR
            project_desc = agent_args_dict["project_desc"]
            print(f"Agent name: {agent_name}, project_desc: {project_desc}")

            response_str, result_code = await PlanningAgent(client=self.client).execute_impl(project_desc)
            if result_code == Agent.TASK_RESULT_SUCCESS:
                self._stream_message_llm(response_str)
            else:
                error_response_str ="There was an error creating a plan for the given task."
                return error_response_str, Agent.AGENT_ERROR

            num_milestones = cl.user_session.get("num_milestones", 8)
            for i in range (1, num_milestones):
                print(f"Calling implementation agent for milestone {i}")
                response_str, result_code = await self._call_implementation_agent(f" milestone {i} ")
                if result_code == Agent.AGENT_ERROR:
                    return response_str, Agent.AGENT_ERROR

            return "All milestones complete.", Agent.AGENT_PROCESSED
        else:
            return None, Agent.AGENT_UNPROCESSED  # The child class might process it.
    
    async def _call_implementation_agent(self, milestone):
        response_str, result_code = await ImplAgent(client=self.client).execute_impl(milestone)
        if result_code == Agent.TASK_RESULT_SUCCESS:
            self._stream_message_llm(response_str)
        else:
            error_response_str = f"There was an error implementing {milestone}."
            return error_response_str, Agent.AGENT_ERROR 

        