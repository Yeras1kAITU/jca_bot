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

# ИМПОРТ КЛАВИАТУР
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

# УЛУЧШЕННЫЙ ОБРАБОТЧИК НЕИЗВЕСТНЫХ КОМАНД
async def smart_unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Умный обработчик неизвестных команд"""
    print(f"\n🔍 SMART UNKNOWN COMMAND:")
    print(f"  Сообщение: '{update.message.text}'")
    print(f"  User_data keys: {list(context.user_data.keys())}")
    
    # ПРОВЕРКА 1: Если сообщение начинается с кнопки меню - игнорируем
    menu_buttons = ["👥", "📊", "➕", "👤", "📋", "❌"]
    if any(update.message.text.startswith(btn) for btn in menu_buttons):
        print(f"  Пропускаю - это кнопка меню")
        return
    
    # ПРОВЕРКА 2: Если в процессе ConversationHandler
    # Ключи, которые указывают на активный ConversationHandler
    conversation_keys = [
        "task_title", "task_description", "assign_to", 
        "selected_users", "available_members", "selection_message_id",
        "new_member_telegram", "new_member_full_name_ru", 
        "new_member_full_name_en", "new_member_group",
        "new_member_personality_type", "new_member_birth_date",
        "awaiting_input", "comment_task_id"
    ]
    
    # Проверяем специальные случаи для ConversationHandler
    # Случай 1: Мы в процессе выдачи задания и вводим название
    if "selected_users" in context.user_data and not context.user_data.get("task_title"):
        print(f"  Пропускаю - в процессе выдачи задания (ввод названия)")
        return
    
    # Случай 2: Мы в процессе выдачи задания и вводим описание
    if "task_title" in context.user_data and not context.user_data.get("task_description"):
        print(f"  Пропускаю - в процессе выдачи задания (ввод описания)")
        return
    
    # Случай 3: Мы в процессе добавления участника
    for key in ["new_member_telegram", "new_member_full_name_ru", "new_member_full_name_en",
                "new_member_group", "new_member_personality_type", "new_member_birth_date"]:
        if key in context.user_data:
            print(f"  Пропускаю - в процессе добавления участника (ключ: {key})")
            return
    
    # Если все проверки пройдены, обрабатываем как неизвестную команду
    await handle_unknown_command(update, context)

# ОБРАБОТЧИКИ КНОПОК ГЛАВНОГО МЕНЮ
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

# СПЕЦИАЛЬНЫЕ ОБРАБОТЧИКИ ДЛЯ ЗАПУСКА CONVERSATION HANDLER
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
    
    # ВАЖНО: Порядок приоритетов
    # 1. Callback handlers (inline кнопки)
    # 2. Кнопка отмены
    # 3. Команды
    # 4. Кнопки меню (которые запускают ConversationHandler)
    # 5. ConversationHandler (самый важный для текстового ввода)
    # 6. Остальные кнопки меню
    # 7. Неизвестные команды
    
    # 1. CALLBACK HANDLERS - самый высокий приоритет
    application.add_handler(CallbackQueryHandler(handle_task_view, pattern="^view_task_"))
    application.add_handler(CallbackQueryHandler(handle_task_status_change, pattern="^set_status"))
    application.add_handler(CallbackQueryHandler(handle_refresh_tasks, pattern="^refresh_tasks$"))
    application.add_handler(CallbackQueryHandler(handle_back_to_list, pattern="^back_to_tasks$"))
    application.add_handler(CallbackQueryHandler(handle_member_info_callback, pattern="^member_info_"))
    # Callback для ConversationHandler
    application.add_handler(CallbackQueryHandler(handle_multi_user_toggle, pattern="^toggle_user_"))
    application.add_handler(CallbackQueryHandler(confirm_multi_selection, pattern="^confirm_selection$"))
    application.add_handler(CallbackQueryHandler(cancel_assignment, pattern="^cancel_multi_select$"))
    print("✅ Callback обработчики добавлены")
    
    # 2. ГЛОБАЛЬНАЯ ОТМЕНА
    application.add_handler(MessageHandler(filters.Regex("^❌ Отмена$"), handle_cancel))
    application.add_handler(CommandHandler("cancel", handle_cancel))
    print("✅ Глобальный обработчик отмены добавлен")
    
    # 3. ОБРАБОТЧИКИ КОМАНД
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("test", test_command))
    print("✅ Командные обработчики добавлены")
    
    # 4. КНОПКИ, КОТОРЫЕ ЗАПУСКАЮТ CONVERSATION HANDLER
    # Они должны быть ДО ConversationHandler
    application.add_handler(MessageHandler(filters.Regex("^➕ Выдать задание$"), start_assign_task))
    application.add_handler(MessageHandler(filters.Regex("^👤 Добавить участника$"), start_add_member))
    print("✅ Кнопки запуска ConversationHandler добавлены")
    
    # 5. CONVERSATION HANDLERS - ВАЖНО: после кнопок запуска
    try:
        application.add_handler(assign_task_multi_conversation)
        application.add_handler(add_member_conversation)
        print("✅ Conversation handlers добавлены")
    except Exception as e:
        print(f"⚠️  Conversation handlers ошибка: {e}")
    
    # 6. ОСТАЛЬНЫЕ КНОПКИ ГЛАВНОГО МЕНЮ
    application.add_handler(MessageHandler(filters.Regex("^👥 Все члены клуба$"), handle_show_members))
    application.add_handler(MessageHandler(filters.Regex("^📊 Статус заданий$"), handle_view_tasks_status))
    application.add_handler(MessageHandler(filters.Regex("^📋 Мои задания$"), handle_show_my_tasks))
    application.add_handler(MessageHandler(filters.Regex("^👥 Информация о себе$"), handle_show_my_info))
    application.add_handler(MessageHandler(filters.Regex("^Панель администратора$"), handle_admin_dashboard))
    print("✅ Кнопки главного меню добавлены")
    
    # 7. УМНЫЙ ОБРАБОТЧИК НЕИЗВЕСТНЫХ КОМАНД - ПОСЛЕДНИЙ
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, smart_unknown_command))
    print("✅ Умный обработчик неизвестных команд добавлен")
    
    print("\n" + "=" * 60)
    print("✅ БОТ ЗАПУЩЕН!")
    print("=" * 60)
    print("🎯 Правильный порядок приоритетов:")
    print("  1. Callback handlers")
    print("  2. Отмена ❌")
    print("  3. Команды (/start, /help)")
    print("  4. Кнопки запуска ConversationHandler")
    print("  5. ConversationHandler (ввод текста)")
    print("  6. Остальные кнопки меню")
    print("  7. Неизвестные команды")
    print("=" * 60)
    
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()