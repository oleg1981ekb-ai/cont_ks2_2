import db_core
import config

def print_data():
    """Вывод красивого и детального текстового дерева базы данных в консоль."""
    print("\n================ ТЕКУЩАЯ СТРУКТУРА БАЗЫ ДАННЫХ ================")
    db = db_core.load_db()
    if not db:
        print("База данных пуста или файл database.json отсутствует.")
        print("===============================================================")
        return

    colors = {1: "🟢 Зеленый", 2: "🟡 Желтый", 3: "🔴 Красный", "": "Нет", "1": "🟢 Зеленый", "2": "🟡 Желтый", "3": "🔴 Красный"}

    for direction in db.keys():
        print(f"\n📍 Направление: {direction}")
        for sub_obj in db[direction].keys():
            print(f"   └─ 🏢 Подобъект: {sub_obj}")
            
            raw_months = list(db[direction][sub_obj].keys())
            available_months = [m for m in db_core.ALL_YEAR_MONTHS if m in raw_months]
            
            for m in raw_months:
                if m not in available_months:
                    available_months.append(m)
            
            for mth in available_months:
                mth_data = db[direction][sub_obj][mth]
                # ИСПРАВЛЕНО: Строгое форматирование разрядов пробелами для дерева консоли
                fmt_sum = db_core.fmt_money(mth_data.get("sum", 0))
                status_raw = mth_data.get("status", "")

                if isinstance(status_raw, dict) and "value" not in status_raw:
                    print(f"        ├─ 📅 {mth}: {fmt_sum} руб. | Статус СтрК: [Раздельный по док.]")
                    for d_name in config.DOCUMENTS_LIST:
                        mask = config.DOCUMENT_ROLES.get(d_name, {})
                        if mask.get("СтрК", 1) == 1:
                            doc_status = status_raw.get(d_name, {})
                            val = doc_status.get("value", "") if isinstance(doc_status, dict) else ""
                            dt = doc_status.get("date", "") if isinstance(doc_status, dict) else ""
                            print(f"           ├── 📄 {d_name} -> {colors.get(val, 'Нет')}{f' ({dt})' if dt else ''}")
                else:
                    val = status_raw.get("value", "") if isinstance(status_raw, dict) else status_raw
                    dt = status_raw.get("date", "") if isinstance(status_raw, dict) else ""
                    print(f"        ├─ 📅 {mth}: {fmt_sum} руб. | Статус СтрК: {colors.get(val, 'Нет')}{f' ({dt})' if dt else ''}")
                    
    print("\n===============================================================")
