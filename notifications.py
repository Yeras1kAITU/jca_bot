# notifications.py
from telegram import Bot
from telegram.error import TelegramError
from config import config
import asyncio
import re

def escape_markdown(text: str) -> str:
    """Экранирует специальные символы MarkdownV2"""
    if not text:
        return ""
    
    # Экранируем только символы, которые могут сломать разметку
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    escaped_text = ""
    for char in str(text):
        if char in escape_chars:
            escaped_text += '\\' + char
        else:
            escaped_text += char
    return escaped_text

class NotificationService:
    def __init__(self, bot_token: str):
        self.bot = Bot(token=bot_token)

    # Использование в вашем коде:
    async def notify_admins_task_update(self, firebase_service, task, old_status, new_status):
        """Уведомить администраторов об изменении статуса задания"""
        try:
            admins = firebase_service.get_admin_chat_ids()
            
            if not admins:
                print("⚠️  Нет администраторов с chat_id")
                return
            
            status_names = {
                "not_started": "Не начато",
                "in_progress": "В процессе",
                "completed": "Завершено"
            }
            
            # Форматируем исполнителей с экранированием
            if isinstance(task.assigned_to, list):
                assigned_users = ', '.join(f'@{user}' for user in task.assigned_to)
            else:
                assigned_users = f'@{task.assigned_to}' if task.assigned_to else "не назначен"
            
            # Экранируем все текстовые поля
            message = (
                f"📢 *Обновление статуса задания*\n\n"
                f"📋 *Задание:* {escape_markdown(task.title)}\n"
                f"👤 *Исполнитель:* {escape_markdown(assigned_users)}\n"
                f"📊 *Статус был:* {escape_markdown(status_names.get(old_status, old_status))}\n"
                f"📈 *Статус стал:* {escape_markdown(status_names.get(new_status, new_status))}\n"
                f"🕐 *Время изменения:* {escape_markdown(task.updated_at if hasattr(task, 'updated_at') else 'только что')}"
            )
            
            success_count = 0
            for admin_username, chat_id in admins:
                try:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode='MarkdownV2'  # Попробуйте MarkdownV2, он более строгий
                    )
                    print(f"✅ Уведомление отправлено администратору @{admin_username}")
                    success_count += 1
                except TelegramError as e:
                    print(f"❌ Ошибка отправки администратору @{admin_username}: {e}")
                    # Пробуем отправить без разметки
                    try:
                        await self.bot.send_message(
                            chat_id=chat_id,
                            text=message.replace('*', '').replace('_', ''),  # Убираем разметку
                            parse_mode=None
                        )
                        print(f"✅ Уведомление отправлено без разметки")
                        success_count += 1
                    except Exception as e2:
                        print(f"❌ Даже без разметки не отправилось: {e2}")
                except Exception as e:
                    print(f"❌ Неизвестная ошибка: {e}")
            
            print(f"📊 Итого: отправлено {success_count}/{len(admins)} уведомлений")
            
        except Exception as e:
            print(f"❌ Ошибка в notify_admins_task_update: {e}")
            import traceback
            traceback.print_exc()
    
    async def notify_member_new_task(self, firebase_service, task):
        """Уведомить участника о новом задании"""
        try:
            # Для многопользовательских заданий
            if isinstance(task.assigned_to, list):
                for username in task.assigned_to:
                    await self._notify_single_member(firebase_service, username, task)
            else:
                # Для одиночных заданий
                await self._notify_single_member(firebase_service, task.assigned_to, task)
                
        except Exception as e:
            print(f"❌ Ошибка в notify_member_new_task: {e}")
            import traceback
            traceback.print_exc()

    async def _notify_single_member(self, firebase_service, username, task):
        """Уведомить одного участника"""
        try:
            chat_id = firebase_service.get_member_chat_id(username)
            
            if not chat_id or chat_id <= 0:
                print(f"⚠️  У участника @{username} нет chat_id или он невалиден (значение: {chat_id})")
                return
            
            message = (
                f"🎯 *Новое задание!*\n\n"
                f"📋 *Название:* {task.title}\n"
                f"📝 *Описание:* {task.description}\n"
                f"👤 *Выдал:* @{task.assigned_by}\n"
            )
            
            if task.deadline:
                message += f"📅 *Дедлайн:* {task.deadline}\n"
            
            message += f"\nНажмите '📋 Мои задания' для просмотра"
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )
            print(f"✅ Уведомление о новом задании отправлено @{username} (chat_id: {chat_id})")
            
        except TelegramError as e:
            print(f"❌ Ошибка отправки участнику @{username}: {e}")
        except Exception as e:
            print(f"❌ Ошибка при уведомлении @{username}: {e}")

# Глобальный экземпляр
notification_service = NotificationService(config.BOT_TOKEN)