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
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

print("🔧 ЗАПУСК ПРОСТОГО РАБОЧЕГО БОТА")
print("=" * 60)

try:
    # Попробуйте импортировать с исправленным путем
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from handlers.common_handlers import start, help_command, handle_unknown_command
    print("✅ common_handlers загружен")
except ImportError as e:
    print(f"❌ Ошибка common_handlers: {e}")
    print(f"   Путь поиска: {sys.path}")
    # Создаем простые заглушки
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Бот работает! (базовый режим)")
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Помощь: /start")
    async def handle_unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Неизвестная команда. Используйте /start")

try:
    from handlers.admin_handlers import (
        admin_dashboard, show_all_members, view_tasks_status,
        handle_member_info_callback, 
        assign_task_multi_conversation,
        add_member_conversation
    )
    print("✅ admin_handlers загружен")
except ImportError as e:
    print(f"⚠️  admin_handlers не загружен: {e}")
    # Заглушки для админских функций
    async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Админ панель")
    async def show_all_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Список членов")
    # и т.д.

try:
    from handlers.member_handlers import (
        show_my_tasks, show_my_info,
        handle_task_view, handle_task_status_change,
        handle_refresh_tasks, handle_back_to_list
    )
    print("✅ member_handlers загружен")
except ImportError as e:
    print(f"⚠️  member_handlers не загружен: {e}")
    # Заглушки для функций членов

print("\n🎯 НАСТРОЙКА CALLBACK ОБРАБОТЧИКОВ")
print("=" * 60)

# ТЕСТОВАЯ КОМАНДА
async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовая команда"""
    print("🎯 TEST COMMAND ВЫЗВАНА!")
    await update.message.reply_text("✅ Тестовая команда работает!")

def main():
    """Запуск простого рабочего бота"""
    print(f"🤖 Бот запускается...")
    
    # Проверяем токен
    if not config.BOT_TOKEN:
        print("❌ ОШИБКА: BOT_TOKEN не установлен!")
        print("   Установите переменную окружения BOT_TOKEN")
        sys.exit(1)
    
    try:
        application = Application.builder().token(config.BOT_TOKEN).build()
        
        # 1. Обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("test", test_command))
        
        # 2. Conversation handlers для админов (если есть)
        try:
            application.add_handler(assign_task_multi_conversation)
            application.add_handler(add_member_conversation)
            print("✅ Conversation handlers добавлены")
        except NameError:
            print("⚠️  Conversation handlers пропущены")
        
        # 3. Callback handlers для заданий (если есть)
        try:
            application.add_handler(CallbackQueryHandler(handle_task_view, pattern="^view_task_"))
            application.add_handler(CallbackQueryHandler(handle_task_status_change, pattern="^set_status"))
            application.add_handler(CallbackQueryHandler(handle_refresh_tasks, pattern="^refresh_tasks$"))
            application.add_handler(CallbackQueryHandler(handle_back_to_list, pattern="^back_to_tasks$"))
            application.add_handler(CallbackQueryHandler(handle_member_info_callback, pattern="^member_info_"))
            print("✅ Callback handlers добавлены")
        except NameError:
            print("⚠️  Callback handlers пропущены")
        
        # 4. Обработчики сообщений (если есть)
        try:
            admin_patterns = [
                ("^👥 Все члены клуба$", show_all_members),
                ("^📊 Статус заданий$", view_tasks_status),
                ("^➕ Выдать задание$", admin_dashboard),
                ("^👤 Добавить участника$", admin_dashboard)
            ]
            
            for pattern, handler in admin_patterns:
                application.add_handler(MessageHandler(filters.Regex(pattern), handler))
            
            application.add_handler(MessageHandler(filters.Regex("^📋 Мои задания$"), show_my_tasks))
            application.add_handler(MessageHandler(filters.Regex("^👥 Информация о себе$"), show_my_info))
            
            print("✅ Message handlers добавлены")
        except NameError:
            print("⚠️  Message handlers пропущены")
        
        # 6. Обработчик неизвестных команд
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_command))
        print("✅ Обработчик неизвестных команд")
        
        print("\n" + "=" * 60)
        print("✅ БОТ ЗАПУЩЕН!")
        print("=" * 60)
        
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
        
    except Exception as e:
        print(f"💥 Критическая ошибка при запуске: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()