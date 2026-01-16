from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Common buttons
    builder.row(
        InlineKeyboardButton(text="📅 My Schedule", callback_data="my_schedule"),
        InlineKeyboardButton(text="📋 Full Schedule", callback_data="full_schedule")
    )
    
    # Admin button
    if is_admin:
        builder.row(InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin_panel"))
    
    return builder.as_markup()


def get_admin_panel() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🔗 Share Join Link", callback_data="share_join"),
        InlineKeyboardButton(text="👥 Manage Members", callback_data="manage_members")
    )
    builder.row(
        InlineKeyboardButton(text="➕ Add Task", callback_data="add_task"),
        InlineKeyboardButton(text="➖ Remove Task", callback_data="remove_task")
    )
    builder.row(
        InlineKeyboardButton(text="🔀 Shuffle Now", callback_data="shuffle_now"),
        InlineKeyboardButton(text="🔔 Test Notification", callback_data="test_notification")
    )
    builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="main_menu"))
    
    return builder.as_markup()


def get_member_management_keyboard(members: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for member in members:
        builder.row(InlineKeyboardButton(
            text=f"❌ {member.name}", 
            callback_data=f"remove_member_{member.id}"
        ))
        
    builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="admin_panel"))
    return builder.as_markup()


def get_task_management_keyboard(tasks: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for task in tasks:
        builder.row(InlineKeyboardButton(
            text=f"❌ {task.name}", 
            callback_data=f"remove_task_{task.id}"
        ))
        
    builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="admin_panel"))
    return builder.as_markup()
