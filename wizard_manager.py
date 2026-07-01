import os
import json
import config
import git_deployer

def load_db():
    json_path = "database.json"
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_db(db):
    json_path = "database.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

def print_data():
    db = load_db()
    print("\n=== ТЕКУЩАЯ БАЗА ДАННЫХ ПРОЕКТА ===")
    if not db:
        print("База данных пуста.")
        return
    for direction, sub_objs in db.items():
        print(f"\n Направление: {direction}")
        for sub_obj, months in sub_objs.items():
            print(f"   └─ Подобъект: {sub_obj}")
            for mth, data in months.items():
                print(f"        ├─ {mth}: {data.get('sum', 0):,} руб. | Статус СтрК: {data.get('status', 'Нет')}")
    print("====================================")

def edit_month_sum():
    print("\n>> РЕДАКТИРОВАНИЕ СУММЫ МЕСЯЦА")
    db = load_db()
    if not db:
        print(" База данных пуста.")
        return

    # 1. Выбор Направления
    directions = list(db.keys())
    print("\nДоступные Направления:")
    for idx, d in enumerate(directions, 1):
        print(f"  {idx}. {d}")
    d_choice = input("\nВыберите номер Направления (или Enter для отмены): ").strip()
    if not d_choice or not d_choice.isdigit(): return
    d_idx = int(d_choice) - 1
    if d_idx < 0 or d_idx >= len(directions): return
    target_dir = directions[d_idx]

    # 2. Выбор Подобъекта
    sub_objs = list(db[target_dir].keys())
    print(f"\nДоступные Подобъекты для '{target_dir}':")
    for idx, s in enumerate(sub_objs, 1):
        print(f"  {idx}. {s}")
    s_choice = input("\nВыберите номер Подобъекта: ").strip()
    if not s_choice or not s_choice.isdigit(): return
    s_idx = int(s_choice) - 1
    if s_idx < 0 or s_idx >= len(sub_objs): return
    target_sub = sub_objs[s_idx]

    # 3. Выбор Месяца
    months = list(db[target_dir][target_sub].keys())
    print(f"\nДоступные Месяцы для '{target_sub}':")
    for idx, m in enumerate(months, 1):
        print(f"  {idx}. {m} (Текущая сумма: {db[target_dir][target_sub][m].get('sum', 0):,} руб.)")
    m_choice = input("\nВыберите номер Месяца: ").strip()
    if not m_choice or not m_choice.isdigit(): return
    m_idx = int(m_choice) - 1
    if m_idx < 0 or m_idx >= len(months): return
    target_mth = months[m_idx]

    # 4. Ввод новой суммы
    new_sum_str = input(f"Введите новую сумму для {target_mth} (цифрами, без пробелов): ").strip()
    try:
        new_sum = int(new_sum_str)
        db[target_dir][target_sub][target_mth]["sum"] = new_sum
        save_db(db)
        print(f" [УСПЕХ] Сумма успешно обновлена в базе данных для {target_mth}: {new_sum:,} руб.")
    except ValueError:
        print(" [ОШИБКА] Сумма должна быть числом!")

def add_new_record():
    print("\n>> ДОБАВЛЕНИЕ НОВОЙ ЗАПИСИ (СТРУКТУРЫ)")
    db = load_db()
    
    direction = input("Введите Направление (например, 01_АНАПА (Таманская)): ").strip()
    if not direction: return
    sub_obj = input("Введите Подобъект (например, 01_271_КН): ").strip()
    if not sub_obj: return
    month = input("Введите Месяц (например, Апрель): ").strip()
    if not month: return
    
    if direction not in db: db[direction] = {}
    if sub_obj not in db[direction]: db[direction][sub_obj] = {}
    
    db[direction][sub_obj][month] = {"sum": 0, "status": ""}
    save_db(db)
    print(" [УСПЕХ] Новая ветка структуры успешно добавлена в базу данных!")

def run_wizard():
    while True:
        print("\n--- СМАРТ-ПОМОЩНИК УПРАВЛЕНИЯ ТРЕКЕРОМ (JSON БАЗА) ---")
        print("1. Посмотреть текущую базу данных (Дерево)")
        print("2. Добавить новую ветку структуры (Объект/Месяц)")
        print("3. Изменить сумму существующего месяца (Ввод бюджетов)")
        print("4. Сгенерировать Excel (с запросом отправки на GitHub)")
        print("5. Выйти из помощника")
        choice = input("Выберите действие (1-5): ").strip()
        
        if choice == "1":
            print_data()
        elif choice == "2":
            add_new_record()
        elif choice == "3":
            edit_month_sum()
        elif choice == "4":
            # Вызываем наш движок развертывания
            success = git_deployer.run_production_pipeline(session_added_rows=["Обновление базы данных трекера"])
        elif choice == "5":
            print("До свидания!"); break
        else:
            print(" Неверный ввод.")

if __name__ == "__main__":
    run_wizard()
