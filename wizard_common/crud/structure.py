import db_core
import wizard_git


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