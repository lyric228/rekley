from together import AsyncTogether
from warnings import warn
from config import *
from db import *


class Ai:
    def __init__(self) -> None:
        self.ai = AsyncTogether(
            api_key=AI_API_KEY,
        )
        self.temperature: float = AI_TEMPERATURE
        self.memory_path: str = "memory.json"
        self.messages: dict[str, list[dict[str, str]]] = load_json(self.memory_path)
    def add_msg(self, id: str, role: str, msg: str):

        if self.messages.get(id) is None:
            self.messages[id] = []
            
        if not len(self.messages[id]) > 1:
            self.messages[id] = [{
                "role": SYSTEM_ROLE, 
                "content": SYSTEM_PROMPT
            }]
            
        self.messages[id].append({"role": role, "content": msg})
        save_json(self.messages, self.memory_path)

    async def ask(self, id: str, question: str | None) -> str:
        if question is None:
            warn("question is None!")
            return ""

        self.add_msg(id, USER_ROLE, question)

        response = await self.ai.chat.completions.create(
            model=AI_MODEL,
            messages=self.messages[id],
            temperature=AI_TEMPERATURE,
            max_tokens=AI_MAX_TOKENS
        )
        answer = response.choices[0].message.content

        if answer is None:
            warn("answer is None!")
            return ""

        self.add_msg(id, AI_ROLE, answer)
        return answer
