# models.py
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from datetime import date
from pydantic import BaseModel, Field, validator, ConfigDict
import re


class UserRole(str, Enum):
    PRESIDENT = "President"
    FIRST_VICE_PRESIDENT = "First Vice-president"
    SECOND_VICE_PRESIDENT = "Second Vice-President"
    SECRETARY = "Secretary"
    SECRETARY_MOMMY = "Secretary/Mommy"
    HEAD_OF_HR = "Head of HR"
    ACCOUNTANT_HR = "Accountant/HR"
    HR = "HR"
    INTERN = "Стажер ↑"
    HEAD_OF_EVENT = "Head of Event Managment Department"
    DEPUTY = "Зам ↑"
    HEAD_OF_PR = "Head of PR & Marketing Department"
    HEAD_OF_CREATIVE = "Head of Creative Arts Department"
    HEAD_OF_EDUCATION = "Head of Educational Department"
    HEAD_OF_JAPAN_GAMES = "Head of Japan Traditional Games"
    HEAD_OF_COSPLAY = "Head of Cosplay Society"
    TRANSLATOR = "Translator"
    DEPUTY_OF_EVENT = "Deputy of Event Managment Department"
    DEPUTY_OF_PR = "Deputy of PR & Marketing Department"
    DEPUTY_OF_CREATIVE = "Deputy of Creative Arts Department"
    DEPUTY_OF_EDUCATION = "Deputy of Educational Department"
    EVENT_MANAGER = "Event Managers"
    TECHNICIAN = "Technician"
    PHOTOGRAPHER = "Photographers"
    DESIGNER = "Designers"
    COPYWRITER = "Copywriters"
    MOBILOGRAPH = "Mobilograph"
    CREATIVE_STUDENT = "Creative Students"
    GAME_MASTER = "Game Master"
    MEMBER = "Member"


class TaskStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class Member(BaseModel):
    """Модель участника клуба"""
    id: Optional[str] = None
    telegram: str = Field(default="")
    chat_id: int = Field(default=0)  # 0 означает "не установлен"
    full_name_ru: str = Field(default="")
    full_name_en: str = Field(default="")
    group: str = Field(default="")
    personality_type: str = Field(default="")
    birth_date: str = Field(default="")
    role: str = Field(default="Member")
    
    @validator('telegram', pre=True)
    def clean_telegram(cls, v):
        if v is None:
            return ""
        # Убираем @ и пробелы
        v = str(v).strip().replace('@', '')
        return v
    
    @validator('chat_id', pre=True)
    def validate_chat_id(cls, v):
        """Валидация chat_id: конвертируем null/None в 0"""
        if v is None or v == "" or str(v).lower() == "null":
            return 0
        try:
            return int(v)
        except (ValueError, TypeError):
            return 0
    
    @validator('full_name_ru', 'full_name_en', 'group', 'personality_type', 'role', pre=True)
    def clean_string_fields(cls, v):
        if v is None:
            return ""
        return str(v).strip()
    
    @validator('birth_date', pre=True)
    def clean_birth_date(cls, v):
        if v is None:
            return ""
        # Приводим к строке и убираем лишние пробелы
        v = str(v).strip()
        # Заменяем точки, которые могут быть разделителями тысяч
        if v.count('.') > 1:
            parts = v.split('.')
            if len(parts) == 3:
                # Это дата в формате дд.мм.гггг
                return v
            else:
                # Исправляем некорректные даты
                v = v.replace('.', ',', v.count('.') - 1)
        return v
    
    @property
    def telegram_username(self):
        return self.telegram
    
    @property
    def has_chat_id(self):
        """Проверка, установлен ли chat_id (не равен 0)"""
        return self.chat_id != 0
    
    @property
    def is_admin(self):
        admin_roles = {
            "President", "First Vice-president", "Second Vice-President",
            "Secretary", "Secretary/Mommy", "Head of HR"
        }
        return self.role in admin_roles
    
    model_config = ConfigDict(populate_by_name=True)


class Task(BaseModel):
    """Модель задания для нескольких пользователей (новый формат)"""
    id: Optional[str] = None
    title: str
    description: str
    assigned_to: List[str] = Field(default_factory=list)  # Список username'ов
    assigned_by: str  # Telegram username of admin
    created_at: str
    deadline: Optional[str] = None
    status: Dict[str, TaskStatus] = Field(default_factory=dict)  # Статус для каждого пользователя
    comments: List[str] = Field(default_factory=list)
    updated_at: Optional[str] = None  # Время последнего обновления
    
    @validator('assigned_to', pre=True)
    def normalize_assigned_to(cls, v):
        """Нормализуем assigned_to в список"""
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return v
        return []
    
    @validator('status', pre=True)
    def normalize_status(cls, v, values):
        """Нормализуем статус в словарь"""
        if v is None:
            v = {}
        
        # Если статус - строка или TaskStatus, преобразуем в словарь
        if isinstance(v, (str, TaskStatus)):
            status_value = v.value if isinstance(v, TaskStatus) else v
            assigned_to = values.get('assigned_to', [])
            if assigned_to:
                return {username: TaskStatus(status_value) for username in assigned_to}
            return {}
        
        # Если это словарь, но значения - строки, преобразуем в TaskStatus
        if isinstance(v, dict):
            result = {}
            for username, status_val in v.items():
                if isinstance(status_val, TaskStatus):
                    result[username] = status_val
                else:
                    try:
                        result[username] = TaskStatus(status_val)
                    except ValueError:
                        result[username] = TaskStatus.NOT_STARTED
            return result
        
        return {}
    
    @validator('title', 'description', pre=True)
    def clean_text_fields(cls, v):
        if v is None:
            return ""
        return str(v).strip()
    
    @property
    def is_single_user(self) -> bool:
        """Проверяет, является ли задание для одного пользователя"""
        return len(self.assigned_to) == 1
    
    def get_status_for_user(self, username: str) -> TaskStatus:
        """Получить статус задания для конкретного пользователя"""
        return self.status.get(username, TaskStatus.NOT_STARTED)
    
    def set_status_for_user(self, username: str, status: TaskStatus):
        """Установить статус задания для конкретного пользователя"""
        self.status[username] = status
    
    model_config = ConfigDict(use_enum_values=True)


class SingleUserTask(BaseModel):
    """Упрощенная модель для задания одного пользователя (старый формат, для обратной совместимости)"""
    id: Optional[str] = None
    title: str
    description: str
    assigned_to: str  # Один пользователь (строка)
    assigned_by: str
    created_at: str
    deadline: Optional[str] = None
    status: TaskStatus = TaskStatus.NOT_STARTED
    comments: List[str] = Field(default_factory=list)
    updated_at: Optional[str] = None
    
    @validator('title', 'description', pre=True)
    def clean_text_fields(cls, v):
        if v is None:
            return ""
        return str(v).strip()
    
    @validator('assigned_to', pre=True)
    def clean_assigned_to(cls, v):
        if v is None:
            return ""
        # Убираем @ если есть
        v = str(v).strip().replace('@', '')
        return v
    
    def to_multi_user_task(self) -> Task:
        """Конвертировать в многопользовательскую модель"""
        return Task(
            id=self.id,
            title=self.title,
            description=self.description,
            assigned_to=[self.assigned_to],  # Помещаем в список
            assigned_by=self.assigned_by,
            created_at=self.created_at,
            deadline=self.deadline,
            status={self.assigned_to: self.status},  # Словарь для одного пользователя
            comments=self.comments,
            updated_at=self.updated_at
        )
    
    @classmethod
    def from_multi_user_task(cls, task: Task) -> Optional['SingleUserTask']:
        """Создать SingleUserTask из Task (если это задание для одного пользователя)"""
        if len(task.assigned_to) != 1:
            return None
        
        # Находим статус для единственного пользователя
        status = task.status.get(task.assigned_to[0], TaskStatus.NOT_STARTED)
        
        return cls(
            id=task.id,
            title=task.title,
            description=task.description,
            assigned_to=task.assigned_to[0],
            assigned_by=task.assigned_by,
            created_at=task.created_at,
            deadline=task.deadline,
            status=status,
            comments=task.comments,
            updated_at=task.updated_at
        )
    
    model_config = ConfigDict(use_enum_values=True)


class TaskAssignment(BaseModel):
    """Модель для назначения задания (старый формат)"""
    admin_username: str
    member_username: str
    task_title: str
    task_description: str
    deadline: Optional[str] = None
    
    def to_single_user_task(self, created_at: str) -> SingleUserTask:
        """Преобразовать в SingleUserTask"""
        return SingleUserTask(
            title=self.task_title,
            description=self.task_description,
            assigned_to=self.member_username,
            assigned_by=self.admin_username,
            created_at=created_at,
            deadline=self.deadline
        )


class MultiTaskAssignment(BaseModel):
    """Модель для назначения задания нескольким пользователям (новый формат)"""
    admin_username: str
    member_usernames: List[str] = Field(default_factory=list)
    task_title: str
    task_description: str
    deadline: Optional[str] = None
    
    def to_task(self, created_at: str) -> Task:
        """Преобразовать в Task"""
        # Создаем словарь статусов для всех пользователей
        status_dict = {username: TaskStatus.NOT_STARTED for username in self.member_usernames}
        
        return Task(
            title=self.task_title,
            description=self.task_description,
            assigned_to=self.member_usernames,
            assigned_by=self.admin_username,
            created_at=created_at,
            deadline=self.deadline,
            status=status_dict
        )


class CreateMemberRequest(BaseModel):
    """Модель для создания нового участника"""
    telegram: str
    full_name_ru: str
    full_name_en: str
    group: str
    personality_type: str = ""
    birth_date: str
    role: str = "Member"
    chat_id: Optional[int] = None
    
    @validator('telegram', pre=True)
    def clean_telegram(cls, v):
        if v is None:
            return ""
        v = str(v).strip().replace('@', '')
        return v


class TaskStatusUpdate(BaseModel):
    """Модель для обновления статуса задания"""
    task_id: str
    username: str
    new_status: TaskStatus
    comment: Optional[str] = None
    
    model_config = ConfigDict(use_enum_values=True)


class TaskFilter(BaseModel):
    """Модель для фильтрации заданий"""
    assigned_to: Optional[str] = None
    assigned_by: Optional[str] = None
    status: Optional[TaskStatus] = None
    deadline_from: Optional[str] = None
    deadline_to: Optional[str] = None
    search_text: Optional[str] = None
    
    model_config = ConfigDict(use_enum_values=True)


# Вспомогательные функции
def create_task_for_single_user(
    title: str,
    description: str,
    assigned_to: str,
    assigned_by: str,
    created_at: str,
    deadline: Optional[str] = None
) -> Union[Task, SingleUserTask]:
    """Создать задание для одного пользователя (возвращает подходящий тип)"""
    # Можно использовать SingleUserTask для простоты
    return SingleUserTask(
        title=title,
        description=description,
        assigned_to=assigned_to,
        assigned_by=assigned_by,
        created_at=created_at,
        deadline=deadline
    )


def create_task_for_multiple_users(
    title: str,
    description: str,
    assigned_to: List[str],
    assigned_by: str,
    created_at: str,
    deadline: Optional[str] = None
) -> Task:
    """Создать задание для нескольких пользователей"""
    status_dict = {username: TaskStatus.NOT_STARTED for username in assigned_to}
    
    return Task(
        title=title,
        description=description,
        assigned_to=assigned_to,
        assigned_by=assigned_by,
        created_at=created_at,
        deadline=deadline,
        status=status_dict
    )