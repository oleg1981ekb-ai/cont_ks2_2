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