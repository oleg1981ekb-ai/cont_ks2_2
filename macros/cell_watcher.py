import json
import os

def log_cell_change(event):
    """
    Макрос LibreOffice Calc. Срабатывает при изменении содержимого ячейки.
    Записывает измененную сумму месяца во временный файл проекта changes.json.
    """
    try:
        # Проверяем, что событие произошло на листе таблицы
        sheet = event.Spreadsheet
        
        # Получаем координаты измененной ячейки (отсчет с 0)
        column_idx = event.CellAddress.Column  # Столбец
        row_idx = event.CellAddress.Row        # Строка
        
        # Нам нужен только столбец C (индекс 2) — Сумма (руб.)
        if column_idx != 2:
            return

        # Считываем новое значение суммы и текстовый маркер строки (название месяца/объекта)
        new_value = event.Value
        row_label = sheet.getCellByPosition(1, row_idx).String  # Столбец B (индекс 1)
        
        # Исключаем служебные строки (шапку, пустые ячейки или строки главных объектов)
        if not row_label or "Сумма" in row_label or "№" in row_label:
            return

        # Путь к файлу изменений в папке проекта
        project_dir = "/Users/test/Desktop/cont_ks2_2"
        json_path = os.path.join(project_dir, "changes.json")
        
        # Загружаем существующую историю изменений, если она есть
        changes = {}
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    changes = json.load(f)
            except:
                pass
                
        # Сохраняем или обновляем сумму для конкретной строки
        changes[str(row_idx)] = {
            "label": row_label.strip(),
            "sum": float(new_value) if new_value else 0.0
        }
        
        # Записываем обновленный буфер обратно на диск
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(changes, f, ensure_ascii=False, indent=4)
            
    except Exception as e:
        # В случае ошибки внутри макроса мы не прерываем работу LibreOffice
        pass

# Регистрируем функцию в LibreOffice, чтобы она была видна в меню выбора макросов
g_exportedScripts = (log_cell_change,)
