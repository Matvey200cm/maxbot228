from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from app.bot import bot
from app.database import get_db
from app.models import User, Test, Question, TestResult
from app.schemas import TestCreate, QuestionCreate
from app.keyboards import get_tests_kb, get_answer_kb, get_main_kb, get_pagination_kb

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
@router.command("test_create")
async def cmd_test_create(message: Message, state: FSMContext, db: AsyncSession):
    user = await _get_user(message.from_user.id, db)
    if not user:
        await message.answer("Сначала введите /start для регистрации.")
        return

    await state.set_state(TestFSM.waiting_subject)
    await message.answer("📝 Введите название предмета для теста:")


@router.command("test_list")
async def cmd_test_list(message: Message, db: AsyncSession):
    user = await _get_user(message.from_user.id, db)
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
async def msg_test_subject(message: Message, state: FSMContext, db: AsyncSession):
    await state.update_data(subject=message.text)
    await message.answer("✏️ Введите название теста:")
    await state.set_state(TestFSM.waiting_title)


@router.message(TestFSM.waiting_title)
async def msg_test_title(message: Message, state: FSMContext, db: AsyncSession):
    data = await state.get_data()
    user = await _get_user(message.from_user.id, db)

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


@router.message(Command("skip"))
async def cmd_skip(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Добавление отменено.", reply_markup=get_main_kb())


# ============ Question CRUD ============
@router.callback_query(lambda c: c.data and c.data.startswith("test_"))
async def test_callback_handler(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
    data = callback.data

    if data == "menu_tests":
        await callback.message.edit_text("📝 Раздел тестов:", reply_markup=get_main_kb())
        return

    if data == "tests_list":
        await cmd_test_list(callback.message, db)
        return

    # test_add_q_{id}
    if data.startswith("test_add_q_"):
        test_id = int(data.split("_")[-1])
        await state.set_state(TestFSM.waiting_question)
        await state.update_data(test_id=test_id)
        await callback.message.answer("📝 Введите текст вопроса:")
        return

    # test_questions_{id}
    if data.startswith("test_questions_"):
        test_id = int(data.split("_")[-1])
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

        await callback.message.edit_text(text)
        await callback.answer()
        return

    # test_start_{id}
    if data.startswith("test_start_"):
        test_id = int(data.split("_")[-1])
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
        return

    # test_delete_{id}
    if data.startswith("test_delete_"):
        test_id = int(data.split("_")[-1])
        result = await db.execute(select(Test).where(Test.id == test_id))
        test = result.scalar_one_or_none()
        if test:
            await db.delete(test)
            await db.commit()
            await callback.answer("🗑 Тест удалён")
            await cmd_test_list(callback.message, db)
        return

    # answer_{question_id}_{answer}
    if data.startswith("answer_"):
        parts = data.split("_")
        question_id = int(parts[1])
        answer = parts[2]

        if answer == "skip":
            await _next_question(callback.message, state, db)
            return

        await _check_answer(callback, state, db, question_id, answer)
        return

    await callback.answer()


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

    kb = get_answer_kb(questions[index], [q.option_a, q.option_b, q.option_c or "", q.option_d or ""])
    await message.answer(text, reply_markup=kb)


async def _check_answer(callback: CallbackQuery, state: FSMContext, db: AsyncSession, question_id: int, answer: str):
    q_result = await db.execute(select(Question).where(Question.id == question_id))
    q = q_result.scalar_one_or_none()

    is_correct = q.correct_answer == answer

    user = await _get_user(callback.from_user.id, db)
    result = TestResult(
        user_id=user.id,
        test_id=callback.data.split("_")[-1] if "_" in callback.data else None,
        question_id=question_id,
        selected_answer=answer,
        is_correct=is_correct,
    )
    db.add(result)
    await db.commit()

    data = await state.get_data()
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


async def _get_user(telegram_id: int, db: AsyncSession):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()
