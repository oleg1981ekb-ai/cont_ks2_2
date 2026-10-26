import db_core
import config
import wizard_git


def select_month(db, direction, sub_obj):
    months_in_db = [m for m in db_core.ALL_YEAR_MONTHS if m in db[direction][sub_obj]]
    print("\nТекущие активные периоды:")
    for idx, m in enumerate(months_in_db, 1):
        mth_data = db[direction][sub_obj].get(m, {})
        if not isinstance(mth_data, dict):
            fmt_sum = db_core.fmt_money(mth_data)
            print(f" {idx}. {m} (Сумма: {fmt_sum} руб. | СтрК: Нет)")
            continue

        st_raw = mth_data.get("status", "")
        st_val = (
            "Раздельный по док."
            if isinstance(st_raw, dict) and "value" not in st_raw
            else (
                st_raw.get("value", "Нет")
                if isinstance(st_raw, dict)
                else (st_raw if st_raw else "Нет")
            )
        )
        fmt_sum = db_core.fmt_money(mth_data.get("sum", 0))
        print(f" {idx}. {m} (Сумма: {fmt_sum} руб. | СтрК: {st_val})")

    m_choice = input("\nВыберите номер периода (0 для Назад): ").strip()
    if m_choice == "0" or not m_choice or not m_choice.isdigit():
        return None
    m_idx = int(m_choice) - 1
    if m_idx < 0 or m_idx >= len(months_in_db):
        return None
    return months_in_db[m_idx]


def edit_month_sum(db, direction, sub_obj, month):
    while True:
        new_sum_str = input("\nВведите новую сумму (или '0' для выхода в меню): ").strip()
        if new_sum_str.lower() in ("выход", "0"):
            return
        try:
            cleaned_sum = float(new_sum_str.replace(" ", "").replace(",", "."))
            if cleaned_sum < 0:
                print(" ❌ [ОШИБКА] Сумма бюджета не может быть отрицательной!")
                continue

            db[direction][sub_obj][month]["sum"] = cleaned_sum
            db["_meta"] = {
                "last_changed_dir": direction,
                "last_changed_sub": sub_obj,
                "is_new_change": True,
            }
            db_core.save_db(db)
            wizard_git.register_action("sum_changed")
            print(f"  [УСПЕХ] Бюджет успешно обновлен на: {db_core.fmt_money(cleaned_sum)} руб.")
            break
        except ValueError:
            print(" ❌ [ОШИБКА ВВОДА] Введите число без букв!")


def rename_month(db, direction, sub_obj, month):
    print("\nВыберите НОВОЕ название месяца (при наличии будет пометка '(УЖЕ ЕСТЬ)'): ")
    active_months = list(db[direction][sub_obj].keys())
    for i, m_name in enumerate(db_core.ALL_YEAR_MONTHS, 1):
        marker = " (УЖЕ ЕСТЬ)" if m_name in active_months else ""
        print(f" {i}. {m_name}{marker}")

    new_mth_choice = input("\nВведите номер (1-12) или 0 для Назад: ").strip()
    if new_mth_choice == "0" or not new_mth_choice or not new_mth_choice.isdigit():
        return
    new_mth_name = db_core.ALL_YEAR_MONTHS[int(new_mth_choice) - 1]

    if new_mth_name == month:
        print("\nℹ Переименование не требуется: выбран тот же месяц.")
        return

    if new_mth_name in db[direction][sub_obj]:
        print(
            f"\n⚠ Месяц '{new_mth_name}' уже существует в этой ветке. "
            "Как согласовать?\n 1. Слить бюджеты (старый -> существующий)\n 2. Отменить переименование"
        )
        confirm = input("\nВаш выбор (1-2): ").strip()
        if confirm != "1":
            return

        old = db[direction][sub_obj].pop(month)
        db[direction][sub_obj][new_mth_name]["sum"] += float(old.get("sum", 0))
        db["_meta"] = {
            "last_changed_dir": direction,
            "last_changed_sub": sub_obj,
            "is_new_change": True,
        }
        db_core.save_db(db)
        wizard_git.register_action("sum_changed")
        return

    db[direction][sub_obj][new_mth_name] = db[direction][sub_obj].pop(month)
    db["_meta"] = {
        "last_changed_dir": direction,
        "last_changed_sub": sub_obj,
        "is_new_change": True,
    }
    db_core.save_db(db)
    wizard_git.register_action("branch_added")
    db_core.update_config_months(new_mth_name)


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


def manage_sub_docs(db, direction, sub_obj):
    sub_docs = db[direction][sub_obj].setdefault("documents", [])
    if not isinstance(sub_docs, list):
        sub_docs = []
        db[direction][sub_obj]["documents"] = sub_docs

    while True:
        print(f"\n>>> ДОКУМЕНТЫ ПОДОБЪЕКТА '{sub_obj}' (уровень 2, братья месяцев)")
        if not sub_docs:
            print("  Документы не найдены.")
        else:
            for idx, doc in enumerate(sub_docs, 1):
                name = doc.get("name", "")
                date = doc.get("date", "")
                status = doc.get("status", "")
                comment = doc.get("comment", "")
                status_txt = f" [{'🟢' if status == 1 else '🟡' if status == 2 else '🔴' if status == 3 else '—'}]"
                date_txt = f" ({date})" if date else ""
                comment_txt = f" — {comment}" if comment else ""
                print(f"  {idx}. {name}{date_txt}{status_txt}{comment_txt}")

        print("\n 1. Добавить документ")
        print(" 2. Удалить документ по номеру")
        print(" 0. Назад в главное меню изменений")
        doc_choice = input("\nВыберите действие (0-2): ").strip()

        if doc_choice == "0":
            break

        elif doc_choice == "1":
            name = input("Введите название документа: ").strip()
            if not name:
                print(" ❌ Название не может быть пустым.")
                continue
            date = input("Введите дату (ДД.ММ, optional): ").strip()
            print("Статус: 1. Зеленый | 2. Желтый | 3. Красный | 0. Без статуса")
            st = input("Выберите статус (0-3): ").strip()
            status_val = ""
            if st == "1":
                status_val = 1
            elif st == "2":
                status_val = 2
            elif st == "3":
                status_val = 3
            elif st not in ("0", ""):
                print(" ❌ Неверный статус, будет установлен без статуса.")
            comment = input("Комментарий (optional): ").strip()

            sub_docs.append({
                "name": name,
                "date": date,
                "status": status_val,
                "comment": comment,
            })
            db["_meta"] = {
                "last_changed_dir": direction,
                "last_changed_sub": sub_obj,
                "is_new_change": True,
            }
            db_core.save_db(db)
            wizard_git.register_action("status_changed")
            print(f" [УСПЕХ] Документ '{name}' добавлен.")

        elif doc_choice == "2":
            if not sub_docs:
                print(" Нет документов для удаления.")
                continue
            num = input("Введите номер документа для удаления: ").strip()
            if not num.isdigit():
                print(" ❌ Введите число.")
                continue
            idx = int(num) - 1
            if idx < 0 or idx >= len(sub_docs):
                print(" ❌ Неверный номер.")
                continue
            removed = sub_docs.pop(idx)
            db["_meta"] = {
                "last_changed_dir": direction,
                "last_changed_sub": sub_obj,
                "is_new_change": True,
            }
            db_core.save_db(db)
            wizard_git.register_action("status_changed")
            print(f" [УСПЕХ] Документ '{removed.get('name', '')}' удален.")

        else:
            print(" ❌ Неверный выбор.")


def manage_payments(db, direction, sub_obj):
    payments = db[direction][sub_obj].setdefault("payments", [])
    if not isinstance(payments, list):
        payments = []
        db[direction][sub_obj]["payments"] = payments

    while True:
        print(f"\n>>> ПЛАТЕЖИ ПОДОБЪЕКТА '{sub_obj}'")
        if not payments:
            print("  Платежи не найдены.")
        else:
            total = sum(float(p) for p in payments if p is not None)
            for idx, p in enumerate(payments, 1):
                print(f"  {idx}. {db_core.fmt_money(p)} руб.")
            print(f"  Итого: {db_core.fmt_money(total)} руб.")

        print("\n 1. Добавить платёж")
        print(" 2. Очистить все платежи")
        print(" 0. Назад в главное меню изменений")
        pay_choice = input("\nВыберите действие (0-2): ").strip()

        if pay_choice == "0":
            return

        elif pay_choice == "1":
            pay_str = input("Введите сумму платежа (руб.): ").strip()
            if not pay_str:
                print(" ❌ Сумма не может быть пустой.")
                continue
            try:
                pay_val = float(pay_str.replace(" ", "").replace(",", "."))
                if pay_val < 0:
                    print(" ❌ Сумма платежа не может быть отрицательной!")
                    continue
            except ValueError:
                print(" ❌ Введите число без букв!")
                continue

            payments.append(pay_val)
            db["_meta"] = {
                "last_changed_dir": direction,
                "last_changed_sub": sub_obj,
                "is_new_change": True,
            }
            db_core.save_db(db)
            wizard_git.register_action("status_changed")
            print(f" [УСПЕХ] Платёж {db_core.fmt_money(pay_val)} руб. добавлен.")

        elif pay_choice == "2":
            confirm = input("Подтвердите удаление всех платежей? (1=Да / 2=Нет): ").strip()
            if confirm != "1":
                continue
            payments.clear()
            db["_meta"] = {
                "last_changed_dir": direction,
                "last_changed_sub": sub_obj,
                "is_new_change": True,
            }
            db_core.save_db(db)
            wizard_git.register_action("status_changed")
            print(" [УСПЕХ] Все платежи удалены.")

        else:
            print(" ❌ Неверный выбор.")


def manage_extra_docs(db, direction, sub_obj, month):
    month_obj = db[direction][sub_obj][month]

    extra_docs = month_obj.get("extra_docs", [])
    if not isinstance(extra_docs, list):
        extra_docs = []

    optional_docs = [
        d
        for d in config.DOCUMENTS_LIST
        if d in ("Акт передачи оборудования", "Акт расхода давальческих материалов")
    ]

    print("\n[ДОКУМЕНТЫ МЕСЯЦА] Добавить/удалить дополнительные документы для: " + str(month))
    for i, d_name in enumerate(optional_docs, 1):
        mark = " [ВКЛЮЧЕНО]" if d_name in extra_docs else " [ВЫКЛЮЧЕНО]"
        print(f" {i}. {d_name}{mark}")

    print("\n1) Добавить выбранный документ\n2) Удалить выбранный документ\n0) Назад")
    op = input("Выберите режим (0-2): ").strip()
    if op == "0" or op not in ("1", "2"):
        return

    doc_choice = input(f"Введите номер документа (1-{len(optional_docs)}): ").strip()
    if not doc_choice or not doc_choice.isdigit():
        return
    di = int(doc_choice) - 1
    if di < 0 or di >= len(optional_docs):
        return

    chosen_doc = optional_docs[di]

    if op == "1":
        if chosen_doc not in extra_docs:
            extra_docs.append(chosen_doc)
    else:
        if chosen_doc in extra_docs:
            extra_docs.remove(chosen_doc)

    month_obj["extra_docs"] = extra_docs
    db["_meta"] = {
        "last_changed_dir": direction,
        "last_changed_sub": sub_obj,
        "is_new_change": True,
    }
    db_core.save_db(db)
    wizard_git.register_action("extra_docs_changed")
    print(" [УСПЕХ] Доп. документы месяца обновлены.")


def edit_contract_sum(db, direction, sub_obj):
    current_contract_sum = db[direction][sub_obj].get("contract_sum", 0.0)
    print(
        f"\nТекущая общая сумма договора для '{sub_obj}': {db_core.fmt_money(current_contract_sum)} руб."
    )

    new_contract_sum_str = input("Введите общую сумму договора (руб.) (или '0' чтобы очистить): ").strip()
    if new_contract_sum_str == "0" or new_contract_sum_str == "":
        db[direction][sub_obj]["contract_sum"] = 0.0
    else:
        cleaned_sum = float(new_contract_sum_str.replace(" ", "").replace(",", "."))
        if cleaned_sum < 0:
            return
        db[direction][sub_obj]["contract_sum"] = cleaned_sum

    db["_meta"] = {
        "last_changed_dir": direction,
        "last_changed_sub": sub_obj,
        "is_new_change": True,
    }
    db_core.save_db(db)
    wizard_git.register_action("contract_sum_changed")
    print(
        f" [УСПЕХ] Общая сумма договора обновлена: {db_core.fmt_money(db[direction][sub_obj]['contract_sum'])} руб."
    )


def manage_payment_comment(db, direction, sub_obj):
    months_in_db = [
        m
        for m in db_core.ALL_YEAR_MONTHS
        if m in db.get(direction, {}).get(sub_obj, {})
    ]
    if not months_in_db:
        print("\n⚠ Для выбранной ветки нет доступных периодов (месяцев).")
        input("\nНажмите Enter для возврата в меню...")
        return

    print("\nТекущие активные периоды:")
    for idx, m in enumerate(months_in_db, 1):
        print(f" {idx}. {m}")

    m_choice = input("\nВведите номер периода (0 для Назад): ").strip()
    if m_choice == "0" or not m_choice or not m_choice.isdigit():
        return

    m_idx = int(m_choice) - 1
    if m_idx < 0 or m_idx >= len(months_in_db):
        return
    target_mth = months_in_db[m_idx]

    current_comment = db[direction][sub_obj][target_mth].get("payment_comment", "")
    print(
        f"\n[ДАННЫЕ JSON] Текущий комментарий к оплате: "
        f"{current_comment if current_comment else 'отсутствует'}"
    )

    print("\nВыберите действие:")
    print(" 1. Изменить/добавить комментарий")
    print(" 2. Полностью удалить комментарий")
    comment_action = input("Ваш выбор (1-2): ").strip()

    if comment_action == "2":
        db[direction][sub_obj][target_mth].pop("payment_comment", None)
        db.setdefault("_meta", {})
        db["_meta"]["is_new_change"] = True
        db["_meta"]["last_changed_dir"] = direction
        db["_meta"]["last_changed_sub"] = sub_obj

        wizard_git.register_action("status_changed")
        db_core.save_db(db)

        print(" [ОК] Комментарий успешно удален из базы данных.")
        input("\nНажмите Enter для возврата в меню...")
        return

    if comment_action != "1":
        return

    print("Выберите шаблон комментария:")
    print(" 1. Переданы инженеру ПТО/СтрК с...")
    print(" 2. Переданы специалисту СДО с...")
    print(" 3. На подписи у ГД с...")
    print(" 4. В подготовке в бухгалтерии с...")
    print(" 9. Ввести свой текстовый вариант (без шаблона)")

    tpl_choice = input("Ваш выбор (1-4 или 9): ").strip()

    if tpl_choice in ("1", "2", "3", "4"):
        date_str = input("Введите дату и месяц (например, DD/MM): ").strip()

        if tpl_choice == "1":
            new_comment = f"Переданы инженеру ПТО/СтрК с {date_str}"
        elif tpl_choice == "2":
            new_comment = f"Переданы специалисту СДО с {date_str}"
        elif tpl_choice == "3":
            new_comment = f"На подписи у ГД с {date_str}"
        else:
            new_comment = f"В подготовке в бухгалтерии с {date_str}"

    elif tpl_choice == "9":
        new_comment = input("Введите свой вариант комментария: ").strip()
    else:
        return

    db[direction][sub_obj][target_mth]["payment_comment"] = new_comment
    db.setdefault("_meta", {})
    db["_meta"]["last_changed_dir"] = direction
    db["_meta"]["last_changed_sub"] = sub_obj
    db["_meta"]["is_new_change"] = True

    wizard_git.register_action("status_changed")
    db_core.save_db(db)

    print("\n[Успех] Комментарий к оплате сохранён.")
    input("\nНажмите Enter для возврата в меню...")
    return


def delete_structure(db, direction, sub_obj, select_target_func):
    months_in_db = [m for m in db_core.ALL_YEAR_MONTHS if m in db[direction][sub_obj]]
    print("\nТекущие активные периоды:")
    for idx, m in enumerate(months_in_db, 1):
        print(f" {idx}. {m}")
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
        m_choice = input("\nВыберите номер периода (0 для Назад): ").strip()
        if m_choice == "0" or not m_choice or not m_choice.isdigit():
            return
        m_idx = int(m_choice) - 1
        if m_idx < 0 or m_idx >= len(months_in_db):
            return
        target_mth = months_in_db[m_idx]

        db[direction][sub_obj].pop(target_mth, None)
        db["_meta"] = {
            "last_changed_dir": direction,
            "last_changed_sub": sub_obj,
            "is_new_change": True,
        }
        db_core.save_db(db)
        wizard_git.register_action("month_deleted")
        print(f" [УСПЕХ] Месяц '{target_mth}' удален.")

    elif del_level == "2":
        db[direction].pop(sub_obj, None)
        db["_meta"] = {
            "last_changed_dir": direction,
            "last_changed_sub": sub_obj,
            "is_new_change": True,
        }
        db_core.save_db(db)
        wizard_git.register_action("sub_object_deleted")
        print(f" [УСПЕХ] Подобъект '{sub_obj}' удален.")

    elif del_level == "3":
        db.pop(direction, None)
        db["_meta"] = {
            "last_changed_dir": direction,
            "last_changed_sub": sub_obj,
            "is_new_change": True,
        }
        db_core.save_db(db)
        wizard_git.register_action("direction_deleted")
        print(f" [УСПЕХ] Направление '{direction}' удалено.")


def rename_direction(db, direction, select_target_func):
    print("\n >> ПЕРЕИМЕНОВАНИЕ НАПРАВЛЕНИЯ")
    new_dir_name = input(f"Введите новое имя для направления '{direction}': ").strip()
    if not new_dir_name or new_dir_name == direction:
        print(" ❌ [ОШИБКА] Имя не может быть пустым или совпадать со старым!")
        return

    if new_dir_name in db:
        print(f" ❌ [ОШИБКА] Направление '{new_dir_name}' уже существует в базе!")
        return

    db[new_dir_name] = db.pop(direction)
    db["_meta"] = {
        "last_changed_dir": new_dir_name,
        "last_changed_sub": "",
        "is_new_change": True
    }
    db_core.save_db(db)
    wizard_git.register_action("status_changed")
    print(f" [УСПЕХ] Направление переименовано в '{new_dir_name}'!")


def delete_structure_simple(db, direction, sub_obj):
    """Удаление структуры с уже выбранными direction/sub_obj (без повторного выбора)."""
    months_in_db = [m for m in db_core.ALL_YEAR_MONTHS if m in db[direction][sub_obj]]
    print("\nТекущие активные периоды:")
    for idx, m in enumerate(months_in_db, 1):
        print(f" {idx}. {m}")
    print("\n[УДАЛЕНИЕ] Выберите объект для удаления:")
    print(" 1. Месяц")
    print(" 2. Подобъект (под-объект) — удалить направление/sub_obj полностью")
    print(" 3. Направление — удалить direction полностью")

    del_level = input("Выберите уровень (1-3): ").strip()
    if del_level not in ("1", "2", "3"):
        return

    if del_level == "1":
        m_choice = input("\nВыберите номер периода (0 для Назад): ").strip()
        if m_choice == "0" or not m_choice or not m_choice.isdigit():
            return
        m_idx = int(m_choice) - 1
        if m_idx < 0 or m_idx >= len(months_in_db):
            return
        target_mth = months_in_db[m_idx]

        db[direction][sub_obj].pop(target_mth, None)
        db["_meta"] = {
            "last_changed_dir": direction,
            "last_changed_sub": sub_obj,
            "is_new_change": True,
        }
        db_core.save_db(db)
        wizard_git.register_action("month_deleted")
        print(f" [УСПЕХ] Месяц '{target_mth}' удален.")

    elif del_level == "2":
        months_cnt = len(db[direction].get(sub_obj, {}))
        confirm = input(
            f"Подтвердите удаление подобъекта '{sub_obj}' в направлении '{direction}'? (1=Да / 2=Нет). Месяцев: {months_cnt}: "
        ).strip()
        if confirm != "1":
            return
        db[direction].pop(sub_obj, None)
        db["_meta"] = {
            "last_changed_dir": direction,
            "last_changed_sub": sub_obj,
            "is_new_change": True,
        }
        db_core.save_db(db)
        wizard_git.register_action("sub_object_deleted")
        print(f" [УСПЕХ] Подобъект '{sub_obj}' удален.")

    elif del_level == "3":
        sub_cnt = len(db.get(direction, {}))
        confirm = input(
            f"Подтвердите удаление направления '{direction}'? (1=Да / 2=Нет). Подобъектов: {sub_cnt}: "
        ).strip()
        if confirm != "1":
            return
        db.pop(direction, None)
        db["_meta"] = {
            "last_changed_dir": direction,
            "last_changed_sub": sub_obj,
            "is_new_change": True,
        }
        db_core.save_db(db)
        wizard_git.register_action("direction_deleted")
        print(f" [УСПЕХ] Направление '{direction}' удалено.")


def rename_sub_object(db, direction, sub_obj):
    print("\n >> ПЕРЕИМЕНОВАНИЕ ПОДОБЪЕКТА")
    new_sub_name = input(f"Введите новое имя для подобъекта '{sub_obj}' в направлении '{direction}': ").strip()
    if not new_sub_name or new_sub_name == sub_obj:
        print(" ❌ [ОШИБКА] Имя не может быть пустым или совпадать со старым!")
        return

    if new_sub_name in db[direction]:
        print(f" ❌ [ОШИБКА] Подобъект '{new_sub_name}' уже существует в направлении '{direction}'!")
        return

    db[direction][new_sub_name] = db[direction].pop(sub_obj)
    db["_meta"] = {
        "last_changed_dir": direction,
        "last_changed_sub": new_sub_name,
        "is_new_change": True
    }
    db_core.save_db(db)
    wizard_git.register_action("status_changed")
    print(f" [УСПЕХ] Подобъект переименован в '{new_sub_name}'!")