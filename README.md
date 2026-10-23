# MaxBot 🤖

Бот для подготовки к экзаменам и управления лабораторными работами.

## Стек технологий

- **FastAPI** — REST API
- **aiogram 3** — Telegram бот
- **PostgreSQL** — база данных
- **SQLAlchemy** — ORM
- **APScheduler** — напоминания

## Функции

### 📚 Экзамены
- Добавление экзаменов с предметом, темой и датой
- Отслеживание прогресса подготовки
- Добавление тем для каждого экзамена
- Отметка экзаменов как завершённых

### 🔬 Лабораторные работы
- Добавление лабораторных с номером и названием
- Установка дедлайнов
- Отслеживание статуса (ожидание / в работе / выполнено)
- Автоматическая сортировка по дедлайнам

### 📝 Тесты / Викторины
- Создание тестов с вопросами (4 варианта ответа)
- Прохождение тестов прямо в Telegram
- Подсчёт результатов и оценка

### 🔔 Напоминания
- Автоматические напоминания за 24 часа до дедлайна
- Список всех предстоящих экзаменов и лабораторных

## Установка

### 1. Клонировать и настроить окружение

```bash
# Создать .env файл
copy .env.example .env
```

### 2. Настроить .env

Откройте `.env` и вставьте токен бота от @BotFather:

```
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
BOT_ADMIN_ID=0
DATABASE_URL=postgresql+asyncpg://maxbot:maxbot_password@localhost:5432/maxbot_db
```

### 3. Запустить PostgreSQL

```bash
# Вариант 1: Docker (рекомендуется)
docker-compose up -d

# Вариант 2: Локальная установка
# Убедитесь что PostgreSQL запущен и создайте БД:
# CREATE DATABASE maxbot_db;
# CREATE USER maxbot WITH PASSWORD 'maxbot_password';
# GRANT ALL PRIVILEGES ON DATABASE maxbot_db TO maxbot;
```

### 4. Установить зависимости

```bash
pip install -r requirements.txt
```

### 5. Запустить

```bash
# Запустить бота с напоминаниями
python -m app.bot_runner

# Или запустить только API
uvicorn app.main:app --reload

# Или всё вместе через uvicorn
uvicorn app.main:app --reload
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Начать работу / Регистрация |
| `/help` | Показать справку |
| `/exam_add` | Добавить экзамен |
| `/exam_list` | Список экзаменов |
| `/lab_add` | Добавить лабораторную |
| `/lab_list` | Список лабораторных |
| `/test_create` | Создать тест |
| `/test_list` | Список тестов |
| `/reminders` | Список напоминаний |

## REST API

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/health` | Проверка состояния |
| POST | `/api/users` | Создать пользователя |
| GET | `/api/users/{id}` | Получить пользователя |
| POST | `/api/exams` | Создать экзамен |
| GET | `/api/users/{id}/exams` | Список экзаменов |
| PUT | `/api/exams/{id}` | Обновить экзамен |
| POST | `/api/labs` | Создать лабораторную |
| GET | `/api/users/{id}/labs` | Список лабораторных |
| POST | `/api/tests` | Создать тест |
| GET | `/api/users/{id}/tests` | Список тестов |
| POST | `/api/questions` | Добавить вопрос |
| GET | `/api/tests/{id}/questions` | Вопросы теста |

## Структура проекта

```
maxbot/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI приложение + API
│   ├── config.py         # Настройки (.env)
│   ├── database.py       # Подключение к БД
│   ├── models.py         # SQLAlchemy модели
│   ├── schemas.py        # Pydantic схемы
│   ├── bot.py            # Bot + Dispatcher
│   ├── keyboards.py      # Inline клавиатуры
│   ├── bot_runner.py     # Запуск бота с APScheduler
│   ├── handlers/
│   │   ├── user.py       # /start, /help
│   │   ├── exams.py      # Экзамены
│   │   ├── labs.py       # Лабораторные
│   │   ├── tests.py      # Тесты
│   │   └── reminders.py  # Напоминания
│   └── services/         # Сервисный слой (расширение)
├── .env.example
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Лицензия

MIT
