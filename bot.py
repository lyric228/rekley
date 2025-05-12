from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, FSInputFile, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.state import State, StatesGroup
from aiogram import Bot, Dispatcher, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from logging import warn, error, info
from os.path import join, exists
from ai import *
import asyncio


ai = Ai()
router = Router()
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💡 Идеи 💡"), KeyboardButton(text="🔧 Техники 🔧")],
        [KeyboardButton(text="📝 Задания 📝"), KeyboardButton(text="📚 Материалы 📚")],
        [KeyboardButton(text="🎭 Арт терапия 🎭"), KeyboardButton(text="✨ Вдохновение ✨")],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)

class TherapyStates(StatesGroup):
    WAITING_TIME = State()
    CONFIRM_TASK = State()
    IN_PROGRESS = State()
    GENERATING_TASK = State()

therapy_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="15 минут"), KeyboardButton(text="30 минут")],
        [KeyboardButton(text="60 минут"), KeyboardButton(text="Свободный режим")],
        [KeyboardButton(text="↩️ Назад в меню")],
    ],
    resize_keyboard=True,
)

reflection_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Да"),
            KeyboardButton(text="Нет"),
        ],
    ],
    resize_keyboard=True,
)

therapy_sessions = {}


def add_msg(id: str, role: str, msg: str):
    if id not in ai.messages:
        ai.messages[id] = [{"role": SYSTEM_ROLE, "content": SYSTEM_PROMPT}]
    ai.messages[id].append({"role": role, "content": msg})

async def send_collage_info(msg: Message) -> None:
    media_group = []
    folder_path = "files"
    all_files_found = True
    id = msg.chat.id

    for i in range(10):
        file_path = join(folder_path, f"{i}.jpg")

        if not exists(file_path):
            logging.error(f"Файл не найден: {file_path}. Отправка медиагруппы отменена.")
            all_files_found = False
            break

        photo_file = FSInputFile(file_path)

        if i == 0:
            media_group.append(InputMediaPhoto(media=photo_file, caption=START_TEXT_COLLAGE))
        else:
            media_group.append(InputMediaPhoto(media=photo_file))

    if all_files_found and media_group:
        try:
            await bot.send_media_group(chat_id=id, media=media_group)
            info(f"Медиагруппа с текстом успешно отправлена в чат {id}")
        except Exception as e:
            error(f"Не удалось отправить медиагруппу в чат {id}: {e}")
    elif not all_files_found:
        warn("Не все фото были найдены.")
    else:
        warn(f"Медиагруппа для чата {id} пуста, хотя ошибок поиска файлов не было.")

async def handle_menu_button(msg: Message, button_name: str, prompt: str) -> None:
    id = str(msg.chat.id)
    msgs = ai.messages.get(id, [])
    system_prompt_exists = msgs and msgs[0].get("role") == SYSTEM_ROLE and msgs[0].get("content") == SYSTEM_PROMPT
    new_msgs = [msgs[0]] if system_prompt_exists else [{"role": SYSTEM_ROLE, "content": SYSTEM_PROMPT}]

    await bot.send_message(id, prompt, reply_markup=main_keyboard)

    msgs_after_send = ai.messages.get(id, [])
    new_msgs_filtered = [{"role": SYSTEM_ROLE, "content": SYSTEM_PROMPT}]
    skip_next_ai = False

    for m in msgs_after_send[1:]:
        if m.get("role") == SYSTEM_ROLE and m.get("content", "").startswith("Теперь пользователь выбрал тему"):
            skip_next_ai = True
            continue
        if skip_next_ai and m.get("role") == AI_ROLE:
            skip_next_ai = False
            continue
        new_msgs_filtered.append(m)
    
    ai.messages[id] = new_msgs_filtered
    add_msg(id, SYSTEM_ROLE, f"Теперь пользователь выбрал тему {button_name}")
    add_msg(id, AI_ROLE, prompt)
    ai.save_messages()

@router.message(CommandStart())
async def handle_start(msg: Message, state: FSMContext) -> None:
    if await state.get_state() == TherapyStates.GENERATING_TASK:
        return

    welcome_text = (
        f"Привет, {msg.chat.first_name}!\n"
        "Я — Ре-Клей, ваш творческий проводник в мир коллажа. "
        "Я помогу вам совершить первые шаги в новом хобби или "
        "создать новые, уникальные работы, найти вдохновение."
    )

    await msg.answer(welcome_text, reply_markup=main_keyboard)
    await send_collage_info(msg)

@router.message(F.text == "💡 Идеи 💡")
async def handle_kb_idea(msg: Message, state: FSMContext) -> None:
    if await state.get_state() == TherapyStates.GENERATING_TASK:
        return

    await handle_menu_button(
        msg,
        "💡 Идеи 💡",
        "Нужна помощь с темой для коллажа? Я готов подобрать то, "
        "что подходит тебе под настроение и уровень, только дай старт!"
    )

@router.message(F.text == "🔧 Техники 🔧")
async def handle_kb_techniques(msg: Message, state: FSMContext) -> None:
    if await state.get_state() == TherapyStates.GENERATING_TASK:
        return

    await handle_menu_button(
        msg,
        "🔧 Техники 🔧",
        "Изучение новых приёмов может сделать твой коллаж продуманнее. "
        "Что хочешь узнать сегодня?"
    )

@router.message(F.text == "📝 Задания 📝")
async def handle_kb_tasks(msg: Message, state: FSMContext) -> None:
    if await state.get_state() == TherapyStates.GENERATING_TASK:
        return

    await handle_menu_button(
        msg,
        "📝 Задания 📝",
        "Практика, и ещё раз практика! Вот путь к успеху. "
        "Что хочешь попробовать сегодня?"
    )

@router.message(F.text == "📚 Материалы 📚")
async def handle_kb_materials(msg: Message, state: FSMContext) -> None:
    if await state.get_state() == TherapyStates.GENERATING_TASK:
        return

    await handle_menu_button(
        msg,
        "📚 Материалы 📚",
        "Материалы способны подарить нам вдохновение! "
        "Расскажи, с чем я могу помочь?"
    )

@router.message(F.text == "✨ Вдохновение ✨")
async def handle_kb_inspiration(msg: Message, state: FSMContext) -> None:
    if await state.get_state() == TherapyStates.GENERATING_TASK:
        return

    await handle_menu_button(
        msg,
        "✨ Вдохновение ✨",
        "Идеи, подборки, мудборды - с этого стоит начать. "
        "Давай подберём что-то для тебя!"
    )

@router.message(F.text == "🎭 Арт терапия 🎭")
async def handle_kb_art_therapy(msg: Message, state: FSMContext):
    current_fsm_state = await state.get_state()
    if current_fsm_state == TherapyStates.GENERATING_TASK:
        return
    if current_fsm_state is None or current_fsm_state not in [TherapyStates.WAITING_TIME, TherapyStates.CONFIRM_TASK, TherapyStates.IN_PROGRESS]:
        await state.set_state(TherapyStates.WAITING_TIME)

    await msg.answer(
        "Выбери продолжительность сессии:",
        reply_markup=therapy_keyboard
    )

@router.message(TherapyStates.WAITING_TIME, F.text == "↩️ Назад в меню")
async def handle_therapy_back_to_menu(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Выбор отменён. Возвращаюсь в главное меню.", reply_markup=main_keyboard)

@router.message(TherapyStates.WAITING_TIME, F.text.in_(["15 минут", "30 минут", "60 минут", "Свободный режим"]))
async def handle_therapy_time(msg: Message, state: FSMContext):
    duration_text = msg.text

    await msg.answer("Генерирую задание...", reply_markup=ReplyKeyboardRemove())
    await state.set_state(TherapyStates.GENERATING_TASK)

    try:
        duration = 0
        if "15 минут" == duration_text:
            duration = 15
        elif "30 минут" == duration_text:
            duration = 30
        elif "60 минут" == duration_text:
            duration = 60

        await state.update_data(duration=duration, duration_text=duration_text)

        id = str(msg.chat.id)
        prompt_for_task = f"Сгенерируй арт-терапевтическое задание для коллажа. Пользователь выбрал продолжительность сессии: {duration_text}. Задание должно быть направлено на расслабление и самопознание. Предложи конкретную тему или идею для коллажа, которую можно выполнить за указанное время."
        if duration_text == "Свободный режим":
            prompt_for_task = "Сгенерируй арт-терапевтическое задание для коллажа в свободном режиме. Задание должно быть направлено на глубокое самопознание и творческое самовыражение без ограничений по времени. Предложи вдохновляющую тему или концепцию."
        
        task = await ai.ask(id, prompt_for_task)
        await state.update_data(current_task=task)

        await state.set_state(TherapyStates.CONFIRM_TASK)
        await msg.answer(
            f"🎨 Ваше задание:\n\n{task}\n\n"
            "Выбери действие:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="✅ Начать задание")],
                    [KeyboardButton(text="🔄 Изменить задание"), KeyboardButton(text="❌ Отменить")],
                ],
                resize_keyboard=True
            )
        )
    except Exception as e:
        warn(f"Error during therapy task generation for chat {msg.chat.id}: {e}")
        await msg.answer("Произошла ошибка при генерации задания. Пожалуйста, попробуйте выбрать время еще раз.", reply_markup=therapy_keyboard)
        await state.set_state(TherapyStates.WAITING_TIME)


@router.message(TherapyStates.CONFIRM_TASK, F.text == "🔄 Изменить задание")
async def handle_change_task(msg: Message, state: FSMContext):
    data = await state.get_data()
    duration_text = data.get("duration_text", "Свободный режим")

    await msg.answer("Генерирую новое задание...", reply_markup=ReplyKeyboardRemove())
    await state.set_state(TherapyStates.GENERATING_TASK)

    try:
        new_task = await ai.generate_therapy_task(str(msg.chat.id), duration_text)
        await state.update_data(current_task=new_task)

        await state.set_state(TherapyStates.CONFIRM_TASK)
        await msg.answer(
            f"🔄 Новое задание:\n\n{new_task}\n\n"
            "Выбери действие:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="✅ Начать задание")],
                    [KeyboardButton(text="🔄 Изменить задание"), KeyboardButton(text="❌ Отменить")],
                ],
                resize_keyboard=True
            )
        )

    except Exception as e:
        warn(f"Error during therapy task generation for chat {msg.chat.id}: {e}")
        await msg.answer("Произошла ошибка при генерации нового задания. Пожалуйста, попробуйте еще раз.", reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="✅ Начать задание")],
                    [KeyboardButton(text="🔄 Изменить задание"), KeyboardButton(text="❌ Отменить")],
                ],
                resize_keyboard=True
            ))
        await state.set_state(TherapyStates.CONFIRM_TASK)


@router.message(TherapyStates.CONFIRM_TASK, F.text == "✅ Начать задание")
async def handle_start_task(msg: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(TherapyStates.IN_PROGRESS)

    duration = data.get("duration", 0)
    id = msg.chat.id

    if duration > 0:
        await msg.answer(
            f"⏳ Таймер запущен на {duration} минут!",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🏁 Завершить задание досрочно")]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )

        therapy_sessions[str(id)] = asyncio.create_task(
            finish_therapy_session(id, duration, state)
        )
    else:
        await msg.answer(
            "🕊️ Свободный режим активирован! Твори сколько хочешь!",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🏁 Завершить сессию")]],
                resize_keyboard=True
            )
        )

@router.message(TherapyStates.IN_PROGRESS, F.text == "🏁 Завершить сессию")
async def handle_finish_free_mode_session(msg: Message, state: FSMContext):
    await finish_session(str(msg.chat.id), state)

@router.message(TherapyStates.IN_PROGRESS, F.text == "🏁 Завершить задание досрочно")
async def handle_early_timer_finish(msg: Message, state: FSMContext):
    await finish_session(str(msg.chat.id), state)


@router.message(TherapyStates.CONFIRM_TASK, F.text == "❌ Отменить")
async def handle_cancel_task(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "Сессия отменена",
        reply_markup=main_keyboard
    )

async def finish_therapy_session(chat_id: int, duration: int, state: FSMContext):
    await asyncio.sleep(duration * 60)
    current_state = await state.get_state()

    if current_state == TherapyStates.IN_PROGRESS:
        await finish_session(str(chat_id), state)

async def finish_session(chat_id_str: str, state: FSMContext):
    chat_id = int(chat_id_str)
    if chat_id_str in therapy_sessions:
        therapy_sessions[chat_id_str].cancel()
        del therapy_sessions[chat_id_str]

    await state.set_state(None)
    try:
        await bot.send_message(
            chat_id,
            "Ух, ты! Как быстро пролетело время. Хочешь поразмышлять над тем, что у тебя получилось?",
            reply_markup=reflection_keyboard
        )
    except TelegramBadRequest as e:
        warn(f"Error sending message in finish_session to {chat_id}: {e}")
        try:
            await bot.send_message(chat_id, "Сессия завершена.", reply_markup=main_keyboard)
        except Exception as final_e:
            warn(f"Error sending final message to {chat_id}: {final_e}")


@router.message(F.text.in_(["Да", "Нет"]))
async def handle_reflection(msg: Message, state: FSMContext):
    if await state.get_state() == TherapyStates.GENERATING_TASK:
        return

    if msg.text == "Да":
        id = str(msg.chat.id)
        await msg.answer("Генерирую вопросы...")
        reflection_prompt = "Сформулируй вопрос для рефлексии по выполненному арт-терапевтическому заданию"
        reflection_question = await ai.ask(id, reflection_prompt)
        await msg.answer(f"Отлично! {reflection_question}", reply_markup=main_keyboard)
    else:
        await msg.answer("Спасибо, что сделал задание со мной! Надеюсь, тебе было интересно)", reply_markup=main_keyboard)

    await state.clear()
@router.message(F.text)
async def handle_msg(msg: Message, state: FSMContext) -> None:
    if await state.get_state() == TherapyStates.GENERATING_TASK:
        return

    current_fsm_state = await state.get_state()

    id = str(msg.chat.id)

    try:
        wait_msg = await msg.answer("⌛ Обрабатываю запрос...", reply_markup=main_keyboard)
        answer = await ai.ask(id, msg.text)

        await wait_msg.delete()
        await msg.answer(answer, reply_markup=main_keyboard)

    except Exception as e:
        warn(f"Error in chat {id}: {e}")
        await msg.answer("⚠ Произошла ошибка, попробуйте позже", reply_markup=main_keyboard)