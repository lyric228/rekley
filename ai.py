from langchain_together import ChatTogether
from config import *
from db import *

messages: dict[str, list] = load_json("bot_memory.json")


class Ai:
    def __init__(self) -> None:
        self.ai = ChatTogether(
            name=AI_NAME,
            model=AI_MODEL,
            temperature=AI_TEMPERATURE,
            max_tokens=AI_MAX_TOKENS,
            api_key=TOGETHER_API_KEY,
        )
        self.system_prompt = BASE_SYSTEM_PROMPT
        
    def add_msg(self, id: int, role: str, msg: str):
        str_id = str(id)
        
        if not messages.get(str_id):
            messages[str_id] = []
            
        if len(messages[str_id]) == 0 and role != SYSTEM_ROLE:
            messages[str_id].append({
                "role": SYSTEM_ROLE, 
                "content": self.system_prompt
            })
            
        messages[str_id].append({"role": role, "content": msg})
        save_json(messages, "bot_memory.json")

    def ask(self, id: int, question: str) -> str:
        str_id = str(id)
        self.add_msg(id, USER_ROLE, question)

        fmt_messages = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in messages[str_id]]
        )
        response = self.ai.invoke(fmt_messages)

        self.add_msg(str_id, AI_ROLE, response.content)

        return response.content
