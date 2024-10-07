from agents.base_agent import Agent


IMPLEMENTATION_PROMPT = """
You are an expert coder as an implementation agent in HTML and CSS scripts and are able to follow an implementation plan. Given the plan.md and related artifacts,
execute the referenced milestone from the plan. Output a modified version of index.html and style.css files as per the plan. If the files
are not already available, generate initial versions of these files given milestone referenced by the user below. Use the tool calling feature to save updated
versions of index.html and style.css files. Do not use the callAgent tool feature since we are the implementation agent.

Once the milestone has been completed, mark off the implemented milestone in the planning document and save the updated plan.md document using the update artifact feature.

"""
class ImplAgent(Agent):

    IMPL_AGENT_NAME: str = "Implementation Agent"
    IMPL_AGENT_STRING: str = "implementation"

    def __init__(self,  client,  gen_kwargs=None) -> None:
        super().__init__(ImplAgent.IMPL_AGENT_NAME, client, prompt=IMPLEMENTATION_PROMPT, gen_kwargs=gen_kwargs)
        self.impl_message_history = [{"role": "system", "content": IMPLEMENTATION_PROMPT},]

    
    async def execute_impl(self, milestone):
        self.impl_message_history.append({"role": "system", "content": f"Implement milestone {milestone} and update the planning document."})
        await self.execute(self.impl_message_history)

    
