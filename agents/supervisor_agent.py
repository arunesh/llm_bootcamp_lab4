from agents.base_agent import Agent, add_to_message
from utils import override

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

# TODO: pass in the message history.
    @override(Agent.callAgent)  
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
        if agent_name == PlanningAgent.IMPL_AGENT_STRING:
            if "task_sesc" not in agent_args_dict:
                print("callAgent('planning') but no task_desc ! ", agent_args_dict)
                return None, Agent.AGENT_ERROR
            task_desc = agent_args_dict["task_desc"]
            print(f"Agent name: {agent_name}, task_desc: {task_desc}")

            response_str, result_code = await PlanningAgent(client=self.client).execute_impl(task_desc)
            #if result_code == Agent.TASK_RESULT_SUCCESS:
            #    add_to_message(super.message_history, super.client, response_str, message_string, **gen_kwargs)

            # add response_str to system message and perform the next step, i.e. implementation. 
            return response_str, Agent.AGENT_PROCESSED
        else:
            return None, Agent.AGENT_UNPROCESSED  # The child class might process it.

        