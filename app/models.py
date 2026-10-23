from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    exams = relationship("Exam", back_populates="user", cascade="all, delete-orphan")
    labs = relationship("LabWork", back_populates="user", cascade="all, delete-orphan")
    tests_taken = relationship("TestResult", back_populates="user", cascade="all, delete-orphan")


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(200), nullable=False)
    topic = Column(String(500), nullable=False)
    date = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)
    progress = Column(Float, default=0.0)  # 0.0 - 100.0
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="exams")
    topics = relationship("ExamTopic", back_populates="exam", cascade="all, delete-orphan")


class ExamTopic(Base):
    __tablename__ = "exam_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    topic_name = Column(String(500), nullable=False)
    is_ready = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    exam = relationship("Exam", back_populates="topics")


class LabWork(Base):
    __tablename__ = "lab_works"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(200), nullable=False)
    lab_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    deadline = Column(DateTime, nullable=True)
    status = Column(String(50), default="pending")  # pending, in_progress, completed, overdue
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="labs")


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(200), nullable=False)
    title = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates=None)
    questions = relationship("Question", back_populates="test", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    option_a = Column(String(500), nullable=False)
    option_b = Column(String(500), nullable=False)
    option_c = Column(String(500), nullable=True)
    option_d = Column(String(500), nullable=True)
    correct_answer = Column(String(10), nullable=False)  # a, b, c, d
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    test = relationship("Test", back_populates="questions")
    results = relationship("TestResult", back_populates="question", cascade="all, delete-orphan")


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    selected_answer = Column(String(10), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="tests_taken")
    question = relationship("Question", back_populates="results")
