import json
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
        self.messages: dict[str, list[dict[str, any]]] = {}
        self.load_messages()

    def load_messages(self):
        self.messages = load_json(self.memory_path) or {}

    def add_msg(self, id: str, role: str, message: str):
        if id not in self.messages:
            self.messages[id] = [{"role": SYSTEM_ROLE, "content": SYSTEM_PROMPT}]
        self.messages[id].append({"role": role, "content": message})
        self.save_messages()

    def save_messages(self):
        save_json(self.messages, self.memory_path)

    def add_dict_msg(self, id: str, message: dict):
        if id not in self.messages:
            self.messages[id] = [{"role": SYSTEM_ROLE, "content": SYSTEM_PROMPT}]
        self.messages[id].append(message)
        self.save_messages()

    def get_or_init_messages(self, id: str) -> list[dict[str, any]]:
        if id not in self.messages:
            self.messages[id] = [{"role": SYSTEM_ROLE, "content": SYSTEM_PROMPT}]
        return self.messages.get(id, []).copy()

    async def ask(self, id: str, question: str | None) -> str:
        if not question or not question.strip():
            return "Пожалуйста, введите осмысленный запрос."

        _ = self.get_or_init_messages(id) 
        
        user_message = {"role": USER_ROLE, "content": question}
        self.add_dict_msg(id, user_message)

        try:
            current_chat_history = list(self.messages.get(id, []))

            response = await self.ai.chat.completions.create(
                model=AI_MODEL,
                messages=current_chat_history,
                temperature=self.temperature,
                tools=[PINTEREST_TOOL_SCHEMA]
            )

            assistant_first_response_message = response.choices[0].message
            assistant_first_response_dict = assistant_first_response_message.model_dump(exclude_unset=True)
            self.add_dict_msg(id, assistant_first_response_dict)

            if assistant_first_response_message.tool_calls:
                return await self._handle_tool_calls(id, assistant_first_response_message.tool_calls)
            
            return assistant_first_response_message.content or "Не получилось сформировать ответ."

        except Exception as e:
            print(f"AI processing error in ask for chat {id}: {e}")
            if self.messages.get(id) and self.messages[id][-1]["role"] == USER_ROLE:
                self.messages[id].pop()
                self.save_messages()
            return "Извините, произошла ошибка при обработке вашего запроса."

    async def _handle_tool_calls(self, id: str, tool_calls_list: list) -> str:
        for tool_call in tool_calls_list:
            tool_result_message_dict = {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_call.function.name,
                "content": f"Ошибка: не удалось выполнить инструмент {tool_call.function.name}",
            }
            if tool_call.function.name == "search_pinterest":
                tool_result_message_dict = await self._execute_pinterest_search(tool_call)
            
            self.add_dict_msg(id, tool_result_message_dict)

        current_chat_history_with_tool_results = list(self.messages.get(id, []))
        
        try:
            final_response = await self.ai.chat.completions.create(
                model=AI_MODEL,
                messages=current_chat_history_with_tool_results,
                temperature=self.temperature
            )
            
            final_assistant_answer_message = final_response.choices[0].message
            self.add_dict_msg(id, final_assistant_answer_message.model_dump(exclude_unset=True))

            return final_assistant_answer_message.content or "Не получилось сформировать ответ после использования инструмента."
        except Exception as e:
            print(f"AI processing error in _handle_tool_calls for chat {id}: {e}")
            return "Извините, произошла ошибка при обработке результатов инструмента."


    async def _execute_pinterest_search(self, tool_call) -> dict:
        function_args = {}
        try:
            function_args = json.loads(tool_call.function.arguments)
            if "query" not in function_args:
                raise ValueError("Missing 'query' argument for search_pinterest")

            pinterest_results = await search_pinterest(query=function_args["query"])
            content = str(pinterest_results) if pinterest_results else "Поиск по Pinterest не дал результатов."
            
            return {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_call.function.name,
                "content": content,
            }
        except json.JSONDecodeError:
            warn(f"Error decoding JSON arguments for search_pinterest: {tool_call.function.arguments}")
            content = "Ошибка: неверный формат аргументов для search_pinterest."
        except ValueError as ve:
            warn(f"ValueError in search_pinterest arguments: {ve}")
            content = f"Ошибка в аргументах для search_pinterest: {ve}"
        except Exception as e:
            warn(f"Error executing Pinterest search with args {function_args}: {e}")
            content = f"Ошибка при выполнении поиска в Pinterest: {e}"
        
        return {
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": tool_call.function.name,
            "content": content,
        }
