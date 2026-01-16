from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from config import config
from database import async_session, Member, Task, Settings
from services.assignment import shuffle_assignments, format_assignments_table
from services.notifier import send_weekly_notification
from keyboards import get_admin_panel, get_member_management_keyboard, get_task_management_keyboard

router = Router()


class AddTaskStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_count = State()


def is_superuser(user_id: int) -> bool:
    return user_id == config.SUPERUSER_ID


@router.callback_query(F.data == "admin_panel")
async def cb_admin_panel(callback: CallbackQuery):
    if not is_superuser(callback.from_user.id):
        await callback.answer("⛔ Admins only!", show_alert=True)
        return
        
    await callback.message.edit_text(
        "⚙️ *Admin Panel*", 
        reply_markup=get_admin_panel(),
        parse_mode="Markdown"
    )


# ============== Member Management ==============

@router.callback_query(F.data == "share_join")
async def cb_share_join(callback: CallbackQuery):
    bot_info = await callback.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start=register"
    
    await callback.message.answer(
        f"🔗 *Share this link with your roommates:*\n\n`{link}`\n\nThey just need to click it and press Start.",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "manage_members")
async def cb_manage_members(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(Member).order_by(Member.name))
        members = result.scalars().all()
        
        await callback.message.edit_text(
            "👥 *Tap a member to remove them:*",
            reply_markup=get_member_management_keyboard(members),
            parse_mode="Markdown"
        )


@router.callback_query(F.data.startswith("remove_member_"))
async def cb_remove_member(callback: CallbackQuery):
    member_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        member = await session.get(Member, member_id)
        if member:
            await session.delete(member)
            await session.commit()
            await callback.answer(f"Removed {member.name}")
        else:
            await callback.answer("Member not found")
            
    # Refresh list
    await cb_manage_members(callback)


# ============== Task Management ==============

@router.callback_query(F.data == "add_task")
async def cb_add_task_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📝 Enter the name of the new task:")
    await state.set_state(AddTaskStates.waiting_for_name)
    await callback.answer()


@router.message(AddTaskStates.waiting_for_name)
async def process_task_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("🔢 How many people are needed for this task? (Enter a number)")
    await state.set_state(AddTaskStates.waiting_for_count)


@router.message(AddTaskStates.waiting_for_count)
async def process_task_count(message: Message, state: FSMContext):
    try:
        count = int(message.text)
        if count < 1: raise ValueError()
    except ValueError:
        await message.answer("❌ Please enter a valid positive number.")
        return

    data = await state.get_data()
    name = data['name']
    
    async with async_session() as session:
        existing = await session.execute(select(Task).where(Task.name == name))
        if existing.scalar_one_or_none():
            await message.answer(f"⚠️ Task '{name}' already exists.")
        else:
            task = Task(name=name, required_people=count)
            session.add(task)
            await session.commit()
            await message.answer(f"✅ Created task: *{name}* ({count} people)", parse_mode="Markdown")
            
    await state.clear()
    # Go back to admin panel
    await message.answer("⚙️ *Admin Panel*", reply_markup=get_admin_panel(), parse_mode="Markdown")


@router.callback_query(F.data == "remove_task")
async def cb_remove_task_list(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(Task).order_by(Task.name))
        tasks = result.scalars().all()
        
        await callback.message.edit_text(
            "📝 *Tap a task to remove it:*",
            reply_markup=get_task_management_keyboard(tasks),
            parse_mode="Markdown"
        )


@router.callback_query(F.data.startswith("remove_task_"))
async def cb_remove_task_action(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        task = await session.get(Task, task_id)
        if task:
            await session.delete(task)
            await session.commit()
            await callback.answer(f"Removed {task.name}")
            
    await cb_remove_task_list(callback)


# ============== Shuffle & Actions ==============

@router.message(Command("shuffle"))
async def cmd_shuffle(message: Message):
    """Manually trigger assignment shuffle."""
    if not is_superuser(message.from_user.id):
        await message.answer("⛔ This command is for admins only.")
        return
    
    async with async_session() as session:
        assignments = await shuffle_assignments(session)
        
        if not assignments:
            # Check why it failed
            from services.assignment import get_active_members, get_active_tasks
            members = await get_active_members(session)
            tasks = await get_active_tasks(session)
            
            error_msg = "⚠️ *Cannot shuffle yet!*"
            if not members:
                error_msg += "\n• No active members found. Share the join link!"
            if not tasks:
                error_msg += "\n• No tasks found. Add some tasks first."
                
            await message.answer(error_msg, parse_mode="Markdown")
            return

        schedule = format_assignments_table(assignments)
        
        await message.answer(
            f"🔀 *Assignments Shuffled!*\n\n{schedule}",
            parse_mode="Markdown"
        )


@router.callback_query(F.data == "shuffle_now")
async def cb_shuffle_now(callback: CallbackQuery):
    async with async_session() as session:
        assignments = await shuffle_assignments(session)
        
        if not assignments:
            # Check why it failed
            from services.assignment import get_active_members, get_active_tasks
            members = await get_active_members(session)
            tasks = await get_active_tasks(session)
            
            error_msg = "⚠️ *Cannot shuffle yet!*"
            if not members:
                error_msg += "\n• No active members found. Share the join link!"
            if not tasks:
                error_msg += "\n• No tasks found. Add some tasks first."
            
            await callback.message.answer(error_msg, parse_mode="Markdown")
        else:
            schedule = format_assignments_table(assignments)
            await callback.message.answer(
                f"🔀 *Assignments Shuffled!*\n\n{schedule}",
                parse_mode="Markdown"
            )
    await callback.answer()


@router.callback_query(F.data == "test_notification")
async def cb_test_notification(callback: CallbackQuery):
    async with async_session() as session:
        await send_weekly_notification(callback.bot, session)
        await callback.answer("Notification sent!")

