import db_core

def select_hierarchy_target(db, allow_new=False):
    """Универсальный кнопочный выбор Направления и Подобъекта по номерам."""
    # 1. Выбор Направления
    target_dir = ""
    directions = list(db.keys())
    
    if directions:
        print("\nДоступные Направления:")
        for idx, d in enumerate(directions, 1):
            print(f"  {idx}. {d}")
        if allow_new:
            print(f"  {len(directions) + 1}. [Создать абсолютно НОВОЕ Направление руками]")
        
        limit = len(directions) + 1 if allow_new else len(directions)
        d_choice = input(f"\nВыберите номер Направления (1-{limit}): ").strip()
        if not d_choice or not d_choice.isdigit(): return None, None
        d_idx = int(d_choice) - 1
        
        if d_idx >= 0 and d_idx < len(directions):
            target_dir = directions[d_idx]
        elif allow_new and d_idx == len(directions):
            target_dir = input("Введите название НОВОГО Направления (например, 03_НОВЫЙ_ОБЪЕКТ): ").strip()
    else:
        target_dir = input("База пуста. Введите название Направления: ").strip()
        
    if not target_dir: return None, None

    # 2. Выбор Подобъекта
    target_sub = ""
    if target_dir in db and db[target_dir]:
        sub_objs = list(db[target_dir].keys())
        print(f"\nДоступные Подобъекты для '{target_dir}':")
        for idx, s in enumerate(sub_objs, 1):
            print(f"  {idx}. {s}")
        if allow_new:
            print(f"  {len(sub_objs) + 1}. [Создать абсолютно НОВОЙ Подобъект руками]")
            
        limit = len(sub_objs) + 1 if allow_new else len(sub_objs)
        s_choice = input(f"Выберите номер Подобъекта (1-{limit}): ").strip()
        if not s_choice or not s_choice.isdigit(): return None, None
        s_idx = int(s_choice) - 1
        
        if s_idx >= 0 and s_idx < len(sub_objs):
            target_sub = sub_objs[s_idx]
        elif allow_new and s_idx == len(sub_objs):
            target_sub = input("Введите название НОВОГО Подобъекта: ").strip()
    else:
        target_sub = input("Введите название Подобъекта: ").strip()
        
    return target_dir, target_sub

def menu_add_record():
    """Логика добавления новой ветки (Пункт 2)."""
    print("\n>> ДОБАВЛЕНИЕ НОВОЙ ВЕТКИ СТРУКТУРЫ")
    db = db_core.load_db()
    
    target_dir, target_sub = select_hierarchy_target(db, allow_new=True)
    if not target_dir or not target_sub: return

    print("\nВыберите Месяц из календаря:")
    active_months = list(db[target_dir][target_sub].keys()) if (target_dir in db and target_sub in db[target_dir]) else []
    for i, m_name in enumerate(db_core.ALL_YEAR_MONTHS, 1):
        marker = " [УЖЕ ЕСТЬ]" if m_name in active_months else ""
        print(f"  {i}. {m_name}{marker}")
        
    mth_choice = input("\nВведите номер месяца (1-12): ").strip()
    if not mth_choice or not mth_choice.isdigit(): return
    mth_idx = int(mth_choice) - 1
    if mth_idx < 0 or mth_idx >= 12: return
    month = db_core.ALL_YEAR_MONTHS[mth_idx]
    
    if target_dir not in db: db[target_dir] = {}
    if target_sub not in db[target_dir]: db[target_dir][target_sub] = {}
    if month in db[target_dir][target_sub]:
        print(f" ⚠️ [ОТМЕНА] Месяц '{month}' уже присутствует в структуре!")
        return
        
    db[target_dir][target_sub][month] = {"sum": 0.0, "status": ""}
    db_core.save_db(db)
    db_core.update_config_months(month)
    print(f" [УСПЕХ] Период '{month}' успешно добавлен в структуру '{target_sub}'!")

def menu_edit_data():
    """Логика изменения бюджетов, месяцев и статусов (Пункт 3)."""
    print("\n>> ВНЕСЕНИЕ ИЗМЕНЕНИЙ В ТАБЛИЦУ")
    db = db_core.load_db()
    if not db:
        print(" База данных пуста.")
        return

    print("Выберите тип изменений:")
    print("  1. Изменить сумму (бюджет) месяца")
    print("  2. Заменить/переименовать месяц в структуре (Перенос данных)")
    print("  3. Изменить стартовый статус СтрК")
    sub_choice = input("Выберите действие (1-3 или Enter для отмены): ").strip()
    if sub_choice not in ("1", "2", "3"): return

    target_dir, target_sub = select_hierarchy_target(db, allow_new=False)
    if not target_dir or not target_sub: return

    months_in_db = list(db[target_dir][target_sub].keys())
    print(f"\nТекущие активные периоды для '{target_sub}':")
    for idx, m in enumerate(months_in_db, 1):
        print(f"  {idx}. {m} (Сумма: {db_core.fmt_money(db[target_dir][target_sub][m].get('sum', 0))} руб. | СтрК: {db[target_dir][target_sub][m].get('status', 'Нет')})")
    
    m_choice = input("\nВыберите номер периода для редактирования: ").strip()
    if not m_choice or not m_choice.isdigit(): return
    m_idx = int(m_choice) - 1
    if m_idx < 0 or m_idx >= len(months_in_db): return
    target_mth = months_in_db[m_idx]

    if sub_choice == "1":
        new_sum_str = input(f"\nВведите новую сумму для {target_mth}: ").strip()
        normalized_sum = new_sum_str.replace(",", ".")
        try:
            new_sum = float(normalized_sum)
            db[target_dir][target_sub][target_mth]["sum"] = new_sum
            db_core.save_db(db)
            print(f" [УСПЕХ] Бюджет обновлен: {db_core.fmt_money(new_sum)} руб.")
        except ValueError:
            print(" [ОШИБКА] Сумма должна быть числом!")

    elif sub_choice == "2":
        print("\nВыберите НОВОЕ название месяца из календаря:")
        for i, m_name in enumerate(db_core.ALL_YEAR_MONTHS, 1):
            print(f"  {i}. {m_name}")
        new_mth_choice = input("\nВведите номер нового месяца (1-12): ").strip()
        if not new_mth_choice or not new_mth_choice.isdigit(): return
        new_mth_idx = int(new_mth_choice) - 1
        if new_mth_idx < 0 or new_mth_idx >= 12: return
        new_mth_name = db_core.ALL_YEAR_MONTHS[new_mth_idx]
        
        if new_mth_name == target_mth: return

        if new_mth_name in db[target_dir][target_sub]:
            print(f"\n⚠️  [КОНФЛИКТ СТРУКТУРЫ] Месяц '{new_mth_name}' УЖЕ СУЩЕСТВУЕТ!")
            print("  1. Отмена | 2. Объединить периоды (Сложить суммы)")
            if input("Выберите действие (1-2): ").strip() == "2":
                old_data = db[target_dir][target_sub].pop(target_mth)
                db[target_dir][target_sub][new_mth_name]["sum"] += float(old_data.get("sum", 0))
                if old_data.get("status") and not db[target_dir][target_sub][new_mth_name].get("status"):
                    db[target_dir][target_sub][new_mth_name]["status"] = old_data.get("status")
                db_core.save_db(db)
                print(" [УСПЕХ] Данные периодов объединены!")
            return

        db[target_dir][target_sub][new_mth_name] = db[target_dir][target_sub].pop(target_mth)
        db_core.save_db(db)
        db_core.update_config_months(new_mth_name)
        print(f" [УСПЕХ] Месяц изменен: {target_mth} ➔ {new_mth_name}")

    elif sub_choice == "3":
        print("\nВыберите стартовый статус для СтрК:\n  1. Зеленый | 2. Желтый | 3. Красный | 0. Очистить")
        st_choice = input("Введите номер статуса (0-3): ").strip()
        if st_choice in ("1", "2", "3"):
            db[target_dir][target_sub][target_mth]["status"] = int(st_choice)
            db_core.save_db(db)
            print(" [УСПЕХ] Статус СтрК обновлен.")
        elif st_choice == "0":
            db[target_dir][target_sub][target_mth]["status"] = ""
            db_core.save_db(db)
            print(" [УСПЕХ] Статус СтрК очищен.")
