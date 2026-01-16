import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from database import Base, Member, Task, Assignment

# Use SQLite in-memory for fast testing
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine):
    async_session = async_sessionmaker(db_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest.fixture
def member_factory(db_session):
    async def _create_members(count=3):
        members = []
        for i in range(count):
            m = Member(telegram_id=1000+i, name=f"User{i}", username=f"user{i}")
            db_session.add(m)
            members.append(m)
        await db_session.commit()
        return members
    return _create_members

@pytest.fixture
def task_factory(db_session):
    async def _create_tasks(count=2, required_people=1):
        tasks = []
        for i in range(count):
            t = Task(name=f"Task{i}", required_people=required_people)
            db_session.add(t)
            tasks.append(t)
        await db_session.commit()
        return tasks
    return _create_tasks
