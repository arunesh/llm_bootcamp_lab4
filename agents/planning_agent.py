from agents.base_agent import Agent
from utils import override

PLANNING_PROMPT = """\
You are a software architect, preparing to build the web page in the image that the user sends. 
Once they send an image, generate a plan, described below, in markdown format.

If the user or reviewer confirms the plan is good, available tools to save it as an artifact \
called `plan.md`. If the user has feedback on the plan, revise the plan, and save it using \
the tool again. A tool is available to update the artifact. Your role is only to plan the \
project. You will not implement the plan, and will not write any code.

If the plan has already been saved, no need to save it again unless there is feedback. Do not \
use the tool again if there are no changes.

For the contents of the markdown-formatted plan, create two sections, "Overview" and "Milestones".

In a section labeled "Overview", analyze the image, and describe the elements on the page, \
their positions, and the layout of the major sections.

Using vanilla HTML and CSS, discuss anything about the layout that might have different \
options for implementation. Review pros/cons, and recommend a course of action.

In a section labeled "Milestones", describe an ordered set of milestones for methodically \
building the web page, so that errors can be detected and corrected early. Pay close attention \
to the aligment of elements, and describe clear expectations in each milestone. Do not include \
testing milestones, just implementation.

Milestones should be formatted like this:

 - [ ] 1. This is the first milestone
 - [ ] 2. This is the second milestone
 - [ ] 3. This is the third milestone

If the user requests that a particular milestone be implemented, use the tool calling feature to implement the requested milestone.
"""


class PlanningAgent(Agent):

    PLANNING_AGENT_NAME: str = "Planning Agent"
    PLANNING_AGENT_STR: str = "planning"

    def __init__(self, client,  gen_kwargs=None) -> None:
        super().__init__(PlanningAgent.PLANNING_AGENT_NAME, client, prompt=PLANNING_PROMPT, gen_kwargs=gen_kwargs)
        self.impl_message_history = [{"role": "system", "content": PLANNING_PROMPT},]

    
    async def execute_impl(self, user_task):
        self.impl_message_history.append({"role": "system", "content": f"Create a plan for the following: {user_task}."})
        await self.execute(self.impl_message_history)
        return "Planning task completed and file saved.", Agent.AGENT_PROCESSED
        # TODO: Send a system message that planning is complete. 

    # no need to override callAgent: normally we would for the implementation agent, but we do it in the base class coz of M4.

    

        