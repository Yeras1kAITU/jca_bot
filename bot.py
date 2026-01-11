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
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)

logger = logging.getLogger(__name__)

print("🔧 ЗАПУСК БОТА")
print("=" * 60)

# Проверяем что нет другого экземпляра
import socket
try:
    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lock_socket.bind(('localhost', 12345))
    lock_socket.listen(1)
except socket.error:
    print("❌ Уже запущен другой экземпляр бота!")
    print("   Остановите его командой: pkill -f 'python.*bot.py'")
    sys.exit(1)

try:
    from handlers.common_handlers import start, help_command
    print("✅ common_handlers загружен")
except ImportError as e:
    print(f"❌ Ошибка common_handlers: {e}")
    sys.exit(1)

try:
    from handlers.admin_handlers import (
        show_all_members, view_tasks_status,
        handle_member_info_callback, 
        assign_task_multi_conversation,
        add_member_conversation
    )
    print("✅ admin_handlers загружен")
except ImportError as e:
    print(f"❌ Ошибка admin_handlers: {e}")
    sys.exit(1)

try:
    from handlers.member_handlers import (
        show_my_tasks, show_my_info,
        handle_task_view, handle_task_status_change,
        handle_refresh_tasks, handle_back_to_list
    )
    print("✅ member_handlers загружен")
except ImportError as e:
    print(f"❌ Ошибка member_handlers: {e}")
    sys.exit(1)

try:
    from keyboards import get_main_menu_keyboard
    print("✅ keyboards загружен")
except ImportError as e:
    print(f"❌ Ошибка keyboards: {e}")
    sys.exit(1)

async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Простой обработчик неизвестных команд"""
    await update.message.reply_text(
        "Используйте кнопки меню для навигации.",
        reply_markup=get_main_menu_keyboard(context.user_data.get("is_admin", False))
    )

async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик отмены"""
    await update.message.reply_text(
        "✅ Отменено.",
        reply_markup=get_main_menu_keyboard(context.user_data.get("is_admin", False))
    )
    return ConversationHandler.END

def main():
    """Главная функция запуска бота"""
    print("Создаю приложение...")
    
    # Создаем приложение
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Регистрируем обработчики в правильном порядке
    
    # 1. Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", handle_cancel))
    print("✅ Команды зарегистрированы")
    
    # 2. Conversation handlers (самый высокий приоритет для текстовых сообщений)
    application.add_handler(assign_task_multi_conversation)
    application.add_handler(add_member_conversation)
    print("✅ Conversation handlers зарегистрированы")
    
    # 3. Callback handlers (для inline кнопок)
    application.add_handler(CallbackQueryHandler(handle_task_view, pattern="^view_task_"))
    application.add_handler(CallbackQueryHandler(handle_task_status_change, pattern="^set_status"))
    application.add_handler(CallbackQueryHandler(handle_refresh_tasks, pattern="^refresh_tasks$"))
    application.add_handler(CallbackQueryHandler(handle_back_to_list, pattern="^back_to_tasks$"))
    application.add_handler(CallbackQueryHandler(handle_member_info_callback, pattern="^member_info_"))
    print("✅ Callback handlers зарегистрированы")
    
    # 4. Кнопки главного меню
    # Админские кнопки
    application.add_handler(MessageHandler(filters.Regex("^👥 Все члены клуба$"), show_all_members))
    application.add_handler(MessageHandler(filters.Regex("^📊 Статус заданий$"), view_tasks_status))
    
    # Пользовательские кнопки
    application.add_handler(MessageHandler(filters.Regex("^📋 Мои задания$"), show_my_tasks))
    application.add_handler(MessageHandler(filters.Regex("^👥 Информация о себе$"), show_my_info))
    
    # Кнопки для запуска ConversationHandler (должны быть после ConversationHandler!)
    application.add_handler(MessageHandler(filters.Regex("^➕ Выдать задание$"), handle_cancel))
    application.add_handler(MessageHandler(filters.Regex("^👤 Добавить участника$"), handle_cancel))
    print("✅ Кнопки меню зарегистрированы")
    
    # 5. Глобальная отмена
    application.add_handler(MessageHandler(filters.Regex("^❌ Отмена$"), handle_cancel))
    
    # 6. Обработчик всего остального (самый низкий приоритет)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown))
    
    print("\n" + "=" * 60)
    print("✅ ВСЕ ОБРАБОТЧИКИ ЗАРЕГИСТРИРОВАНЫ")
    print("=" * 60)
    print("\n📋 Порядок приоритетов:")
    print("1. Команды (/start, /help, /cancel)")
    print("2. ConversationHandler (добавление участника, выдача заданий)")
    print("3. Callback кнопки (inline кнопки)")
    print("4. Кнопки главного меню")
    print("5. Кнопка '❌ Отмена'")
    print("6. Неизвестные сообщения")
    print("=" * 60)
    
    # Запускаем бота
    print("\n🚀 Запускаю бота...")
    print("Нажмите Ctrl+C для остановки")
    print("=" * 60)
    
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            close_loop=False
        )
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        logger.exception("Критическая ошибка при запуске бота")
    finally:
        lock_socket.close()

if __name__ == '__main__':
    main()