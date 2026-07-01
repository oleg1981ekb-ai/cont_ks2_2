import json
import os

def log_cell_change(event):
    """
    Глобальный макрос LibreOffice Calc. Срабатывает при сохранении документа.
    Сканирует активный лист, собирает суммы месяцев и пишет в changes.json.
    """
    try:
        model = event.Source
        sheet = model.CurrentController.ActiveSheet
        
        valid_months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", 
                        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        
        changes = {}
        project_dir = "/Users/test/Desktop/cont_ks2_2"
        json_path = os.path.join(project_dir, "changes.json")
        
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    changes = json.load(f)
            except:
                pass

        direction = ""
        sub_obj = ""
        
        for r_idx in range(1, 300):
            lbl = str(sheet.getCellByPosition(1, r_idx).String).strip()
            if not lbl:
                continue
                
            if lbl.startswith("01_") or lbl.startswith("02_"):
                direction = lbl
                sub_obj = "" 
                continue
                
            if (lbl.startswith("•") or lbl.startswith("Акт") or lbl.startswith("Справка") or 
                lbl.startswith("Счет") or lbl == "Наименование объекта / Месяц / Документ"):
                continue
                
            if lbl in valid_months:
                val_cell = sheet.getCellByPosition(2, r_idx).Value
                if direction and sub_obj:
                    storage_key = f"{direction}||{sub_obj}||{lbl}"
                    changes[storage_key] = {
                        "direction": direction,
                        "sub_obj": sub_obj,
                        "month": lbl,
                        "sum": float(val_cell) if val_cell else 0.0
                    }
            else:
                sub_obj = lbl

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(changes, f, ensure_ascii=False, indent=4)

    except Exception:
        pass

g_exportedScripts = (log_cell_change,)
