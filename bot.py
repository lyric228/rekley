from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.exceptions import TelegramBadRequest
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
from ai import *


ai = Ai()
router = Router()
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💡 Идеи 💡"), KeyboardButton(text="🔧 Техники 🔧")],
        [KeyboardButton(text="📝 Задания 📝"), KeyboardButton(text="📚 Материалы 📚")],
        [KeyboardButton(text="✨ Вдохновение ✨")],
    ],
    resize_keyboard=True
)


@router.message(CommandStart())
async def handle_start(msg: Message):
    await msg.answer(f"Привет, {msg.chat.first_name}!\nЯ — Ре-Клей, ваш творческий проводник в мир коллажа. Я помогу вам совершить первые шаги в новом хобби или создать новые, уникальные работы, найти вдохновение.", reply_markup=main_keyboard)
    
@router.message(F.text == "💡 Идеи 💡")
async def handle_kb_idea(msg: Message):
    await bot.send_message(msg.chat.id, "Нужна помощь с темой для коллажа? Я готов подобрать то, что подходит тебе под настроение и уровень, только дай старт!")
    ai.add_msg(str(msg.chat.id), SYSTEM_ROLE, "Теперь пользователь выбрал тему 💡 Идеи 💡")
    
@router.message(F.text == "🔧 Техники 🔧")
async def handle_kb_techniques(msg: Message):
    await bot.send_message(msg.chat.id, "Изучение новых приёмов может сделать твой коллаж продуманнее. Что хочешь узнать сегодня?")
    ai.add_msg(str(msg.chat.id), SYSTEM_ROLE, "Теперь пользователь выбрал тему 🔧 Техники 🔧")
    
@router.message(F.text == "📝 Задания 📝")
async def handle_kb_tasks(msg: Message):
    await bot.send_message(msg.chat.id, "Практика, и ещё раз практика! Вот путь к успеху. Что хочешь попробовать сегодня?")
    ai.add_msg(str(msg.chat.id), SYSTEM_ROLE, "Теперь пользователь выбрал тему 📝 Задания 📝")
    
@router.message(F.text == "📚 Материалы 📚")
async def handle_kb_materials(msg: Message):
    await bot.send_message(msg.chat.id, "Материалы способны подарить нам вдохновение! Расскажи? с чем я могу помочь?")
    ai.add_msg(str(msg.chat.id), SYSTEM_ROLE, "Теперь пользователь выбрал тему 📚 Материалы 📚")
    
@router.message(F.text == "✨ Вдохновение ✨")
async def handle_kb_inspiration(msg: Message):
    await bot.send_message(msg.chat.id, "Идеи, подборки, мудборды - с этого стоит начать. Давай подберём что-то для тебя!")
    ai.add_msg(str(msg.chat.id), SYSTEM_ROLE, "Теперь пользователь выбрал тему ✨ Вдохновение ✨")

@router.message(F.text)
async def handle_msg(msg: Message):
    try:
        wait_msg = await msg.answer("Думаю...   (Ответ займет около минуты)")
        answer = ai.ask(msg.chat.id, msg.text)
        await wait_msg.edit_text(answer)
        
    except TelegramBadRequest as e:
        print(e)
