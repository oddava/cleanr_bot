from datetime import datetime
from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, DateTime, select
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from config import config


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Member(Base):
    __tablename__ = "members"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    assignments: Mapped[list["Assignment"]] = relationship("Assignment", back_populates="member")
    
    def __repr__(self) -> str:
        return f"<Member {self.name} ({self.telegram_id})>"


class Task(Base):
    __tablename__ = "tasks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    required_people: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    assignments: Mapped[list["Assignment"]] = relationship("Assignment", back_populates="task")
    
    def __repr__(self) -> str:
        return f"<Task {self.name} ({self.required_people} people)>"


class Assignment(Base):
    __tablename__ = "assignments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(Integer, ForeignKey("members.id"), nullable=False)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    member: Mapped["Member"] = relationship("Member", back_populates="assignments")
    task: Mapped["Task"] = relationship("Task", back_populates="assignments")
    
    def __repr__(self) -> str:
        return f"<Assignment {self.member.name} -> {self.task.name} (Week {self.week_number}/{self.year})>"


class Settings(Base):
    __tablename__ = "settings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(String(200), nullable=False)


# Database engine and session
engine = create_async_engine(config.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    """Get a new database session."""
    async with async_session() as session:
        yield session
