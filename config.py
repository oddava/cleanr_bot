import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    SUPERUSER_ID: int = int(os.getenv("SUPERUSER_ID", "0"))
    GROUP_CHAT_ID: int = int(os.getenv("GROUP_CHAT_ID", "0"))
    NOTIFICATION_DAY: int = int(os.getenv("NOTIFICATION_DAY", "0"))  # Monday
    NOTIFICATION_HOUR: int = int(os.getenv("NOTIFICATION_HOUR", "9"))
    TIMEZONE: str = os.getenv("TIMEZONE", "UTC")
    # Default to Postgres in Docker, fallback to sqlite locally if needed
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:postgres@localhost:5432/cleanr_bot"
    )


config = Config()
