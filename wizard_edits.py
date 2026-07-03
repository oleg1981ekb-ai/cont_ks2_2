import db_core
import config
import wizard_git

def menu_edit_data(select_target_func):
    """Логика изменения бюджетов, месяцев и статусов (Пункт 3)."""
    print("\n>> ВНЕСЕНИЕ ИЗМЕНЕНИЙ В ТАБЛИЦУ")
    db = db_core.load_db()
    if not db: return
    print("Выберите тип изменений:\n 1. Изменить сумму месяца\n 2. Переименовать месяц\n 3. Изменить статус СтрК")
    sub_choice = input("Выберите действие (1-3): ").strip()
    if sub_choice not in ("1", "2", "3"): return
    
    target_dir, target_sub = select_target_func(db, allow_new=False)
    if not target_dir or not target_sub: return
    
    months_in_db = list(db[target_dir][target_sub].keys())
    print(f"\nТекущие активные периоды:")
    for idx, m in enumerate(months_in_db, 1):
        st_raw = db[target_dir][target_sub][m].get("status", "")
        st_val = "Раздельный по док." if isinstance(st_raw, dict) and "value" not in st_raw else (st_raw.get("value", "Нет") if isinstance(st_raw, dict) else (st_raw if st_raw else "Нет"))
        # ИСПРАВЛЕНО: Добавлено красивое форматирование разрядов пробелами при выводе списка
        fmt_sum = db_core.fmt_money(db[target_dir][target_sub][m].get('sum', 0))
        print(f" {idx}. {m} (Сумма: {fmt_sum} руб. | СтрК: {st_val})")
    
    m_choice = input("\nВыберите номер периода: ").strip()
    if not m_choice or not m_choice.isdigit(): return
    m_idx = int(m_choice) - 1
    if m_idx < 0 or m_idx >= len(months_in_db): return
    target_mth = months_in_db[m_idx]

    if sub_choice == "1":
        while True:
            new_sum_str = input(f"\nВведите новую сумму (или '0' для выхода в меню): ").strip()
            if new_sum_str.lower() in ("выход", "0"):
                break
            try:
                cleaned_sum = float(new_sum_str.replace(" ", "").replace(",", "."))
                if cleaned_sum < 0:
                    print(" ❌ [ОШИБКА] Сумма бюджета не может быть отрицательной!")
                    continue
                
                db[target_dir][target_sub][target_mth]["sum"] = cleaned_sum
                db_core.save_db(db)
                
                wizard_git.register_action("sum_changed")
                # ИСПРАВЛЕНО: Форматирование разрядов при выводе сообщения об успехе
                print(f"  [УСПЕХ] Бюджет успешно обновлен на: {db_core.fmt_money(cleaned_sum)} руб.")
                break
            except ValueError:
                print(" ❌ [ОШИБКА ВВОДА] Введите число без букв!")

    elif sub_choice == "2":
        print("\nВыберите НОВОЕ название месяца:")
        for i, m_name in enumerate(db_core.ALL_YEAR_MONTHS, 1): print(f" {i}. {m_name}")
        new_mth_choice = input("\nВведите номер (1-12): ").strip()
        if not new_mth_choice or not new_mth_choice.isdigit(): return
        new_mth_name = db_core.ALL_YEAR_MONTHS[int(new_mth_choice) - 1]
        
        if new_mth_name in db[target_dir][target_sub]:
            print(" ⚠ Месяц уже существует! Объединяем бюджеты? (1-Да / 2-Нет)")
            if input().strip() == "1":
                old = db[target_dir][target_sub].pop(target_mth)
                db[target_dir][target_sub][new_mth_name]["sum"] += float(old.get("sum", 0))
                db_core.save_db(db)
                wizard_git.register_action("sum_changed")
                return
        db[target_dir][target_sub][new_mth_name] = db[target_dir][target_sub].pop(target_mth)
        db_core.save_db(db)
        wizard_git.register_action("branch_added")
        db_core.update_config_months(new_mth_name)

    elif sub_choice == "3":
        print("\nВыберите статус СтрК:\n 1. Зеленый | 2. Желтый | 3. Красный | 0. Очистить")
        st_choice = input("Введите номер (0-3): ").strip()
        if st_choice not in ("1", "2", "3", "0"):
            print(" [ОШИБКА] Неверный статус.")
            return

        status_value = "" if st_choice == "0" else int(st_choice)
        status_date = "" if st_choice == "0" else db_core.get_short_date()

        print("\nКак применить статус к документам этого месяца?")
        print(" 1. Заполнить ВСЕ документы сразу")
        print(" 2. Выбрать КОНКРЕТНЫЙ документ из списка")
        apply_mode = input("Выберите вариант (1-2): ").strip()

        if apply_mode == "1":
            db[target_dir][target_sub][target_mth]["status"] = {"value": status_value, "date": status_date}
            db_core.save_db(db)
            wizard_git.register_action("status_changed")
            print(f" [УСПЕХ] Статус успешно присвоен ВСЕМ документам периода!")
        elif apply_mode == "2":
            allowed_docs = []
            for doc_name in config.DOCUMENTS_LIST:
                mask = config.DOCUMENT_ROLES.get(doc_name, {})
                if mask.get("СтрК", 1) == 1:
                    allowed_docs.append(doc_name)

            if not allowed_docs:
                print(" ⚠ [ВНИМАНИЕ] Нет доступных документов для СтрК!")
                return

            print(f"\nДоступные документы для изменения СтрК:")
            for idx, doc_name in enumerate(allowed_docs, 1):
                print(f" {idx}. {doc_name}")
            
            doc_choice = input(f"Выберите номер документа (1-{len(allowed_docs)}): ").strip()
            if not doc_choice or not doc_choice.isdigit(): return
            doc_idx = int(doc_choice) - 1
            if doc_idx < 0 or doc_idx >= len(allowed_docs): return
            target_doc = allowed_docs[doc_idx]

            current_status = db[target_dir][target_sub][target_mth].get("status", {})
            if not isinstance(current_status, dict) or "value" in current_status:
                db[target_dir][target_sub][target_mth]["status"] = {}
                for d_name in config.DOCUMENTS_LIST:
                    db[target_dir][target_sub][target_mth]["status"][d_name] = {
                        "value": current_status.get("value", "") if isinstance(current_status, dict) else "",
                        "date": current_status.get("date", "") if isinstance(current_status, dict) else ""
                    }

            db[target_dir][target_sub][target_mth]["status"][target_doc] = {"value": status_value, "date": status_date}
            db_core.save_db(db)
            wizard_git.register_action("status_changed")
            print(f" [УСПЕХ] Статус документа '{target_doc}' успешно обновлен!")
