import os
import json
import config
import git_deployer

# Список месяцев для жесткой цифровой валидации (1-12)
ALL_YEAR_MONTHS = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]

def load_db():
    json_path = "database.json"
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_db(db):
    json_path = "database.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

def update_config_months(new_month):
    """Автоматически добавляет новый месяц в config.py, если его там нет."""
    if new_month not in config.MONTHS_LIST:
        config_path = "config.py"
        with open(config_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        updated_months = [m for m in ALL_YEAR_MONTHS if m in config.MONTHS_LIST or m == new_month]
        old_line_repr = f"MONTHS_LIST = {repr(config.MONTHS_LIST)}"
        new_line_repr = f"MONTHS_LIST = {repr(updated_months)}"
        
        if old_line_repr in code:
            code = code.replace(old_line_repr, new_line_repr)
        else:
            import re
            code = re.sub(r"MONTHS_LIST\s*=\s*\[.*?\]", new_line_repr, code)
            
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(code)
        print(f" [СИНХРОНИЗАЦИЯ] Месяц '{new_month}' добавлен в хронологический список config.py")

def print_data():
    db = load_db()
    print("\n=== ТЕКУЩАЯ БАЗА ДАННЫХ ПРОЕКТА ===")
    if not db:
        print("База данных пуста.")
        return
    for direction, sub_objs in db.items():
        print(f"\n Направление: {direction}")
        for sub_obj, months in sub_objs.items():
            print(f"   └─ Подобъект: {sub_obj}")
            for mth, data in months.items():
                print(f"        ├─ {mth}: {data.get('sum', 0):,} руб. | Статус СтрК: {data.get('status', 'Нет')}")
    print("====================================")

def edit_table_data():
    print("\n>> ВНЕСЕНИЕ ИЗМЕНЕНИЙ В ТАБЛИЦУ")
    db = load_db()
    if not db:
        print(" База данных пуста.")
        return

    print("Выберите тип изменений:")
    print("  1. Изменить сумму (бюджет) месяца")
    print("  2. Заменить/переименовать месяц в структуре (Перенос данных)")
    sub_choice = input("Выберите действие (1-2 или Enter для отмены): ").strip()
    if sub_choice not in ("1", "2"):
        print(" Отменено.")
        return

    # Шаг 1. Выбор Направления
    directions = list(db.keys())
    print("\nДоступные Направления:")
    for idx, d in enumerate(directions, 1):
        print(f"  {idx}. {d}")
    d_choice = input("\nВыберите номер Направления: ").strip()
    if not d_choice or not d_choice.isdigit(): return
    d_idx = int(d_choice) - 1
    if d_idx < 0 or d_idx >= len(directions): return
    target_dir = directions[d_idx]

    # Шаг 2. Выбор Подобъекта
    sub_objs = list(db[target_dir].keys())
    print(f"\nДоступные Подобъекты для '{target_dir}':")
    for idx, s in enumerate(sub_objs, 1):
        print(f"  {idx}. {s}")
    s_choice = input("\nВыберите номер Подобъекта: ").strip()
    if not s_choice or not s_choice.isdigit(): return
    s_idx = int(s_choice) - 1
    if s_idx < 0 or s_idx >= len(sub_objs): return
    target_sub = sub_objs[s_idx]

    # Шаг 3. Выбор Месяца
    months_in_db = list(db[target_dir][target_sub].keys())
    print(f"\nТекущие активные периоды для '{target_sub}':")
    for idx, m in enumerate(months_in_db, 1):
        print(f"  {idx}. {m} (Текущая сумма: {db[target_dir][target_sub][m].get('sum', 0):,} руб.)")
    
    m_choice = input("\nВыберите номер периода для редактирования: ").strip()
    if not m_choice or not m_choice.isdigit(): return
    m_idx = int(m_choice) - 1
    if m_idx < 0 or m_idx >= len(months_in_db): return
    target_mth = months_in_db[m_idx]

    # Шаг 4. Обработка подпунктов
    if sub_choice == "1":
        new_sum_str = input(f"\nВведите новую сумму для {target_mth} (цифрами, без пробелов): ").strip()
        try:
            new_sum = int(new_sum_str)
            db[target_dir][target_sub][target_mth]["sum"] = new_sum
            save_db(db)
            print(f" [УСПЕХ] Бюджет обновлен в базе для {target_mth}: {new_sum:,} руб.")
        except ValueError:
            print(" [ОШИБКА] Сумма должна быть числом!")

    elif sub_choice == "2":
        print("\nВыберите НОВОЕ название месяца из календаря:")
        for i, m_name in enumerate(ALL_YEAR_MONTHS, 1):
            print(f"  {i}. {m_name}")
            
        new_mth_choice = input("\nВведите номер нового месяца (1-12): ").strip()
        if not new_mth_choice or not new_mth_choice.isdigit():
            print(" Отменено.")
            return
            
        new_mth_idx = int(new_mth_choice) - 1
        if new_mth_idx < 0 or new_mth_idx >= 12:
            print(" [ОШИБКА] Неверный номер месяца.")
            return
            
        new_mth_name = ALL_YEAR_MONTHS[new_mth_idx]
        
        if new_mth_name == target_mth:
            print(" [ИНФО] Выбран тот же самый месяц. Изменения структуры не требуются.")
            return

        # --- ВНЕДРЕНИЕ ПРЕДОХРАНИТЕЛЯ ОТ ДУБЛИРОВАНИЯ ---
        if new_mth_name in db[target_dir][target_sub]:
            print(f"\n⚠️  [КОНФЛИКТ СТРУКТУРЫ] Месяц '{new_mth_name}' УЖЕ СУЩЕСТВУЕТ в объекте '{target_sub}'!")
            print(f"  Текущие данные '{new_mth_name}': {db[target_dir][target_sub][new_mth_name].get('sum', 0):,} руб.")
            print(f"  Переносимые данные '{target_mth}': {db[target_dir][target_sub][target_mth].get('sum', 0):,} руб.")
            print("\nВыберите метод разрешения конфликта:")
            print("  1. Отмена (Выйти без изменений, данные в безопасности)")
            print("  2. Объединить периоды (Сложить суммы бюджетов, сохранить статусы)")
            
            conflict_choice = input("Выберите действие (1-2): ").strip()
            
            if conflict_choice == "2":
                # Логика объединения (Суммируем деньги)
                old_data = db[target_dir][target_sub].pop(target_mth)
                db[target_dir][target_sub][new_mth_name]["sum"] += old_data.get("sum", 0)
                
                # Если у переносимого месяца был статус, а у целевого нет — подтягиваем статус
                if old_data.get("status") and not db[target_dir][target_sub][new_mth_name].get("status"):
                    db[target_dir][target_sub][new_mth_name]["status"] = old_data.get("status")
                    
                save_db(db)
                print(f" [УСПЕХ] Данные периодов '{target_mth}' и '{new_mth_name}' успешно объединены!")
                return
            else:
                print(" [ИНФО] Операция отменена пользователем. Структура базы данных сохранена без изменений.")
                return
        # ------------------------------------------------

        # Если дубликата нет — стандартный безопасный перенос ветки данных
        mth_data_backup = db[target_dir][target_sub].pop(target_mth)
        db[target_dir][target_sub][new_mth_name] = mth_data_backup
        
        save_db(db)
        update_config_months(new_mth_name)
        print(f" [УСПЕХ] Месяц в структуре успешно изменен: {target_mth} ➔ {new_mth_name}")

def add_new_record():
    print("\n>> ДОБАВЛЕНИЕ НОВОЙ ВЕТКИ СТРУКТУРЫ")
    db = load_db()
    
    direction = input("Введите Направление (например, 01_АНАПА (Таманская)): ").strip()
    if not direction: return
    sub_obj = input("Введите Подобъект (например, 01_271_КН): ").strip()
    if not sub_obj: return
    
    print("\nВыберите Месяц из календаря:")
    for i, m_name in enumerate(ALL_YEAR_MONTHS, 1):
        print(f"  {i}. {m_name}")
    mth_choice = input("\nВведите номер месяца (1-12): ").strip()
    if not mth_choice or not mth_choice.isdigit(): return
    mth_idx = int(mth_choice) - 1
    if mth_idx < 0 or mth_idx >= 12: return
    month = ALL_YEAR_MONTHS[mth_idx]
    
    if direction not in db: db[direction] = {}
    if sub_obj not in db[direction]: db[direction][sub_obj] = {}
    
    # Защита от дублирования при добавлении абсолютно новой строки
    if month in db[direction][sub_obj]:
        print(f" ⚠️ [ОТМЕНА] Месяц '{month}' уже присутствует в структуре этого объекта!")
        return
        
    db[direction][sub_obj][month] = {"sum": 0, "status": ""}
    save_db(db)
    update_config_months(month)
    print(" [УСПЕХ] Новая ветка структуры добавлена в базу данных!")

def run_wizard():
    while True:
        print("\n--- СМАРТ-ПОМОЩНИК УПРАВЛЕНИЯ ТРЕКЕРОМ (JSON БАЗА) ---")
        print("1. Посмотреть текущую базу данных (Дерево)")
        print("2. Добавить новую ветку структуры (Объект/Месяц)")
        print("3. Внести изменения в таблицу")
        print("4. Сгенерировать Excel (с запросом отправки на GitHub)")
        print("5. Выйти из помощника")
        choice = input("Выберите действие (1-5): ").strip()
        
        if choice == "1":
            print_data()
        elif choice == "2":
            add_new_record()
        elif choice == "3":
            edit_table_data()
        elif choice == "4":
            success = git_deployer.run_production_pipeline(session_added_rows=["Обновление базы данных трекера"])
        elif choice == "5":
            print("До свидания!"); break
        else:
            print(" Неверный ввод.")

if __name__ == "__main__":
    run_wizard()
