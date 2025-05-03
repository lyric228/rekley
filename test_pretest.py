import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart

TOKEN = "7444719229:AAGMf4bIX9Vv4IALFbLMA0uYtJ-MCQL6A0M"
bot = Bot(token=TOKEN)
dp = Dispatcher() #ответчает за жизненный цикл бота

@dp.message(CommandStart()) #команда работает при команде start
async def start(message: Message):
    await message.answer(f"Привет, {message.chat.first_name}")

async def main():
    await dp.start_polling(bot)

# Запуск основного цикла событий
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO) #log будет отпарвлять сообщения о работе
    asyncio.run(main())