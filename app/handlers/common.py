from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.keyboards import get_main_kb


async def handle_command_while_input(
    message: Message,
    state: FSMContext,
    cancel_text: str = "Добавление отменено.",
) -> bool:
    """Перехватывает команды, введённые во время FSM-ввода текста.

    /skip — отменяет текущий сценарий, остальные команды — предупреждение.
    Возвращает True, если команда обработана (хендлер должен завершиться).
    """
    if not message.text or not message.text.startswith("/"):
        return False

    if message.text.strip().lower() == "/skip":
        await state.clear()
        await message.answer(f"❌ {cancel_text}", reply_markup=get_main_kb())
    else:
        await message.answer("❌ Сейчас ожидается ввод текста. Для отмены введите /skip.")
    return True
