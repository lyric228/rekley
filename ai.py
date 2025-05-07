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
            self.save_messages()
        return self.messages.get(id, []).copy()

    async def ask(self, id: str, question: str | None) -> str:
        if not question or not question.strip():
            return "Пожалуйста, введите осмысленный запрос."
        current_messages = self.get_or_init_messages(id)
        user_message = {"role": USER_ROLE, "content": question}
        try:
            response = await self.ai.chat.completions.create(
                model=AI_MODEL,
                messages=[*current_messages, user_message],
                temperature=self.temperature,
                tools=[PINTEREST_TOOL_SCHEMA]
            )

            if response.choices[0].message.tool_calls:
                return await self._handle_tool_calls(id, current_messages, response)

            return response.choices[0].message.content or "Не получилось сформировать ответ."
        except Exception as e:
            print(f"AI processing error: {e}")
            return "Извините, произошла ошибка при обработке запроса."

    async def _handle_tool_calls(self, id: str, messages: list, response) -> str:
        tool_messages = []

        for tool_call in response.choices[0].message.tool_calls:
            if tool_call.function.name == "search_pinterest":
                result = await self._execute_pinterest_search(tool_call)
                tool_messages.append(result)

        self.messages[id].extend(tool_messages)
        self.save_messages()

        final_response = await self.ai.chat.completions.create(
            model=AI_MODEL,
            messages=[*messages, *tool_messages],
            temperature=self.temperature
        )
        return final_response.choices[0].message.content

    async def _execute_pinterest_search(self, tool_call):
        function_args = json.loads(tool_call.function.arguments)
        if "query" not in function_args:
            raise ValueError("Missing 'query' argument for search_pinterest")

        try:
            result = await search_pinterest(**function_args)
            return {
                "role": "tool",
                "name": "search_pinterest",
                "content": str(result),
                "tool_call_id": tool_call.id
            }
        except Exception as e:
            warn(f"Error executing Pinterest search: {e}")
            return {
                "role": "tool",
                "name": "search_pinterest",
                "content": f"Ошибка при выполнении поиска в Pinterest: {e}",
                "tool_call_id": tool_call.id
            }
