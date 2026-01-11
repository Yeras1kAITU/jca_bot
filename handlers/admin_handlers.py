from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from firebase_service import FirebaseService
from models import Task, TaskAssignment, TaskStatus, UserRole, Member
from config import config
from datetime import datetime
import html
import re
from keyboards import (
    get_main_menu_keyboard, 
    get_members_keyboard, 
    get_task_selection_keyboard, 
    get_cancel_keyboard,
    get_multi_member_selection_keyboard
)

# States для ConversationHandler
ASSIGN_TASK, SELECT_MEMBER, TASK_DETAILS = range(3)
ADD_MEMBER, GET_TELEGRAM, GET_NAME_RU, GET_NAME_EN, GET_GROUP, GET_PERSONALITY, GET_BIRTHDATE, GET_ROLE = range(8)
MULTI_SELECT_MEMBERS, MULTI_TASK_DETAILS = range(10, 12)

firebase_service = FirebaseService()

# В начале файла
async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню администратора с проверкой прав"""
    if not context.user_data.get("is_admin"):
        await update.message.reply_text("У вас нет прав администратора.")
        return
    
    from keyboards import get_main_menu_keyboard
    await update.message.reply_text(
        "Панель администратора",
        reply_markup=get_main_menu_keyboard(is_admin=True)
    )

# Добавим функцию для начала процесса добавления участника
async def add_member_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать процесс добавления нового участника"""
    if not context.user_data.get("is_admin"):
        await update.message.reply_text("У вас нет прав администратора.")
        return
    
    await update.message.reply_text(
        "👤 *Добавление нового участника*\n\n"
        "Введите Telegram username (без @):",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )
    
    return GET_TELEGRAM


async def get_member_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить Telegram username нового участника"""
    telegram_username = update.message.text.strip()
    
    # Проверяем, что username не начинается с @
    if telegram_username.startswith('@'):
        telegram_username = telegram_username[1:]
    
    # Проверяем, существует ли уже такой пользователь
    existing_member = firebase_service.get_member_by_telegram(telegram_username)
    if existing_member:
        await update.message.reply_text(
            f"❌ Пользователь @{telegram_username} уже существует!\n"
            f"Имя: {existing_member.full_name_ru}\n"
            f"Роль: {existing_member.role}\n\n"
            "Введите другой Telegram username или нажмите 'Отмена':"
        )
        return GET_TELEGRAM
    
    context.user_data["new_member_telegram"] = telegram_username
    
    await update.message.reply_text(
        "Введите ФИО на русском языке:\n"
        "Пример: *Иванов Иван Иванович*",
        parse_mode='Markdown'
    )
    
    return GET_NAME_RU


async def get_member_name_ru(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить ФИО на русском"""
    full_name_ru = update.message.text.strip()
    
    if len(full_name_ru) < 2:
        await update.message.reply_text(
            "❌ Имя слишком короткое. Введите полное ФИО на русском:"
        )
        return GET_NAME_RU
    
    context.user_data["new_member_full_name_ru"] = full_name_ru
    
    await update.message.reply_text(
        "Введите ФИО на английском языке:\n"
        "Пример: *Ivanov Ivan Ivanovich*",
        parse_mode='Markdown'
    )
    
    return GET_NAME_EN


async def get_member_name_en(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить ФИО на английском"""
    full_name_en = update.message.text.strip()
    
    if len(full_name_en) < 2:
        await update.message.reply_text(
            "❌ Имя слишком короткое. Введите полное ФИО на английском:"
        )
        return GET_NAME_EN
    
    context.user_data["new_member_full_name_en"] = full_name_en
    
    await update.message.reply_text(
        "Введите учебную группу:\n"
        "Пример: *ITE-2401*, *SE-2417*, *CS-2502*",
        parse_mode='Markdown'
    )
    
    return GET_GROUP


async def get_member_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить учебную группу"""
    group = update.message.text.strip().upper()  # Приводим к верхнему регистру
    
    if len(group) < 2:
        await update.message.reply_text(
            "❌ Название группы слишком короткое. Введите учебную группу:"
        )
        return GET_GROUP
    
    context.user_data["new_member_group"] = group
    
    await update.message.reply_text(
        "Введите тип личности (MBTI):\n"
        "Пример: *ENTJ*, *INFP*, *ISTP*\n\n"
        "⚠️ *Это поле необязательное* - можно отправить 'пропустить' или '-'",
        parse_mode='Markdown'
    )
    
    return GET_PERSONALITY


async def get_member_personality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить тип личности"""
    personality_type = update.message.text.strip().upper()
    
    # Если пользователь хочет пропустить
    if personality_type.lower() in ['пропустить', 'skip', '-', 'нет', 'no', '']:
        personality_type = ""
    
    context.user_data["new_member_personality_type"] = personality_type
    
    await update.message.reply_text(
        "Введите дату рождения в формате *ДД.ММ.ГГГГ*:\n"
        "Пример: *15.05.2005*, *20.04.2007*",
        parse_mode='Markdown'
    )
    
    return GET_BIRTHDATE


async def get_member_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить дату рождения"""
    birth_date = update.message.text.strip()
    
    # Проверяем формат даты
    try:
        day, month, year = map(int, birth_date.split('.'))
        if not (1 <= day <= 31 and 1 <= month <= 12 and year >= 1900):
            raise ValueError
        # Форматируем обратно с ведущими нулями
        birth_date = f"{day:02d}.{month:02d}.{year}"
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Неправильный формат даты!\n"
            "Введите дату в формате *ДД.ММ.ГГГГ*:\n"
            "Пример: *15.05.2005*",
            parse_mode='Markdown'
        )
        return GET_BIRTHDATE
    
    context.user_data["new_member_birth_date"] = birth_date
    
    # Создаем клавиатуру с основными ролями
    roles_keyboard = [
        ["Member", "Event Managers"],
        ["Creative Students", "Photographers"],
        ["Designers", "Copywriters"],
        ["Технические специалисты", "Ввести свою роль"]
    ]
    
    await update.message.reply_text(
        "Выберите или введите роль участника:\n\n"
        "Основные роли:\n"
        "• *Member* - Обычный участник\n"
        "• *Event Managers* - Организатор мероприятий\n"
        "• *Creative Students* - Креативный отдел\n"
        "• *Photographers* - Фотографы\n"
        "• *Designers* - Дизайнеры\n"
        "• *Copywriters* - Копирайтеры\n"
        "• *Технические специалисты* - Техники, переводчики и др.\n\n"
        "Или введите свою роль:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(roles_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    
    return GET_ROLE


async def get_member_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить роль участника и сохранить его"""
    role = update.message.text.strip()
    
    # Собираем все данные
    member_data = {
        "telegram": context.user_data["new_member_telegram"],
        "full_name_ru": context.user_data["new_member_full_name_ru"],
        "full_name_en": context.user_data["new_member_full_name_en"],
        "group": context.user_data["new_member_group"],
        "personality_type": context.user_data["new_member_personality_type"],
        "birth_date": context.user_data["new_member_birth_date"],
        "role": role
    }
    
    try:
        # Создаем объект Member
        member = Member(**member_data)
        
        # Сохраняем в Firebase
        members = firebase_service.db.child("members").get().val() or {}
        new_member_id = f"member_{len(members) + 1:03d}"
        
        firebase_service.db.child("members").child(new_member_id).set(member.dict(exclude={"id"}))
        
        # Отправляем подтверждение
        confirmation_text = (
            "✅ *Новый участник успешно добавлен!*\n\n"
            f"*ID:* {new_member_id}\n"
            f"*Telegram:* @{member.telegram}\n"
            f"*ФИО (рус):* {member.full_name_ru}\n"
            f"*ФИО (англ):* {member.full_name_en}\n"
            f"*Группа:* {member.group}\n"
            f"*Тип личности:* {member.personality_type if member.personality_type else 'Не указан'}\n"
            f"*Дата рождения:* {member.birth_date}\n"
            f"*Роль:* {member.role}\n\n"
            f"👤 Участник может авторизоваться в боте с помощью команды /start"
        )
        
        await update.message.reply_text(
            confirmation_text,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(is_admin=True)
        )
        
        # Очищаем временные данные
        for key in ["new_member_telegram", "new_member_full_name_ru", "new_member_full_name_en", 
                   "new_member_group", "new_member_personality_type", "new_member_birth_date"]:
            context.user_data.pop(key, None)
        
        return ConversationHandler.END
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка при добавлении участника: {str(e)}\n\n"
            "Попробуйте снова или отмените операцию.",
            reply_markup=get_cancel_keyboard()
        )
        return GET_ROLE


async def cancel_add_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена добавления участника"""
    # Очищаем временные данные
    for key in ["new_member_telegram", "new_member_full_name_ru", "new_member_full_name_en", 
               "new_member_group", "new_member_personality_type", "new_member_birth_date"]:
        context.user_data.pop(key, None)
    
    await update.message.reply_text(
        "❌ Добавление участника отменено.",
        reply_markup=get_main_menu_keyboard(is_admin=True)
    )
    
    return ConversationHandler.END


# Создаем ConversationHandler для добавления участников
add_member_conversation = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^👤 Добавить участника$"), add_member_start)],
    states={
        GET_TELEGRAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_member_telegram)],
        GET_NAME_RU: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_member_name_ru)],
        GET_NAME_EN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_member_name_en)],
        GET_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_member_group)],
        GET_PERSONALITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_member_personality)],
        GET_BIRTHDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_member_birthdate)],
        GET_ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_member_role)],
    },
    fallbacks=[
        MessageHandler(filters.Regex("^❌ Отмена$"), cancel_add_member),
        CommandHandler("cancel", cancel_add_member)
    ],
)

async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню администратора"""
    if not context.user_data.get("is_admin"):
        await update.message.reply_text("У вас нет прав администратора.")
        return
    
    await update.message.reply_text(
        "Панель администратора",
        reply_markup=get_main_menu_keyboard(is_admin=True)
    )


async def show_all_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать всех членов клуба"""
    members = firebase_service.get_all_members()
    
    if not members:
        await update.message.reply_text("Список членов клуба пуст.")
        return
    
    await update.message.reply_text(
        "Выберите члена клуба для просмотра информации:",
        reply_markup=get_members_keyboard(members, "member_info")
    )

async def assign_task_multi_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать процесс выдачи задания нескольким людям"""
    if not context.user_data.get("is_admin"):
        await update.message.reply_text("У вас нет прав администратора.")
        return
    
    members = firebase_service.get_all_members()
    non_admin_members = [m for m in members if not m.is_admin]
    
    if not non_admin_members:
        await update.message.reply_text("❌ Нет доступных участников.")
        return
    
    # Инициализируем список выбранных пользователей
    context.user_data["selected_users"] = []
    context.user_data["available_members"] = [m.telegram_username for m in non_admin_members]
    
    # Отправляем сообщение с клавиатурой выбора
    message = await update.message.reply_text(
        "👥 *Выберите участников для задания*\n\n"
        "Нажмите на имя чтобы выбрать/отменить выбор.\n"
        "Нажмите '✅ Готово' когда выберете всех.",
        parse_mode='Markdown',
        reply_markup=get_multi_member_selection_keyboard(non_admin_members)
    )
    
    # Сохраняем message_id для последующего редактирования
    context.user_data["selection_message_id"] = message.message_id
    
    return MULTI_SELECT_MEMBERS

async def assign_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать процесс выдачи задания - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    if not context.user_data.get("is_admin"):
        await update.message.reply_text("У вас нет прав администратора.")
        return
    
    members = firebase_service.get_all_members()
    
    if not members:
        await update.message.reply_text("❌ В базе данных нет членов клуба.")
        return
    
    print(f"\n🔍 ДЕБАГ assign_task_start:")
    print(f"  Всего членов в базе: {len(members)}")
    print(f"  ADMIN_ROLES: {config.ADMIN_ROLES}")
    
    # Подробная отладка фильтрации
    non_admin_members = []
    admin_members = []
    
    for i, member in enumerate(members):
        is_admin = member.role in config.ADMIN_ROLES
        if is_admin:
            admin_members.append(member)
        else:
            non_admin_members.append(member)
        
        # Вывод для первых 10 участников
        if i < 10:
            print(f"  [{i+1}] {member.full_name_ru} (@{member.telegram})")
            print(f"      Роль: '{member.role}'")
            print(f"      В ADMIN_ROLES: {is_admin}")
    
    print(f"\n📊 ИТОГО:")
    print(f"  Администраторов: {len(admin_members)}")
    print(f"  Не-администраторов: {len(non_admin_members)}")
    
    if not non_admin_members:
        # Детальное сообщение об ошибке
        error_msg = (
            "❌ **Нет доступных членов клуба для назначения заданий.**\n\n"
            "**Статистика:**\n"
            f"• Всего участников: {len(members)}\n"
            f"• Администраторов: {len(admin_members)}\n"
            f"• Обычных участников: 0\n\n"
            "**Причина:** Все участники имеют административные роли.\n\n"
            "**Решение:**\n"
            "1. Измените `ADMIN_ROLES` в `config.py`\n"
            "2. Или добавьте участников с ролью 'Member'"
        )
        await update.message.reply_text(error_msg, parse_mode='Markdown')
        return
    
    # Показываем первых 5 доступных участников для отладки
    print(f"\n🎯 ДОСТУПНЫЕ ДЛЯ ЗАДАНИЙ (первые 5):")
    for i, member in enumerate(non_admin_members[:5]):
        print(f"  {i+1}. {member.full_name_ru} (@{member.telegram}) - {member.role}")
    
    await update.message.reply_text(
        f"Выберите кому назначить задание (доступно: {len(non_admin_members)} участников):",
        reply_markup=get_members_keyboard(non_admin_members, "assign_to")
    )
    
    return SELECT_MEMBER


async def select_member_for_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора члена клуба для задания"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("assign_to_"):
        member_username = query.data.replace("assign_to_", "")
        context.user_data["assign_to"] = member_username
        
        await query.edit_message_text(
            f"Выбран: @{member_username}\n\n"
            f"Введите название задания:"
        )
        
        return TASK_DETAILS

async def view_tasks_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр статусов всех заданий - РАБОЧАЯ версия"""
    if not context.user_data.get("is_admin"):
        await update.message.reply_text("У вас нет прав администратора.")
        return
    
    print(f"⏱️  Начало view_tasks_status")
    
    try:
        # Получаем все задачи
        all_tasks = firebase_service.get_all_tasks()
        
        if not all_tasks:
            await update.message.reply_text("📭 Нет активных заданий.")
            return
        
        print(f"✅ Загружено задач: {len(all_tasks)}")
        
        # Отладочная информация
        for task in all_tasks:
            print(f"🔍 Задание: {task.title}")
            print(f"  ID: {task.id}")
            print(f"  Assigned to: {task.assigned_to}")
            print(f"  Status type: {type(task.status)}")
            print(f"  Status value: {task.status}")
        
        # Группируем по статусу
        tasks_by_status = {
            "not_started": [],
            "in_progress": [],
            "completed": []
        }
        
        # Собираем все задачи с деталями
        for task in all_tasks:
            if isinstance(task.status, dict):
                # Новый формат: словарь статусов
                for username, status_value in task.status.items():
                    if isinstance(status_value, TaskStatus):
                        status_str = status_value.value
                    else:
                        status_str = str(status_value)
                    
                    if status_str in tasks_by_status:
                        tasks_by_status[status_str].append({
                            "task": task,
                            "username": username,
                            "status": status_str
                        })
            else:
                # Старый формат
                if isinstance(task.status, TaskStatus):
                    status_str = task.status.value
                else:
                    status_str = str(task.status)
                
                if status_str in tasks_by_status:
                    # Для старых заданий берем первого пользователя
                    username = task.assigned_to[0] if task.assigned_to else "unknown"
                    tasks_by_status[status_str].append({
                        "task": task,
                        "username": username,
                        "status": status_str
                    })
        
        # Формируем отчет
        report = "<b>📊 Статус всех заданий:</b>\n\n"
        
        status_display = {
            "not_started": ("🟡 Не начато", "not_started"),
            "in_progress": ("🟠 В процессе", "in_progress"),
            "completed": ("🟢 Завершено", "completed")
        }
        
        total_shown = 0
        
        for display_name, status_key in status_display.values():
            tasks_list = tasks_by_status.get(status_key, [])
            
            report += f"<b>{display_name}</b> ({len(tasks_list)}):\n"
            
            if tasks_list:
                for item in tasks_list[:15]:  # Ограничим 15 заданиями на статус
                    task = item["task"]
                    username = item["username"]
                    
                    # Экранируем HTML
                    safe_title = html.escape(task.title) if hasattr(html, 'escape') else task.title
                    safe_username = html.escape(username) if hasattr(html, 'escape') else username
                    
                    report += f"• {safe_title} (@{safe_username})\n"
                    total_shown += 1
                
                if len(tasks_list) > 15:
                    report += f"... и еще {len(tasks_list) - 15} заданий\n"
            else:
                report += "Нет заданий\n"
            
            report += "\n"
        
        report += f"<b>📈 Всего заданий в системе:</b> {len(all_tasks)}\n"
        report += f"<b>👥 Уникальных исполнителей:</b> {len(set(item['username'] for status_list in tasks_by_status.values() for item in status_list))}\n"
        report += f"<b>👁️ Показано:</b> {total_shown} заданий"
        
        print(f"✅ Отчет сформирован")
        
        await update.message.reply_text(report, parse_mode='HTML')
        
    except Exception as e:
        print(f"❌ Ошибка в view_tasks_status: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text("❌ Ошибка при получении статуса заданий.")

async def assign_task_multi_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать процесс выдачи задания нескольким людям"""
    if not context.user_data.get("is_admin"):
        await update.message.reply_text("У вас нет прав администратора.")
        return
    
    members = firebase_service.get_all_members()
    non_admin_members = [m for m in members if not m.is_admin]
    
    if not non_admin_members:
        await update.message.reply_text("❌ Нет доступных участников.")
        return
    
    # Инициализируем список выбранных пользователей
    context.user_data["selected_users"] = []
    context.user_data["available_members"] = [m.telegram_username for m in non_admin_members]
    
    await update.message.reply_text(
        "👥 *Выберите участников для задания*\n\n"
        "Нажмите на имя чтобы выбрать/отменить выбор.\n"
        "Нажмите '✅ Готово' когда выберете всех.",
        parse_mode='Markdown',
        reply_markup=get_multi_member_selection_keyboard(non_admin_members)
    )
    
    return MULTI_SELECT_MEMBERS


async def handle_multi_user_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора/отмены выбора пользователя"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("toggle_user_"):
        username = query.data.replace("toggle_user_", "")
        selected_users = context.user_data.get("selected_users", [])
        
        if username in selected_users:
            # Удаляем если уже выбран
            selected_users.remove(username)
        else:
            # Добавляем если не выбран
            selected_users.append(username)
        
        context.user_data["selected_users"] = selected_users
        
        # Обновляем клавиатуру
        members = firebase_service.get_all_members()
        non_admin_members = [m for m in members if not m.is_admin]
        
        try:
            await query.edit_message_reply_markup(
                reply_markup=get_multi_member_selection_keyboard(
                    non_admin_members, 
                    selected_users
                )
            )
        except Exception as e:
            print(f"❌ Ошибка обновления клавиатуры: {e}")

async def confirm_multi_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение выбора нескольких пользователей"""
    query = update.callback_query
    await query.answer()
    
    selected_users = context.user_data.get("selected_users", [])
    
    if not selected_users:
        await query.edit_message_text("❌ Не выбрано ни одного участника.")
        return ConversationHandler.END
    
    await query.edit_message_text(
        f"✅ Выбрано {len(selected_users)} участников:\n" +
        "\n".join([f"• @{user}" for user in selected_users]) +
        "\n\nВведите название задания:"
    )
    
    return MULTI_TASK_DETAILS


async def get_multi_task_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение деталей задания для нескольких пользователей"""
    if not context.user_data.get("task_title"):
        context.user_data["task_title"] = update.message.text
        await update.message.reply_text("Введите описание задания:")
        return MULTI_TASK_DETAILS
    elif not context.user_data.get("task_description"):
        context.user_data["task_description"] = update.message.text
        await update.message.reply_text(
            "Введите дедлайн (ДД.ММ.ГГГГ или 'нет'):",
            reply_markup=get_cancel_keyboard()
        )
        return MULTI_TASK_DETAILS
    else:
        deadline = update.message.text
        deadline = None if deadline.lower() == 'нет' else deadline
        
        selected_users = context.user_data.get("selected_users", [])
        admin_username = context.user_data.get("telegram_username", "admin")
        
        # Создаем задание для нескольких пользователей
        from datetime import datetime
        task = Task(
            title=context.user_data["task_title"],
            description=context.user_data["task_description"],
            assigned_to=selected_users,  # Список пользователей
            assigned_by=admin_username,
            created_at=datetime.now().strftime("%d.%m.%Y %H:%M"),
            deadline=deadline,
            status={}  # Будет заполнено автоматически
        )
        
        task_id = firebase_service.create_multi_user_task(task)
        
        if task_id:
            print(f"✅ Многопользовательское задание создано: {task_id}")
            
            # Отправляем уведомления всем выбранным участникам
            from notifications import notification_service
            import asyncio
            
            for username in selected_users:
                # Создаем копию задания для каждого пользователя
                user_task = task.copy()
                user_task.assigned_to = username
                
                asyncio.create_task(
                    notification_service.notify_member_new_task(firebase_service, user_task)
                )
            
            # Сообщение администратору
            await update.message.reply_text(
                f"✅ Задание создано для {len(selected_users)} участников!\n\n"
                f"📋 Название: {task.title}\n"
                f"👤 Для: {len(selected_users)} участников\n"
                f"🆔 ID задания: {task_id}\n\n"
                f"Все участники получили уведомления.",
                reply_markup=get_main_menu_keyboard(is_admin=True)
            )
            
            # Очищаем временные данные
            context.user_data.pop("task_title", None)
            context.user_data.pop("task_description", None)
            context.user_data.pop("selected_users", None)
            context.user_data.pop("available_members", None)
            
        else:
            await update.message.reply_text("❌ Ошибка при создании задания")
        
        return ConversationHandler.END

# admin_handlers.py - добавьте перед ConversationHandler

async def cancel_assignment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Универсальный обработчик отмены для ConversationHandler"""
    try:
        print(f"\n🔍 DEBUG cancel_assignment:")
        
        # Очищаем временные данные
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
                print(f"  Удаляю из user_data: {key}")
                context.user_data.pop(key, None)
        
        # Определяем откуда пришел запрос
        if update.callback_query:
            query = update.callback_query
            await query.answer("Отмена...")
            message = query.message
        elif update.message:
            message = update.message
        else:
            return ConversationHandler.END
        
        # Отправляем сообщение с правильной клавиатурой
        is_admin = context.user_data.get("is_admin", False)
        from keyboards import get_main_menu_keyboard
        
        await message.reply_text(
            "❌ Операция отменена.",
            reply_markup=get_main_menu_keyboard(is_admin)
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        print(f"❌ Ошибка в cancel_assignment: {e}")
        return ConversationHandler.END

async def handle_member_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка запроса информации о члене клуба"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("member_info_"):
        member_username = query.data.replace("member_info_", "")
        member = firebase_service.get_member_by_telegram(member_username)
        
        if member:
            def escape_markdown_v2(text):
                if not text:
                    return ""
                escape_chars = r'_*[]()~`>#+-=|{}.!'
                result = []
                for char in str(text):
                    if char in escape_chars:
                        result.append(f'\\{char}')
                    else:
                        result.append(char)
                return ''.join(result)
            
            # Экранируем все поля
            name_ru = escape_markdown_v2(member.full_name_ru)
            name_en = escape_markdown_v2(member.full_name_en)
            telegram = escape_markdown_v2(member.telegram)
            group = escape_markdown_v2(member.group)
            personality = escape_markdown_v2(member.personality_type)
            birth_date = escape_markdown_v2(member.birth_date)
            role = escape_markdown_v2(member.role)
            
            info_text = (
                f"👤 *Информация о члене клуба\\:*\n\n"
                f"*ФИО \\(рус\\)\\:* {name_ru}\n"
                f"*ФИО \\(англ\\)\\:* {name_en}\n"
                f"*Telegram\\:* @{telegram}\n"
                f"*Группа\\:* {group}\n"
                f"*Тип личности\\:* {personality}\n"
                f"*Дата рождения\\:* {birth_date}\n"
                f"*Роль\\:* {role}\n\n"
                f"*Активные задания\\:*"
            )
            
            tasks = firebase_service.get_member_tasks(member_username)
            if tasks:
                for task in tasks:
                    status_text = {
                        TaskStatus.NOT_STARTED: "Не начато",
                        TaskStatus.IN_PROGRESS: "В процессе",
                        TaskStatus.COMPLETED: "Завершено"
                    }[task.status]
                    
                    task_title = escape_markdown_v2(task.title)
                    info_text += f"\n• {task_title} \\({status_text}\\)"
            else:
                info_text += "\nНет активных заданий"
            
            try:
                await query.edit_message_text(
                    info_text, 
                    parse_mode='MarkdownV2'
                )
            except Exception as e:
                # Если все равно ошибка, отправляем без Markdown
                print(f"❌ Markdown ошибка: {e}")
                simple_text = (
                    f"👤 Информация о члене клуба:\n\n"
                    f"ФИО (рус): {member.full_name_ru}\n"
                    f"ФИО (англ): {member.full_name_en}\n"
                    f"Telegram: @{member.telegram}\n"
                    f"Группа: {member.group}\n"
                    f"Тип личности: {member.personality_type}\n"
                    f"Дата рождения: {member.birth_date}\n"
                    f"Роль: {member.role}\n\n"
                    f"Активные задания:"
                )
                
                if tasks:
                    for task in tasks:
                        status_text = {
                            TaskStatus.NOT_STARTED: "Не начато",
                            TaskStatus.IN_PROGRESS: "В процессе",
                            TaskStatus.COMPLETED: "Завершено"
                        }[task.status]
                        simple_text += f"\n• {task.title} ({status_text})"
                else:
                    simple_text += "\nНет активных заданий"
                
                await query.edit_message_text(simple_text)
        else:
            await query.edit_message_text("Член клуба не найден.")

assign_task_multi_conversation = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^➕ Выдать задание$"), assign_task_multi_start)],
    states={
        MULTI_SELECT_MEMBERS: [
            CallbackQueryHandler(handle_multi_user_toggle, pattern="^toggle_user_"),
            CallbackQueryHandler(confirm_multi_selection, pattern="^confirm_selection$"),
            CallbackQueryHandler(cancel_assignment, pattern="^cancel_multi_select$"),
        ],
        MULTI_TASK_DETAILS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_multi_task_details),
        ],
    },
    fallbacks=[
        MessageHandler(filters.Regex("^❌ Отмена$"), cancel_assignment),
        CommandHandler("cancel", cancel_assignment)
    ],
)