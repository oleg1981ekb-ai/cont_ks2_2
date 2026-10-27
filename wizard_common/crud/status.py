import config
import db_core
import wizard_git


def _normalize_status_for_month(month_obj, direction, sub_obj, month, db):
    status_obj = month_obj.get("status", {})
    if not isinstance(status_obj, dict):
        return

    if "value" in status_obj and "date" in status_obj and "col_key" in status_obj:
        col_key = status_obj.get("col_key")
        flat_value = status_obj.get("value")
        flat_date = status_obj.get("date")
        for d_name in config.DOCUMENTS_LIST:
            mask = config.DOCUMENT_ROLES.get(d_name, {})
            if mask.get(col_key, 1) != 1:
                continue
            doc_entry = status_obj.setdefault(d_name, {})
            if not isinstance(doc_entry, dict):
                doc_entry = {}
                status_obj[d_name] = doc_entry
            doc_entry[col_key] = {"value": flat_value, "date": flat_date}
        status_obj.pop("value", None)
        status_obj.pop("date", None)
        status_obj.pop("col_key", None)
        month_obj["status"] = status_obj
        db["_meta"] = {
            "last_changed_dir": direction,
            "last_changed_sub": sub_obj,
            "is_new_change": True,
        }
        db_core.save_db(db)
        wizard_git.register_action("status_changed")


def edit_status(db, direction, sub_obj, month):
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

        month_obj = db[direction][sub_obj][month]
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
            "last_changed_dir": direction,
            "last_changed_sub": sub_obj,
            "is_new_change": True,
        }
        db_core.save_db(db)
        wizard_git.register_action("status_mark_not_started")
        print(" [УСПЕХ] Все доступные ячейки проставлены как не начатые (3).")
        return

    month_obj = db[direction][sub_obj][month]
    _normalize_status_for_month(month_obj, direction, sub_obj, month, db)

    tmp_status = month_obj.get("status", {})
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

    print(f"\nТекущее значение для '{status_key}' в периоде '{month}': {cur_value} (дата: {cur_date})")

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
        current_status = month_obj.get("status", {})
        if not isinstance(current_status, dict):
            current_status = {}

        if not isinstance(db[direction][sub_obj][month].get("status", {}), dict):
            db[direction][sub_obj][month]["status"] = {}

        for d_name in config.DOCUMENTS_LIST:
            mask = config.DOCUMENT_ROLES.get(d_name, {})
            if mask.get(status_key, 1) != 1:
                continue

            doc_entry = db[direction][sub_obj][month].setdefault("status", {}).get(d_name)
            if not isinstance(doc_entry, dict):
                doc_entry = {}
                db[direction][sub_obj][month].setdefault("status", {})[d_name] = doc_entry

            if status_key in doc_entry and isinstance(doc_entry[status_key], dict):
                doc_entry[status_key] = {"value": status_value, "date": status_date}
            else:
                doc_entry[status_key] = {"value": status_value, "date": status_date}

        db["_meta"] = {
            "last_changed_dir": direction,
            "last_changed_sub": sub_obj,
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

        month_obj = db.get(direction, {}).get(sub_obj, {}).get(month)
        if not isinstance(month_obj, dict):
            print(f"\n ❌ [ОШИБКА] Период '{month}' в базе поврежден (ожидался dict). Операция отменена.")
            return

        status_obj = month_obj.get("status", {})
        if not isinstance(status_obj, dict):
            status_obj = {}
            month_obj["status"] = status_obj

        doc_entry = status_obj.get(target_doc)
        if not isinstance(doc_entry, dict):
            doc_entry = {}
            status_obj[target_doc] = doc_entry

        doc_entry[status_key] = {"value": status_value, "date": status_date}
        db[direction][sub_obj][month] = month_obj

        db["_meta"] = {
            "last_changed_dir": direction,
            "last_changed_sub": sub_obj,
            "is_new_change": True,
        }
        db_core.save_db(db)
        wizard_git.register_action("status_changed")
        print(f" [УСПЕХ] Статус {status_key} документа '{target_doc}' успешно обновлен!")

    else:
        print(" [ОШИБКА] Неверный выбор.")