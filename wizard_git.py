import os
import sys
import config

session_flags = {
    "sum_changed": False,
    "status_changed": False,
    "branch_added": False
}

def register_action(action_type):
    if action_type in session_flags:
        session_flags[action_type] = True

def calculate_next_version(current_ver):
    ver_clean = current_ver.strip().lower().replace("v", "")
    try:
        parts = [int(p) for p in ver_clean.split(".")]
        if len(parts) < 3:
            parts += [0] * (3 - len(parts))
    except ValueError:
        parts = [1, 0, 0]

    major, minor, patch = parts

    if session_flags["branch_added"]:
        minor += 1
        patch = 0
    elif session_flags["sum_changed"] or session_flags["status_changed"]:
        patch += 1

    return f"v{major}.{minor}.{patch}"

def update_config_version(new_version):
    if not os.path.exists("config.py"):
        return
    with open("config.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    version_replaced = False
    for idx, line in enumerate(lines):
        if line.strip().startswith("VERSION") or line.strip().startswith("CURRENT_VERSION"):
            var_name = "VERSION" if line.strip().startswith("VERSION") else "CURRENT_VERSION"
            lines[idx] = f'{var_name} = "{new_version}"\n'
            version_replaced = True
            break
            
    if not version_replaced:
        lines.append(f'\nVERSION = "{new_version}"\n')
        
    with open("config.py", "w", encoding="utf-8") as f:
        f.writelines(lines)

def run_git_sync():
    print("\n📡 Подготовка к синхронизации с GitHub...")
    current_ver = getattr(config, "VERSION", getattr(config, "CURRENT_VERSION", "v1.0.0"))
    suggested_ver = calculate_next_version(current_ver)
    
    print("\n=== АНАЛИЗ ТЕКУЩЕЙ СЕССИИ ===")
    actions = []
    if session_flags["branch_added"]: actions.append("• Добавлены новые ветки структуры (Направления/Подобъекты/Месяцы)")
    if session_flags["sum_changed"]: actions.append("• Изменены бюджеты периодов")
    if session_flags["status_changed"]: actions.append("• Обновлены статусы документов СтрК")
    
    if not actions:
        print(" Изменений данных в сессии не зафиксировано (только пересборка Excel).")
    else:
        for a in actions: print(a)
        
    print(f"\nПредыдущая версия: {current_ver}")
    if current_ver != suggested_ver:
        print(f"Рекомендуемая новая версия: {suggested_ver}")
    else:
        print(f"Рекомендуемая версия: без изменений ({current_ver})")
    print("=============================")

    while True:
        print("\nВыберите действие для выгрузки:")
        print(f" 1. Принять рекомендуемую версию ({suggested_ver})")
        print(f" 2. Оставить прежнюю версию ({current_ver})")
        print(" 3. Ввести номер версии вручную")
        print(" 9. Назад (Отмена выгрузки, возврат в Главное меню)")
        print(" 0. Полный экстренный выход из программы")

        # Важно: по ТЗ «0» в корневом меню = выход из программы.
        # Поэтому здесь «0» оставляем как экстренный выход, а «назад» делаем через 9.

        
        choice = input("\nВыберите вариант: ").strip()
        
        if choice == "1":
            final_version = suggested_ver
            break
        elif choice == "2":
            final_version = current_ver
            break
        elif choice == "3":
            final_version = input("Введите номер версии (например, v1.2.5): ").strip()
            if not final_version.startswith("v"):
                final_version = f"v{final_version}"
            break
        elif choice == "9":
            print("\n🧹 Выгрузка отменена. Локальный файл сохранен. Возврат в Главное меню...")
            return False
        elif choice == "0":
            print("\nПрограмма экстренно завершена. Всего доброго!")
            sys.exit(0)
        else:
            print(" ❌ [ОШИБКА] Неверный выбор варианта!")

    comment = input("\nВведите комментарий к коммиту: ").strip()
    commit_msg = f"{final_version} {comment}".strip()
    update_config_version(final_version)
    
    print("\n📡 Синхронизация с сервером GitHub...")
    os.system("git add .")
    os.system(f'git commit -m "{commit_msg}"')
    os.system("git push")
    print("✅ [GITHUB] Все изменения успешно отправлены в репозиторий!")
    
    for key in session_flags:
        session_flags[key] = False
        
    return True
