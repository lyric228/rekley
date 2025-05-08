from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
from ai import * # Assuming this imports Ai, SYSTEM_ROLE, SYSTEM_PROMPT, TELEGRAM_BOT_TOKEN, AI_ROLE
import asyncio


ai = Ai()
router = Router()
# Assuming TELEGRAM_BOT_TOKEN is defined in ai.py or elsewhere accessible
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

# Добавляем состояния FSM
class TherapyStates(StatesGroup):
    WAITING_TIME = State()
    CONFIRM_TASK = State()
    IN_PROGRESS = State()
    GENERATING_TASK = State() # Добавляем новое состояние

# Добавляем клавиатуры
therapy_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="15 минут"), KeyboardButton(text="30 минут")],
        [KeyboardButton(text="60 минут"), KeyboardButton(text="Свободный режим")],
        [KeyboardButton(text="↩️ Назад в меню")]
    ],
    resize_keyboard=True
)

reflection_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Да"), KeyboardButton(text="Нет")],
    ],
    resize_keyboard=True
)

# Глобальный словарь для отслеживания таймеров
therapy_sessions = {}


# Corrected add_msg function based on the original code's intent
def add_msg(id: str, role: str, msg: str):
    if id not in ai.messages:
        # Ensure the first message is the system prompt
        ai.messages[id] = [{"role": SYSTEM_ROLE, "content": SYSTEM_PROMPT}]
    # Append the new message. Use extend or direct append if messages is a list.
    # Assuming ai.messages[id] is a list based on the for loop below.
    ai.messages[id].append({"role": role, "content": msg})


async def handle_menu_button(msg: Message, button_name: str, prompt: str) -> None:
    id = str(msg.chat.id)
    # The original code sent the prompt first, then potentially removed messages
    # and added system messages. This might be inconsistent.
    # Let's stick to the order the diff suggests adding messages:
    # 1. Get current messages
    # 2. Filter/Recreate messages (keeping initial system prompt)
    # 3. Add new system message about menu choice
    # 4. Add AI response
    # 5. Send AI response message
    # 6. Save messages
    msgs = ai.messages.get(id, [])
    # Start new_msgs with the system prompt if it exists, or add it if not
    system_prompt_exists = msgs and msgs[0].get("role") == SYSTEM_ROLE and msgs[0].get("content") == SYSTEM_PROMPT
    new_msgs = [msgs[0]] if system_prompt_exists else [{"role": SYSTEM_ROLE, "content": SYSTEM_PROMPT}]

    # Logic to remove previous "user chose topic" and AI response.
    # This logic seems complex and potentially buggy if history format changes.
    # A simpler approach might be to just append the new system message
    # and AI response, but the original code attempts this removal.
    # Let's replicate the diff's *implied* message structure update,
    # assuming the goal is to replace the previous menu choice context.
    # The diff's `handle_menu_button` logic wasn't shown, but the message
    # handling logic suggests it modifies the message history.
    # The diff's modification happens *after* sending the message, which is unusual.
    # Let's assume the intent is to update the history *before* the next turn.
    # Keeping the structure from the original code provided, which is also unusual (modifying history after sending).

    await bot.send_message(id, prompt, reply_markup=main_keyboard)

    # Replicate the original code's history modification logic after sending
    msgs_after_send = ai.messages.get(id, []) # Get current messages *after* the ask or initial state
    # Re-evaluate the base: Always start with the system prompt.
    new_msgs_filtered = [{"role": SYSTEM_ROLE, "content": SYSTEM_PROMPT}]

    # Append messages from the history, skipping the previous menu context injection
    skip_next_ai = False
    for m in msgs_after_send[1:]: # Start from the second message
        if m.get("role") == SYSTEM_ROLE and m.get("content", "").startswith("Теперь пользователь выбрал тему"):
            skip_next_ai = True # The next AI message is the response to the old menu choice
            continue
        if skip_next_ai and m.get("role") == AI_ROLE:
            skip_next_ai = False
            continue
        new_msgs_filtered.append(m)
    
    ai.messages[id] = new_msgs_filtered

    # Now add the context for the *current* menu choice and the bot's response
    # Using the corrected add_msg logic
    add_msg(id, SYSTEM_ROLE, f"Теперь пользователь выбрал тему {button_name}")
    add_msg(id, AI_ROLE, prompt) # The prompt sent to the user is the AI's "response" to the menu click
    ai.save_messages() # Assuming ai class has save_messages
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

@router.message(F.text == "🎨 Референсы 🎨")
async def handle_kb_references(msg: Message, state: FSMContext) -> None:
    if await state.get_state() == TherapyStates.GENERATING_TASK:
        return
    await handle_menu_button(
        msg,
        "🎨 Референсы 🎨",
        "Давай подберём интересные работы для вдохновения! "
        "Какой стиль тебя интересует?"
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
    if current_fsm_state == TherapyStates.GENERATING_TASK: # Проверяем, не генерируем ли уже
        return
    # Если мы уже в каком-то другом состоянии арт-терапии, не нужно сбрасывать его просто так
    # Но если это первый вход или мы не в состоянии генерации, то устанавливаем WAITING_TIME
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
    await state.set_state(TherapyStates.GENERATING_TASK) # Устанавливаем состояние генерации

    try:
        duration = 0
        if "15 минут" == duration_text:
            duration = 15
        elif "30 минут" == duration_text:
            duration = 30
        elif "60 минут" == duration_text:
            duration = 60

        await state.update_data(duration=duration, duration_text=duration_text)

        # Assuming ai.generate_therapy_task exists and works
        task = await ai.generate_therapy_task(str(msg.chat.id), duration_text)
        await state.update_data(current_task=task)

        await state.set_state(TherapyStates.CONFIRM_TASK) # Переходим к подтверждению
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
        print(f"Error during therapy task generation for chat {msg.chat.id}: {e}")
        await msg.answer("Произошла ошибка при генерации задания. Пожалуйста, попробуйте выбрать время еще раз.", reply_markup=therapy_keyboard)
        await state.set_state(TherapyStates.WAITING_TIME) # Возвращаем в состояние выбора времени


@router.message(TherapyStates.CONFIRM_TASK, F.text == "🔄 Изменить задание")
async def handle_change_task(msg: Message, state: FSMContext):
    data = await state.get_data()
    duration_text = data.get('duration_text', "Свободный режим") # Fallback if not set, though it should be

    await msg.answer("Генерирую новое задание...", reply_markup=ReplyKeyboardRemove())
    await state.set_state(TherapyStates.GENERATING_TASK)

    try:
        # Assuming ai.generate_therapy_task exists and works
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
        print(f"Error during therapy task generation for chat {msg.chat.id}: {e}")
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

    duration = data.get('duration', 0)
    if duration > 0:
        await msg.answer(
            f"⏳ Таймер запущен на {duration} минут!",
            # Заменяем ReplyKeyboardRemove на клавиатуру с кнопкой досрочного завершения
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🏁 Завершить задание досрочно")]],
                resize_keyboard=True,
                one_time_keyboard=True # Можно сделать одноразовой, если хотите
            )
        )

        therapy_sessions[str(msg.chat.id)] = asyncio.create_task(
            finish_therapy_session(msg.chat.id, duration, state)
        )
    else:
        await msg.answer(
            "🕊️ Свободный режим активирован! Твори сколько хочешь!",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🏁 Завершить сессию")]],
                resize_keyboard=True
            )
        )

# Этот обработчик для кнопки "Завершить сессию" (для свободного режима)
@router.message(TherapyStates.IN_PROGRESS, F.text == "🏁 Завершить сессию")
async def handle_finish_free_mode_session(msg: Message, state: FSMContext):
    await finish_session(str(msg.chat.id), state)

# Новый обработчик для кнопки "Завершить задание досрочно" (для таймера)
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
    # Check if the state is still IN_PROGRESS before finishing
    # This prevents finishing if the user manually cancelled or finished early
    current_state = await state.get_state()
    if current_state == TherapyStates.IN_PROGRESS:
        await finish_session(str(chat_id), state)

async def finish_session(chat_id_str: str, state: FSMContext):
    chat_id = int(chat_id_str)
    if chat_id_str in therapy_sessions:
        therapy_sessions[chat_id_str].cancel()
        del therapy_sessions[chat_id_str]

    await state.set_state(None) # As per diff, clears only state, not data immediately.
    try:
        await bot.send_message(
            chat_id,
            "Ух, ты! Как быстро пролетело время. Хочешь поразмышлять над тем, что у тебя получилось?",
            reply_markup=reflection_keyboard
        )
    except TelegramBadRequest as e:
        print(f"Error sending message in finish_session to {chat_id}: {e}")
        # Potentially send to main_keyboard if reflection_keyboard causes issues or user blocked bot
        try:
            await bot.send_message(chat_id, "Сессия завершена.", reply_markup=main_keyboard)
        except Exception as final_e:
            print(f"Error sending final message to {chat_id}: {final_e}")


@router.message(F.text.in_(["Да", "Нет"]))
async def handle_reflection(msg: Message, state: FSMContext):
    if await state.get_state() == TherapyStates.GENERATING_TASK:
        return
    # Этот обработчик слишком широкий, лучше привязать к состоянию.
    # Пока оставим так, но добавим проверку.
    # Check if the user is actually expected to provide reflection input,
    # i.e., if the state was just cleared from IN_PROGRESS
    # This is tricky without a specific reflection state.
    # For now, we rely on the state.clear() happening *after* this check and logic.
    # If a state like TherapyStates.AWAITING_REFLECTION was used after IN_PROGRESS,
    # this handler could be tied to that state.

    if msg.text == "Да":
        reflection_prompt = "Сформулируй вопрос для рефлексии по выполненному арт-терапевтическому заданию"
        # Assuming ai.ask exists and works
        reflection_question = await ai.ask(str(msg.chat.id), reflection_prompt)
        await msg.answer(f"Отлично! {reflection_question}", reply_markup=main_keyboard)
    else:
        await msg.answer("Спасибо, что сделал задание со мной! Надеюсь, тебе было интересно)", reply_markup=main_keyboard)

    await state.clear() # Clear the state after handling reflection
@router.message(F.text)
async def handle_msg(msg: Message, state: FSMContext) -> None:
    if await state.get_state() == TherapyStates.GENERATING_TASK:
        return

    # Проверяем, не находимся ли мы в специфическом состоянии арт-терапии,
    # где текстовый ввод ожидается для чего-то другого (сейчас таких нет, но на будущее)
    current_fsm_state = await state.get_state()
    # If we are in one of these states, the text might be meant for that state's
    # handler (e.g., a custom duration in WAITING_TIME, though not implemented).
    # Since no specific text handlers exist for these states besides the buttons,
    # letting it fall through to ai.ask might be the desired behavior
    # for unhandled text input within these states, but it's potentially confusing.
    # A better approach might be to add specific handlers for F.text in those states
    # that inform the user they need to use the buttons.
    if current_fsm_state in [TherapyStates.WAITING_TIME, TherapyStates.CONFIRM_TASK, TherapyStates.IN_PROGRESS]:
        # If the text is not one of the specific buttons handled by other handlers
        # within these states, it will reach here.
        # For now, process it via ai.ask, but acknowledge this is a potential UX point.
        pass


    id = str(msg.chat.id)

    try:
        wait_msg = await msg.answer("⌛ Обрабатываю запрос...", reply_markup=main_keyboard)
        # Assuming ai.ask exists and works
        answer = await ai.ask(id, msg.text)

        await wait_msg.delete()
        await msg.answer(answer, reply_markup=main_keyboard)

    except Exception as e:
        print(f"Error in chat {id}: {e}")
        await msg.answer("⚠ Произошла ошибка, попробуйте позже", reply_markup=main_keyboard)

# Assuming main() or run_bot() function is defined elsewhere to start the dispatcher
# Example:
# async def main():
#     await dp.start_polling(bot)
#
# if __name__ == "__main__":
#     asyncio.run(main())
