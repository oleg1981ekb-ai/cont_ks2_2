import db_core
import config
import wizard_git


def menu_edit_data(select_target_func):
    """Логика изменения бюджетов, месяцев и статусов (Пункт 3)."""
    print("\n>> ВНЕСЕНИЕ ИЗМЕНЕНИЙ В ТАБЛИЦУ")
    db = db_core.load_db()
    if not db:
        return

    print("Выберите тип изменений:\n 1. Изменить сумму месяца\n 2. Переименовать месяц\n 3. Изменить статусы")
    sub_choice = input("Выберите действие (1-3): ").strip()
    if sub_choice not in ("1", "2", "3"):
        return

    target_dir, target_sub = select_target_func(db, allow_new=False)
    if not target_dir or not target_sub:
        return

    months_in_db = list(db[target_dir][target_sub].keys())
    print("\nТекущие активные периоды:")
    for idx, m in enumerate(months_in_db, 1):
        st_raw = db[target_dir][target_sub][m].get("status", "")
        st_val = (
            "Раздельный по док."
            if isinstance(st_raw, dict) and "value" not in st_raw
            else (
                st_raw.get("value", "Нет")
                if isinstance(st_raw, dict)
                else (st_raw if st_raw else "Нет")
            )
        )
        # ИСПРАВЛЕНО: Добавлено красивое форматирование разрядов пробелами при выводе списка
        fmt_sum = db_core.fmt_money(db[target_dir][target_sub][m].get("sum", 0))
        print(f" {idx}. {m} (Сумма: {fmt_sum} руб. | СтрК: {st_val})")

    m_choice = input("\nВыберите номер периода: ").strip()
    if not m_choice or not m_choice.isdigit():
        return
    m_idx = int(m_choice) - 1
    if m_idx < 0 or m_idx >= len(months_in_db):
        return
    target_mth = months_in_db[m_idx]

    if sub_choice == "1":
        while True:
            new_sum_str = input("\nВведите новую сумму (или '0' для выхода в меню): ").strip()
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
        for i, m_name in enumerate(db_core.ALL_YEAR_MONTHS, 1):
            print(f" {i}. {m_name}")

        new_mth_choice = input("\nВведите номер (1-12): ").strip()
        if not new_mth_choice or not new_mth_choice.isdigit():
            return

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
        print("\nЧто изменить? 1 - СтрК, 2 - СДО, 3 - ГенДир, 4 - 1 экз. З., 5 - 1 экз. П")
        which = input("Введите номер (1-5): ").strip()
        if which not in ("1", "2", "3", "4", "5"):
            print(" [ОШИБКА] Неверный выбор.")
            return

        if which == "1":
            status_key = "СтрК"
        elif which == "2":
            status_key = "СДО"
        elif which == "3":
            status_key = "ГенДир"
        elif which == "4":
            status_key = "1 экз. З."
        else:
            status_key = "1 экз. П"

        print(f"\nВыберите статус {status_key}:\n 1. Зеленый | 2. Желтый | 3. Красный | 0. Очистить")
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
            # Обновляем строго выбранный статус-ключ, не перезаписывая соседние статусы.
            # Ожидаем структуру: status = {<doc_name>: {<status_key>: {value,date}}}
            # но поддерживаем совместимость со старыми форматами.
            current_status = db[target_dir][target_sub][target_mth].get("status", {})

            # Старый формат: общий "status" = {value,date} — это НЕ раздельные по ключам статусы.
            if isinstance(current_status, dict) and "value" in current_status:
                # В этом формате действительно единственный статус — обновляем его.
                db[target_dir][target_sub][target_mth]["status"] = {"value": status_value, "date": status_date}
            else:
                # Новый формат: status[doc] = {value,date} или status[doc][status_key] = {value,date}
                if not isinstance(current_status, dict):
                    current_status = {}

                # гарантируем, что в месяце есть dict по status
                if not isinstance(db[target_dir][target_sub][target_mth].get("status", {}), dict):
                    db[target_dir][target_sub][target_mth]["status"] = {}

                for d_name in config.DOCUMENTS_LIST:
                    mask = config.DOCUMENT_ROLES.get(d_name, {})
                    if mask.get(status_key, 1) != 1:
                        continue

                    doc_entry = db[target_dir][target_sub][target_mth].setdefault("status", {}).get(d_name)
                    if not isinstance(doc_entry, dict):
                        doc_entry = {}
                        db[target_dir][target_sub][target_mth].setdefault("status", {})[d_name] = doc_entry

                    # Изолированное обновление выбранного ключа
                    # Если структура уже status[doc][status_key]
                    if status_key in doc_entry and isinstance(doc_entry[status_key], dict):
                        doc_entry[status_key] = {"value": status_value, "date": status_date}
                    else:
                        # Если структура старая: status[doc] = {value,date}, то обновляем ТОЛЬКО value/date для этого документа,
                        # не затрагивая другие status_key (если они присутствуют где-то ещё).
                        # При наличии нескольких статусов в doc_entry — обновится только status_key.
                        doc_entry[status_key] = {"value": status_value, "date": status_date}

            db_core.save_db(db)
            wizard_git.register_action("status_changed")
            print(f" [УСПЕХ] Статус {status_key} успешно присвоен нужным документам периода! (изолированно) ")


        elif apply_mode == "2":
            allowed_docs = []
            for doc_name in config.DOCUMENTS_LIST:
                mask = config.DOCUMENT_ROLES.get(doc_name, {})
                if mask.get(status_key, 1) == 1:
                    allowed_docs.append(doc_name)

            if not allowed_docs:
                print(f" ⚠ [ВНИМАНИЕ] Нет доступных документов для {status_key}!")
                return

            print(f"\nДоступные документы для изменения {status_key}:")
            for idx, doc_name in enumerate(allowed_docs, 1):
                print(f" {idx}. {doc_name}")

            doc_choice = input(f"Выберите номер документа (1-{len(allowed_docs)}): ").strip()
            if not doc_choice or not doc_choice.isdigit():
                return

            doc_idx = int(doc_choice) - 1
            if doc_idx < 0 or doc_idx >= len(allowed_docs):
                return

            target_doc = allowed_docs[doc_idx]

            current_status = db[target_dir][target_sub][target_mth].get("status", {})

            # Приводим к структуре status[doc] либо status[doc][status_key].
            if not isinstance(current_status, dict):
                current_status = {}

            if "value" in current_status:
                # Старый формат: status = {value,date} (один общий статус) —
                # корректно разворачиваем в status[doc] = {status_key: {value,date}}.
                # Важно: сохраняем независимость статусов по ключам.
                db[target_dir][target_sub][target_mth]["status"] = {}
                for d_name in config.DOCUMENTS_LIST:
                    db[target_dir][target_sub][target_mth]["status"][d_name] = {
                        status_key: {
                            "value": current_status.get("value", ""),
                            "date": current_status.get("date", ""),
                        }
                    }

            # Достаём entry именно для выбранного документа.
            doc_entry = db[target_dir][target_sub][target_mth].setdefault("status", {}).get(target_doc)
            if not isinstance(doc_entry, dict):
                doc_entry = {}
                db[target_dir][target_sub][target_mth].setdefault("status", {})[target_doc] = doc_entry

            # Изолированно обновляем конкретный статус-ключ, не затрагивая соседние ключи.
            doc_entry[status_key] = {"value": status_value, "date": status_date}


            db_core.save_db(db)
            wizard_git.register_action("status_changed")
            print(f" [УСПЕХ] Статус {status_key} документа '{target_doc}' успешно обновлен!")

