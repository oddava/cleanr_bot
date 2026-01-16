import random
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import Member, Task, Assignment


def get_current_week() -> tuple[int, int]:
    """Get current ISO week number and year."""
    now = datetime.now()
    iso_calendar = now.isocalendar()
    return iso_calendar[1], iso_calendar[0]  # week, year


async def get_active_members(session: AsyncSession) -> list[Member]:
    """Get all active members."""
    result = await session.execute(
        select(Member).where(Member.active == True).order_by(Member.name)
    )
    return list(result.scalars().all())


async def get_active_tasks(session: AsyncSession) -> list[Task]:
    """Get all active tasks."""
    result = await session.execute(
        select(Task).where(Task.active == True).order_by(Task.name)
    )
    return list(result.scalars().all())


async def get_current_assignments(session: AsyncSession) -> list[Assignment]:
    """Get assignments for the current week."""
    week, year = get_current_week()
    result = await session.execute(
        select(Assignment)
        .options(selectinload(Assignment.member), selectinload(Assignment.task))
        .where(Assignment.week_number == week, Assignment.year == year)
    )
    return list(result.scalars().all())


async def get_member_assignments(session: AsyncSession, telegram_id: int) -> list[Assignment]:
    """Get current week's assignments for a specific member."""
    week, year = get_current_week()
    result = await session.execute(
        select(Assignment)
        .join(Member)
        .options(selectinload(Assignment.task))
        .where(
            Member.telegram_id == telegram_id,
            Assignment.week_number == week,
            Assignment.year == year
        )
    )
    return list(result.scalars().all())


async def clear_current_assignments(session: AsyncSession) -> None:
    """Clear all assignments for the current week."""
    week, year = get_current_week()
    await session.execute(
        delete(Assignment).where(
            Assignment.week_number == week,
            Assignment.year == year
        )
    )
    await session.commit()


async def shuffle_assignments(session: AsyncSession) -> dict[str, list[str]]:
    """
    Shuffle and create new assignments for the current week.
    Returns a dict mapping task names to list of member names.
    """
    week, year = get_current_week()
    
    # Clear existing assignments for this week
    await clear_current_assignments(session)
    
    # Get active members and tasks
    members = await get_active_members(session)
    tasks = await get_active_tasks(session)
    
    if not members or not tasks:
        return {}
    
    # Calculate total required people
    total_required = sum(task.required_people for task in tasks)
    
    # Create a pool of member indices that can be reused if needed
    member_pool = list(range(len(members)))
    random.shuffle(member_pool)
    
    # If we need more slots than members, we'll cycle through
    extended_pool = []
    while len(extended_pool) < total_required:
        random.shuffle(member_pool)
        extended_pool.extend(member_pool)
    
    # Assign members to tasks
    result: dict[str, list[str]] = {}
    pool_index = 0
    
    for task in tasks:
        result[task.name] = []
        for _ in range(task.required_people):
            if pool_index < len(extended_pool):
                member_idx = extended_pool[pool_index]
                member = members[member_idx]
                
                # Create assignment
                assignment = Assignment(
                    member_id=member.id,
                    task_id=task.id,
                    week_number=week,
                    year=year
                )
                session.add(assignment)
                result[task.name].append(member.name)
                pool_index += 1
    
    await session.commit()
    return result


def format_assignments_table(assignments: dict[str, list[str]]) -> str:
    """Format assignments as a nice text table."""
    if not assignments:
        return "📋 No assignments yet. Use /shuffle to create them."
    
    week, year = get_current_week()
    lines = [
        f"🧹 *Cleaning Schedule - Week {week}/{year}*",
        "",
        "```"
    ]
    
    # Find max lengths for formatting
    max_task_len = max(len(task) for task in assignments.keys())
    
    for task, members in assignments.items():
        members_str = ", ".join(members) if members else "No one assigned"
        lines.append(f"{task:<{max_task_len}} │ {members_str}")
    
    lines.append("```")
    return "\n".join(lines)


async def get_formatted_schedule(session: AsyncSession) -> str:
    """Get the current week's schedule formatted as a table."""
    assignments = await get_current_assignments(session)
    
    if not assignments:
        return "📋 No assignments for this week. Admin can use /shuffle to create them."
    
    # Group by task
    task_assignments: dict[str, list[str]] = {}
    for assignment in assignments:
        task_name = assignment.task.name
        if task_name not in task_assignments:
            task_assignments[task_name] = []
        task_assignments[task_name].append(assignment.member.name)
    
    return format_assignments_table(task_assignments)
