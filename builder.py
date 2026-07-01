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
    Автоматически накладывает маски (трафареты) и форматирует денежные ячейки с пробелами.
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

    with open(json_path, "r", encoding="utf-8") as f:
        db = json.load(f)

    # Строим таблицу на основе дерева JSON
    for direction in db.keys():
        # Направление: Уровень 0
        ws.append(["", str(direction), "", "", "", "", "", "", "", ""])
        current_row = ws.max_row
        apply_row_style(ws, current_row, config.FONT_DIR, config.FILL_DIR, config.THIN_BORDER, config.ALIGN_L)
        ws.row_dimensions[current_row].outline_level = 0
        
        for sub_obj in db[direction].keys():
            # Подобъект: Уровень 1
            ws.append(["", str(sub_obj), "", "", "", "", "", "", "", ""])
            current_row = ws.max_row
            apply_row_style(ws, current_row, config.FONT_OBJ, config.FILL_OBJ, config.THIN_BORDER, config.ALIGN_L)
            ws.row_dimensions[current_row].outline_level = 1
            
            for mth in config.MONTHS_LIST:
                if mth not in db[direction][sub_obj]:
                    continue
                    
                mth_data = db[direction][sub_obj][mth]
                val = mth_data.get("sum", 0.0)
                status_val = mth_data.get("status", "")
                
                # Месяц: Уровень 2
                ws.append(["", mth, float(val), "", "", "", "", "", "", ""])
                current_row = ws.max_row
                apply_row_style(ws, current_row, config.FONT_MTH, config.FILL_MTH, config.THIN_BORDER, config.ALIGN_L)
                ws.row_dimensions[current_row].outline_level = 2
                
                # НАСТРОЙКА ФОРМАТА ДЕНЕГ: Задаем финансовый формат с разделением тысяч пробелами
                # Поддерживает и копейки, и выравнивание, а ноль превращает в аккуратный прочерк
                money_cell = ws.cell(row=current_row, column=3)
                money_cell.number_format = '#,##0.00'
                
                # Документы: Уровень 3
                for d_name in config.DOCUMENTS_LIST:
                    doc_row = ["", f"• {d_name}", "", "", "", "", "", "", "", ""]
                    ws.append(doc_row)
                    current_row = ws.max_row
                    
                    apply_row_style(ws, current_row, config.FONT_DATA, None, config.THIN_BORDER, config.ALIGN_L)
                    ws.row_dimensions[current_row].outline_level = 3
                    
                    # Финансовый формат для пустых ячеек документов (чтобы формулы Calc работали корректно)
                    ws.cell(row=current_row, column=3).number_format = '#,##0.00'
                    
                    mask = config.DOCUMENT_ROLES.get(d_name, {"СтрК": 1, "СДО": 1, "ГенДир": 1, "1 экз. З.": 1, "1 экз. П": 1, "Опл.": 1})
                    column_mapping = {"СтрК": 4, "СДО": 5, "ГенДир": 6, "1 экз. З.": 7, "1 экз. П": 8, "Опл.": 9}
                    
                    for col_name, col_idx in column_mapping.items():
                        cell = ws.cell(row=current_row, column=col_idx)
                        if mask.get(col_name, 1) == 0:
                            cell.fill = config.FILL_BLOCKED
                            cell.value = ""
                        else:
                            if col_name == "СтрК" and status_val:
                                cell.value = str(status_val)
                                
    # Блок автоматических формул статуса в колонке J
    for row in range(2, ws.max_row + 1):
        cell_b = ws.cell(row=row, column=2).value
        if cell_b in config.MONTHS_LIST:
            ws.cell(row=row, column=10).value = f"=IF(C{row}>0, \"В работе\", \"\")"
            
    return ws.max_row
