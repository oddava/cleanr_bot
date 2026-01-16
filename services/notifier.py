from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from services.assignment import get_current_assignments, get_formatted_schedule
from config import config


async def send_weekly_notification(bot: Bot, session: AsyncSession) -> None:
    """Send weekly cleaning notification to the group chat."""
    schedule = await get_formatted_schedule(session)
    
    message = (
        "🔔 *Weekly Cleaning Reminder!*\n\n"
        f"{schedule}\n\n"
        "Good luck everyone! 💪"
    )
    
    try:
        await bot.send_message(
            chat_id=config.GROUP_CHAT_ID,
            text=message,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Failed to send notification: {e}")


async def notify_member(bot: Bot, telegram_id: int, tasks: list[str]) -> None:
    """Send a direct message to a member about their tasks."""
    if not tasks:
        return
    
    tasks_list = "\n".join(f"• {task}" for task in tasks)
    message = (
        "🧹 *Your Cleaning Tasks This Week:*\n\n"
        f"{tasks_list}\n\n"
        "Don't forget to complete them! 💪"
    )
    
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=message,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Failed to notify member {telegram_id}: {e}")
