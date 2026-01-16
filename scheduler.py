import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from sqlalchemy import select

from database import async_session, Settings
from config import config
from services.assignment import shuffle_assignments
from services.notifier import send_weekly_notification


scheduler = AsyncIOScheduler()


async def weekly_shuffle_and_notify(bot: Bot):
    """Weekly job: shuffle assignments and send notifications."""
    async with async_session() as session:
        # Shuffle assignments
        await shuffle_assignments(session)
        
        # Send notification to group
        await send_weekly_notification(bot, session)


async def get_notification_settings() -> tuple[int, int]:
    """Get notification day and hour from database or config."""
    async with async_session() as session:
        day_result = await session.execute(
            select(Settings).where(Settings.key == "notification_day")
        )
        hour_result = await session.execute(
            select(Settings).where(Settings.key == "notification_hour")
        )
        
        day_setting = day_result.scalar_one_or_none()
        hour_setting = hour_result.scalar_one_or_none()
        
        day = int(day_setting.value) if day_setting else config.NOTIFICATION_DAY
        hour = int(hour_setting.value) if hour_setting else config.NOTIFICATION_HOUR
        
        return day, hour


def setup_scheduler(bot: Bot):
    """Setup the scheduler with weekly jobs."""
    async def run_job():
        await weekly_shuffle_and_notify(bot)
    
    async def update_schedule():
        """Update the scheduler with current settings."""
        day, hour = await get_notification_settings()
        
        # Remove existing job if any
        try:
            scheduler.remove_job("weekly_notification")
        except:
            pass
        
        # APScheduler uses 0=Monday, which matches our config
        # CronTrigger day_of_week: 0=Monday, 6=Sunday
        scheduler.add_job(
            run_job,
            CronTrigger(day_of_week=day, hour=hour, minute=0),
            id="weekly_notification",
            replace_existing=True
        )
        print(f"Scheduler set for day {day}, hour {hour}")
    
    # Schedule the update
    asyncio.get_event_loop().create_task(update_schedule())
    
    return scheduler


def start_scheduler():
    """Start the scheduler."""
    if not scheduler.running:
        scheduler.start()


def stop_scheduler():
    """Stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
