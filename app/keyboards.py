from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_exam_kb(exam_id: int):
    """Клавиатура для экзамена"""
    kb = [
        [
            InlineKeyboardButton(text="📝 Добавить тему", callback_data=f"exam_topic_add_{exam_id}"),
            InlineKeyboardButton(text="📋 Темы", callback_data=f"exam_topics_{exam_id}"),
        ],
        [
            InlineKeyboardButton(text="✅ Завершить", callback_data=f"exam_complete_{exam_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"exam_delete_{exam_id}"),
        ],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="exams_list")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_labs_kb(lab_id: int):
    """Клавиатура для лабораторной"""
    kb = [
        [
            InlineKeyboardButton(text="🔄 В работу", callback_data=f"lab_status_{lab_id}_in_progress"),
            InlineKeyboardButton(text="✅ Готово", callback_data=f"lab_status_{lab_id}_completed"),
        ],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="labs_list")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_main_kb():
    """Главное меню"""
    kb = [
        [InlineKeyboardButton(text="📚 Экзамены", callback_data="menu_exams")],
        [InlineKeyboardButton(text="🔬 Лабораторные", callback_data="menu_labs")],
        [InlineKeyboardButton(text="📝 Тесты", callback_data="menu_tests")],
        [InlineKeyboardButton(text="🔔 Напоминания", callback_data="menu_reminders")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_tests_kb(test_id: int):
    """Клавиатура для теста"""
    kb = [
        [
            InlineKeyboardButton(text="➕ Добавить вопрос", callback_data=f"test_add_q_{test_id}"),
            InlineKeyboardButton(text="📋 Вопросы", callback_data=f"test_questions_{test_id}"),
        ],
        [
            InlineKeyboardButton(text="🚀 Начать тест", callback_data=f"test_start_{test_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"test_delete_{test_id}"),
        ],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="tests_list")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_answer_kb(question_id: int, answers: list):
    """Клавиатура для ответов в тесте"""
    buttons = []
    labels = ["a", "b", "c", "d"]
    for i, label in enumerate(labels):
        if i < len(answers):
            buttons.append(
                InlineKeyboardButton(text=f"{labels[i]}. {answers[i]}", callback_data=f"answer_{question_id}_{labels[i]}")
            )
    kb = [buttons]
    kb.append([InlineKeyboardButton(text="⬅ Пропустить", callback_data=f"answer_skip_{question_id}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_pagination_kb(current: int, total: int, callback_prefix: str):
    """Пагинация"""
    kb = []
    if current > 1:
        kb.append(InlineKeyboardButton(text="⬅ Назад", callback_data=f"{callback_prefix}_page_{current - 1}"))
    if total > 1:
        kb.append(InlineKeyboardButton(text=f"{current}/{total}", callback_data="noop"))
    if current < total:
        kb.append(InlineKeyboardButton(text="Вперёд ➡", callback_data=f"{callback_prefix}_page_{current + 1}"))
    return InlineKeyboardMarkup(inline_keyboard=[kb]) if kb else InlineKeyboardMarkup(inline_keyboard=[])
