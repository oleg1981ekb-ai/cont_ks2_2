import db_core
import config
import wizard_git
import wizard_common


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
        " 4. Удалить (месяц / podobъект / направление) с подтверждением\n"
        " 5. Документы Подобъекта (братья месяцев)"
    )
    sub_choice = input("Выберите действие (1-5): ").strip()
    if sub_choice not in ("1", "2", "3", "4", "5"):
        return

    # Общая точка выбора (direction/sub_obj). Для варианта 4 могут потребоваться дополнительные шаги выбора.
    target_dir, target_sub = select_target_func(db, allow_new=False)
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

    m_choice = input("\nВыберите номер периода: ").strip()
    if not m_choice or not m_choice.isdigit():
        return
    m_idx = int(m_choice) - 1
    if m_idx < 0 or m_idx >= len(months_in_db):
        return
    target_mth = months_in_db[m_idx]

    if sub_choice == "1":
        wizard_common.edit_month_sum(db, target_dir, target_sub, target_mth)
        return

    elif sub_choice == "2":
        wizard_common.rename_month(db, target_dir, target_sub, target_mth)
        return

    elif sub_choice == "3":
        wizard_common.edit_status(db, target_dir, target_sub, target_mth)
        return

    elif sub_choice == "4":
        wizard_common.delete_structure_simple(db, target_dir, target_sub)
        return

    elif sub_choice == "5":
        wizard_common.manage_sub_docs(db, target_dir, target_sub)
        return
