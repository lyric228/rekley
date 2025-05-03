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


def check_old(id: str) -> None:
    messages = ai.messages.get(id, [])
    if len(messages) > 1 and messages[-1]["role"] == SYSTEM_ROLE:
        messages.pop()


main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💡 Идеи 💡"), KeyboardButton(text="🔧 Техники 🔧")],
        [KeyboardButton(text="📝 Задания 📝"), KeyboardButton(text="📚 Материалы 📚")],
        [KeyboardButton(text="🎨 Референсы 🎨"), KeyboardButton(text="✨ Вдохновение ✨")],
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)


async def handle_menu_button(msg: Message, button_name: str, prompt: str) -> None:
    chat_id = str(msg.chat.id)
    check_old(chat_id)
    await bot.send_message(chat_id, prompt)
    ai.add_msg(chat_id, SYSTEM_ROLE, f"Теперь пользователь выбрал тему {button_name}")


@router.message(CommandStart())
async def handle_start(msg: Message) -> None:
    welcome_text = (
        f"Привет, {msg.chat.first_name}!\n"
        "Я — Ре-Клей, ваш творческий проводник в мир коллажа. "
        "Я помогу вам совершить первые шаги в новом хобби или "
        "создать новые, уникальные работы, найти вдохновение."
    )
    await msg.answer(welcome_text, reply_markup=main_keyboard)


# Menu button handlers
@router.message(F.text == "💡 Идеи 💡")
async def handle_kb_idea(msg: Message) -> None:
    await handle_menu_button(
        msg,
        "💡 Идеи 💡",
        "Нужна помощь с темой для коллажа? Я готов подобрать то, "
        "что подходит тебе под настроение и уровень, только дай старт!"
    )

@router.message(F.text == "🔧 Техники 🔧")
async def handle_kb_techniques(msg: Message) -> None:
    await handle_menu_button(
        msg,
        "🔧 Техники 🔧",
        "Изучение новых приёмов может сделать твой коллаж продуманнее. "
        "Что хочешь узнать сегодня?"
    )

@router.message(F.text == "📝 Задания 📝")
async def handle_kb_tasks(msg: Message) -> None:
    await handle_menu_button(
        msg,
        "📝 Задания 📝",
        "Практика, и ещё раз практика! Вот путь к успеху. "
        "Что хочешь попробовать сегодня?"
    )

@router.message(F.text == "📚 Материалы 📚")
async def handle_kb_materials(msg: Message) -> None:
    await handle_menu_button(
        msg,
        "📚 Материалы 📚",
        "Материалы способны подарить нам вдохновение! "
        "Расскажи, с чем я могу помочь?"
    )

@router.message(F.text == "🎨 Референсы 🎨")
async def handle_kb_references(msg: Message) -> None:
    await handle_menu_button(
        msg,
        "🎨 Референсы 🎨",
        "Давай подберём интересные работы для вдохновения! "
        "Какой стиль тебя интересует?"
    )

@router.message(F.text == "✨ Вдохновение ✨")
async def handle_kb_inspiration(msg: Message) -> None:
    await handle_menu_button(
        msg,
        "✨ Вдохновение ✨",
        "Идеи, подборки, мудборды - с этого стоит начать. "
        "Давай подберём что-то для тебя!"
    )


@router.message(F.text)
async def handle_msg(msg: Message) -> None:
    """Handle all text messages not caught by other handlers."""
    try:
        wait_msg = await msg.answer("Думаю...   (Ответ займет около минуты)")
        answer = await ai.ask(msg.chat.id, msg.text)
        await wait_msg.edit_text(answer)
        
    except TelegramBadRequest as e:
        print(f"Telegram API error: {e}")