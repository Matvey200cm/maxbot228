from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.models import User, Exam, LabWork, Test, Question
from app.schemas import (
    UserCreate, UserOut,
    ExamCreate, ExamOut, ExamUpdate,
    LabWorkCreate, LabWorkOut,
    TestCreate, TestOut,
    QuestionCreate, QuestionOut,
)
from app.config import get_settings

settings = get_settings()
app = FastAPI(title="MaxBot API", version="1.0.0")


# ============ Users ============
@app.post("/api/users", response_model=UserOut)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.telegram_id == user.telegram_id))
    if existing.scalar_one_or_none():
        return existing.scalar_one_or_none()
    db_user = User(**user.model_dump())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@app.get("/api/users/{telegram_id}", response_model=UserOut)
async def get_user(telegram_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ============ Exams ============
@app.post("/api/exams", response_model=ExamOut)
async def create_exam(exam: ExamCreate, user_id: int, db: AsyncSession = Depends(get_db)):
    db_exam = Exam(user_id=user_id, **exam.model_dump())
    db.add(db_exam)
    await db.commit()
    await db.refresh(db_exam)
    return db_exam


@app.get("/api/users/{user_id}/exams", response_model=List[ExamOut])
async def get_exams(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Exam).where(Exam.user_id == user_id).order_by(Exam.date))
    return result.scalars().all()


@app.put("/api/exams/{exam_id}", response_model=ExamOut)
async def update_exam(exam_id: int, exam: ExamUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    db_exam = result.scalar_one_or_none()
    if not db_exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    for key, value in exam.model_dump(exclude_unset=True).items():
        setattr(db_exam, key, value)
    await db.commit()
    await db.refresh(db_exam)
    return db_exam


# ============ Lab Works ============
@app.post("/api/labs", response_model=LabWorkOut)
async def create_lab(lab: LabWorkCreate, user_id: int, db: AsyncSession = Depends(get_db)):
    db_lab = LabWork(user_id=user_id, **lab.model_dump())
    db.add(db_lab)
    await db.commit()
    await db.refresh(db_lab)
    return db_lab


@app.get("/api/users/{user_id}/labs", response_model=List[LabWorkOut])
async def get_labs(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LabWork).where(LabWork.user_id == user_id).order_by(LabWork.deadline)
    )
    return result.scalars().all()


# ============ Tests ============
@app.post("/api/tests", response_model=TestOut)
async def create_test(test: TestCreate, user_id: int, db: AsyncSession = Depends(get_db)):
    db_test = Test(user_id=user_id, **test.model_dump())
    db.add(db_test)
    await db.commit()
    await db.refresh(db_test)
    return db_test


@app.get("/api/users/{user_id}/tests", response_model=List[TestOut])
async def get_tests(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Test).where(Test.user_id == user_id).order_by(Test.created_at.desc()))
    return result.scalars().all()


# ============ Questions ============
@app.post("/api/questions", response_model=QuestionOut)
async def create_question(question: QuestionCreate, db: AsyncSession = Depends(get_db)):
    db_question = Question(**question.model_dump())
    db.add(db_question)
    await db.commit()
    await db.refresh(db_question)
    return db_question


@app.get("/api/tests/{test_id}/questions", response_model=List[QuestionOut])
async def get_questions(test_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Question).where(Question.test_id == test_id))
    return result.scalars().all()


# ============ Health ============
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "maxbot"}
