import db_core
import git_deployer

def print_data():
    db = db_core.load_db()
    print("\n=== ТЕКУЩАЯ БАЗА ДАННЫХ ПРОЕКТА ===")
    if not db:
        print("База данных пуста.")
        return
    for direction, sub_objs in db.items():
        print(f"\n Направление: {direction}")
        for sub_obj, months in sub_objs.items():
            print(f"   └─ Подобъект: {sub_obj}")
            for mth, data in months.items():
                print(f"        ├─ {mth}: {db_core.fmt_money(data.get('sum', 0))} руб. | Статус СтрК: {data.get('status', 'Нет')}")
    print("====================================")

def edit_table_data():
    print("\n>> ВНЕСЕНИЕ ИЗМЕНЕНИЙ В ТАБЛИЦУ")
    db = db_core.load_db()
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
        print(f"  {idx}. {m} (Текущая сумма: {db_core.fmt_money(db[target_dir][target_sub][m].get('sum', 0))} руб.)")
    
    m_choice = input("\nВыберите номер периода для редактирования: ").strip()
    if not m_choice or not m_choice.isdigit(): return
    m_idx = int(m_choice) - 1
    if m_idx < 0 or m_idx >= len(months_in_db): return
    target_mth = months_in_db[m_idx]

    # Шаг 4. Обработка подпунктов
    if sub_choice == "1":
        new_sum_str = input(f"\nВведите новую сумму для {target_mth} (можно с копейками через точку или запятую): ").strip()
        normalized_sum = new_sum_str.replace(",", ".")
        try:
            new_sum = float(normalized_sum)
            db[target_dir][target_sub][target_mth]["sum"] = new_sum
            db_core.save_db(db)
            print(f" [УСПЕХ] Бюджет обновлен в базе для {target_mth}: {db_core.fmt_money(new_sum)} руб.")
        except ValueError:
            print(" [ОШИБКА] Сумма должна быть числом (например: 150000 или 150000,50)!")

    elif sub_choice == "2":
        print("\nВыберите НОВОЕ название месяца из календаря:")
        for i, m_name in enumerate(db_core.ALL_YEAR_MONTHS, 1):
            print(f"  {i}. {m_name}")
            
        new_mth_choice = input("\nВведите номер нового месяца (1-12): ").strip()
        if not new_mth_choice or not new_mth_choice.isdigit():
            print(" Отменено.")
            return
            
        new_mth_idx = int(new_mth_choice) - 1
        if new_mth_idx < 0 or new_mth_idx >= 12:
            print(" [ОШИБКА] Неверный номер месяца.")
            return
            
        new_mth_name = db_core.ALL_YEAR_MONTHS[new_mth_idx]
        
        if new_mth_name == target_mth:
            print(" [ИНФО] Выбран тот же самый месяц. Изменения структуры не требуются.")
            return

        # ПРЕДОХРАНИТЕЛЬ ОТ ДУБЛИРОВАНИЯ
        if new_mth_name in db[target_dir][target_sub]:
            print(f"\n⚠️  [КОНФЛИКТ СТРУКТУРЫ] Месяц '{new_mth_name}' УЖЕ СУЩЕСТВУЕТ в объекте '{target_sub}'!")
            print(f"  Текущие данные '{new_mth_name}': {db_core.fmt_money(db[target_dir][target_sub][new_mth_name].get('sum', 0))} руб.")
            print(f"  Переносимые данные '{target_mth}': {db_core.fmt_money(db[target_dir][target_sub][target_mth].get('sum', 0))} руб.")
            print("\nВыберите метод разрешения конфликта:")
            print("  1. Отмена (Выйти без изменений, данные в безопасности)")
            print("  2. Объединить периоды (Сложить суммы бюджетов, сохранить статусы)")
            
            conflict_choice = input("Выберите действие (1-2): ").strip()
            
            if conflict_choice == "2":
                old_data = db[target_dir][target_sub].pop(target_mth)
                db[target_dir][target_sub][new_mth_name]["sum"] += float(old_data.get("sum", 0))
                
                if old_data.get("status") and not db[target_dir][target_sub][new_mth_name].get("status"):
                    db[target_dir][target_sub][new_mth_name]["status"] = old_data.get("status")
                    
                db_core.save_db(db)
                print(f" [УСПЕХ] Данные периодов '{target_mth}' и '{new_mth_name}' успешно объединены!")
                return
            else:
                print(" [ИНФО] Операция отменена пользователем. Структура базы данных сохранена без изменений.")
                return

        mth_data_backup = db[target_dir][target_sub].pop(target_mth)
        db[target_dir][target_sub][new_mth_name] = mth_data_backup
        
        db_core.save_db(db)
        db_core.update_config_months(new_mth_name)
        print(f" [УСПЕХ] Месяц в соответствии со структурой успешно изменен: {target_mth} ➔ {new_mth_name}")

def add_new_record():
    print("\n>> ДОБАВЛЕНИЕ НОВОЙ ВЕТКИ СТРУКТУРЫ")
    db = db_core.load_db()
    
    direction = input("Введите Направление (например, 01_АНАПА (Таманская)): ").strip()
    if not direction: return
    sub_obj = input("Введите Подобъект (например, 01_271_КН): ").strip()
    if not sub_obj: return
    
    print("\nВыберите Месяц из календаря:")
    for i, m_name in enumerate(db_core.ALL_YEAR_MONTHS, 1):
        print(f"  {i}. {m_name}")
    mth_choice = input("\nВведите номер месяца (1-12): ").strip()
    if not mth_choice or not mth_choice.isdigit(): return
    mth_idx = int(mth_choice) - 1
    if mth_idx < 0 or mth_idx >= 12: return
    month = db_core.ALL_YEAR_MONTHS[mth_idx]
    
    if direction not in db: db[direction] = {}
    if sub_obj not in db[direction]: db[direction][sub_obj] = {}
    
    if month in db[direction][sub_obj]:
        print(f" ⚠️ [ОТМЕНА] Месяц '{month}' уже присутствует в структуре этого объекта!")
        return
        
    db[direction][sub_obj][month] = {"sum": 0.0, "status": ""}
    db_core.save_db(db)
    db_core.update_config_months(month)
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
