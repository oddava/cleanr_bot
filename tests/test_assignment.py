import pytest
from sqlalchemy import select
from database import Member, Task, Assignment
from services.assignment import shuffle_assignments, get_current_assignments

@pytest.mark.asyncio
async def test_shuffle_basics(db_session, member_factory, task_factory):
    """Test basic shuffle functionality."""
    # Setup: 3 members, 2 tasks (1 person each)
    await member_factory(count=3)
    await task_factory(count=2, required_people=1)
    
    # Run shuffle
    result = await shuffle_assignments(db_session)
    
    # Verify exact number of assignments (2 tasks * 1 person = 2 assignments)
    assert len(result) == 2  # 2 tasks in dict
    
    assignments = await get_current_assignments(db_session)
    assert len(assignments) == 2
    
    # Verify assigned members are unique (since we have enough members)
    assigned_members = [a.member.name for a in assignments]
    assert len(set(assigned_members)) == 2

@pytest.mark.asyncio
async def test_shuffle_not_enough_members(db_session, member_factory, task_factory):
    """Test shuffle when tasks require more people than available."""
    # Setup: 2 members, 3 tasks (1 person each) -> Need 3 slots
    await member_factory(count=2)
    # Task 0, Task 1, Task 2
    await task_factory(count=3, required_people=1)
    
    # Run shuffle
    await shuffle_assignments(db_session)
    assignments = await get_current_assignments(db_session)
    
    # Should have 3 assignments
    assert len(assignments) == 3
    
    # Verify someone is double-assigned or both are used
    # With 2 members and 3 slots, at least one member must appear twice (pigeonhole principle)
    assigned_ids = [a.member_id for a in assignments]
    unique_ids = set(assigned_ids)
    assert len(unique_ids) == 2  # Both members used

@pytest.mark.asyncio
async def test_shuffle_multi_person_task(db_session, member_factory, task_factory):
    """Test task requiring multiple people."""
    await member_factory(count=4)
    # 1 task requiring 3 people
    await task_factory(count=1, required_people=3)
    
    await shuffle_assignments(db_session)
    assignments = await get_current_assignments(db_session)
    
    assert len(assignments) == 3
    assert assignments[0].task.name == "Task0"
    
    # Verify 3 different people assigned
    assigned_ids = set(a.member_id for a in assignments)
    assert len(assigned_ids) == 3

@pytest.mark.asyncio
async def test_empty_shuffle(db_session):
    """Test shuffle with no data."""
    result = await shuffle_assignments(db_session)
    assert result == {}
    
    assignments = await get_current_assignments(db_session)
    assert len(assignments) == 0

@pytest.mark.asyncio
async def test_reshuffle_clears_previous(db_session, member_factory, task_factory):
    """Test that shuffling again clears previous assignments for the week."""
    await member_factory(count=3)
    await task_factory(count=2)
    
    # First shuffle
    await shuffle_assignments(db_session)
    first_assignments = await get_current_assignments(db_session)
    assert len(first_assignments) == 2
    
    # Second shuffle
    await shuffle_assignments(db_session)
    second_assignments = await get_current_assignments(db_session)
    assert len(second_assignments) == 2
    
    # Total assignments should still be 2 (previous ones deleted)
    result = await db_session.execute(select(Assignment))
    all_assignments = result.scalars().all()
    assert len(all_assignments) == 2
