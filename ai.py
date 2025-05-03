from openai import AsyncClient
from warnings import warn
from config import *
from db import *


class Ai:
    def __init__(self) -> None:
        self.ai = AsyncClient(
            api_key=CHUTES_API_KEY,
            base_url=BASE_URL,
        )
        self.temperature: float = AI_TEMPERATURE
        self.memory_path: str = "memory.json"
        self.messages: dict[str, list] = load_json(self.memory_path)
        
    def add_msg(self, id: int | str, role: str, msg: str):
        if isinstance(id, int):
            id = str(id)
        
        if not self.messages.get(id):
            self.messages[id] = []
            
        if len(self.messages[id]) == 0 and role != SYSTEM_ROLE:
            self.messages[id].append({
                "role": SYSTEM_ROLE, 
                "content": SYSTEM_PROMPT
            })
            
        self.messages[id].append({"role": role, "content": msg})
        save_json(self.messages, self.memory_path)

    async def ask(self, id: int | str, question: str | None) -> str:
        if isinstance(id, int):
            id = str(id)

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
