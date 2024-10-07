from agents.base_agent import Agent


REVIWER_PROMPT = """
You are an expert code reviewer as a software engineer in HTML and CSS scripts and are able to check and verify if an implementation plan has been implemented.
Given the plan.md and related artifacts and the milestone under consideration, use the tool calling feature to output a reviewResult using simple "yes" or "no" if the given milestone has been implemented in the
attached artifacts.

If the plan has not been implemented correctly, output an updated plan.md document to reflect your findings and use the tool calling feature to save the updated plan.md if needed.

"""
class ReviewerAgent(Agent):

    REVIEWER_AGENT_NAME: str = "Reviewer Agent"
    REVIEWER_AGENT_STRING: str = "reviewer"

    def __init__(self,  client,  gen_kwargs=None) -> None:
        super().__init__(ReviewerAgent.REVIEWER_AGENT_NAME, client, prompt=REVIWER_PROMPT, gen_kwargs=gen_kwargs)
        self.impl_message_history = [{"role": "system", "content": REVIWER_PROMPT},]

    
    async def execute_impl(self, milestone):
        self.review_result = "no"
        self.milestone = "0"
        self.impl_message_history.append({"role": "system", "content": f"As an expert software reviewer, verify if milestone {milestone} has been implemented and plan.md reflects this accurately."})
        await self.execute(self.impl_message_history)
        return f"Review of milestone {milestone} completed.", Agent.AGENT_PROCESSED
