# check_members.py
from firebase_service import firebase_service
from config import config

def analyze_members():
    print("🔍 АНАЛИЗ БАЗЫ ДАННЫХ УЧАСТНИКОВ")
    print("=" * 60)
    
    try:
        members = firebase_service.get_all_members()
        
        if not members:
            print("❌ В базе данных нет ни одного участника")
            return
        
        print(f"📊 Всего участников: {len(members)}")
        print("\n📋 РАСПРЕДЕЛЕНИЕ ПО РОЛЯМ:")
        
        # Группируем по ролям
        role_counts = {}
        for member in members:
            role = member.role if member.role else "Без роли"
            if role not in role_counts:
                role_counts[role] = []
            role_counts[role].append(member)
        
        # Сортируем по количеству
        for role, members_list in sorted(role_counts.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  {role}: {len(members_list)} участников")
            
            # Покажем первых 3 участников каждой роли
            for i, member in enumerate(members_list[:3]):
                print(f"    {i+1}. {member.full_name_ru} (@{member.telegram})")
            if len(members_list) > 3:
                print(f"    ... и еще {len(members_list) - 3}")
            print()
        
        # Проверяем администраторов
        print("👑 ПРОВЕРКА АДМИНИСТРАТОРОВ:")
        admins = [m for m in members if m.role in config.ADMIN_ROLES]
        non_admins = [m for m in members if m.role not in config.ADMIN_ROLES]
        
        print(f"  Администраторов: {len(admins)}")
        print(f"  Не-администраторов: {len(non_admins)}")
        
        if not non_admins:
            print("\n⚠️  ПРОБЛЕМА: В базе нет обычных участников!")
            print("   Все пользователи помечены как администраторы.")
        else:
            print("\n✅ В базе есть обычные участники для назначения заданий:")
            for i, member in enumerate(non_admins[:5]):
                print(f"   {i+1}. {member.full_name_ru} (@{member.telegram}) - {member.role}")
            if len(non_admins) > 5:
                print(f"   ... и еще {len(non_admins) - 5}")
        
        # Проверяем логику фильтрации
        print("\n🔧 ТЕСТ ФИЛЬТРАЦИИ:")
        test_member = members[0] if members else None
        if test_member:
            is_admin = test_member.role in config.ADMIN_ROLES
            print(f"  Пример участника: {test_member.full_name_ru}")
            print(f"  Роль: '{test_member.role}'")
            print(f"  Входит в ADMIN_ROLES: {is_admin}")
            print(f"  ADMIN_ROLES содержит: {config.ADMIN_ROLES}")
        
    except Exception as e:
        print(f"❌ Ошибка при анализе: {e}")

if __name__ == "__main__":
    analyze_members()