from maxapi import Router, F
from maxapi.types import Message, CallbackQuery
from maxapi.filters import Command, StateFilter
from maxapi.fsm.context import FSMContext
from maxapi.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User, Test, Question, TestResult
from app.handlers.common import handle_command_while_input
from app.keyboards import get_tests_kb, get_answer_kb, get_main_kb

router = Router()


class TestFSM(StatesGroup):
    waiting_subject = State()
    waiting_title = State()
    waiting_question = State()
    waiting_option_a = State()
    waiting_option_b = State()
    waiting_option_c = State()
    waiting_option_d = State()
    waiting_correct = State()
    waiting_answer = State()


# ============ Test CRUD ============
@router.message(Command("test_create"))
async def cmd_test_create(message: Message, state: FSMContext, db: AsyncSession):
    user = await _get_user(message.from_user.id, db)
    if not user:
        await message.answer("Сначала введите /start для регистрации.")
        return

    await state.set_state(TestFSM.waiting_subject)
    await message.answer("📝 Введите название предмета для теста:")


@router.message(Command("test_list"))
async def cmd_test_list(message: Message, db: AsyncSession, user_id: str | None = None):
    user = await _get_user(user_id or message.from_user.id, db)
    if not user:
        await message.answer("Сначала введите /start.")
        return

    result = await db.execute(select(Test).where(Test.user_id == user.id).order_by(Test.created_at.desc()))
    tests = result.scalars().all()

    if not tests:
        await message.answer("📝 У вас пока нет тестов.\nВведите /test_create чтобы создать.")
        return

    text = "<b>📝 Ваши тесты:</b>\n\n"
    for test in tests:
        text += f"📚 <b>{test.subject}</b>\n"
        text += f"   📝 {test.title}\n"
        text += f"   🆔 ID: {test.id}\n\n"

    await message.answer(text, reply_markup=get_main_kb())


@router.message(TestFSM.waiting_subject)
async def msg_test_subject(message: Message, state: FSMContext):
    if await handle_command_while_input(message, state, cancel_text="Добавление отменено."):
        return
    if not message.text:
        await message.answer("❌ Введите название предмета текстом.")
        return
    await state.update_data(subject=message.text)
    await message.answer("✏️ Введите название теста:")
    await state.set_state(TestFSM.waiting_title)


@router.message(TestFSM.waiting_title)
async def msg_test_title(message: Message, state: FSMContext, db: AsyncSession):
    if await handle_command_while_input(message, state, cancel_text="Добавление отменено."):
        return
    if not message.text:
        await message.answer("❌ Введите название теста текстом.")
        return

    data = await state.get_data()
    user = await _get_user(message.from_user.id, db)
    if not user:
        await message.answer("Сначала введите /start для регистрации.")
        await state.clear()
        return

    test = Test(
        user_id=user.id,
        subject=data["subject"],
        title=message.text,
    )
    db.add(test)
    await db.commit()
    await db.refresh(test)

    await state.update_data(test_id=test.id)
    await message.answer(
        f"✅ Тест создан!\n\n📝 {test.title}\n📚 {test.subject}\n\n"
        f"Теперь добавьте вопросы.",
        reply_markup=get_tests_kb(test.id),
    )


@router.message(TestFSM.waiting_question)
async def msg_test_question(message: Message, state: FSMContext):
    if await handle_command_while_input(message, state, cancel_text="Добавление отменено."):
        return
    if not message.text:
        await message.answer("❌ Введите текст вопроса.")
        return
    await state.update_data(question_text=message.text)
    await message.answer("✏️ Введите вариант a:")
    await state.set_state(TestFSM.waiting_option_a)


@router.message(TestFSM.waiting_option_a)
async def msg_test_option_a(message: Message, state: FSMContext):
    if await handle_command_while_input(message, state, cancel_text="Добавление отменено."):
        return
    if not message.text:
        await message.answer("❌ Введите вариант a текстом.")
        return
    await state.update_data(option_a=message.text)
    await message.answer("✏️ Введите вариант b:")
    await state.set_state(TestFSM.waiting_option_b)


@router.message(TestFSM.waiting_option_b)
async def msg_test_option_b(message: Message, state: FSMContext):
    if await handle_command_while_input(message, state, cancel_text="Добавление отменено."):
        return
    if not message.text:
        await message.answer("❌ Введите вариант b текстом.")
        return
    await state.update_data(option_b=message.text)
    await message.answer("✏️ Введите вариант c (необязательно) или /skip:")
    await state.set_state(TestFSM.waiting_option_c)


@router.message(TestFSM.waiting_option_c)
async def msg_test_option_c(message: Message, state: FSMContext):
    if message.text and message.text.strip().lower() == "/skip":
        await state.update_data(option_c=None)
    else:
        if not message.text:
            await message.answer("❌ Введите вариант c текстом или /skip")
            return
        await state.update_data(option_c=message.text)
    await message.answer("✏️ Введите вариант d (необязательно) или /skip:")
    await state.set_state(TestFSM.waiting_option_d)


@router.message(TestFSM.waiting_option_d)
async def msg_test_option_d(message: Message, state: FSMContext):
    if message.text and message.text.strip().lower() == "/skip":
        await state.update_data(option_d=None)
    else:
        if not message.text:
            await message.answer("❌ Введите вариант d текстом или /skip")
            return
        await state.update_data(option_d=message.text)
    await message.answer("✅ Какой ответ правильный? Введите букву (a/b/c/d):")
    await state.set_state(TestFSM.waiting_correct)


@router.message(TestFSM.waiting_correct)
async def msg_test_correct(message: Message, state: FSMContext, db: AsyncSession):
    if await handle_command_while_input(message, state, cancel_text="Добавление отменено."):
        return
    if not message.text:
        await message.answer("❌ Введите букву a, b, c или d:")
        return

    answer = message.text.strip().lower()
    if answer not in ("a", "b", "c", "d"):
        await message.answer("❌ Введите букву a, b, c или d:")
        return

    data = await state.get_data()
    if not data.get(f"option_{answer}"):
        await message.answer(f"❌ Варианта «{answer}» нет в этом вопросе. Введите другую букву:")
        return

    db.add(
        Question(
            test_id=data["test_id"],
            question_text=data["question_text"],
            option_a=data["option_a"],
            option_b=data["option_b"],
            option_c=data.get("option_c"),
            option_d=data.get("option_d"),
            correct_answer=answer,
        )
    )
    await db.commit()
    await state.clear()
    await message.answer("✅ Вопрос добавлен!", reply_markup=get_tests_kb(data["test_id"]))


@router.message(Command("skip"), StateFilter(TestFSM))
async def cmd_skip(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Добавление отменено.", reply_markup=get_main_kb())


# ============ Question CRUD ============
@router.callback_query(F.data == "menu_tests")
async def cb_menu_tests(callback: CallbackQuery, db: AsyncSession):
    await cmd_test_list(callback.message, db, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data.startswith("test_"))
async def test_callback_handler(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
    data = callback.data

    if data == "tests_list":
        await cmd_test_list(callback.message, db, callback.from_user.id)
        await callback.answer()
        return

    # test_add_q_{id}
    if data.startswith("test_add_q_"):
        test_id = int(data.rsplit("_", 1)[-1])
        await state.set_state(TestFSM.waiting_question)
        await state.update_data(test_id=test_id)
        await callback.message.answer("📝 Введите текст вопроса:")
        await callback.answer()
        return

    # test_questions_{id}
    if data.startswith("test_questions_"):
        test_id = int(data.rsplit("_", 1)[-1])
        result = await db.execute(select(Question).where(Question.test_id == test_id))
        questions = result.scalars().all()

        result2 = await db.execute(select(Test).where(Test.id == test_id))
        test = result2.scalar_one_or_none()

        if not test:
            await callback.answer("Тест не найден")
            return

        text = f"<b>{test.title}</b> ({test.subject})\n\n"
        text += f"<b>Вопросов: {len(questions)}</b>\n\n"

        for i, q in enumerate(questions, 1):
            text += f"{i}. {q.question_text}\n"
            text += f"   a) {q.option_a}\n"
            text += f"   b) {q.option_b}\n"
            if q.option_c:
                text += f"   c) {q.option_c}\n"
            if q.option_d:
                text += f"   d) {q.option_d}\n"
            text += f"   ✅ Ответ: {q.correct_answer}\n\n"

        await callback.message.edit_text(text, reply_markup=get_tests_kb(test_id))
        await callback.answer()
        return

    # test_start_{id}
    if data.startswith("test_start_"):
        test_id = int(data.rsplit("_", 1)[-1])
        result = await db.execute(select(Question).where(Question.test_id == test_id))
        questions = result.scalars().all()

        if not questions:
            await callback.answer("В тесте нет вопросов!")
            return

        await state.update_data(
            test_id=test_id,
            questions=[q.id for q in questions],
            current_index=0,
            correct_count=0,
            total=len(questions),
        )
        await state.set_state(TestFSM.waiting_answer)
        await _show_question(callback.message, state, db)
        await callback.answer()
        return

    # test_delete_{id}
    if data.startswith("test_delete_"):
        test_id = int(data.rsplit("_", 1)[-1])
        result = await db.execute(select(Test).where(Test.id == test_id))
        test = result.scalar_one_or_none()
        if test:
            await db.delete(test)
            await db.commit()
            await callback.answer("🗑 Тест удалён")
            await cmd_test_list(callback.message, db, callback.from_user.id)
        return

    await callback.answer()


# ============ Прохождение теста ============
@router.callback_query(F.data.startswith("answer_"))
async def answer_callback_handler(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
    data = callback.data

    # answer_skip_{question_id}
    if data.startswith("answer_skip_"):
        await _next_question(callback.message, state, db)
        await callback.answer()
        return

    # answer_{question_id}_{letter}
    parts = data.split("_")
    if len(parts) != 3:
        await callback.answer("⚠️ Неизвестная кнопка")
        return

    question_id = int(parts[1])
    answer = parts[2]
    await _check_answer(callback, state, db, question_id, answer)


async def _show_question(message: Message, state: FSMContext, db: AsyncSession):
    data = await state.get_data()
    questions = data.get("questions", [])
    index = data.get("current_index", 0)

    if index >= len(questions):
        await _show_results(message, state, db)
        return

    q_result = await db.execute(select(Question).where(Question.id == questions[index]))
    q = q_result.scalar_one_or_none()

    if not q:
        await message.answer("❌ Вопрос не найден")
        return

    text = f"<b>Вопрос {index + 1} из {data['total']}:</b>\n\n"
    text += f"{q.question_text}\n\n"
    text += f"a) {q.option_a}\n"
    text += f"b) {q.option_b}\n"
    if q.option_c:
        text += f"c) {q.option_c}\n"
    if q.option_d:
        text += f"d) {q.option_d}\n"

    kb = get_answer_kb(q.id, [q.option_a, q.option_b, q.option_c or "", q.option_d or ""])
    await message.answer(text, reply_markup=kb)


async def _check_answer(callback: CallbackQuery, state: FSMContext, db: AsyncSession, question_id: int, answer: str):
    q_result = await db.execute(select(Question).where(Question.id == question_id))
    q = q_result.scalar_one_or_none()

    if not q:
        await callback.answer("❌ Вопрос не найден")
        return

    data = await state.get_data()
    is_correct = q.correct_answer == answer

    user = await _get_user(callback.from_user.id, db)
    if user:
        result = TestResult(
            user_id=user.id,
            test_id=data.get("test_id"),
            question_id=question_id,
            selected_answer=answer,
            is_correct=is_correct,
        )
        db.add(result)
        await db.commit()

    if is_correct:
        data["correct_count"] = data.get("correct_count", 0) + 1
        await callback.answer("✅ Правильно!")
    else:
        await callback.answer(f"❌ Неправильно! Правильный ответ: {q.correct_answer}")

    await state.update_data(**data)
    await _next_question(callback.message, state, db)


async def _next_question(message: Message, state: FSMContext, db: AsyncSession):
    data = await state.get_data()
    index = data.get("current_index", 0) + 1
    await state.update_data(current_index=index)
    await _show_question(message, state, db)


async def _show_results(message: Message, state: FSMContext, db: AsyncSession):
    data = await state.get_data()
    correct = data.get("correct_count", 0)
    total = data.get("total", 0)
    percent = (correct / total * 100) if total > 0 else 0

    if percent >= 90:
        grade = "🏆 Отлично!"
    elif percent >= 70:
        grade = "👍 Хорошо!"
    elif percent >= 50:
        grade = "📖 Неплохо, но можно лучше"
    else:
        grade = "📚 Нужно подучить материал"

    text = f"<b>📊 Результаты теста:</b>\n\n"
    text += f"✅ Правильных: {correct}/{total}\n"
    text += f"📈 Процент: {percent:.0f}%\n\n"
    text += grade

    await message.answer(text, reply_markup=get_main_kb())
    await state.clear()


async def _get_user(max_user_id: str, db: AsyncSession):
    result = await db.execute(select(User).where(User.max_user_id == max_user_id))
    return result.scalar_one_or_none()
