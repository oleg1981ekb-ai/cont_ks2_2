import config
import db_core
import wizard_git


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
        print(" 3. Редактировать документ (статус/дата/комментарий)")
        print(" 0. Назад в главное меню изменений")
        doc_choice = input("\nВыберите действие (0-3): ").strip()

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

        elif doc_choice == "3":
            if not sub_docs:
                print(" Нет документов для редактирования.")
                continue
            num = input("Введите номер документа для редактирования: ").strip()
            if not num.isdigit():
                print(" ❌ Введите число.")
                continue
            idx = int(num) - 1
            if idx < 0 or idx >= len(sub_docs):
                print(" ❌ Неверный номер.")
                continue
            doc = sub_docs[idx]
            print(f"\n[РЕДАКТИРОВАНИЕ] Документ: {doc.get('name', '')}")
            print(" 1. Изменить статус (1/2/3/0)")
            print(" 2. Изменить дату (ДД.ММ)")
            print(" 3. Изменить комментарий")
            edit_choice = input("Выберите (1-3): ").strip()
            if edit_choice == "1":
                doc["status"] = ""
                st = input("Статус: 1. Зеленый | 2. Желтый | 3. Красный | 0. Без статуса: ").strip()
                if st == "1":
                    doc["status"] = 1
                elif st == "2":
                    doc["status"] = 2
                elif st == "3":
                    doc["status"] = 3
                else:
                    doc["status"] = ""
            elif edit_choice == "2":
                doc["date"] = input("Новая дата (ДД.ММ): ").strip()
            elif edit_choice == "3":
                doc["comment"] = input("Новый комментарий: ").strip()

            db["_meta"] = {
                "last_changed_dir": direction,
                "last_changed_sub": sub_obj,
                "is_new_change": True,
            }
            db_core.save_db(db)
            wizard_git.register_action("status_changed")
            print(f" [УСПЕХ] Документ '{doc.get('name', '')}' обновлен.")

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
        print(" 2. Изменить платёж по номеру")
        print(" 3. Удалить платёж по номеру")
        print(" 4. Очистить все платежи")
        print(" 0. Назад в главное меню изменений")
        pay_choice = input("\nВыберите действие (0-4): ").strip()

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
            if not payments:
                print(" Платежи не найдены для изменения.")
                continue
            num = input("Введите номер платежа для изменения: ").strip()
            if not num.isdigit():
                print(" ❌ Введите число.")
                continue
            idx = int(num) - 1
            if idx < 0 or idx >= len(payments):
                print(" ❌ Неверный номер.")
                continue
            print(f" Текущее значение: {db_core.fmt_money(payments[idx])} руб.")
            new_str = input("Введите новую сумму платежа (руб.): ").strip()
            if not new_str:
                print(" ❌ Сумма не может быть пустой.")
                continue
            try:
                new_val = float(new_str.replace(" ", "").replace(",", "."))
                if new_val < 0:
                    print(" ❌ Сумма платежа не может быть отрицательной!")
                    continue
            except ValueError:
                print(" ❌ Введите число без букв!")
                continue
            old_val = payments[idx]
            payments[idx] = new_val
            db["_meta"] = {
                "last_changed_dir": direction,
                "last_changed_sub": sub_obj,
                "is_new_change": True,
            }
            db_core.save_db(db)
            wizard_git.register_action("status_changed")
            print(f" [УСПЕХ] Платёж изменён: {db_core.fmt_money(old_val)} → {db_core.fmt_money(new_val)} руб.")

        elif pay_choice == "3":
            if not payments:
                print(" Платежи не найдены для удаления.")
                continue
            num = input("Введите номер платежа для удаления: ").strip()
            if not num.isdigit():
                print(" ❌ Введите число.")
                continue
            idx = int(num) - 1
            if idx < 0 or idx >= len(payments):
                print(" ❌ Неверный номер.")
                continue
            removed = payments.pop(idx)
            db["_meta"] = {
                "last_changed_dir": direction,
                "last_changed_sub": sub_obj,
                "is_new_change": True,
            }
            db_core.save_db(db)
            wizard_git.register_action("status_changed")
            print(f" [УСПЕХ] Платёж {db_core.fmt_money(removed)} руб. удалён.")

        elif pay_choice == "4":
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
    print(" 1. Изменить/Добавить комментарий")
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