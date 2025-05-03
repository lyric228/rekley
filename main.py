# Установить все нужные пакеты:
# pip install -r requirements.txt

from bot import *
import logging
import asyncio


async def main() -> None:
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
