from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart

from database import async_session
from services.assignment import get_formatted_schedule, get_member_assignments

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    await message.answer(
        "👋 *Welcome to CleanrBot!*\n\n"
        "I help manage weekly apartment cleaning duties.\n\n"
        "Use /help to see available commands.",
        parse_mode="Markdown"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command - show all commands table."""
    help_text = """
🧹 *CleanrBot Commands*

*General Commands:*
```
/start      - Welcome message
/help       - Show this help
/schedule   - View current week's schedule
/my_tasks   - View your assigned tasks
```

*Admin Commands:*
```
/add_member <id> <name>    - Add member
/remove_member <id>        - Remove member
/list_members              - List all members

/add_task <name> <count>   - Add task
/remove_task <name>        - Remove task  
/list_tasks                - List all tasks

/shuffle                   - Shuffle assignments
/set_notification <d> <h>  - Set reminder day/hour
```

💡 *Tips:*
• Get your Telegram ID from @userinfobot
• Day: 0=Mon, 6=Sun | Hour: 0-23
"""
    await message.answer(help_text, parse_mode="Markdown")


@router.message(Command("schedule"))
async def cmd_schedule(message: Message):
    """Handle /schedule command - show current assignments."""
    async with async_session() as session:
        schedule = await get_formatted_schedule(session)
        await message.answer(schedule, parse_mode="Markdown")


@router.message(Command("my_tasks"))
async def cmd_my_tasks(message: Message):
    """Handle /my_tasks command - show user's assigned tasks."""
    async with async_session() as session:
        assignments = await get_member_assignments(session, message.from_user.id)
        
        if not assignments:
            await message.answer(
                "✨ You have no tasks assigned this week!\n\n"
                "_You might not be registered. Ask the admin to add you._",
                parse_mode="Markdown"
            )
            return
        
        tasks = [a.task.name for a in assignments]
        tasks_list = "\n".join(f"• {task}" for task in tasks)
        
        await message.answer(
            f"🧹 *Your Tasks This Week:*\n\n{tasks_list}",
            parse_mode="Markdown"
        )
