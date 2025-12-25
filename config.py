# config.py - ОБНОВЛЕННАЯ ВЕРСИЯ
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot Token
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Firebase Configuration
    FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY')
    FIREBASE_AUTH_DOMAIN = os.getenv('FIREBASE_AUTH_DOMAIN')
    FIREBASE_DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL')
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')
    FIREBASE_STORAGE_BUCKET = os.getenv('FIREBASE_STORAGE_BUCKET')
    FIREBASE_MESSAGING_SENDER_ID = os.getenv('FIREBASE_MESSAGING_SENDER_ID')
    FIREBASE_APP_ID = os.getenv('FIREBASE_APP_ID')
    
    # 🔧 КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ:
    # Только ВЕРХНЕЕ руководство считается администраторами
    ADMIN_ROLES = {
        "President",
        "First Vice-president", 
        "Second Vice-President",
        "Secretary",
        "Secretary/Mommy",
        "Head of HR",
        # Accountant/HR - НЕ админ (это исполнительная роль)
        # HR - НЕ админ (это исполнительная роль)
        "Head of Event Managment Department",  # Руководитель отдела
        "Head of PR & Marketing Department",   # Руководитель отдела  
        "Head of Creative Arts Department",    # Руководитель отдела
        "Head of Educational Department",      # Руководитель отдела
        "Head of Japan Traditional Games",     # Руководитель отдела
        "Head of Cosplay Society"              # Руководитель отдела
    }
    
    # Заместители и рядовые сотрудники - НЕ администраторы
    # "Зам ↑", "Deputy", "Event Managers", "Creative Students" и т.д. - обычные участники
    
    # Task statuses
    TASK_STATUSES = {
        "not_started": "Не начато",
        "in_progress": "В процессе",
        "completed": "Завершено"
    }

config = Config()