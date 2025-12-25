# firebase_service.py
import pyrebase
from typing import Optional, List, Dict, Any, Union
from config import config
from models import Member, Task, TaskStatus, UserRole, SingleUserTask
import time
from datetime import datetime

# Глобальный экземпляр Firebase
_firebase_instance = None
_db_instance = None

def get_firebase():
    """Получить экземпляр Firebase (синглтон)"""
    global _firebase_instance, _db_instance
    
    if _firebase_instance is None:
        # Конфигурация Firebase
        firebase_config = {
            "apiKey": config.FIREBASE_API_KEY,
            "authDomain": config.FIREBASE_AUTH_DOMAIN,
            "databaseURL": config.FIREBASE_DATABASE_URL,
            "projectId": config.FIREBASE_PROJECT_ID,
            "storageBucket": config.FIREBASE_STORAGE_BUCKET,
            "messagingSenderId": config.FIREBASE_MESSAGING_SENDER_ID,
            "appId": config.FIREBASE_APP_ID
        }
        
        try:
            _firebase_instance = pyrebase.initialize_app(firebase_config)
            _db_instance = _firebase_instance.database()
            print("✅ Firebase успешно инициализирован")
        except Exception as e:
            print(f"❌ Ошибка инициализации Firebase: {e}")
            raise
    
    return _firebase_instance, _db_instance


class FirebaseService:
    def __init__(self):
        self.firebase, self.db = get_firebase()
    
    # ============== МЕТОДЫ ДЛЯ УЧАСТНИКОВ ==============
    
    def get_member_by_telegram(self, telegram_username: str) -> Optional[Member]:
        """Получить информацию о члене клуба по Telegram username"""
        try:
            # Удаляем @ если есть
            if telegram_username.startswith('@'):
                telegram_username = telegram_username[1:]
            
            members = self.db.child("members").get().val()
            if not members:
                print("❌ В базе данных нет членов")
                return None
            
            print(f"🔍 Поиск пользователя: {telegram_username}")
            
            for member_id, member_data in members.items():
                member_telegram = member_data.get("telegram", "")
                # Сравниваем без учета регистра
                if member_telegram.lower() == telegram_username.lower():
                    print(f"✅ Найден пользователь: {member_telegram}")
                    
                    # Нормализуем chat_id
                    if "chat_id" in member_data:
                        chat_id = member_data["chat_id"]
                        # Конвертируем None/null в 0
                        if chat_id is None or chat_id == "" or str(chat_id).lower() == "null":
                            member_data["chat_id"] = 0
                    else:
                        member_data["chat_id"] = 0
                    
                    # Добавляем ID
                    member_data_with_id = member_data.copy()
                    member_data_with_id["id"] = member_id
                    
                    # Создаем объект Member
                    try:
                        member = Member(**member_data_with_id)
                        return member
                    except Exception as e:
                        print(f"❌ Ошибка создания Member: {e}")
                        print(f"📊 Данные: {member_data_with_id}")
                        # Возвращаем упрощенную версию
                        return Member(
                            id=member_id,
                            telegram=member_telegram,
                            full_name_ru=member_data.get("full_name_ru", ""),
                            role=member_data.get("role", "Member"),
                            chat_id=member_data.get("chat_id", 0)
                        )
            
            print(f"❌ Пользователь {telegram_username} не найден")
            return None
        except Exception as e:
            print(f"❌ Ошибка при поиске пользователя: {e}")
            return None
    
    def get_all_members(self) -> List[Member]:
        """Получить всех членов клуба"""
        try:
            members = self.db.child("members").get().val()
            if not members:
                print("⚠️  В базе данных нет членов")
                return []
            
            result = []
            errors = []
            
            for member_id, member_data in members.items():
                try:
                    # Добавляем ID
                    member_data_with_id = member_data.copy()
                    member_data_with_id["id"] = member_id
                    
                    # Создаем объект Member
                    member = Member(**member_data_with_id)
                    result.append(member)
                    
                except Exception as e:
                    errors.append(f"Ошибка в member {member_id}: {e}")
                    print(f"⚠️  Ошибка парсинга member {member_id}: {e}")
                    print(f"📊 Проблемные данные: {member_data}")
                    
                    # Добавляем упрощенную версию
                    try:
                        simple_member = Member(
                            id=member_id,
                            telegram=member_data.get("telegram", ""),
                            full_name_ru=member_data.get("full_name_ru", "Неизвестно"),
                            role=member_data.get("role", "Member")
                        )
                        result.append(simple_member)
                    except:
                        pass
            
            if errors:
                print(f"⚠️  Всего ошибок при загрузке: {len(errors)}")
                for error in errors[:3]:  # Показываем первые 3 ошибки
                    print(f"   - {error}")
                if len(errors) > 3:
                    print(f"   ... и еще {len(errors) - 3} ошибок")
            
            print(f"✅ Успешно загружено {len(result)} из {len(members)} членов клуба")
            return result
            
        except Exception as e:
            print(f"❌ Критическая ошибка при получении всех членов: {e}")
            return []
    
    def update_member_chat_id(self, member_id: str, chat_id: int) -> bool:
        """Обновить chat_id участника"""
        try:
            print(f"\n🔥 DEBUG update_member_chat_id:")
            print(f"  member_id: {member_id}")
            print(f"  chat_id для сохранения: {chat_id} (тип: {type(chat_id)})")
            
            # Проверяем, что member_id существует
            if not member_id:
                print(f"  ❌ member_id пустой")
                return False
            
            # Проверяем, что chat_id валидный
            if not chat_id or chat_id <= 0:
                print(f"  ❌ Невалидный chat_id: {chat_id}")
                return False
            
            # Получаем текущие данные для логирования
            try:
                current_data = self.db.child("members").child(member_id).get().val()
                print(f"  📊 Текущие данные в Firebase: {current_data}")
                
                if current_data:
                    current_chat_id = current_data.get("chat_id", 0)
                    print(f"  📱 Текущий chat_id в Firebase: {current_chat_id}")
                else:
                    print(f"  ⚠️  Участник {member_id} не найден в Firebase")
                    return False
            except Exception as e:
                print(f"  ❌ Ошибка получения текущих данных: {e}")
                return False
            
            print(f"  🔄 Обновляю chat_id...")
            
            try:
                # Обновляем в базе
                self.db.child("members").child(member_id).update({"chat_id": chat_id})
                print(f"  ✅ Запрос на обновление отправлен")
            except Exception as e:
                print(f"  ❌ Ошибка при отправке запроса: {e}")
                return False
            
            # Небольшая задержка для обновления
            import time
            time.sleep(0.5)
            
            # Проверяем обновление
            try:
                updated_data = self.db.child("members").child(member_id).get().val()
                print(f"  📊 Обновленные данные: {updated_data}")
                
                if updated_data:
                    updated_chat_id = updated_data.get("chat_id")
                    print(f"  📱 Обновленный chat_id в Firebase: {updated_chat_id}")
                    
                    if updated_chat_id == chat_id:
                        print(f"  ✅ Chat_id успешно обновлен в Firebase!")
                        return True
                    else:
                        print(f"  ❌ Ошибка: chat_id не совпадает. Ожидалось: {chat_id}, получено: {updated_chat_id}")
                        return False
                else:
                    print(f"  ❌ Данные не найдены после обновления")
                    return False
                    
            except Exception as e:
                print(f"  ❌ Ошибка при проверке обновления: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Критическая ошибка в update_member_chat_id: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    def get_chat_id_by_username(self, telegram_username: str) -> Optional[int]:
        """Получить chat_id по Telegram username"""
        try:
            member = self.get_member_by_telegram(telegram_username)
            if member and hasattr(member, 'chat_id'):
                print(f"🔍 Chat_id для @{telegram_username}: {member.chat_id}")
                return member.chat_id
            print(f"⚠️  Chat_id не найден для @{telegram_username}")
            return None
        except Exception as e:
            print(f"❌ Ошибка получения chat_id: {e}")
            return None
    
    def get_member_chat_id(self, telegram_username: str) -> Optional[int]:
        """Получить chat_id участника по username"""
        try:
            member = self.get_member_by_telegram(telegram_username)
            if member and hasattr(member, 'chat_id'):
                # Используем chat_id напрямую, проверяя что он > 0
                if member.chat_id and member.chat_id > 0:
                    print(f"✅ Chat_id для @{telegram_username}: {member.chat_id}")
                    return member.chat_id
                else:
                    print(f"⚠️  Chat_id не установлен для @{telegram_username} (значение: {member.chat_id})")
                    return None
            print(f"⚠️  Пользователь @{telegram_username} не найден")
            return None
        except Exception as e:
            print(f"❌ Ошибка получения chat_id для @{telegram_username}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_admin_chat_ids(self) -> List[tuple]:
        """Получить chat_id всех администраторов"""
        try:
            members = self.get_all_members()
            admin_chat_ids = []
            
            for member in members:
                if hasattr(member, 'is_admin') and member.is_admin and hasattr(member, 'chat_id') and member.chat_id:
                    admin_chat_ids.append((member.telegram, member.chat_id))
            
            print(f"✅ Найдено администраторов с chat_id: {len(admin_chat_ids)}")
            return admin_chat_ids
        except Exception as e:
            print(f"❌ Ошибка получения chat_id администраторов: {e}")
            return []
    
    # ============== МЕТОДЫ ДЛЯ ЗАДАНИЙ ==============
    
    def create_task(self, task: Union[Task, SingleUserTask]) -> Optional[str]:
        """Универсальный метод создания задания"""
        try:
            # Конвертируем SingleUserTask в Task если нужно
            if isinstance(task, SingleUserTask):
                task = task.to_multi_user_task()
            
            task_dict = task.dict(exclude={"id"})
            
            # Обеспечиваем правильный формат статуса
            if not isinstance(task_dict.get("status"), dict):
                # Если статус не словарь, преобразуем
                status_dict = {}
                for username in task.assigned_to:
                    status_dict[username] = task.status.value if hasattr(task.status, 'value') else str(task.status)
                task_dict["status"] = status_dict
            
            # Добавляем timestamp
            task_dict["updated_at"] = datetime.now().isoformat()
            
            result = self.db.child("tasks").push(task_dict)
            task_id = result["name"]
            print(f"✅ Задание создано с ID: {task_id}")
            return task_id
        except Exception as e:
            print(f"❌ Ошибка при создании задания: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def create_multi_user_task(self, task: Task) -> Optional[str]:
        """Создать задание для нескольких пользователей"""
        return self.create_task(task)
    
    def get_all_tasks(self) -> List[Task]:
        """Получить ВСЕ задания"""
        try:
            tasks_data = self.db.child("tasks").get().val()
            if not tasks_data:
                print("📭 Нет задач в базе")
                return []
            
            result = []
            for task_id, task_data in tasks_data.items():
                try:
                    print(f"🔍 Обработка задачи {task_id}:")
                    print(f"  Данные: {task_data}")
                    
                    # Обработка assigned_to
                    if isinstance(task_data.get("assigned_to"), str):
                        print(f"  Преобразую assigned_to из строки в список")
                        task_data["assigned_to"] = [task_data["assigned_to"]]
                    
                    # Обработка статуса
                    if not isinstance(task_data.get("status"), dict):
                        print(f"  Статус не словарь: {task_data.get('status')}")
                        if isinstance(task_data.get("assigned_to"), list) and task_data["assigned_to"]:
                            print(f"  Создаю словарь статусов")
                            status_dict = {}
                            for username in task_data["assigned_to"]:
                                status_dict[username] = task_data.get("status", TaskStatus.NOT_STARTED.value)
                            task_data["status"] = status_dict
                            print(f"  Новый статус: {status_dict}")
                    
                    task_data["id"] = task_id
                    result.append(Task(**task_data))
                    print(f"  ✅ Успешно преобразовано")
                    
                except Exception as e:
                    print(f"⚠️  Ошибка парсинга задачи {task_id}: {e}")
                    print(f"📊 Проблемные данные: {task_data}")
            
            print(f"✅ Итого загружено {len(result)} задач")
            return result
        
        except Exception as e:
            print(f"❌ Критическая ошибка при получении всех задач: {e}")
            return []
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Получить задание по ID"""
        try:
            task_data = self.db.child("tasks").child(task_id).get().val()
            if task_data:
                # Обработка старых форматов
                if isinstance(task_data.get("assigned_to"), str):
                    task_data["assigned_to"] = [task_data["assigned_to"]]
                
                if not isinstance(task_data.get("status"), dict):
                    if isinstance(task_data.get("assigned_to"), list) and task_data["assigned_to"]:
                        status_dict = {}
                        for username in task_data["assigned_to"]:
                            status_dict[username] = task_data.get("status", TaskStatus.NOT_STARTED.value)
                        task_data["status"] = status_dict
                
                task_data["id"] = task_id
                return Task(**task_data)
            return None
        except Exception as e:
            print(f"❌ Ошибка при получении задания: {e}")
            return None
    
    def get_member_tasks(self, telegram_username: str) -> List[Task]:
        """Получить все задания для конкретного пользователя"""
        try:
            all_tasks = self.get_all_tasks()
            result = []
            
            for task in all_tasks:
                if telegram_username in task.assigned_to:
                    result.append(task)
            
            print(f"✅ Найдено {len(result)} задач для @{telegram_username}")
            return result
        except Exception as e:
            print(f"❌ Ошибка при получении заданий пользователя: {e}")
            return []
    
    def update_task_status(self, task_id: str, username: str, status: TaskStatus) -> bool:
        """Обновить статус задания для конкретного пользователя"""
        try:
            # Преобразуем TaskStatus в строку
            status_str = status.value if hasattr(status, 'value') else str(status)
            
            # Обновляем статус для конкретного пользователя
            self.db.child("tasks").child(task_id).child("status").child(username).set(status_str)
            
            # Обновляем timestamp
            self.db.child("tasks").child(task_id).update({
                "updated_at": datetime.now().isoformat()
            })
            
            print(f"✅ Статус задания {task_id} для @{username} обновлен на: {status_str}")
            return True
        except Exception as e:
            print(f"❌ Ошибка при обновлении статуса: {e}")
            return False
    
    def get_task_status_for_user(self, task_id: str, username: str) -> Optional[TaskStatus]:
        """Получить статус задания для конкретного пользователя"""
        try:
            task_data = self.db.child("tasks").child(task_id).get().val()
            if task_data and "status" in task_data and username in task_data["status"]:
                return TaskStatus(task_data["status"][username])
            return None
        except Exception as e:
            print(f"❌ Ошибка при получении статуса: {e}")
            return None
    
    def add_task_comment(self, task_id: str, comment: str) -> bool:
        """Добавить комментарий к заданию"""
        try:
            # Получаем текущие комментарии
            task_data = self.db.child("tasks").child(task_id).get().val()
            comments = task_data.get("comments", []) if task_data else []
            
            # Добавляем новый комментарий
            comments.append(comment)
            
            # Обновляем в базе
            self.db.child("tasks").child(task_id).update({
                "comments": comments,
                "updated_at": datetime.now().isoformat()
            })
            
            print(f"✅ Комментарий добавлен к заданию {task_id}")
            return True
        except Exception as e:
            print(f"❌ Ошибка при добавлении комментария: {e}")
            return False
    
    # ============== МЕТОДЫ ДЛЯ МИГРАЦИИ ==============
    
    def migrate_old_tasks(self):
        """Мигрировать старые задания в новый формат"""
        try:
            tasks_data = self.db.child("tasks").get().val()
            if not tasks_data:
                print("📭 Нет заданий для миграции")
                return
            
            migrated_count = 0
            
            for task_id, task_data in tasks_data.items():
                try:
                    # Проверяем нужно ли мигрировать
                    needs_migration = False
                    
                    # Проверяем assigned_to
                    if isinstance(task_data.get("assigned_to"), str):
                        needs_migration = True
                        old_username = task_data["assigned_to"]
                        task_data["assigned_to"] = [old_username]
                    
                    # Проверяем статус
                    if not isinstance(task_data.get("status"), dict):
                        if "assigned_to" in task_data and task_data["assigned_to"]:
                            needs_migration = True
                            if isinstance(task_data["assigned_to"], list):
                                status_dict = {}
                                for username in task_data["assigned_to"]:
                                    status_dict[username] = task_data.get("status", TaskStatus.NOT_STARTED.value)
                                task_data["status"] = status_dict
                    
                    if needs_migration:
                        # Обновляем задание
                        self.db.child("tasks").child(task_id).set(task_data)
                        migrated_count += 1
                        print(f"✅ Мигрировано задание {task_id}")
                        
                except Exception as e:
                    print(f"⚠️  Ошибка миграции задания {task_id}: {e}")
            
            print(f"🎯 Всего мигрировано: {migrated_count}/{len(tasks_data)} заданий")
            
        except Exception as e:
            print(f"❌ Ошибка миграции: {e}")
            import traceback
            traceback.print_exc()
    
    # ============== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==============
    
    def count_tasks_by_status(self):
        """Посчитать задачи по статусам"""
        try:
            tasks = self.get_all_tasks()
            stats = {
                "total": 0,
                "not_started": 0,
                "in_progress": 0,
                "completed": 0,
                "by_user": {}
            }
            
            for task in tasks:
                stats["total"] += 1
                
                # Считаем по пользователям
                for username, status in task.status.items():
                    if isinstance(status, TaskStatus):
                        status_value = status.value
                    else:
                        status_value = status
                    
                    if status_value == TaskStatus.NOT_STARTED.value:
                        stats["not_started"] += 1
                    elif status_value == TaskStatus.IN_PROGRESS.value:
                        stats["in_progress"] += 1
                    elif status_value == TaskStatus.COMPLETED.value:
                        stats["completed"] += 1
                    
                    # Статистика по пользователям
                    if username not in stats["by_user"]:
                        stats["by_user"][username] = {
                            "total": 0,
                            "not_started": 0,
                            "in_progress": 0,
                            "completed": 0
                        }
                    
                    stats["by_user"][username]["total"] += 1
                    if status_value == TaskStatus.NOT_STARTED.value:
                        stats["by_user"][username]["not_started"] += 1
                    elif status_value == TaskStatus.IN_PROGRESS.value:
                        stats["by_user"][username]["in_progress"] += 1
                    elif status_value == TaskStatus.COMPLETED.value:
                        stats["by_user"][username]["completed"] += 1
            
            return stats
            
        except Exception as e:
            print(f"❌ Ошибка подсчета статистики: {e}")
            return None


# Создаем глобальный экземпляр
firebase_service = FirebaseService()