import openpyxl
import json
import os
import config

def apply_row_style(ws, row_idx, font, fill, border, alignment=None):
    """Применяет стили оформления к указанной строке таблицы."""
    for col in range(1, ws.max_column + 1):
        cell = ws.cell(row=row_idx, column=col)
        if font: cell.font = font
        if fill: cell.fill = fill
        if border: cell.border = border
        if alignment: cell.alignment = alignment

def build_structure(ws, mock_data=None, saved_statuses=None, saved_sums=None):
    """
    Генерирует структуру табличной части напрямую из базы данных database.json.
    Сохраняет уровни структуры (Outline) и все пастельные стили оформления.
    """
    # Настройка кнопок группировки СВЕРХУ над блоками
    ws.sheet_properties.outlinePr.summaryBelow = False

    # Добавляем шапку таблицы, если лист пустой
    if ws.max_row == 1 and ws.cell(row=1, column=1).value is None:
        ws.append(config.HEADERS)
        apply_row_style(ws, 1, config.FONT_HDR, config.FILL_HDR, config.THIN_BORDER, config.ALIGN_C)
    
    json_path = "database.json"
    if not os.path.exists(json_path):
        print(" [ОШИБКА] Файл базы данных database.json не найден!")
        return ws.max_row

    # Загружаем данные из нашей иерархической базы
    with open(json_path, "r", encoding="utf-8") as f:
        db = json.load(f)

    # Строим таблицу на основе дерева JSON
    for direction in db.keys():
        # Направление: Уровень структуры 0
        ws.append(["", str(direction), "", "", "", "", "", "", "", ""])
        current_row = ws.max_row
        apply_row_style(ws, current_row, config.FONT_DIR, config.FILL_DIR, config.THIN_BORDER, config.ALIGN_L)
        ws.row_dimensions[current_row].outline_level = 0
        
        for sub_obj in db[direction].keys():
            # Подобъект: Уровень структуры 1
            ws.append(["", str(sub_obj), "", "", "", "", "", "", "", ""])
            current_row = ws.max_row
            apply_row_style(ws, current_row, config.FONT_OBJ, config.FILL_OBJ, config.THIN_BORDER, config.ALIGN_L)
            ws.row_dimensions[current_row].outline_level = 1
            
            for mth in config.MONTHS_LIST:
                # Если этого месяца нет в базе для данного объекта — пропускаем
                if mth not in db[direction][sub_obj]:
                    continue
                    
                mth_data = db[direction][sub_obj][mth]
                val = mth_data.get("sum", 0)
                status_val = mth_data.get("status", "")
                
                # Месяц: Уровень структуры 2 (Сумма пишется только сюда)
                ws.append(["", mth, val, "", "", "", "", "", "", ""])
                current_row = ws.max_row
                apply_row_style(ws, current_row, config.FONT_MTH, config.FILL_MTH, config.THIN_BORDER, config.ALIGN_L)
                ws.row_dimensions[current_row].outline_level = 2
                
                # Документы: Уровень структуры 3
                for d_name in config.DOCUMENTS_LIST:
                    # Исторический статус (извлекаем сохраненное значение СтрК из базы, остальные пустые)
                    s0 = str(status_val) if status_val else ""
                    
                    doc_row = ["", f"• {d_name}", "", s0, "", "", "", "", "", ""]
                    ws.append(doc_row)
                    current_row = ws.max_row
                    apply_row_style(ws, current_row, config.FONT_DATA, None, config.THIN_BORDER, config.ALIGN_L)
                    ws.row_dimensions[current_row].outline_level = 3
                    
    # Блок восстановления автоматических формул статуса в колонке J
    for row in range(2, ws.max_row + 1):
        cell_b = ws.cell(row=row, column=2).value
        if cell_b in config.MONTHS_LIST:
            ws.cell(row=row, column=10).value = f"=IF(C{row}>0, \"В работе\", \"\")"
            
    return ws.max_row
