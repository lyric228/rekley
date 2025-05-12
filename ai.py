from openai import AsyncClient
from logging import warn
from config import *
from db import *
import re


class Ai:
    def __init__(self) -> None:
        self.ai = AsyncClient(
            api_key=AI_API_KEY,
            base_url=AI_BASE_URL,
        )

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

        self.get_or_init_messages(id)
        user_message = {"role": USER_ROLE, "content": question}
        self.add_dict_msg(id, user_message)

        try:
            current_chat_history = list(self.messages.get(id, []))
            response = await self.ai.chat.completions.create(
                model=AI_MODEL,
                messages=current_chat_history,
                temperature=self.temperature,
            )

            assistant_response_message = response.choices[0].message
            assistant_response_dict = assistant_response_message.model_dump(exclude_unset=True)
            self.add_dict_msg(id, assistant_response_dict)
            result = re.sub(r"<think>.*?</think>\n?", "", assistant_response_message.content, flags=re.DOTALL)
            max_len = AI_MAX_ANSWER_LEN

            if len(result) > max_len:
                result = text[:max_len]

            return result

        except Exception as e:
            warn(f"AI processing error in ask for chat {id}: {e}")
            if self.messages.get(id) and self.messages[id][-1]["role"] == USER_ROLE:
                 last_msg = self.messages[id][-1]
                 if last_msg.get("content") == question and last_msg.get("role") == USER_ROLE:
                     self.messages[id].pop()
                     self.save_messages()
            return "Извините, произошла ошибка при обработке вашего запроса."
