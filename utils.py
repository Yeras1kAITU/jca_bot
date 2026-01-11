from telegram import ReplyKeyboardMarkup
from keyboards import get_main_menu_keyboard

def get_cancel_keyboard():
    """Клавиатура только с кнопкой отмены"""
    keyboard = [["❌ Отмена"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def cleanup_context(context):
    """Очистка временных данных из context.user_data"""
    keys_to_remove = [
        "task_title", "task_description", "assign_to", 
        "selected_users", "available_members", "selection_message_id",
        "new_member_telegram", "new_member_full_name_ru", 
        "new_member_full_name_en", "new_member_group",
        "new_member_personality_type", "new_member_birth_date",
        "awaiting_input", "comment_task_id", "current_state"
    ]
    
    for key in keys_to_remove:
        context.user_data.pop(key, None)