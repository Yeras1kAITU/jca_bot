import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from telegram.ext import ContextTypes  # ← ВАЖНО!
from config import config
import sys
import pkg_resources  # Явный импорт для инициализации

# Принудительная инициализация pkg_resources
try:
    pkg_resources.require("setuptools>=65.5.0")
except pkg_resources.DistributionNotFound:
    pass

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
        add_member_conversation
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

print("\n🎯 НАСТРОЙКА CALLBACK ОБРАБОТЧИКОВ")
print("=" * 60)

# ТЕСТОВАЯ КОМАНДА (добавь перед main())
async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовая команда"""
    print("🎯 TEST COMMAND ВЫЗВАНА!")
    await update.message.reply_text("✅ Тестовая команда работает!")

def main():
    """Запуск простого рабочего бота"""
    print(f"🤖 Бот запускается...")
    
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # 1. Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("test", test_command))  # ← ДОБАВЬ ЭТУ СТРОКУ
    
    # 2. Conversation handlers для админов
    try:
        application.add_handler(assign_task_multi_conversation)
        application.add_handler(add_member_conversation)
        print("✅ Conversation handlers добавлены")
    except:
        print("⚠️  Conversation handlers пропущены")
    
    # 3. Callback handlers для заданий
    print("\n📌 Регистрация callback обработчиков:")
    
    application.add_handler(CallbackQueryHandler(handle_task_view, pattern="^view_task_"))
    print("✅ handle_task_view (view_task_)")
    
    application.add_handler(CallbackQueryHandler(handle_task_status_change, pattern="^set_status"))
    print("✅ handle_task_status_change (set_status)")
    
    application.add_handler(CallbackQueryHandler(handle_refresh_tasks, pattern="^refresh_tasks$"))
    print("✅ handle_refresh_tasks (refresh_tasks)")
    
    application.add_handler(CallbackQueryHandler(handle_back_to_list, pattern="^back_to_tasks$"))
    print("✅ handle_back_to_list (back_to_tasks)")
    
    application.add_handler(CallbackQueryHandler(handle_member_info_callback, pattern="^member_info_"))
    print("✅ handle_member_info_callback (member_info_)")
    
    # 4. Обработчики сообщений для администраторов
    admin_patterns = [
        ("^👥 Все члены клуба$", show_all_members),
        ("^📊 Статус заданий$", view_tasks_status),
        ("^➕ Выдать задание$", admin_dashboard),
        ("^👤 Добавить участника$", admin_dashboard)
    ]
    
    for pattern, handler in admin_patterns:
        application.add_handler(MessageHandler(filters.Regex(pattern), handler))
    print("✅ Админские обработчики")
    
    # 5. Обработчики сообщений для членов клуба
    application.add_handler(MessageHandler(filters.Regex("^📋 Мои задания$"), show_my_tasks))
    application.add_handler(MessageHandler(filters.Regex("^👥 Информация о себе$"), show_my_info))
    print("✅ Пользовательские обработчики")
    
    # 6. Обработчик неизвестных команд
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_command))
    print("✅ Обработчик неизвестных команд")
    
    print("\n" + "=" * 60)
    print("✅ БОТ ЗАПУЩЕН!")
    print("=" * 60)
    print("🎯 Теперь кнопки заданий должны работать")
    print("=" * 60)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()