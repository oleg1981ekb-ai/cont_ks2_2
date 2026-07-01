import os
import json
import config

ALL_YEAR_MONTHS = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]

def fmt_money(value):
    """Форматирует число с пробелами и русской запятой для копеек (русский стандарт)."""
    try:
        val_float = float(value)
        if val_float.is_integer():
            return f"{int(val_float):_}".replace("_", " ")
        else:
            parts = f"{val_float:.2f}".split(".")
            thousand_part = f"{int(parts[0]):_}".replace("_", " ")
            return f"{thousand_part},{parts[1]}"
    except:
        return str(value)

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

def update_config_months(new_month):
    """Автоматически добавляет новый месяц в config.py с сохранением хронологии."""
    if new_month not in config.MONTHS_LIST:
        config_path = "config.py"
        with open(config_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        updated_months = [m for m in ALL_YEAR_MONTHS if m in config.MONTHS_LIST or m == new_month]
        old_line_repr = f"MONTHS_LIST = {repr(config.MONTHS_LIST)}"
        new_line_repr = f"MONTHS_LIST = {repr(updated_months)}"
        
        if old_line_repr in code:
            code = code.replace(old_line_repr, new_line_repr)
        else:
            import re
            code = re.sub(r"MONTHS_LIST\s*=\s*\[.*?\]", new_line_repr, code)
            
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(code)
        print(f" [СИНХРОНИЗАЦИЯ] Месяц '{new_month}' добавлен в хронологический список config.py")
