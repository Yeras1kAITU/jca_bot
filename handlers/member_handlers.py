# handlers/member_handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from firebase_service import firebase_service
from keyboards import get_main_menu_keyboard, get_task_status_keyboard, get_task_selection_keyboard
from models import TaskStatus
import datetime


async def show_my_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать задания текущего пользователя - ОБНОВЛЕННАЯ для словаря статусов"""
    telegram_username = context.user_data.get("telegram_username")
    
    if not telegram_username:
        await update.message.reply_text("Ошибка: пользователь не идентифицирован.")
        return
    
    tasks = firebase_service.get_member_tasks(telegram_username)
    
    if not tasks:
        await update.message.reply_text("У вас нет активных заданий.")
        return
    
    print(f"\n🔍 ДЕБАГ show_my_tasks для @{telegram_username}:")
    print(f"  Найдено заданий: {len(tasks)}")
    
    # Показываем все задания
    for i, task in enumerate(tasks, 1):
        print(f"  {i}. ID: {task.id}, Title: {task.title}")
    
    # Создаем клавиатуру
    keyboard = []
    
    for task in tasks:
        # Получаем статус для текущего пользователя
        if isinstance(task.status, dict):
            # Новый формат: словарь статусов
            user_status = task.status.get(telegram_username)
            if isinstance(user_status, str):
                try:
                    user_status = TaskStatus(user_status)
                except:
                    user_status = TaskStatus.NOT_STARTED
        else:
            # Старый формат: один статус для всех
            user_status = task.status
        
        # Эмодзи в зависимости от статуса
        if not isinstance(user_status, TaskStatus):
            user_status = TaskStatus.NOT_STARTED
        
        status_emoji = {
            TaskStatus.NOT_STARTED: "🟡",
            TaskStatus.IN_PROGRESS: "🟠",
            TaskStatus.COMPLETED: "🟢"
        }[user_status]
        
        task_title = task.title[:30] + "..." if len(task.title) > 30 else task.title
        button_text = f"{status_emoji} {task_title}"
        callback_data = f"view_task_{task.id}"
        
        print(f"  Кнопка: {button_text}")
        print(f"  Callback data: {callback_data}")
        print(f"  Статус пользователя: {user_status}")
        
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    # Добавляем кнопку обновления
    keyboard.append([InlineKeyboardButton("🔄 Обновить список", callback_data="refresh_tasks")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📋 *Ваши задания:*\n\nВыберите задание для просмотра и изменения статуса:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def handle_task_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать детали задания - С HTML форматированием"""
    query = update.callback_query
    await query.answer()
    
    print(f"\n🔍 ДЕБАГ handle_task_view:")
    print(f"  Callback data: {query.data}")
    print(f"  User: @{context.user_data.get('telegram_username', 'unknown')}")
    
    if query.data.startswith("view_task_"):
        task_id = query.data.replace("view_task_", "")
        
        task = firebase_service.get_task(task_id)
        
        if not task:
            await query.edit_message_text("❌ Задание не найдено.")
            return
        
        # Получаем текущего пользователя
        telegram_username = context.user_data.get("telegram_username")
        
        if not telegram_username:
            await query.edit_message_text("❌ Ошибка: пользователь не идентифицирован.")
            return
        
        # Получаем статус для текущего пользователя
        if isinstance(task.status, dict):
            user_status = task.status.get(telegram_username)
            if isinstance(user_status, str):
                try:
                    user_status = TaskStatus(user_status)
                except:
                    user_status = TaskStatus.NOT_STARTED
            elif not isinstance(user_status, TaskStatus):
                user_status = TaskStatus.NOT_STARTED
        else:
            user_status = task.status if isinstance(task.status, TaskStatus) else TaskStatus.NOT_STARTED
        
        print(f"  Статус пользователя @{telegram_username}: {user_status}")
        
        # Тексты статусов
        status_texts = {
            TaskStatus.NOT_STARTED: "🟡 Не начато",
            TaskStatus.IN_PROGRESS: "🟠 В процессе",
            TaskStatus.COMPLETED: "🟢 Завершено"
        }
        
        # Функция для экранирования HTML
        def escape_html(text):
            if not text:
                return ""
            return (str(text)
                    .replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                    .replace('"', '&quot;')
                    .replace("'", '&#39;'))
        
        # Экранируем все текстовые поля
        safe_title = escape_html(task.title)
        safe_description = escape_html(task.description) if task.description else ""
        safe_assigned_by = escape_html(task.assigned_by)
        safe_created_at = escape_html(task.created_at)
        safe_deadline = escape_html(task.deadline) if task.deadline else ""
        
        # Формируем информацию о задании в HTML
        task_info = f"📋 <b>{safe_title}</b>\n\n{status_texts[user_status]}"
        
        if safe_description:
            task_info += f"\n\n📝 <b>Описание:</b>\n{safe_description}"
        
        # Показываем кому выдано задание
        if isinstance(task.assigned_to, list):
            if len(task.assigned_to) == 1:
                safe_assigned_to = escape_html(task.assigned_to[0])
                task_info += f"\n\n👤 <b>Исполнитель:</b> @{safe_assigned_to}"
            else:
                task_info += f"\n\n👥 <b>Исполнители:</b> {len(task.assigned_to)} человек"
                for i, username in enumerate(task.assigned_to[:3], 1):
                    safe_username = escape_html(username)
                    task_info += f"\n  {i}. @{safe_username}"
                if len(task.assigned_to) > 3:
                    task_info += f"\n  ... и еще {len(task.assigned_to) - 3}"
        else:
            safe_assigned_to = escape_html(task.assigned_to)
            task_info += f"\n\n👤 <b>Исполнитель:</b> @{safe_assigned_to}"
        
        task_info += f"\n👑 <b>Выдал:</b> @{safe_assigned_by}"
        task_info += f"\n🕐 <b>Создано:</b> {safe_created_at}"
        
        if safe_deadline:
            task_info += f"\n📅 <b>Дедлайн:</b> {safe_deadline}"
        
        # Создаем клавиатуру
        keyboard = [
            [
                InlineKeyboardButton("🟡 Не начато", 
                    callback_data=f"set_status|{task_id}|NOT"),
                InlineKeyboardButton("🟠 В процессе", 
                    callback_data=f"set_status|{task_id}|IN"),
                InlineKeyboardButton("🟢 Завершено", 
                    callback_data=f"set_status|{task_id}|COMPLETED")
            ],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_tasks")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                task_info,
                parse_mode='HTML',  # ← Используем HTML вместо Markdown
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            await query.message.reply_text(
                task_info,
                parse_mode='HTML',
                reply_markup=reply_markup
            )


async def handle_task_status_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка изменения статуса задания - ИСПРАВЛЕННЫЙ ФОРМАТ с |"""
    query = update.callback_query
    await query.answer()
    
    print(f"\n🔍 ДЕБАГ handle_task_status_change:")
    print(f"  Callback data: {query.data}")
    print(f"  User data: {context.user_data}")
    
    if query.data.startswith("set_status|"):
        # Используем разделитель |
        parts = query.data.split("|")
        print(f"  Parts (|): {parts}")
        
        if len(parts) == 3:  # set_status|task_id|status_code
            task_id = parts[1]
            status_code = parts[2]  # 'NOT', 'IN', 'COMPLETED'
            
            # Получаем текущего пользователя
            telegram_username = context.user_data.get("telegram_username")
            
            if not telegram_username:
                print("❌ Ошибка: telegram_username не найден в context.user_data")
                await query.edit_message_text("❌ Ошибка: пользователь не идентифицирован.")
                return
            
            print(f"  User: @{telegram_username}")
            print(f"  Task ID: {task_id}")
            print(f"  Status code: {status_code}")
            
            # Преобразуем код в статус
            status_mapping = {
                "NOT": "not_started",
                "IN": "in_progress",
                "COMPLETED": "completed"
            }
            
            if status_code in status_mapping:
                new_status_value = status_mapping[status_code]
                new_status = TaskStatus(new_status_value)
                
                print(f"  New status: {new_status_value} ({new_status})")
                
                # Обновляем статус для конкретного пользователя
                print(f"  🔥 Вызов firebase_service.update_task_status...")
                success = firebase_service.update_task_status(task_id, telegram_username, new_status)
                
                if success:
                    print(f"  ✅ Firebase обновлен успешно")
                    
                    # Получаем задание для уведомлений
                    task = firebase_service.get_task(task_id)
                    
                    if task:
                        print(f"  ✅ Задание получено из Firebase")
                        
                        # Отправляем уведомления администраторам
                        from notifications import notification_service
                        import asyncio
                        
                        # Получаем старый статус
                        if isinstance(task.status, dict):
                            old_status = task.status.get(telegram_username, "not_started")
                        else:
                            old_status = str(task.status)
                        
                        print(f"  Old status: {old_status}")
                        
                        # Запускаем уведомление в фоне
                        try:
                            asyncio.create_task(
                                notification_service.notify_admins_task_update(
                                    firebase_service, task, str(old_status), new_status_value
                                )
                            )
                            print(f"  ✅ Уведомление запущено")
                        except Exception as e:
                            print(f"  ⚠️ Ошибка при запуске уведомления: {e}")
                        
                        # Сообщение пользователю
                        status_names = {
                            TaskStatus.NOT_STARTED: "Не начато",
                            TaskStatus.IN_PROGRESS: "В процессе", 
                            TaskStatus.COMPLETED: "Завершено"
                        }
                        
                        await query.edit_message_text(
                            f"✅ Статус обновлен: *{status_names[new_status]}*\n\n"
                            f"Администраторы уведомлены об изменении.",
                            parse_mode='Markdown'
                        )
                    else:
                        print(f"  ⚠️ Задание не найдено после обновления")
                        await query.edit_message_text("✅ Статус обновлен.")
                else:
                    print(f"  ❌ Ошибка в firebase_service.update_task_status")
                    await query.edit_message_text("❌ Ошибка обновления статуса.")
            else:
                print(f"  ❌ Неизвестный status_code: {status_code}")
                await query.edit_message_text(f"❌ Неизвестный статус: {status_code}")
        else:
            print(f"  ❌ Неверное количество частей: {len(parts)}")
            await query.edit_message_text(f"❌ Неверный формат callback: {query.data}")
    else:
        print(f"  ❌ Callback не начинается с set_status|")
        await query.edit_message_text(f"❌ Неизвестный запрос")


async def show_tasks_list(update, context, telegram_username, query=None):
    """Показать список заданий (общая функция)"""
    tasks = firebase_service.get_member_tasks(telegram_username)
    
    if not tasks:
        if query:
            await query.edit_message_text("📭 Нет активных заданий.")
        else:
            await update.message.reply_text("📭 Нет активных заданий.")
        return
    
    keyboard = []
    for task in tasks:
        status_emoji = {
            TaskStatus.NOT_STARTED: "🟡",
            TaskStatus.IN_PROGRESS: "🟠",
            TaskStatus.COMPLETED: "🟢"
        }[task.status]
        
        task_title = task.title[:30] + "..." if len(task.title) > 30 else task.title
        button_text = f"{status_emoji} {task_title}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"view_task_{task.id}")])
    
    keyboard.append([InlineKeyboardButton("🔄 Обновить", callback_data="refresh_tasks")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = "📋 *Ваши задания:*\n\nВыберите задание:"
    
    if query:
        await query.message.reply_text(message_text, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await update.message.reply_text(message_text, parse_mode='Markdown', reply_markup=reply_markup)


async def handle_refresh_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обновить список заданий"""
    query = update.callback_query
    await query.answer("Обновляю список...")
    
    await show_my_tasks_for_query(query, context)

async def handle_back_to_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться к списку заданий - ОБНОВЛЕННАЯ для словаря статусов"""
    query = update.callback_query
    await query.answer("Возвращаюсь к списку...")
    
    print(f"\n🔍 ДЕБАГ handle_back_to_list:")
    print(f"  Callback data: {query.data}")
    
    telegram_username = context.user_data.get("telegram_username")
    
    if not telegram_username:
        await query.edit_message_text("Ошибка: пользователь не идентифицирован.")
        return
    
    tasks = firebase_service.get_member_tasks(telegram_username)
    
    if not tasks:
        await query.edit_message_text("У вас нет активных заданий.")
        return
    
    keyboard = []
    for task in tasks:
        # Получаем статус для текущего пользователя
        if isinstance(task.status, dict):
            # Новый формат: словарь статусов
            user_status = task.status.get(telegram_username)
            if isinstance(user_status, str):
                try:
                    user_status = TaskStatus(user_status)
                except:
                    user_status = TaskStatus.NOT_STARTED
            elif not isinstance(user_status, TaskStatus):
                user_status = TaskStatus.NOT_STARTED
        else:
            # Старый формат
            user_status = task.status if isinstance(task.status, TaskStatus) else TaskStatus.NOT_STARTED
        
        # Эмодзи в зависимости от статуса
        status_emoji = {
            TaskStatus.NOT_STARTED: "🟡",
            TaskStatus.IN_PROGRESS: "🟠",
            TaskStatus.COMPLETED: "🟢"
        }[user_status]
        
        task_title = task.title[:30] + "..." if len(task.title) > 30 else task.title
        button_text = f"{status_emoji} {task_title}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"view_task_{task.id}")])
    
    keyboard.append([InlineKeyboardButton("🔄 Обновить", callback_data="refresh_tasks")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📋 *Ваши задания:*\n\nВыберите задание:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def show_my_tasks_for_query(query, context):
    """Вспомогательная функция для отображения заданий - ОБНОВЛЕННАЯ"""
    telegram_username = context.user_data.get("telegram_username")
    
    if not telegram_username:
        await query.edit_message_text("Ошибка: пользователь не идентифицирован.")
        return
    
    tasks = firebase_service.get_member_tasks(telegram_username)
    
    if not tasks:
        await query.edit_message_text("У вас нет активных заданий.")
        return
    
    keyboard = []
    for task in tasks:
        # Получаем статус для текущего пользователя
        if isinstance(task.status, dict):
            user_status = task.status.get(telegram_username)
            if isinstance(user_status, str):
                try:
                    user_status = TaskStatus(user_status)
                except:
                    user_status = TaskStatus.NOT_STARTED
            elif not isinstance(user_status, TaskStatus):
                user_status = TaskStatus.NOT_STARTED
        else:
            user_status = task.status if isinstance(task.status, TaskStatus) else TaskStatus.NOT_STARTED
        
        status_emoji = {
            TaskStatus.NOT_STARTED: "🟡",
            TaskStatus.IN_PROGRESS: "🟠",
            TaskStatus.COMPLETED: "🟢"
        }[user_status]
        
        task_title = task.title[:30] + "..." if len(task.title) > 30 else task.title
        button_text = f"{status_emoji} {task_title}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"view_task_{task.id}")])
    
    keyboard.append([InlineKeyboardButton("🔄 Обновить", callback_data="refresh_tasks")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📋 *Ваши задания:*\n\nВыберите задание:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_add_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать добавление комментария к заданию"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("add_comment_"):
        task_id = query.data.replace("add_comment_", "")
        context.user_data["comment_task_id"] = task_id
        
        await query.edit_message_text(
            "Введите комментарий к заданию:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Отмена", callback_data=f"view_task_{task_id}")]
            ])
        )
        
        # Устанавливаем состояние для получения комментария
        context.user_data["awaiting_comment"] = True


async def handle_comment_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработать введенный комментарий"""
    if context.user_data.get("awaiting_comment"):
        comment = update.message.text
        task_id = context.user_data.get("comment_task_id")
        
        if task_id:
            # Добавляем комментарий к заданию
            success = firebase_service.add_task_comment(task_id, comment)
            
            if success:                
                await update.message.reply_text(
                    "✅ Комментарий добавлен!\n\n"
                    f"📝 *Ваш комментарий:* {comment}",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("❌ Ошибка при добавлении комментария.")
        
        # Очищаем состояние
        context.user_data.pop("awaiting_comment", None)
        context.user_data.pop("comment_task_id", None)
    else:
        await update.message.reply_text("Используйте кнопки меню для навигации.")

async def show_my_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать информацию о себе"""
    member = context.user_data.get("member")
    
    if not member:
        await update.message.reply_text("Информация о вас не найдена.")
        return
    
    info_text = (
        f"👤 **Ваша информация:**\n\n"
        f"**ФИО (рус):** {member.full_name_ru}\n"
        f"**ФИО (англ):** {member.full_name_en}\n"
        f"**Группа:** {member.group}\n"
        f"**Тип личности:** {member.personality_type}\n"
        f"**Дата рождения:** {member.birth_date}\n"
        f"**Роль:** {member.role}"
    )
    
    await update.message.reply_text(info_text, parse_mode='Markdown')