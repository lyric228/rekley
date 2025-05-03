from openai import AsyncClient
from config import *
from db import *

messages: dict[str, list] = load_json("bot_memory.json")

class Ai:
    def __init__(self):
        self.ai = AsyncClient(
            api_key=CHUTES_API_KEY,
            base_url=BASE_URL,
        )
        
    def add_msg(self, id: int | str, role: str, msg: str):
        if isinstance(id, int):
            id = str(id)
        
        if not messages.get(id):
            messages[id] = []
            
        if len(messages[id]) == 0 and role != SYSTEM_ROLE:
            messages[id].append({
                "role": SYSTEM_ROLE, 
                "content": SYSTEM_PROMPT
            })
            
        messages[id].append({"role": role, "content": msg})
        save_json(messages, "memory.json")

    async def ask(self, id: int | str, question: str) -> str:
        if isinstance(id, int):
            id = str(id)

        self.add_msg(id, USER_ROLE, question)

        response = await self.ai.chat.completions.create(
            model=AI_MODEL,
            messages=messages[id],
            temperature=AI_TEMPERATURE,
            max_tokens=AI_MAX_TOKENS
        )

        answer = response.choices[0].message.content
        if answer is None:
            print("WARNING: answer is None!")
            answer = ""
        self.add_msg(id, AI_ROLE, answer)

        return answer
