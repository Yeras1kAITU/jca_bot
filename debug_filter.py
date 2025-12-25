# debug_filter.py
from firebase_service import firebase_service
from config import config

def test_filter_logic():
    print("🔍 ТЕСТ ЛОГИКИ ФИЛЬТРАЦИИ")
    print("=" * 60)
    
    members = firebase_service.get_all_members()
    
    # Тестовые роли из вашего вывода
    test_roles = ["HR", "Стажер ↑", "Зам ↑", "Event Managers", "Creative Students"]
    
    print("📋 ПРОВЕРКА КОНКРЕТНЫХ РОЛЕЙ:")
    for role in test_roles:
        is_admin = role in config.ADMIN_ROLES
        print(f"  Роль '{role}' в ADMIN_ROLES: {is_admin}")
    
    print("\n👥 ПРИМЕРЫ УЧАСТНИКОВ И ИХ СТАТУС:")
    
    # Проверим нескольких конкретных участников
    test_usernames = ["hakujiisan", "l05842", "dazaixc", "random_resaet", "shikonokonok"]
    
    for username in test_usernames:
        member = firebase_service.get_member_by_telegram(username)
        if member:
            is_admin = member.role in config.ADMIN_ROLES
            print(f"  @{username}:")
            print(f"    Имя: {member.full_name_ru}")
            print(f"    Роль: '{member.role}'")
            print(f"    Является админом: {is_admin}")
            print(f"    (ADMIN_ROLES содержит '{member.role}': {member.role in config.ADMIN_ROLES})")
            print()
    
    # Посчитаем статистику
    print("📊 СТАТИСТИКА ПО ТЕКУЩЕЙ ЛОГИКЕ:")
    admins_count = 0
    non_admins_count = 0
    
    for member in members:
        if member.role in config.ADMIN_ROLES:
            admins_count += 1
        else:
            non_admins_count += 1
    
    print(f"  Всего участников: {len(members)}")
    print(f"  Администраторов (по текущей логике): {admins_count}")
    print(f"  Не-администраторов (по текущей логике): {non_admins_count}")
    
    # Покажем первых 5 не-админов
    print("\n📋 ПЕРВЫЕ 5 НЕ-АДМИНИСТРАТОРОВ (по текущей логике):")
    count = 0
    for member in members:
        if member.role not in config.ADMIN_ROLES and count < 5:
            print(f"  {count+1}. {member.full_name_ru} (@{member.telegram}) - {member.role}")
            count += 1

if __name__ == "__main__":
    test_filter_logic()