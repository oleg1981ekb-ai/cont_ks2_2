import db_core
import config
import wizard_git


def menu_edit_data(select_target_func):
    """Логика изменения бюджетов, месяцев и статусов (Пункт 3)."""
    print("\n>> ВНЕСЕНИЕ ИЗМЕНЕНИЙ В ТАБЛИЦУ")
    db = db_core.load_db()
    if not db:
        return

    print(
        "Выберите тип изменений:\n"
        " 1. Изменить сумму месяца\n"
        " 2. Переименовать месяц\n"
        " 3. Изменить статусы\n"
        " 4. Удалить (месяц / подобъект / направление) с подтверждением\n"
        " 5. Изменить общую сумму договора (строка объекта)"

    )
    sub_choice = input("Выберите действие (1-5) или 0 для Назад: ").strip()
    if sub_choice == "0":
        return
    if sub_choice not in ("1", "2", "3", "4", "5"):
        return


    # Общая точка выбора (direction/sub_obj). Для варианта 4 могут потребоваться дополнительные шаги выбора.
    target_dir, target_sub = select_target_func(db, allow_new=False)
    if target_dir is None and target_sub is None:
        return
    if target_dir is None and target_sub is not None:
        # 0 на выборе Подобъекта => назад к выбору действия
        return
    if not target_dir or not target_sub:
        return

    # === ВАРИАНТ 1: сумма месяца ===
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
        fmt_sum = db_core.fmt_money(db[target_dir][target_sub][m].get("sum", 0))
        print(f" {idx}. {m} (Сумма: {fmt_sum} руб. | СтрК: {st_val})")

    m_choice = input("\nВыберите номер периода (0 для Назад): ").strip()
    if m_choice == "0":
        return
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
                return
            try:
                cleaned_sum = float(new_sum_str.replace(" ", "").replace(",", "."))
                if cleaned_sum < 0:
                    print(" ❌ [ОШИБКА] Сумма бюджета не может быть отрицательной!")
                    continue

                db[target_dir][target_sub][target_mth]["sum"] = cleaned_sum
                db["_meta"] = {
                    "last_changed_dir": target_dir,
                    "last_changed_sub": target_sub,
                    "is_new_change": True,
                }
                db_core.save_db(db)

                wizard_git.register_action("sum_changed")
                print(f"  [УСПЕХ] Бюджет успешно обновлен на: {db_core.fmt_money(cleaned_sum)} руб.")
                break
            except ValueError:
                print(" ❌ [ОШИБКА ВВОДА] Введите число без букв!")

    elif sub_choice == "2":
        # === Переименование месяца с пометкой '(УЖЕ ЕСТЬ)' при наличии месяца в той же ветке ===
        active_months = list(db[target_dir][target_sub].keys())

        print("\nВыберите НОВОЕ название месяца (при наличии будет пометка '(УЖЕ ЕСТЬ)'): ")
        for i, m_name in enumerate(db_core.ALL_YEAR_MONTHS, 1):
            marker = " (УЖЕ ЕСТЬ)" if m_name in active_months else ""
            print(f" {i}. {m_name}{marker}")

        new_mth_choice = input("\nВведите номер (1-12) или 0 для Назад: ").strip()
        if new_mth_choice == "0":
            return
        if not new_mth_choice or not new_mth_choice.isdigit():
            return

        new_mth_name = db_core.ALL_YEAR_MONTHS[int(new_mth_choice) - 1]

        # если пользователь выбрал тот же месяц — ничего не делаем
        if new_mth_name == target_mth:
            print("\nℹ Переименование не требуется: выбран тот же месяц.")
            return

        # согласование конфликта: новый месяц уже существует
        if new_mth_name in db[target_dir][target_sub]:
            print(
                f"\n⚠ Месяц '{new_mth_name}' уже существует в этой ветке. "
                "Как согласовать?\n 1. Слить бюджеты (старый -> существующий)\n 2. Отменить переименование"
            )
            confirm = input("\nВаш выбор (1-2): ").strip()
            if confirm != "1":
                return

            old = db[target_dir][target_sub].pop(target_mth)
            db[target_dir][target_sub][new_mth_name]["sum"] += float(old.get("sum", 0))

            db["_meta"] = {
                "last_changed_dir": target_dir,
                "last_changed_sub": target_sub,
                "is_new_change": True,
            }
            db_core.save_db(db)
            wizard_git.register_action("sum_changed")
            return

        # бесконфликтное переименование
        db[target_dir][target_sub][new_mth_name] = db[target_dir][target_sub].pop(target_mth)
        db["_meta"] = {
            "last_changed_dir": target_dir,
            "last_changed_sub": target_sub,
            "is_new_change": True,
        }
        db_core.save_db(db)
        wizard_git.register_action("branch_added")
        db_core.update_config_months(new_mth_name)

    elif sub_choice == "3":
        print("\nЧто изменить? 1 - СтрК, 2 - СДО, 3 - ГенДир, 4 - 1 экз. З., 5 - 1 экз. П")
        which = input("Введите номер (1-6) или 0 для Назад: ").strip()
        if which == "0":
            return
        if which not in ("1", "2", "3", "4", "5", "6"):
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
        elif which == "5":
            status_key = "1 экз. П"
        else:
            status_key = None

        if which == "6":
            status_value = 3
            status_date = db_core.get_short_date()

            month_obj = db[target_dir][target_sub][target_mth]
            month_status = month_obj.get("status", {})
            if not isinstance(month_status, dict):
                month_status = {}
            month_obj["status"] = month_status

            for d_name in config.DOCUMENTS_LIST:
                doc_entry = month_obj.setdefault("status", {}).setdefault(d_name, {})
                if not isinstance(doc_entry, dict):
                    doc_entry = {}
                    month_obj["status"][d_name] = doc_entry

                for sk in ("СтрК", "СДО", "ГенДир", "1 экз. З.", "1 экз. П"):
                    mask = config.DOCUMENT_ROLES.get(d_name, {})
                    if mask.get(sk, 1) != 1:
                        continue
                    doc_entry[sk] = {"value": status_value, "date": status_date}

            db["_meta"] = {
                "last_changed_dir": target_dir,
                "last_changed_sub": target_sub,
                "is_new_change": True,
            }
            db_core.save_db(db)
            wizard_git.register_action("status_mark_not_started")
            print(" [УСПЕХ] Все доступные ячейки проставлены как не начатые (3).")
            return

        tmp_status = db[target_dir][target_sub][target_mth].get("status", {})

        cur_value = ""
        cur_date = ""
        if isinstance(tmp_status, dict) and "value" in tmp_status:
            cur_value = tmp_status.get("value", "")
            cur_date = tmp_status.get("date", "")
        elif isinstance(tmp_status, dict):
            for d_name in config.DOCUMENTS_LIST:
                doc_obj = tmp_status.get(d_name)
                if not isinstance(doc_obj, dict):
                    continue
                sk_obj = doc_obj.get(status_key)
                if isinstance(sk_obj, dict) and ("value" in sk_obj or "date" in sk_obj):
                    cur_value = sk_obj.get("value", "")
                    cur_date = sk_obj.get("date", "")
                    break

        print(f"\nТекущее значение для '{status_key}' в периоде '{target_mth}': {cur_value} (дата: {cur_date})")

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
            current_status = db[target_dir][target_sub][target_mth].get("status", {})
            if isinstance(current_status, dict) and "value" in current_status:
                db[target_dir][target_sub][target_mth]["status"] = {"value": status_value, "date": status_date}
            else:
                if not isinstance(current_status, dict):
                    current_status = {}

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

                    if status_key in doc_entry and isinstance(doc_entry[status_key], dict):
                        doc_entry[status_key] = {"value": status_value, "date": status_date}
                    else:
                        doc_entry[status_key] = {"value": status_value, "date": status_date}

            db["_meta"] = {
                "last_changed_dir": target_dir,
                "last_changed_sub": target_sub,
                "is_new_change": True,
            }
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

            if not isinstance(current_status, dict):
                current_status = {}

            if "value" in current_status:
                db[target_dir][target_sub][target_mth]["status"] = {}
                for d_name in config.DOCUMENTS_LIST:
                    db[target_dir][target_sub][target_mth]["status"][d_name] = {
                        status_key: {
                            "value": current_status.get("value", ""),
                            "date": current_status.get("date", ""),
                        }
                    }

            doc_entry = db[target_dir][target_sub][target_mth].setdefault("status", {}).get(target_doc)
            if not isinstance(doc_entry, dict):
                doc_entry = {}
                db[target_dir][target_sub][target_mth].setdefault("status", {})[target_doc] = doc_entry

            doc_entry[status_key] = {"value": status_value, "date": status_date}

            db["_meta"] = {
                "last_changed_dir": target_dir,
                "last_changed_sub": target_sub,
                "is_new_change": True,
            }
            db_core.save_db(db)
            wizard_git.register_action("status_changed")
            print(f" [УСПЕХ] Статус {status_key} документа '{target_doc}' успешно обновлен!")

    elif sub_choice == "5":
        # === СУММА ДОГОВОРА: строка объекта (direction/sub_obj) ===
        # Общая сумма договора хранится на уровне db[direction][sub_obj]
        current_contract_sum = db[target_dir][target_sub].get("contract_sum", 0.0)
        print(f"\nТекущая общая сумма договора для '{target_sub}': {db_core.fmt_money(current_contract_sum)} руб.")
        
        while True:
            new_contract_sum_str = input("Введите общую сумму договора (руб.) (или '0' чтобы очистить): ").strip()
            if new_contract_sum_str.lower() == "выход":
                return
            if new_contract_sum_str == "0" or new_contract_sum_str == "":
                db[target_dir][target_sub]["contract_sum"] = 0.0
                break
            try:
                cleaned_sum = float(new_contract_sum_str.replace(" ", "").replace(",", "."))
                if cleaned_sum < 0:
                    print(" ❌ [ОШИБКА] Сумма договора не может быть отрицательной!")
                    continue
                db[target_dir][target_sub]["contract_sum"] = cleaned_sum
                break
            except ValueError:
                print(" ❌ [ОШИБКА ВВОДА] Введите число без букв!")

        db["_meta"] = {
            "last_changed_dir": target_dir,
            "last_changed_sub": target_sub,
            "is_new_change": True,
        }
        db_core.save_db(db)
        wizard_git.register_action("contract_sum_changed")
        print(f" [УСПЕХ] Общая сумма договора обновлена: {db_core.fmt_money(db[target_dir][target_sub]['contract_sum'])} руб.")

    elif sub_choice == "4":

        # === УДАЛЕНИЕ: собрать в одну кнопку 4 ===
        print("\n[УДАЛЕНИЕ] Выберите объект для удаления:")
        print(" 1. Месяц")
        print(" 2. Подобъект (под-объект) — удалить направление/sub_obj полностью")
        print(" 3. Направление — удалить direction полностью")

        del_level = input("Выберите уровень (1-3) или 0 для Назад: ").strip()
        if del_level == "0":
            return
        if del_level not in ("1", "2", "3"):
            return

        if del_level == "1":
            cur_sum = db[target_dir][target_sub][target_mth].get("sum", 0)
            cur_status = db[target_dir][target_sub][target_mth].get("status", {})
            print(f"\nБудет удален месяц: {target_mth}")
            print(f" Текущая сумма: {cur_sum}")
            print(f" Текущий status (кратко): {'dict' if isinstance(cur_status, dict) else cur_status}")
            confirm = input(
                f"Подтвердите удаление месяца '{target_mth}'? (1=Да / 2=Нет, 0=Назад): "
            ).strip()
            if confirm == "0":
                return
            if confirm != "1":
                return
            db[target_dir][target_sub].pop(target_mth, None)
            db["_meta"] = {
                "last_changed_dir": target_dir,
                "last_changed_sub": target_sub,
                "is_new_change": True,
            }
            db_core.save_db(db)
            wizard_git.register_action("month_deleted")
            print(f" [УСПЕХ] Месяц '{target_mth}' удален.")

        elif del_level == "2":
            months_cnt = len(db[target_dir].get(target_sub, {}))
            confirm = input(
                f"Подтвердите удаление подобъекта '{target_sub}' в направлении '{target_dir}'? (1=Да / 2=Нет, 0=Назад). Месяцев: {months_cnt}: "
            ).strip()
            if confirm == "0":
                return
            if confirm != "1":
                return
            db[target_dir].pop(target_sub, None)
            db["_meta"] = {
                "last_changed_dir": target_dir,
                "last_changed_sub": target_sub,
                "is_new_change": True,
            }
            db_core.save_db(db)
            wizard_git.register_action("sub_object_deleted")
            print(f" [УСПЕХ] Подобъект '{target_sub}' удален.")

        elif del_level == "3":
            sub_cnt = len(db.get(target_dir, {}))
            confirm = input(
                f"Подтвердите удаление направления '{target_dir}'? (1=Да / 2=Нет, 0=Назад). Подобъектов: {sub_cnt}: "
            ).strip()
            if confirm == "0":
                return
            if confirm != "1":
                return
            db.pop(target_dir, None)
            db["_meta"] = {
                "last_changed_dir": target_dir,
                "last_changed_sub": target_sub,
                "is_new_change": True,
            }
            db_core.save_db(db)
            wizard_git.register_action("direction_deleted")
            print(f" [УСПЕХ] Направление '{target_dir}' удалено.")

