from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart, CommandObject

from database import async_session, select, Member
from services.assignment import get_formatted_schedule, get_member_assignments
from keyboards import get_main_menu
from config import config

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    """Handle /start command. Supports deep linking for registration."""
    # Check for deep link parameters
    args = command.args
    
    if args == "register":
        # Registration flow
        telegram_id = message.from_user.id
        name = message.from_user.first_name
        username = message.from_user.username
        
        async with async_session() as session:
            existing = await session.execute(
                select(Member).where(Member.telegram_id == telegram_id)
            )
            if existing.scalar_one_or_none():
                await message.answer("✅ You are already registered!")
            else:
                member = Member(telegram_id=telegram_id, name=name, username=username)
                session.add(member)
                await session.commit()
                await message.answer(f"✅ Welcome *{name}*! You have been added to the cleaning rota.", parse_mode="Markdown")
        
        # Show main menu after registration
        await message.answer(
            "🏠 *Main Menu*",
            reply_markup=get_main_menu(is_admin=message.from_user.id == config.SUPERUSER_ID),
            parse_mode="Markdown"
        )
        return

    # Normal start
    await message.answer(
        "👋 *Welcome to CleanrBot!*\n\n"
        "I help manage weekly apartment cleaning duties.",
        reply_markup=get_main_menu(is_admin=message.from_user.id == config.SUPERUSER_ID),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏠 *Main Menu*",
        reply_markup=get_main_menu(is_admin=callback.from_user.id == config.SUPERUSER_ID),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "full_schedule")
async def cb_schedule(callback: CallbackQuery):
    async with async_session() as session:
        schedule = await get_formatted_schedule(session)
        # Append "Back" button by creating a temporary keyboard or just sending a new message
        # For simplicity, edit message and keep main menu button? 
        # Better: Send as answer-alert or edit text and add Back button.
        
        # Let's edit text and add a Back button
        from keyboards import get_main_menu # simplified back flow
        back_kb = get_main_menu(is_admin=callback.from_user.id == config.SUPERUSER_ID)
        
        await callback.message.edit_text(schedule, reply_markup=back_kb, parse_mode="Markdown")


@router.callback_query(F.data == "my_schedule")
async def cb_my_tasks(callback: CallbackQuery):
    async with async_session() as session:
        assignments = await get_member_assignments(session, callback.from_user.id)
        
        back_kb = get_main_menu(is_admin=callback.from_user.id == config.SUPERUSER_ID)
        
        if not assignments:
            await callback.message.edit_text(
                "✨ You have no tasks assigned this week!",
                reply_markup=back_kb,
                parse_mode="Markdown"
            )
            return
        
        tasks = [a.task.name for a in assignments]
        tasks_list = "\n".join(f"• {task}" for task in tasks)
        
        await callback.message.edit_text(
            f"🧹 *Your Tasks This Week:*\n\n{tasks_list}",
            reply_markup=back_kb,
            parse_mode="Markdown"
        )
