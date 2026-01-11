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
    
    # ПРИНУДИТЕЛЬНЫЙ СБРОС ВСЕХ СОСТОЯНИЙ
    # 1. Очищаем user_data кроме ключевых данных
    important_keys = ["is_admin", "member", "telegram_username"]
    important_data = {}
    
    for key in important_keys:
        if key in context.user_data:
            important_data[key] = context.user_data[key]
            print(f"  Сохраняю: {key} = {context.user_data[key]}")
    
    # 2. Полностью очищаем user_data
    context.user_data.clear()
    print("  User_data очищен")
    
    # 3. Восстанавливаем важные данные
    context.user_data.update(important_data)
    
    # 4. Возвращаем ConversationHandler.END чтобы выйти из любого состояния
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

# ОБЕРТКИ ДЛЯ КНОПОК ГЛАВНОГО МЕНЮ С ПРИНУДИТЕЛЬНЫМ СБРОСОМ
async def reset_and_show_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбросить состояние и показать всех членов"""
    await global_cancel(update, context)  # ТИХИЙ сброс
    await show_all_members(update, context)

async def reset_and_show_my_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбросить состояние и показать мои задания"""
    await global_cancel(update, context)  # ТИХИЙ сброс
    await show_my_tasks(update, context)

async def reset_and_show_my_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбросить состояние и показать информацию о себе"""
    await global_cancel(update, context)  # ТИХИЙ сброс
    await show_my_info(update, context)

async def reset_and_view_tasks_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбросить состояние и показать статус заданий"""
    await global_cancel(update, context)  # ТИХИЙ сброс
    await view_tasks_status(update, context)

async def reset_and_admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбросить состояние и показать админ панель"""
    await global_cancel(update, context)  # ТИХИЙ сброс
    await admin_dashboard(update, context)

# СПЕЦИАЛЬНЫЕ ОБЕРТКИ ДЛЯ ЗАПУСКА CONVERSATION HANDLER
async def start_assign_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать процесс выдачи задания"""
    await global_cancel(update, context)  # ТИХИЙ сброс
    # Теперь нужно запустить ConversationHandler
    from handlers.admin_handlers import assign_task_multi_start
    return await assign_task_multi_start(update, context)

async def start_add_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать процесс добавления участника"""
    await global_cancel(update, context)  # ТИХИЙ сброс
    # Теперь нужно запустить ConversationHandler
    from handlers.admin_handlers import add_member_start
    return await add_member_start(update, context)

def main():
    """Запуск простого рабочего бота"""
    print(f"Бот запускается...")
    
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # 0. ГЛОБАЛЬНЫЙ ОБРАБОТЧИК ОТМЕНЫ - ВЫСШИЙ ПРИОРИТЕТ
    application.add_handler(MessageHandler(filters.Regex("^❌ Отмена$"), handle_cancel))
    application.add_handler(CommandHandler("cancel", handle_cancel))
    print("✅ Глобальный обработчик отмены добавлен")
    
    # 1. Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("test", test_command))
    print("✅ Командные обработчики добавлены")
    
    # 2. ОБРАБОТЧИКИ КНОПОК ГЛАВНОГО МЕНЮ С СБРОСОМ СОСТОЯНИЯ
    # Для администраторов
    admin_patterns = [
        ("^👥 Все члены клуба$", reset_and_show_members),
        ("^📊 Статус заданий$", reset_and_view_tasks_status),
        ("^➕ Выдать задание$", start_assign_task),  # СПЕЦИАЛЬНЫЙ обработчик для запуска ConversationHandler
        ("^👤 Добавить участника$", start_add_member),  # СПЕЦИАЛЬНЫЙ обработчик для запуска ConversationHandler
    ]
    
    for pattern, handler in admin_patterns:
        application.add_handler(MessageHandler(filters.Regex(pattern), handler))
    print("✅ Админские обработчики с сбросом состояния")
    
    # Для всех пользователей
    user_patterns = [
        ("^📋 Мои задания$", reset_and_show_my_tasks),
        ("^👥 Информация о себе$", reset_and_show_my_info),
    ]
    
    for pattern, handler in user_patterns:
        application.add_handler(MessageHandler(filters.Regex(pattern), handler))
    print("✅ Пользовательские обработчики с сбросом состояния")
    
    # 3. CONVERSATION HANDLERS для админов (ТЕПЕРЬ ПОСЛЕ основных обработчиков)
    try:
        # ConversationHandler для выдачи задания
        application.add_handler(assign_task_multi_conversation)
        # ConversationHandler для добавления участника
        application.add_handler(add_member_conversation)
        print("✅ Conversation handlers добавлены")
    except Exception as e:
        print(f"⚠️  Conversation handlers ошибка: {e}")
    
    # 4. CALLBACK HANDLERS для заданий
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
    
    # 5. Обработчик неизвестных команд
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_command))
    print("✅ Обработчик неизвестных команд")
    
    print("\n" + "=" * 60)
    print("✅ БОТ ЗАПУЩЕН!")
    print("=" * 60)
    print("🎯 Теперь кнопки главного меню будут работать правильно")
    print("=" * 60)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()