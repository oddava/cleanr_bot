from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import select, delete

from config import config
from database import async_session, Member, Task, Settings
from services.assignment import shuffle_assignments, format_assignments_table

router = Router()


def is_superuser(user_id: int) -> bool:
    """Check if user is the superuser."""
    return user_id == config.SUPERUSER_ID


# ============== Member Management ==============

@router.message(Command("add_member"))
async def cmd_add_member(message: Message):
    """Add a new member. Usage: /add_member <telegram_id> <name>"""
    if not is_superuser(message.from_user.id):
        await message.answer("⛔ This command is for admins only.")
        return
    
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer(
            "❌ *Usage:* `/add_member <telegram_id> <name>`\n\n"
            "_Example: /add_member 123456789 John_",
            parse_mode="Markdown"
        )
        return
    
    try:
        telegram_id = int(args[1])
    except ValueError:
        await message.answer("❌ Invalid Telegram ID. Must be a number.")
        return
    
    name = args[2]
    
    async with async_session() as session:
        # Check if member already exists
        existing = await session.execute(
            select(Member).where(Member.telegram_id == telegram_id)
        )
        if existing.scalar_one_or_none():
            await message.answer(f"⚠️ Member with ID {telegram_id} already exists.")
            return
        
        member = Member(telegram_id=telegram_id, name=name)
        session.add(member)
        await session.commit()
        
        await message.answer(f"✅ Added member: *{name}* (ID: `{telegram_id}`)", parse_mode="Markdown")


@router.message(Command("remove_member"))
async def cmd_remove_member(message: Message):
    """Remove a member. Usage: /remove_member <telegram_id>"""
    if not is_superuser(message.from_user.id):
        await message.answer("⛔ This command is for admins only.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "❌ *Usage:* `/remove_member <telegram_id>`\n\n"
            "_Example: /remove_member 123456789_",
            parse_mode="Markdown"
        )
        return
    
    try:
        telegram_id = int(args[1])
    except ValueError:
        await message.answer("❌ Invalid Telegram ID. Must be a number.")
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(Member).where(Member.telegram_id == telegram_id)
        )
        member = result.scalar_one_or_none()
        
        if not member:
            await message.answer(f"⚠️ Member with ID {telegram_id} not found.")
            return
        
        name = member.name
        await session.delete(member)
        await session.commit()
        
        await message.answer(f"✅ Removed member: *{name}*", parse_mode="Markdown")


@router.message(Command("list_members"))
async def cmd_list_members(message: Message):
    """List all members."""
    if not is_superuser(message.from_user.id):
        await message.answer("⛔ This command is for admins only.")
        return
    
    async with async_session() as session:
        result = await session.execute(select(Member).order_by(Member.name))
        members = result.scalars().all()
        
        if not members:
            await message.answer("📋 No members registered yet.")
            return
        
        lines = ["👥 *Registered Members:*\n"]
        for m in members:
            status = "✅" if m.active else "❌"
            lines.append(f"{status} {m.name} (`{m.telegram_id}`)")
        
        await message.answer("\n".join(lines), parse_mode="Markdown")


# ============== Task Management ==============

@router.message(Command("add_task"))
async def cmd_add_task(message: Message):
    """Add a new task. Usage: /add_task <name> <required_people>"""
    if not is_superuser(message.from_user.id):
        await message.answer("⛔ This command is for admins only.")
        return
    
    args = message.text.split()
    if len(args) < 3:
        await message.answer(
            "❌ *Usage:* `/add_task <name> <required_people>`\n\n"
            "_Example: /add_task Kitchen 2_",
            parse_mode="Markdown"
        )
        return
    
    name = args[1]
    try:
        required_people = int(args[2])
        if required_people < 1:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Required people must be a positive number.")
        return
    
    async with async_session() as session:
        # Check if task already exists
        existing = await session.execute(
            select(Task).where(Task.name == name)
        )
        if existing.scalar_one_or_none():
            await message.answer(f"⚠️ Task '{name}' already exists.")
            return
        
        task = Task(name=name, required_people=required_people)
        session.add(task)
        await session.commit()
        
        await message.answer(
            f"✅ Added task: *{name}* (requires {required_people} people)",
            parse_mode="Markdown"
        )


@router.message(Command("remove_task"))
async def cmd_remove_task(message: Message):
    """Remove a task. Usage: /remove_task <name>"""
    if not is_superuser(message.from_user.id):
        await message.answer("⛔ This command is for admins only.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "❌ *Usage:* `/remove_task <name>`\n\n"
            "_Example: /remove_task Kitchen_",
            parse_mode="Markdown"
        )
        return
    
    name = args[1]
    
    async with async_session() as session:
        result = await session.execute(
            select(Task).where(Task.name == name)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            await message.answer(f"⚠️ Task '{name}' not found.")
            return
        
        await session.delete(task)
        await session.commit()
        
        await message.answer(f"✅ Removed task: *{name}*", parse_mode="Markdown")


@router.message(Command("list_tasks"))
async def cmd_list_tasks(message: Message):
    """List all tasks."""
    if not is_superuser(message.from_user.id):
        await message.answer("⛔ This command is for admins only.")
        return
    
    async with async_session() as session:
        result = await session.execute(select(Task).order_by(Task.name))
        tasks = result.scalars().all()
        
        if not tasks:
            await message.answer("📋 No tasks created yet.")
            return
        
        lines = ["📝 *Cleaning Tasks:*\n"]
        total_people = 0
        for t in tasks:
            status = "✅" if t.active else "❌"
            lines.append(f"{status} {t.name} - {t.required_people} people")
            total_people += t.required_people
        
        lines.append(f"\n_Total: {total_people} people needed_")
        
        await message.answer("\n".join(lines), parse_mode="Markdown")


# ============== Shuffle & Notifications ==============

@router.message(Command("shuffle"))
async def cmd_shuffle(message: Message):
    """Manually trigger assignment shuffle."""
    if not is_superuser(message.from_user.id):
        await message.answer("⛔ This command is for admins only.")
        return
    
    async with async_session() as session:
        assignments = await shuffle_assignments(session)
        
        if not assignments:
            await message.answer(
                "⚠️ Cannot shuffle. Make sure you have members and tasks added first."
            )
            return
        
        schedule = format_assignments_table(assignments)
        await message.answer(
            f"🔀 *Assignments shuffled!*\n\n{schedule}",
            parse_mode="Markdown"
        )


@router.message(Command("set_notification"))
async def cmd_set_notification(message: Message):
    """Set notification day and hour. Usage: /set_notification <day> <hour>"""
    if not is_superuser(message.from_user.id):
        await message.answer("⛔ This command is for admins only.")
        return
    
    args = message.text.split()
    if len(args) < 3:
        await message.answer(
            "❌ *Usage:* `/set_notification <day> <hour>`\n\n"
            "_Day: 0=Mon, 1=Tue, ..., 6=Sun_\n"
            "_Hour: 0-23 (24h format)_\n\n"
            "_Example: /set_notification 0 9_ (Monday 9 AM)",
            parse_mode="Markdown"
        )
        return
    
    try:
        day = int(args[1])
        hour = int(args[2])
        if day < 0 or day > 6 or hour < 0 or hour > 23:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Invalid values. Day: 0-6, Hour: 0-23")
        return
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    async with async_session() as session:
        # Update or create settings
        for key, value in [("notification_day", str(day)), ("notification_hour", str(hour))]:
            result = await session.execute(select(Settings).where(Settings.key == key))
            setting = result.scalar_one_or_none()
            if setting:
                setting.value = value
            else:
                session.add(Settings(key=key, value=value))
        
        await session.commit()
    
    await message.answer(
        f"✅ Notifications set to *{days[day]}* at *{hour:02d}:00*",
        parse_mode="Markdown"
    )
