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
        [KeyboardButton(text="🎨 Референсы 🎨"), KeyboardButton(text="✨ Вдохновение ✨")],
        [KeyboardButton(text="🎭 Арт терапия 🎭")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

def add_msg(id: str, role: str, msg: str):
    if id not in ai.messages:
        ai.messages[id] = [{"role": SYSTEM_ROLE, "content": SYSTEM_PROMPT}]
    ai.messages[id].append({"role": role, "content": msg})

async def handle_menu_button(msg: Message, button_name: str, prompt: str) -> None:
    id = str(msg.chat.id)
    await bot.send_message(id, prompt, reply_markup=main_keyboard)
    
    msgs = ai.messages.get(id, [])
    # Добавляем проверку на пустую историю
    new_msgs = [msgs[0]] if msgs and len(msgs) > 0 else [{"role": SYSTEM_ROLE, "content": SYSTEM_PROMPT}]
    to_remove = False
    
    for m in msgs[1:]:
        if m.get("role") == SYSTEM_ROLE and m.get("content", "").startswith("Теперь пользователь выбрал тему"):
            to_remove = True
            continue
        if to_remove and m.get("role") == AI_ROLE:
            to_remove = False
            continue
        new_msgs.append(m)
    
    ai.messages[id] = new_msgs
    ai.add_msg(id, SYSTEM_ROLE, f"Теперь пользователь выбрал тему {button_name}")
    ai.add_msg(id, AI_ROLE, prompt)
    ai.save_messages()

@router.message(CommandStart())
async def handle_start(msg: Message) -> None:
    welcome_text = (
        f"Привет, {msg.chat.first_name}!\n"
        "Я — Ре-Клей, ваш творческий проводник в мир коллажа. "
        "Я помогу вам совершить первые шаги в новом хобби или "
        "создать новые, уникальные работы, найти вдохновение."
    )
    await msg.answer(welcome_text, reply_markup=main_keyboard)

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

@router.message(F.text == "🎭 Арт терапия 🎭")
async def handle_kb_art_therapy(msg: Message) -> None:
    await handle_menu_button(
        msg,
        "🎭 Арт терапия 🎭",
        "Коллаж - прекрасный способ самопознания. Давай создадим работу, "
        "которая поможет тебе выразить свои эмоции и чувства через искусство. "
        "Сколько времени у тебя есть на задание?"
    )

@router.message(F.text)
async def handle_msg(msg: Message) -> None:
    id = str(msg.chat.id)

    try:
        wait_msg = await msg.answer("⌛ Обрабатываю запрос...", reply_markup=main_keyboard)
        answer = await ai.ask(id, msg.text)

        await wait_msg.delete()
        await msg.answer(answer, reply_markup=main_keyboard)

    except Exception as e:
        print(f"Error in chat {id}: {e}")
        await msg.answer("⚠ Произошла ошибка, попробуйте позже", reply_markup=main_keyboard)
