import logging
import sys
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from telegram.ext import ContextTypes
from config import config

# Добавьте путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

print("🔧 ЗАПУСК ПРОСТОГО РАБОЧЕГО БОТА")
print("=" * 60)

try:
    from handlers.common_handlers import start, help_command, handle_unknown_command
    print("✅ common_handlers загружен")
except ImportError as e:
    print(f"❌ Ошибка common_handlers: {e}")
    exit(1)

try:
    from handlers.admin_handlers import (
        admin_dashboard, show_all_members, view_tasks_status,
        handle_member_info_callback, 
        assign_task_multi_conversation,
        add_member_conversation,
        handle_multi_user_toggle,
        confirm_multi_selection,
        cancel_assignment,
        assign_task_multi_start,
        add_member_start,
        get_multi_task_details
    )
    print("✅ admin_handlers загружен")
except ImportError as e:
    print(f"❌ Ошибка admin_handlers: {e}")
    exit(1)

try:
    from handlers.member_handlers import (
        show_my_tasks, show_my_info,
        handle_task_view, handle_task_status_change,
        handle_refresh_tasks, handle_back_to_list
    )
    print("✅ member_handlers загружен")
except ImportError as e:
    print(f"❌ Ошибка member_handlers: {e}")
    exit(1)

# ИМПОРТ КЛАВИАТУР - ДОБАВЬТЕ ЭТО
try:
    from keyboards import get_main_menu_keyboard
    print("✅ keyboards загружен")
except ImportError as e:
    print(f"❌ Ошибка keyboards: {e}")
    exit(1)

print("\n🎯 НАСТРОЙКА CALLBACK ОБРАБОТЧИКОВ")
print("=" * 60)

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовая команда"""
    print("🎯 TEST COMMAND ВЫЗВАНА!")
    await update.message.reply_text("✅ Тестовая команда работает!")

# ТИХИЙ ГЛОБАЛЬНЫЙ ОБРАБОТЧИК ОТМЕНЫ - ТОЛЬКО СБРОС
async def global_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Глобальный обработчик отмены для всех состояний - ТИХАЯ ВЕРСИЯ"""
    print("\n🔍 ГЛОБАЛЬНАЯ ОТМЕНА (тихий сброс):")
    print(f"  Пользователь: @{update.effective_user.username}")
    
    # Сбрасываем только временные данные, не весь context
    keys_to_remove = [
        "task_title", "task_description", "assign_to", 
        "selected_users", "available_members", "selection_message_id",
        "new_member_telegram", "new_member_full_name_ru", 
        "new_member_full_name_en", "new_member_group",
        "new_member_personality_type", "new_member_birth_date",
        "awaiting_input", "comment_task_id"
    ]
    
    for key in keys_to_remove:
        if key in context.user_data:
            print(f"  Удаляю: {key}")
            context.user_data.pop(key, None)
    
    # Возвращаем ConversationHandler.END чтобы выйти из любого состояния
    return ConversationHandler.END

# ОБРАБОТЧИК КНОПКИ ОТМЕНЫ
async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки '❌ Отмена' - показывает сообщение"""
    await global_cancel(update, context)  # тихий сброс
    is_admin = context.user_data.get("is_admin", False)
    
    await update.message.reply_text(
        "✅ Операция отменена.",
        reply_markup=get_main_menu_keyboard(is_admin)
    )

# ИСПРАВЛЕННЫЙ ОБРАБОТЧИК НЕИЗВЕСТНЫХ КОМАНД
async def smart_unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Умный обработчик неизвестных команд - не срабатывает при активном ConversationHandler"""
    print(f"\n🔍 SMART UNKNOWN COMMAND:")
    print(f"  Сообщение: {update.message.text}")
    print(f"  User_data keys: {list(context.user_data.keys())}")
    
    # Проверяем, есть ли признаки активного ConversationHandler
    # Если есть ключи ConversationHandler, пропускаем обработку
    conversation_keys = [
        "task_title", "task_description", "assign_to", 
        "selected_users", "available_members", "selection_message_id",
        "new_member_telegram", "new_member_full_name_ru", 
        "new_member_full_name_en", "new_member_group",
        "new_member_personality_type", "new_member_birth_date",
        "awaiting_input", "comment_task_id"
    ]
    
    # Если есть любой из этих ключей, значит ConversationHandler активен
    for key in conversation_keys:
        if key in context.user_data:
            print(f"  Пропускаю - активен ConversationHandler (ключ: {key})")
            return  # НЕ ОБРАБАТЫВАЕМ, пусть ConversationHandler сам разберется
    
    # Иначе обрабатываем как неизвестную команду
    await handle_unknown_command(update, context)

# ОБЫЧНЫЕ ОБРАБОТЧИКИ КНОПОК ГЛАВНОГО МЕНЮ (БЕЗ СБРОСА)
async def handle_show_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать всех членов"""
    await show_all_members(update, context)

async def handle_show_my_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать мои задания"""
    await show_my_tasks(update, context)

async def handle_show_my_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать информацию о себе"""
    await show_my_info(update, context)

async def handle_view_tasks_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статус заданий"""
    await view_tasks_status(update, context)

async def handle_admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать админ панель"""
    await admin_dashboard(update, context)

# СПЕЦИАЛЬНЫЕ ОБРАБОТЧИКИ ДЛЯ ЗАПУСКА CONVERSATION HANDLER (СО СБРОСОМ)
async def start_assign_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать процесс выдачи задания"""
    await global_cancel(update, context)  # сброс перед началом
    return await assign_task_multi_start(update, context)

async def start_add_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать процесс добавления участника"""
    await global_cancel(update, context)  # сброс перед началом
    return await add_member_start(update, context)

def main():
    """Запуск простого рабочего бота"""
    print(f"Бот запускается...")
    
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # 0. CALLBACK HANDLERS - ВЫСШИЙ ПРИОРИТЕТ
    application.add_handler(CallbackQueryHandler(handle_task_view, pattern="^view_task_"))
    application.add_handler(CallbackQueryHandler(handle_task_status_change, pattern="^set_status"))
    application.add_handler(CallbackQueryHandler(handle_refresh_tasks, pattern="^refresh_tasks$"))
    application.add_handler(CallbackQueryHandler(handle_back_to_list, pattern="^back_to_tasks$"))
    application.add_handler(CallbackQueryHandler(handle_member_info_callback, pattern="^member_info_"))
    # Callback для выбора пользователей в ConversationHandler
    application.add_handler(CallbackQueryHandler(handle_multi_user_toggle, pattern="^toggle_user_"))
    application.add_handler(CallbackQueryHandler(confirm_multi_selection, pattern="^confirm_selection$"))
    application.add_handler(CallbackQueryHandler(cancel_assignment, pattern="^cancel_multi_select$"))
    print("✅ Callback обработчики добавлены")
    
    # 1. ГЛОБАЛЬНЫЙ ОБРАБОТЧИК ОТМЕНЫ
    application.add_handler(MessageHandler(filters.Regex("^❌ Отмена$"), handle_cancel))
    application.add_handler(CommandHandler("cancel", handle_cancel))
    print("✅ Глобальный обработчик отмены добавлен")
    
    # 2. Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("test", test_command))
    print("✅ Командные обработчики добавлены")
    
    # 3. CONVERSATION HANDLERS для админов - ВАЖНО: ДО обработчиков кнопок!
    try:
        # ConversationHandler для выдачи задания
        application.add_handler(assign_task_multi_conversation)
        # ConversationHandler для добавления участника
        application.add_handler(add_member_conversation)
        print("✅ Conversation handlers добавлены (ВЫСОКИЙ ПРИОРИТЕТ)")
    except Exception as e:
        print(f"⚠️  Conversation handlers ошибка: {e}")
    
    # 4. ОБРАБОТЧИКИ КНОПОК ГЛАВНОГО МЕНЮ - ПОСЛЕ ConversationHandler
    # Для администраторов
    admin_patterns = [
        ("^👥 Все члены клуба$", handle_show_members),
        ("^📊 Статус заданий$", handle_view_tasks_status),
        ("^➕ Выдать задание$", start_assign_task),
        ("^👤 Добавить участника$", start_add_member),
    ]
    
    for pattern, handler in admin_patterns:
        application.add_handler(MessageHandler(filters.Regex(pattern), handler))
    print("✅ Админские обработчики")
    
    # Для всех пользователей
    user_patterns = [
        ("^📋 Мои задания$", handle_show_my_tasks),
        ("^👥 Информация о себе$", handle_show_my_info),
    ]
    
    for pattern, handler in user_patterns:
        application.add_handler(MessageHandler(filters.Regex(pattern), handler))
    print("✅ Пользовательские обработчики")
    
    # 5. УМНЫЙ ОБРАБОТЧИК НЕИЗВЕСТНЫХ КОМАНД - САМЫЙ ПОСЛЕДНИЙ
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, smart_unknown_command))
    print("✅ Умный обработчик неизвестных команд добавлен")
    
    print("\n" + "=" * 60)
    print("✅ БОТ ЗАПУЩЕН!")
    print("=" * 60)
    print("🎯 ConversationHandler теперь имеет приоритет")
    print("=" * 60)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()