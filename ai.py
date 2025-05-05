import json
import asyncio
from together import AsyncTogether
from warnings import warn
from config import *
from db import *
from tools import search_pinterest, PINTEREST_TOOL_SCHEMA


class Ai:
    def __init__(self) -> None:
        self.ai = AsyncTogether(api_key=AI_API_KEY)
        self.temperature: float = AI_TEMPERATURE
        self.memory_path: str = "memory.json"
        self.messages: dict[str, list[dict[str, any]]] = load_json(self.memory_path) or {}

    def _add_msg(self, id: str, message: dict):
        if id not in self.messages:
             self.messages[id] = [{"role": SYSTEM_ROLE, "content": SYSTEM_PROMPT}]
        self.messages[id].append(message)
        save_json(self.messages, self.memory_path)

    def _get_or_init_messages(self, id: str) -> list[dict[str, any]]:
        if id not in self.messages or not self.messages[id]:
            self.messages[id] = [{"role": SYSTEM_ROLE, "content": SYSTEM_PROMPT}]
        return list(self.messages[id])

    async def ask(self, id: str, question: str | None) -> str:
        if question is None:
            warn("question is None!")
            return ""

        current_messages = self._get_or_init_messages(id)

        user_message = {"role": USER_ROLE, "content": question}
        current_messages.append(user_message)
        self._add_msg(id, user_message)

        final_answer: str | None = None

        try:
            response = await self.ai.chat.completions.create(
                model=AI_MODEL,
                messages=current_messages,
                temperature=AI_TEMPERATURE,
                max_tokens=AI_MAX_TOKENS,
                tools=[PINTEREST_TOOL_SCHEMA]
            )
            response_message = response.choices[0].message
            response_message_dict = response_message.model_dump(exclude_unset=True)

            self._add_msg(id, response_message_dict)
            current_messages.append(response_message_dict)

            tool_calls = response_message.tool_calls
            if tool_calls:
                available_tools = {"search_pinterest": search_pinterest}
                tool_results_messages = []

                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_to_call = available_tools.get(function_name)
                    tool_message_content = f"Error: Unknown tool '{function_name}'"

                    if function_to_call:
                        try:
                            function_args = json.loads(tool_call.function.arguments)
                            if function_name == "search_pinterest" and "query" not in function_args:
                                raise ValueError("Missing 'query' argument for search_pinterest")

                            if asyncio.iscoroutinefunction(function_to_call):
                                function_response = await function_to_call(**function_args)
                            else:
                                function_response = function_to_call(**function_args)
                            tool_message_content = str(function_response)

                        except (json.JSONDecodeError, ValueError, TypeError) as e:
                            warn(f"Error processing tool {function_name}: {e}")
                            tool_message_content = f"Error processing tool call: {e}"
                        except Exception as e:
                            warn(f"Unexpected error executing tool {function_name}: {e}")
                            tool_message_content = f"Error: Failed to execute tool - {e}"

                    tool_message = {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": tool_message_content,
                    }
                    tool_results_messages.append(tool_message)

                for msg in tool_results_messages:
                    self._add_msg(id, msg)
                    current_messages.append(msg)

                final_response = await self.ai.chat.completions.create(
                    model=AI_MODEL,
                    messages=current_messages,
                    temperature=AI_TEMPERATURE,
                    max_tokens=AI_MAX_TOKENS
                )
                final_answer = final_response.choices[0].message.content
                final_answer_message = final_response.choices[0].message.model_dump(exclude_unset=True)
                self._add_msg(id, final_answer_message)

            else:
                final_answer = response_message.content

        except Exception as e:
            warn(f"Error during API call or processing: {e}")
            return "Sorry, I encountered an error trying to process your request."

        if final_answer is None:
            warn("Final answer is None after processing!")
            return "Sorry, I couldn't generate a proper response."

        return final_answer
    