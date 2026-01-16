# CleanrBot 🧹

A Telegram bot for managing weekly apartment cleaning duties with automatic task rotation, built with Python, aiogram, and PostgreSQL.

## Features

- **Interactive UI**: No complex commands—use buttons for everything.
- **Fair Rotation**: Automatically shuffles tasks every week so everyone contributes equally.
- **Smart Assignment**: Handles cases where there are more tasks than people (or vice versa).
- **Scheduled Notifications**: Sends weekly reminders to your group chat.
- **Easy Onboarding**: Share a "Join Link" to instantly add roommates.
- **Dockerized**: Easy to deploy with Docker Compose.

## Tech Stack

- **Framework**: [aiogram 3.x](https://docs.aiogram.dev/)
- **Database**: PostgreSQL (async via `asyncpg` + SQLAlchemy)
- **Scheduler**: APScheduler
- **Package Manager**: [uv](https://github.com/astral-sh/uv)
- **Deployment**: Docker & Docker Compose

## Quick Start

### Prerequisites
- Docker & Docker Compose
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

### 1. Setup Environment

```bash
cp .env.example .env
```

Edit `.env` and set your values:
- `BOT_TOKEN`: Your Telegram bot token.
- `SUPERUSER_ID`: Your Telegram user ID (get it from [@userinfobot](https://t.me/userinfobot)).
- `GROUP_CHAT_ID`: The ID of the group chat for notifications (optional, can be getting later).

### 2. Run with Docker

```bash
make build
make up
```

Your bot should now be running! Check logs with `make logs`.

## Usage Guide

### Getting Started
1. Start the bot: `/start`
2. You will see the **Main Menu**.

### Admin Panel (Superuser Only)
Click **[⚙️ Admin Panel]** to access management tools:
- **🔗 Share Join Link**: Generates a link (e.g., `t.me/mybot?start=register`). Send this to your roommates to add them.
- **👥 Manage Members**: Remove members if needed.
- **➕ Add Task**: Create cleaning tasks (e.g., "Kitchen", "Bathroom"). You'll specify how many people are needed for each.
- **🔀 Shuffle Now**: Manually trigger a shuffle to assign tasks immediately.

### For Roommates
- Click the **Join Link** shared by the admin to register.
- Click **[📅 My Schedule]** in the main menu to see their assigned tasks for the week.

## Development

The project uses `uv` for dependencies and includes a `Makefile` for convenience.

| Command | Description |
|---------|-------------|
| `make up` | Start containers in background |
| `make down` | Stop containers |
| `make logs` | View logs (alias: `make log`) |
| `make shell` | Open shell inside bot container |
| `make build` | Rebuild Docker images |

## License

MIT
