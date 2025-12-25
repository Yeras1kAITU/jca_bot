# handlers/common_handlers.py
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from firebase_service import firebase_service
from keyboards import get_main_menu_keyboard
from config import config
import logging

firebase_service = firebase_service

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЕДИНСТВЕННАЯ функция /start"""
    print("\n" + "="*50)
    print("🚀 /start ВЫЗВАН!")
    
    username = update.effective_user.username
    chat_id = update.effective_chat.id
    
    print(f"👤 Username: @{username}")
    print(f"💬 Chat ID: {chat_id}")
    
    if not username:
        await update.message.reply_text("Установи username в настройках Telegram.")
        return
    
    # Ищем пользователя
    member = firebase_service.get_member_by_telegram(username)
    
    if member:
        print(f"✅ Найден: {member.full_name_ru}")
        print(f"📌 ID: {member.id}")
        print(f"💾 Текущий chat_id: {member.chat_id}")
        
        # СОХРАНЯЕМ CHAT_ID В FIREBASE
        try:
            print(f"💾 Сохраняю chat_id {chat_id}...")
            firebase_service.db.child("members").child(member.id).update({"chat_id": chat_id})
            print(f"✅ Chat_id сохранен в Firebase!")
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
        
        # Сохраняем данные в context
        is_admin = member.role in config.ADMIN_ROLES
        context.user_data["is_admin"] = is_admin
        context.user_data["member"] = member
        context.user_data["telegram_username"] = username
        
        # Приветствие
        welcome_text = f"Добро пожаловать, {member.full_name_ru}!"
        if is_admin:
            welcome_text += f"\n\nВы вошли как администратор ({member.role})."
        else:
            welcome_text += f"\n\nВы вошли как член клуба ({member.role})."
        
        await update.message.reply_text(welcome_text, reply_markup=get_main_menu_keyboard(is_admin))
        
    else:
        print(f"❌ Пользователь не найден в базе")
        await update.message.reply_text(
            f"Привет, {update.effective_user.first_name}!\n"
            f"Твой username: @{username}\n\n"
            "Ты не найден в базе данных членов клуба.\n"
            "Обратись к администратору для добавления."
        )
    
    print("="*50 + "\n")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /help"""
    help_text = (
        "🤖 **University Club Bot**\n\n"
        "**Основные команды:**\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n\n"
        
        "**Для членов клуба:**\n"
        "• 📋 Мои задания - Просмотр ваших заданий\n"
        "• 👥 Информация о себе - Ваша информация\n\n"
        
        "**Для администраторов:**\n"
        "• 👥 Все члены клуба - Список всех членов\n"
        "• 👤 Добавить участника - Добавить нового члена\n"
        "• ➕ Выдать задание - Назначить новое задание\n"
        "• 📊 Статус заданий - Обзор всех заданий\n"
        "• 🔔 Уведомления - Просмотр уведомлений\n\n"
        
        "**Работа с заданиями:**\n"
        "1. Администраторы назначают задания\n"
        "2. Члены клуба получают уведомления\n"
        "3. Члены обновляют статус заданий\n"
        "4. Администраторы получают уведомления об изменениях"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка неизвестных команд"""
    await update.message.reply_text(
        "Неизвестная команда. Используйте /help для просмотра доступных команд."
    )