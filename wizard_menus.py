import db_core
import config

def select_hierarchy_target(db, allow_new=False):
    """Выбор Направления и Подобъекта по шагам с поддержкой "0".

    ТЗ:
      - "0" на выборе Направления => Назад на предыдущий шаг (None, None)
      - "0" на выборе Подобъекта => Назад на шаг выбора Направления (None, target_dir)

    Возвращаемые значения:
      - (target_dir, target_sub) при успешном выборе
      - (None, None) при выходе "Назад" с шага направления или при отмене
      - (None, target_dir) при "Назад" с шага подобъекта
    """

    target_dir = ""
    directions = list(db.keys())

    if not directions:
        if allow_new:
            target_dir = input("База пуста. Введите название Направления: ").strip()
        else:
            return None, None

    while True:
        # --- Шаг 1: Направление ---
        if directions:
            print("\nДоступные Направления:")
            for idx, d in enumerate(directions, 1):
                print(f" {idx}. {d}")
            if allow_new:
                print(f" {len(directions) + 1}. [Создать НОВОЕ Направление]")

            limit = len(directions) + 1 if allow_new else len(directions)
            d_choice = input(f"\nВыберите номер Направления (1-{limit}) или 0 для Назад: ").strip()

            if d_choice == "0":
                return None, None
            if not d_choice or not d_choice.isdigit():
                return None, None

            d_idx = int(d_choice) - 1
            if 0 <= d_idx < len(directions):
                target_dir = directions[d_idx]
            elif allow_new and d_idx == len(directions):
                target_dir = input("Введите название НОВОГО Направления: ").strip()
            else:
                return None, None

        if not target_dir:
            return None, None

        # --- Шаг 2: Подобъект ---
        if target_dir in db and db[target_dir]:
            sub_objs = list(db[target_dir].keys())
            print(f"\nДоступные Подобъекты для '{target_dir}':")
            for idx, s in enumerate(sub_objs, 1):
                print(f" {idx}. {s}")
            if allow_new:
                print(f" {len(sub_objs) + 1}. [Создать НОВОЙ Подобъект]")

            limit = len(sub_objs) + 1 if allow_new else len(sub_objs)
            s_choice = input(f"Выберите номер Подобъекта (1-{limit}) или 0 для Назад: ").strip()

            if s_choice == "0":
                return None, target_dir
            if not s_choice or not s_choice.isdigit():
                return None, None

            s_idx = int(s_choice) - 1
            if 0 <= s_idx < len(sub_objs):
                target_sub = sub_objs[s_idx]
            elif allow_new and s_idx == len(sub_objs):
                target_sub = input("Введите название НОВОГО Подобъекта: ").strip()
            else:
                return None, None

            if not target_sub:
                return None, None
            return target_dir, target_sub

        # если направлений в базе нет/пусто
        if allow_new:
            target_sub = input("Введите название Подобъекта: ").strip()
            if target_sub:
                return target_dir, target_sub

        return None, None

def menu_add_record():
    print("\n>> ДОБАВЛЕНИЕ НОВОЙ ВЕТКИ СТРУКТУРЫ")
    db = db_core.load_db()

    target_dir, target_sub = select_hierarchy_target(db, allow_new=True)
    if not target_dir or not target_sub:
        return

    while True:
        print("\nВыберите Месяц из календаря:")

        active_months = []
        if target_dir in db and target_sub in db[target_dir]:
            if isinstance(db[target_dir][target_sub], dict):
                active_months = list(db[target_dir][target_sub].keys())

        for i, m_name in enumerate(db_core.ALL_YEAR_MONTHS, 1):
            marker = " [УЖЕ ЕСТЬ]" if m_name in active_months else ""
            print(f" {i}. {m_name}{marker}")

        mth_choice = input("\nВведите номер месяца (1-12) или '0' для отмены: ").strip()
        if mth_choice == "0":
            return

        if not mth_choice or not mth_choice.isdigit():
            print(" ❌ [ОШИБКА] Введите число от 1 до 12!")
            continue

        mth_idx = int(mth_choice) - 1
        if mth_idx < 0 or mth_idx >= 12:
            print(" ❌ [ОШИБКА] Номер должен быть от 1 до 12!")
            continue

        month = db_core.ALL_YEAR_MONTHS[mth_idx]

        if target_dir in db and target_sub in db[target_dir] and month in db[target_dir][target_sub]:
            print(f"\n ⚠ [ВНИМАНИЕ] Период '{month}' УЖЕ существует у этого объекта!")
            print(" Используйте Главное меню -> Пункт 3 для изменения его данных.")
            input("\nНажмите Enter...")
            return

        break

    if target_dir not in db:
        db[target_dir] = {}
    if target_sub not in db[target_dir]:
        db[target_dir][target_sub] = {}

    db[target_dir][target_sub][month] = {"sum": 0.0, "status": {"value": "", "date": ""}}
    db_core.save_db(db)
    db_core.update_config_months(month)
    print(f" [УСПЕХ] Период '{month}' успешно добавлен в базу!")

