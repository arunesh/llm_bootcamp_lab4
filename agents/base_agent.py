import os
import chainlit as cl
import json


async def add_to_message(message_history, client, response_message, message_string, **gen_kwargs):
    # Add a message to the message history
    message_history.append({
        "role": "system",
        "content": message_string
    })

    stream = await client.chat.completions.create(messages=message_history, stream=True, **gen_kwargs)
    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await response_message.stream_token(token)  


class Agent:
    """
    Base class for all agents.
    """

    AGENT_ERROR: int =  0
    AGENT_PROCESSED: int = 1
    AGENT_UNPROCESSED: int = 2

    TASK_RESULT_SUCCESS: int = 0
    TASK_RESULT_FAILURE: int = 1


    BASE_TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "updateArtifact",
                "description": "Update a single artifact file which is HTML, CSS, or markdown with the given contents. For multiple files, call this one after another.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "The name of the file to update.",
                        },
                        "contents": {
                            "type": "string",
                            "description": "The markdown, HTML, or CSS contents to write to the file.",
                        },
                        "num_milestones": {
                            "type": "integer",
                        "description": "When creating a planning document, this provides the total number of milestones present in the plan."
                        }
                    },
                    "required": ["filename", "contents"],
                    "additionalProperties": False,
                },
            }
        },
         {
            "type": "function",
            "function": {
                "name": "callAgent",
                "description": "Calls an agent to perform a task.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "agent_name": {
                            "type": "string",
                            "description": "The name of the agent: supported agents include 'implementation' and 'planning'.",
                        },
                        "milestone": {
                            "type": "string",
                            "description": "if agent_name is 'implementation', then this parameter describes the milestone to be implemented by the agent.",
                        },
                        "project_desc": {
                            "type": "string",
                            "description": "if agent_name is 'planning', then this parameter describes the coding project for which a plan needs to be created.",
                        },
                    },
                    "required": ["agent_name",],
                    "additionalProperties": False,
                },
            }
        },
    ]

    def __init__(self, name, client, prompt="", gen_kwargs=None):
        self.name = name
        self.client = client
        self.prompt = prompt
        self.gen_kwargs = gen_kwargs or {
            "model": "gpt-4o",
            "temperature": 0.2
        }
        self.tools = Agent.BASE_TOOLS


    async def _execute_function(self, message_history, response_message, function_name, arguments):
        if function_name:
            print("DEBUG: function_name:")
            print("type:", type(function_name))
            print("value:", function_name)
            print("DEBUG: arguments:")
            print("type:", type(arguments))
            print("value:", arguments)
            
        if function_name == "updateArtifact":
            arguments_dict = json.loads(arguments)
            filename = arguments_dict.get("filename")
            contents = arguments_dict.get("contents")
            print(f"updateArtifacts: filename={filename}, contents={contents}")
            if filename and contents:
                os.makedirs("artifacts", exist_ok=True)
                with open(os.path.join("artifacts", filename), "w") as file:
                    file.write(contents)
                if "num_milestones" in arguments_dict:
                    n = arguments_dict.get("num_milestones")
                    print(f"Number of milestones set to {n}")
                    cl.user_session.set("num_milestones", n)
                # Add a message to the message history
                message_history.append({
                    "role": "system",
                    "content": f"The artifact '{filename}' was updated."
                })

                stream = await self.client.chat.completions.create(messages=message_history, stream=True, **self.gen_kwargs)
                async for part in stream:
                    if token := part.choices[0].delta.content or "":
                        await response_message.stream_token(token)  
                self.message_history = message_history
        elif function_name == "callAgent":
            arguments_dict = json.loads(arguments)
            agent_name = arguments_dict.get("agent_name")
            milestone = arguments_dict.get("milestone")
            agent_response_message_string, result_code = await self.callAgent(arguments_dict)
            # from agents.implementation_agent import ImplAgent
            # if self.name == ImplAgent.IMPL_AGENT_NAME:
            #     print("Within ")
            # if agent_name and milestone:
            #     print(f"Agent name: {agent_name}, milestone: {milestone}")

            #     await ImplAgent(client=self.client).execute_impl(milestone)

                            
            # Add a message to the message history. This should be a separate message.
            self._stream_message_llm(agent_response_message_string)

        else:
            print("No tool call")

        await response_message.update()



    async def callAgent(self, agent_args_dict):
        if "agent_name" not in agent_args_dict:
            print("callAgent() but no agent name ! ", agent_args_dict)
            return None, Agent.AGENT_ERRROR

        agent_name = agent_args_dict["agent_name"]
        if self.name == agent_name:
            print(f"Recursive call to self. Can't proceed. self = f{self.name}, agent_name = {agent_name}")
            return None, Agent.AGENT_ERROR
        from agents.implementation_agent import ImplAgent
        if agent_name == ImplAgent.IMPL_AGENT_STRING:
            if "milestone" not in agent_args_dict:
                print("callAgent('implementation') but no milestone ! ", agent_args_dict)
                return None, Agent.AGENT_ERROR
            milestone = agent_args_dict["milestone"]
            print(f"Agent name: {agent_name}, milestone: {milestone}")

            await ImplAgent(client=self.client).execute_impl(milestone)
            return None, Agent.AGENT_PROCESSED
        else:
            return None, Agent.AGENT_UNPROCESSED  # The child class might process it.

    async def execute(self, message_history):
        """
        Executes the agent's main functionality.

        Note: probably shouldn't couple this with chainlit, but this is just a prototype.
        """
        copied_message_history = message_history.copy()

        # Check if the first message is a system prompt
        if copied_message_history and copied_message_history[0]["role"] == "system":
            # Replace the system prompt with the agent's prompt
            copied_message_history[0] = {"role": "system", "content": self._build_system_prompt()}
        else:
            # Insert the agent's prompt at the beginning
            copied_message_history.insert(0, {"role": "system", "content": self._build_system_prompt()})

        response_message = cl.Message(content="")
        await response_message.send()

        stream = await self.client.chat.completions.create(messages=copied_message_history, stream=True, tools=self.tools, tool_choice="auto", **self.gen_kwargs)

        function_list = []
        function_name = ""
        arguments = ""
        async for part in stream:
            if part.choices[0].delta.tool_calls:
                tool_call = part.choices[0].delta.tool_calls[0]
                function_name_delta = tool_call.function.name or ""
                arguments_delta = tool_call.function.arguments or ""
                print(f"function_name_delta = {function_name_delta}")
                
                if function_name_delta and arguments:
                    print(f"Adding {function_name_delta} and {arguments} to the stack.")
                    function_list.append((function_name, arguments)) # prev function.
                    arguments = ""
                    function_name = ""
                function_name += function_name_delta
                arguments += arguments_delta
                print(f"arguments delta = {arguments_delta}")
        
            if token := part.choices[0].delta.content or "":
                await response_message.stream_token(token)        

        if function_name and arguments:
            function_list.append((function_name, arguments)) # prev function.
            
        for function_name, arguments in function_list:
            await self._execute_function(message_history, response_message, function_name, arguments)

        return response_message.content

    def _build_system_prompt(self):
        """
        Builds the system prompt including the agent's prompt and the contents of the artifacts folder.
        """
        artifacts_content = "<ARTIFACTS>\n"
        artifacts_dir = "artifacts"

        if os.path.exists(artifacts_dir) and os.path.isdir(artifacts_dir):
            for filename in os.listdir(artifacts_dir):
                file_path = os.path.join(artifacts_dir, filename)
                if os.path.isfile(file_path):
                    with open(file_path, "r") as file:
                        file_content = file.read()
                        artifacts_content += f"<FILE name='{filename}'>\n{file_content}\n</FILE>\n"
        
        artifacts_content += "</ARTIFACTS>"

        return f"{self.prompt}\n{artifacts_content}"


    async def _stream_message_llm(self, message_string):
        message_history = self.message_history
        message_history.append({
                "role": "system",
                "content": message_string
            })
        temp_response_message = cl.Message(content="")
        await temp_response_message.send()

        stream = await self.client.chat.completions.create(messages=message_history, stream=True, **self.gen_kwargs)
        async for part in stream:
            if token := part.choices[0].delta.content or "":
                await temp_response_message.stream_token(token)  
