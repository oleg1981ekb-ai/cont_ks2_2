import db_core
import wizard_menus
import git_deployer

def print_data():
    db = db_core.load_db()
    print("\n=== ТЕКУЩАЯ БАЗА ДАННЫХ ПРОЕКТА ===")
    if not db:
        print("База данных пуста.")
        return
    for direction, sub_objs in db.items():
        print(f"\n Направление: {direction}")
        for sub_obj, months in sub_objs.items():
            print(f"   └─ Подобъект: {sub_obj}")
            for mth, data in months.items():
                print(f"        ├─ {mth}: {db_core.fmt_money(data.get('sum', 0))} руб. | Статус СтрК: {data.get('status', 'Нет')}")
    print("====================================")

def run_wizard():
    while True:
        print("\n--- СМАРТ-ПОМОЩНИК УПРАВЛЕНИЯ ТРЕКЕРОМ (JSON БАЗА) ---")
        print("1. Посмотреть текущую базу данных (Дерево)")
        print("2. Добавить новую ветку структуры (Объект/Месяц)")
        print("3. Внести изменения в таблицу")
        print("4. Сгенерировать Excel (с запросом отправки на GitHub)")
        print("5. Выйти из помощника")
        choice = input("Выберите действие (1-5): ").strip()
        
        if choice == "1":
            print_data()
        elif choice == "2":
            wizard_menus.menu_add_record()
        elif choice == "3":
            wizard_menus.menu_edit_data()
        elif choice == "4":
            git_deployer.run_production_pipeline(session_added_rows=["Обновление базы данных трекера"])
        elif choice == "5":
            print("До свидания!"); break
        else:
            print(" Неверный ввод.")

if __name__ == "__main__":
    run_wizard()
