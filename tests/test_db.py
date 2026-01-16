import pytest
from sqlalchemy import select
from database import Member, Task, Settings

@pytest.mark.asyncio
async def test_create_and_retrieve_member(db_session):
    member = Member(telegram_id=123, name="Test User", username="testuser")
    db_session.add(member)
    await db_session.commit()
    
    result = await db_session.execute(select(Member).where(Member.telegram_id == 123))
    retrieved = result.scalar_one()
    
    assert retrieved.name == "Test User"
    assert retrieved.username == "testuser"
    assert retrieved.active is True

@pytest.mark.asyncio
async def test_update_member(db_session):
    member = Member(telegram_id=456, name="Old Name")
    db_session.add(member)
    await db_session.commit()
    
    member.name = "New Name"
    await db_session.commit()
    
    result = await db_session.execute(select(Member).where(Member.telegram_id == 456))
    retrieved = result.scalar_one()
    assert retrieved.name == "New Name"

@pytest.mark.asyncio
async def test_delete_member(db_session):
    member = Member(telegram_id=789, name="To Delete")
    db_session.add(member)
    await db_session.commit()
    
    await db_session.delete(member)
    await db_session.commit()
    
    result = await db_session.execute(select(Member).where(Member.telegram_id == 789))
    assert result.scalar_one_or_none() is None

@pytest.mark.asyncio
async def test_settings(db_session):
    # Test settings creation and retrieval
    s1 = Settings(key="test_key", value="test_value")
    db_session.add(s1)
    await db_session.commit()
    
    result = await db_session.execute(select(Settings).where(Settings.key == "test_key"))
    retrieved = result.scalar_one()
    assert retrieved.value == "test_value"
