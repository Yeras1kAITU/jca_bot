# keyboards.py - ОБНОВЛЕННАЯ ВЕРСИЯ
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from config import config
from models import TaskStatus


def get_main_menu_keyboard(is_admin: bool):
    """Главное меню в зависимости от роли"""
    if is_admin:
        keyboard = [
            ["📋 Мои задания", "👥 Все члены клуба"],
            ["➕ Выдать задание", "👤 Добавить участника"],
            ["📊 Статус заданий"]
        ]
    else:
        keyboard = [
            ["📋 Мои задания"],
            ["👥 Информация о себе"]
        ]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_task_status_keyboard(task_id: str):
    """Клавиатура для изменения статуса задания - С ИСПРАВЛЕННЫМ ФОРМАТОМ"""
    keyboard = [
        [
            InlineKeyboardButton("🟡 Не начато", 
                callback_data=f"set_status|{task_id}|NOT"),
            InlineKeyboardButton("🟠 В процессе", 
                callback_data=f"set_status|{task_id}|IN"),
        ],
        [
            InlineKeyboardButton("🟢 Завершено", 
                callback_data=f"set_status|{task_id}|COMPLETED")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_members_keyboard(members, action: str = "info"):
    """Клавиатура со списком членов клуба"""
    keyboard = []
    for member in members:
        button_text = f"{member.full_name_ru} ({member.telegram_username})"
        callback_data = f"{action}_{member.telegram_username}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    return InlineKeyboardMarkup(keyboard)


def get_task_selection_keyboard(tasks, action: str = "view"):
    """Клавиатура для выбора задания"""
    keyboard = []
    for task in tasks:
        button_text = f"{task.title} ({config.TASK_STATUSES[task.status]})"
        callback_data = f"{action}_task_{task.id}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    return InlineKeyboardMarkup(keyboard)

def get_multi_member_selection_keyboard(members, selected_users=None):
    """Клавиатура для выбора нескольких участников"""
    if selected_users is None:
        selected_users = []
    
    keyboard = []
    
    for member in members:
        # Добавляем галочку если пользователь выбран
        if not member.telegram_username:
            continue
            
        prefix = "✅ " if member.telegram_username in selected_users else "☐ "
        button_text = f"{prefix}{member.full_name_ru} (@{member.telegram_username})"
        callback_data = f"toggle_user_{member.telegram_username}"
        
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    # Кнопки действий
    action_row = []
    if selected_users:
        action_row.append(InlineKeyboardButton(
            f"📋 Выбрано: {len(selected_users)}", 
            callback_data="show_selected"
        ))
        action_row.append(InlineKeyboardButton(
            "✅ Готово", 
            callback_data="confirm_selection"
        ))
    
    if action_row:
        keyboard.append(action_row)
    
    keyboard.append([
        InlineKeyboardButton("❌ Отмена", callback_data="cancel_multi_select")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_cancel_keyboard():
    """Клавиатура для отмены действия"""
    keyboard = [["❌ Отмена"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)